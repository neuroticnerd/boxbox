
"""
need to check out
https://github.com/VRGhost/vbox
"""
import re
import os

from subprocess import CalledProcessError
from .shellcommand import ShellCommand
from . import utils

re_sctl = r'(?P<sctl>.{0,}?)\s*\((?P<device>\d+),\s*(?P<port>\d+)\)\s*:'
re_vmdk = r'\s*(?P<vmdkfile>.{0,}?)\s*'
re_uuid = r'\(UUID:\s*(?P<uuid>[\w\-]+)\)\s*'
re_vm = re.compile(r'^{0}{1}{2}$'.format(re_sctl, re_vmdk, re_uuid))


class VMInfo(object):
    pass


def get_vm_info(vmname):
    showvm = 'VBoxManage showvminfo {vmname}'
    command = ShellCommand(showvm, vmname=vmname).grep(vmname).grep('vmdk')
    utils.debug(command.prompt)
    utils.debug(command)
    vminfomatch = re_vm.match(command.out)
    if vminfomatch is None:
        utils.error('ERROR: cannot extract VM data for {0}'.format(vmname))
        return None
    vminfo = vminfomatch.groupdict()
    vm = VMInfo()
    vm.hddfile = vminfo['vmdkfile']
    vm.basedir = os.path.dirname(vm.hddfile)
    vm.hdduuid = vminfo['uuid']
    vm.hddsctl = vminfo['sctl']
    vm.sctldev = vminfo['device']
    vm.sctlport = vminfo['port']
    return vm


def remove_vm_hdd(vmuuid, vminfo, hdduuid):
    cmd = ' '.join([
        'VBoxManage',
        'storageattach {vm}',
        '--storagectl {sctl}',
        '--medium {med}',
        '--device {dev}',
        '--port {port}',
        '--type hdd',
    ])
    command = ShellCommand(
        cmd,
        vm=vmuuid,
        sctl=vminfo.hddsctl,
        med='none',
        dev=vminfo.sctldev,
        port=vminfo.sctlport
        )
    utils.debug(command.prompt)
    result = command.out
    if result:
        utils.debug(result)
    return result


def set_vm_hdd(vm, sctl=None, img=None, dev=0, port=0):
    default = '~/VirtualBox VMs/{0}/box-disk1.vmdk'
    sctl = sctl if sctl else 'SATAController'
    img = img if img else os.path.expanduser(default.format(vm))
    cmd = ' '.join([
        'VBoxManage',
        'storageattach {vm}',
        '--storagectl {sctl}',
        '--medium "{vmdk}"',
        '--device {dev}',
        '--port {port}',
        '--type hdd',
    ])
    command = ShellCommand(cmd, vm=vm, sctl=sctl, vmdk=img, dev=dev, port=port)
    utils.debug(command.prompt)
    result = command.out
    if result:
        utils.debug(result)
    return result
