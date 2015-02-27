
import logging
import os
import sys
import click
import json
import yaml

from collections import OrderedDict

from .exceptions import BoxBoxError
from .utils import nl, log, debug, error
from .tasks import TaskRunner
from . import tasks


"""
http://www.quora.com/What-is-the-easiest-command-line-interface-library-for-Python-2-7
http://docs.python-guide.org/en/latest/scenarios/cli/
https://news.ycombinator.com/item?id=7639214
http://click.pocoo.org/3/
"""
help_cfg = 'configuration file location'
help_loglevel = 'loglevel options are mutually exclusive and set logging level'
help_logfile = 'log output to the given file path (file will be truncated)'
help_ver = 'print the boxbox version and exit'
help_warn = ''.join([
    'This tool has the potential to seriously mess up',
    ' your VirtualBox configuration if certain errors occur.',
    ' An in-depth knowledge of VirtualBox may be required to resolve',
    ' the resulting misconfiguration manually.',
    ' Are you sure you wish to continue?',
    ])

@click.group(invoke_without_command=True, chain=True)
#@click.confirmation_option(prompt=help_warn)
@click.option(
    '-c', '--config', 'config',
    type=click.File('rb'),
    help=help_cfg)
@click.option(
    '-l', '--level', 'loglevel',
    type=click.Choice(['debug', 'info', 'warning', 'error']),
    default='info',
    help=help_loglevel)
@click.option(
    '-f', '--log', 'logfile',
    type=click.Path(),
    help=help_logfile)
@click.option(
    '-v', '--version', 'version',
    is_flag=True,
    default=False,
    help=help_ver)
def CLI(config, loglevel, logfile, version):
    loglevel = getattr(logging, loglevel.upper())
    logging.basicConfig(format='%(message)s', level=loglevel)
    #logging.debug('CWD="{0}"'.format(os.getcwd()))


@click.command()
@click.argument('runfile', type=click.File('rb'), default='boxbox.json')
def run(runfile):
    tasks = []
    debug('task config="{0}"'.format(runfile))
    log('reading task configuration...')
    try:
        config = yaml.safe_load(runfile)
        #raise ValueError(json.dumps(config, indent=2))
    except:
        debug('ValueError occurred during config processing:', exc_info=True)
        raise BoxBoxError('invalid task file formatting!')
    """
    try:
        config = json.loads(runfile.read(), object_pairs_hook=OrderedDict)
        debug(json.dumps(config, indent=2))
    except ValueError:
        debug('ValueError occurred during config processing:', exc_info=True)
        raise BoxBoxError('invalid task file formatting!')
    """
    try:
        iter(config)
    except:
        config = config['tasks']
    for conf in config:
        tasks.append(TaskRunner(conf))
    log('config validated; {0} tasks defined.'.format(len(tasks)))
    for task in tasks:
        task.run()


@click.command()
@click.argument('host')
@click.argument('user', required=False, default=None)
@click.option(
    '--full', 'full',
    is_flag=True,
    default=False,
    help='also performs dd for full disk zero')
def prepare(host, user, full):
    debug('performing disk zero: {0}'.format(full))
    try:
        user, host = host.split('@')
    except:
        if user is None:
            raise BoxBoxError('user must also be specified with host')
    tasks.prepare(host, user, full)


@click.command()
@click.argument('vmname')
@click.argument('boxloc', type=click.Path(exists=True))
@click.option(
    '--fake', 'fake',
    is_flag=True,
    default=False,
    help='do not actually modify the relevant VMs')
@click.option(
    '--update', 'update',
    is_flag=True,
    default=True,
    help='update the VM to use the new clone as its hdd')
def shrink(vmname, boxloc, fake, update, boxname=None, uuid=None):
    boxname = tasks.shrink(vmname, update=update, fake=fake)


@click.command()
@click.argument('name')
@click.argument('boxloc', type=click.Path())
@click.argument('boxname')
def package(name, boxloc, boxname):
    tasks.package(name, os.path.join(boxloc, boxname))


@click.command()
def upload():
    tasks.box_upload()


CLI.add_command(run)
CLI.add_command(prepare)
CLI.add_command(shrink)
CLI.add_command(package)
CLI.add_command(upload)
