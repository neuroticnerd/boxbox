
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

    boxloc = os.path.expanduser('~/git/jlor/boxes')
    host = 'streams.junyo.vm'
    name = 'streams'
    user = 'vagrant'

    # run the program
    #tasks.prepare(host, user)
    #boxname = tasks.shrink(name, update=True, fake=False)
    #tasks.package(name, os.path.join(boxloc, boxname))
    #package_lzma()
    #box_upload()


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
def vbox():
    logging.error('here is the vbox subcommand')


@click.command()
def vagrant():
    logging.error('here is the vagrant subcommand')


CLI.add_command(run)
#CLI.add_command(vbox)
#CLI.add_command(vagrant)
