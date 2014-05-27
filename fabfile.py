from fabric.api import local, cd
import os
import time
import datetime
from fabric.operations import sudo
from fabric.state import env
from fabric.context_managers import settings


PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
manage_py = os.path.join(PROJECT_ROOT, 'manage.py')

env.hosts = ['getstream.io']

env.user = 'stream'
env.forward_agent = True


def publish(test='no'):
    '''
    The whole merging stuff etc
    '''
    if test == 'yes':
        validate()
    tag = get_new_tag()
    time.sleep(1)
    merge_master()
    local('git tag %s' % tag)
    local('git push origin production %s' % tag)
    time.sleep(1)
    local('git checkout master')


def merge_master():
    # update our local data
    local('git fetch --all')
    time.sleep(1)
    # update with the changes
    local('git checkout production')
    time.sleep(1)
    # merge the remote branch
    local('git merge origin/production')
    time.sleep(1)
    # now merge master
    local('git merge origin/master')


def get_new_tag():
    tag_command = local('git tag', capture=True)

    tags = [l.strip().replace('_', '-')
            for l in tag_command.split('\n') if l.startswith('20')]
    tags_dict = dict.fromkeys(tags)
    tag_format = unicode(datetime.date.today()) + '-v%s'
    version = 1

    while tag_format % version in tags_dict:
        version += 1

    new_tag = tag_format % version

    return new_tag


def validate():
    with cd(PROJECT_ROOT):
        local(
            'pep8 --exclude=migrations --ignore=E501,E225 .')
        local('%s test' % manage_py)


def clean():
    # all dirs which contain python code
    python_dirs = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        python_dir = any(f.endswith('.py') for f in files)
        if python_dir:
            python_dirs.append(root)
    for d in python_dirs:
        print d
        local('bash -c "autopep8 -i %s/*.py"' % d)


def docs():
    local('sphinx-build -Eav docs html')
