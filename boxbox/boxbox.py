
import logging
import os
import sys

from . import utils
from . import tasks


"""
http://www.quora.com/What-is-the-easiest-command-line-interface-library-for-Python-2-7
"""


def CLI():
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)
    logging.debug('__package__ = "{0}"'.format(__package__))

    warnmsg = [
        'This script has the potential to really mess up',
        ' your VirtualBox configuration if certain errors occur;',
        ' an in-depth knowledge of VirtualBox may be required to resolve',
        ' these error manually. Are you sure you wish to continue?',
        ]
    if not utils.yesno(''.join(warnmsg), 'yes', 'no'):
        sys.exit(0)

    # vars
    boxloc = os.path.expanduser('~/git/jlor/boxes')
    host = 'streams.junyo.vm'
    name = 'streams'
    user = 'vagrant'

    # run the program
    #tasks.prepare(host, user)
    boxname = tasks.shrink(name, update=True, fake=False)
    #tasks.package(name, os.path.join(boxloc, boxname))
    #package_lzma()
    #box_upload()
