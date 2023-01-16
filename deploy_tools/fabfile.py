from fabric import task
import os
import random


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
    current_commit = c.run(f'cd {source_folder} && git log -n 1 --format=%H')
    c.run(f'cd {source_folder} && git reset --hard {current_commit.stdout.strip()}')

def _create_or_update_dotenv(c, source_folder):
    if not os.path.exists('.env'):
        print("Creating a new local .env")
        with open('.env', 'w') as f:
            f.write('DJANGO_DEBUG_FALSE=y\r')
            f.write(f'SITENAME={c.host}\r')
    with open('.env', 'r') as f:
        my_env = f.read()
    if 'DJANGO_SECRET_KEY' not in my_env:  
        new_secret = ''.join(random.SystemRandom().choices(  
            'abcdefghijklmnopqrstuvwxyz0123456789', k=50
        ))
        with open('.env', 'a') as f:
            f.write(f"DJANGO_SECRET_KEY={new_secret}\r")
    c.put('.env', f'{source_folder}')


def _update_service_files(c, source_folder):
    nginx_service_path = source_folder + '/deploy_tools/firmware_finder.nginx.conf'
    c.run(f"sed -i 's/\*\*SERVER NAME\*\*/{c.host}/g' {nginx_service_path}")
    c.run(f"sed -i 's/\*\*SITE NAME\*\*/{REPO_NAME}/g' {nginx_service_path}")


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


def _restart_service(c):
    c.run(f"sudo systemctl restart {REPO_NAME}.service")
