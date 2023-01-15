from fabric.contrib.files import append, exists, sed
from fabric.api import env, local, run
import random

REPO_URL = 'git@bitbucket.org:itsmagic/firmware_finder.git'


def deploy():
    site_folder = f'/home/{env.user}/sites/firmware_finder'
    source_folder = site_folder + '/source'
    _create_directory_structure_if_necessary(site_folder)
    _get_latest_source(source_folder)
    _create_or_update_dotenv()
    _update_service_files(source_folder, env.host)
    _update_virtualenv(source_folder)
    _update_static_files(source_folder)
    _update_database(source_folder)
    _restart_service()


def _create_directory_structure_if_necessary(site_folder):
    for subfolder in ('database', 'static', '.env', 'source'):
        run(f'mkdir -p {site_folder}/{subfolder}')


def _get_latest_source(source_folder):
    if exists(source_folder + '/.git'):
        run(f'cd {source_folder} && git fetch')
    else:
        run(f'git clone {REPO_URL} {source_folder}')
    current_commit = local("git log -n 1 --format=%H", capture=True)
    run(f'cd {source_folder} && git reset --hard {current_commit}')

def _create_or_update_dotenv():
    append('.env', 'DJANGO_DEBUG_FALSE=y')  
    append('.env', f'SITENAME={env.host}')
    current_contents = run('cat .env')  
    if 'DJANGO_SECRET_KEY' not in current_contents:  
        new_secret = ''.join(random.SystemRandom().choices(  
            'abcdefghijklmnopqrstuvwxyz0123456789', k=50
        ))
        append('.env', f'DJANGO_SECRET_KEY={new_secret}')


def _update_service_files(source_folder, site_name):
    nginx_service_path = source_folder + '/deploy_tools/firmware_finder.nginx.conf'
    sed(nginx_service_path,
        '\*\*ADDRESS HERE\*\*', site_name)
    sed(nginx_service_path,
        '\*\*USER NAME HERE\*\*', env.user)


def _update_virtualenv(source_folder):
    virtualenv_folder = source_folder + '/../.env' # maybe this needs work
    if not exists(virtualenv_folder + '/bin/pip'):
        run(f'python -m venv {virtualenv_folder}')
    run(f'{virtualenv_folder}/bin/pip install --upgrade pip')
    run(f'{virtualenv_folder}/bin/pip install --upgrade -r {source_folder}/requirements.txt')


def _update_static_files(source_folder): 
    run(
        f'cd {source_folder}'
        ' && ../.env/bin/python manage.py collectstatic --noinput'
    )


def _update_database(source_folder):
    run(
        f'cd {source_folder}'
        ' && ../.env/bin/python manage.py migrate --noinput'
    )


def _restart_service():
    run("sudo systemctl restart firmware_finder.service")

