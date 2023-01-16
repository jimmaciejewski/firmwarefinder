from fabric import task
import os
import random
import getpass


# Django project name
PROJECT_NAME = 'firmwarefinder'
# Git name
REPO_NAME = 'firmware_finder'

REPO_URL = f'git@bitbucket.org:itsmagic/{REPO_NAME}.git'

@task
def deploy(c):
    site_folder = f'/home/{c.user}/sites/{REPO_NAME}'
    source_folder = site_folder + '/source'
    _create_directory_structure_if_necessary(c, site_folder)
    _get_latest_source(c, source_folder)
    _create_or_update_dotenv(c, source_folder)
    _update_service_files(c, source_folder)
    _update_virtualenv(c, source_folder)
    _update_static_files(c, source_folder)
    _update_database(c, source_folder)
    _add_service(c, source_folder)
    _add_nginx_config(c, source_folder)
    _restart_service(c)



def _create_directory_structure_if_necessary(c, site_folder):
    for subfolder in ('database', 'static', 'source'):
        if c.run(f'test -d {site_folder}/{subfolder}', warn=True).failed:
            c.run(f'mkdir -p {site_folder}/{subfolder}')
            print(f'mkdir -p {site_folder}/{subfolder}')


def _get_latest_source(c, source_folder):
    if c.run(f'test -d {source_folder}/.git', warn=True).failed:
        print("No .git found")
        c.run(f'git clone {REPO_URL} {source_folder}')
    else:
        print("Found git fetching")
        c.run(f'cd {source_folder} && git fetch')
    c.run(f'cd {source_folder} && git reset --hard')
    c.run(f'cd {source_folder} && git pull')
    # current_commit = c.run(f'cd {source_folder} && git log -n 1 --format=%H')
    # c.run(f'cd {source_folder} && git reset --hard {current_commit.stdout.strip()}')

def _create_or_update_dotenv(c, source_folder):
    if c.run(f'test -f {source_folder}/../.env', warn=True).failed:
        print("Creating a .env")
        c.run(f'cd {source_folder} && echo DJANGO_DEBUG_FALSE=y > ../.env')

        c.run(f'cd {source_folder} && echo SITENAME={c.host} >> ../.env')
        new_secret = ''.join(random.SystemRandom().choices(  
            'abcdefghijklmnopqrstuvwxyz0123456789', k=50
        ))

        c.run(f'cd {source_folder} && echo DJANGO_SECRET_KEY={new_secret} >> ../.env')


def _update_service_files(c, source_folder):
    nginx_service_path = source_folder + '/deploy_tools/firmware_finder.nginx.conf'
    c.run(f"sed -i 's/\*\*SERVER NAME\*\*/{c.host}/g' {nginx_service_path}")
    c.run(f"sed -i 's/\*\*SITE NAME\*\*/{REPO_NAME}/g' {nginx_service_path}")

    service_path = source_folder + '/deploy_tools/firmware_finder.service'
    c.run(f"sed -i 's/\*\*PROJECT NAME\*\*/{PROJECT_NAME}/g' {service_path}")
    c.run(f"sed -i 's/\*\*SERVER NAME\*\*/{c.host}/g' {service_path}")
    c.run(f"sed -i 's/\*\*SITE NAME\*\*/{REPO_NAME}/g' {service_path}")

def _update_virtualenv(c, source_folder):
    virtualenv_folder = source_folder + '/../virtualenv' # maybe this needs work
    if c.run(f'test -f {virtualenv_folder}/bin/pip', warn=True).failed:
        c.run(f'python -m venv {virtualenv_folder}')
    c.run(f'{virtualenv_folder}/bin/pip install --upgrade pip')
    c.run(f'{virtualenv_folder}/bin/pip install --upgrade -r {source_folder}/requirements.txt')


def _update_static_files(c, source_folder): 
    c.run(f'cd {source_folder} && ../virtualenv/bin/python manage.py collectstatic --noinput')


def _update_database(c, source_folder):
    c.run(f'cd {source_folder} && ../virtualenv/bin/python manage.py migrate --noinput')


def _add_service(c, source_folder, force=False):
    if c.run(f'test -f /etc/systemd/system/{REPO_NAME}.service', warn=True).failed or force:
        # The service file doesn't exist, lets add it
        print("Adding service file")
        _get_sudo(c)
        c.sudo(f'cp {source_folder}/deploy_tools/{REPO_NAME}.service /etc/systemd/system/{REPO_NAME}.service', hide='stderr')
        c.sudo(f'systemctl enable {REPO_NAME}.service', hide='stderr')
        c.sudo(f'systemctl daemon-reload', hide='stderr')
        c.sudo(f'systemctl start {REPO_NAME}.service', hide='stderr')
        
def _add_nginx_config(c, source_folder, force=False):
    if c.run(f'test -f /etc/nginx/sites-available/{REPO_NAME}.nginx.conf', warn=True).failed or force:
        # The config file doesn't exist, lets add it
        print("Adding nginx config file")
        _get_sudo(c)
        c.sudo(f'cp {source_folder}/deploy_tools/{REPO_NAME}.nginx.conf /etc/nginx/sites-available/{REPO_NAME}.nginx.conf', hide='stderr')
        c.sudo(f'ln -sf /etc/nginx/sites-available/{REPO_NAME}.nginx.conf /etc/nginx/sites-enabled/', hide='stderr')
        check_config = c.sudo(f'nginx -t', hide='stderr')
        if check_config.stdout != "":
            print("NGINX config failed test, not restarting nginx")
            print(check_config)
        else:
            c.sudo(f'systemctl restart nginx', hide='stderr')

def _restart_service(c):
    c.run(f"sudo systemctl restart {REPO_NAME}.service")


def _get_sudo(c):
    if c.config.sudo.password == None:
        c.config.sudo.password = getpass.getpass(f"What is the sudo password for {c.user}?")
