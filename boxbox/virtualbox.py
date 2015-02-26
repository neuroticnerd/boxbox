
re_sctl = r'(?P<sctl>.{0,}?)\s*\((?P<device>\d+),\s*(?P<port>\d+)\)\s*:'
re_vmdk = r'\s*(?P<vmdkfile>.{0,}?)\s*'
re_uuid = r'\(UUID:\s*(?P<uuid>[\w\-]+)\)\s*'
re_vm = re.compile(r'^{0}{1}{2}$'.format(re_sctl, re_vmdk, re_uuid))
showvm = 'VBoxManage showvminfo {vmname}'


class VMInfo(object):
    pass


def get_vm_info():
    command = ShellCommand(showvm, vmname=vmname).grep(vmname).grep('vmdk')
    debug(command.prompt)
    debug(command)
    vminfomatch = re_vm.match(command.out)
    if vminfomatch is None:
        log('ERROR: cannot extract VM data')
        return
    vminfo = vminfomatch.groupdict()
    vm = VMInfo()
    vm.hddfile = vminfo['vmdkfile']
    vm.basedir = os.path.dirname(vm.hddfile)
    vm.hdduuid = vminfo['uuid']
    vm.hddsctl = vminfo['sctl']
    vm.sctldev = vminfo['device']
    vm.sctlport = vminfo['port']
    return vm


bootstrap script
json config
requirements
