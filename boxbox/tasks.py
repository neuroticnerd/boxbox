
import logging
import paramiko
import datetime
import time
import re
import json
import os

from subprocess import CalledProcessError
from .utils import task, log, warning, debug, nl, error
from .exceptions import BoxBoxError
from .shellcommand import ShellCommand as CMD
from .sshcommand import SSHCommand as SSHCMD
from .virtualbox import get_vm_info, remove_vm_hdd, set_vm_hdd
from .vagrant import vagrant_package as package

OPS = ('vagrant', 'virtualbox', 's3')


class TaskRunner(object):
    def __init__(self, config):
        self._cfg = config
        try:
            self.op = config['op']
            self.task = config['task']
        except (KeyError, TypeError):
            raise BoxBoxError(
                'invalid task configuration for\n{0}'.format(
                    json.dumps(config, indent=2)))
        if self.op == 'virtualbox':
            try:
                self.vmid = config['vmid']
                self.update = config.get('update', True)
                self.fake = config.get('fake', False)
            except KeyError:
                raise BoxBoxError('vmid is required (either uuid or name)')

    def run(self):
        if self.op == 'virtualbox':
            shrink(self.vmid, self.update, self.fake)


def prepare(host, user, full=False):
    """
    use paramiko for ssh into vagrant VM to prep it

    http://www.hashbangcode.com/blog/connecting-vagrant-box-without-vagrant-ssh-command
    http://jessenoller.com/blog/2009/02/05/ssh-programming-with-paramiko-completely-different
    http://docs.paramiko.org/en/latest/api/client.html
    http://stackoverflow.com/questions/15071924/authenticate-with-private-key-using-paramiko-transport-channel
    http://stackoverflow.com/questions/8144545/turning-off-logging-in-paramiko
    """
    logging.getLogger("paramiko").setLevel(logging.WARNING)

    commands = [
        'sudo apt-get clean',
        'sudo apt-get autoclean',
        'sudo apt-get autoremove',
    ]
    if full:
        log('note: also zeroing disk space using dd')
        commands.extend([
            'dd if=/dev/zero of=zerofile',
            'rm zerofile',
        ])
    vagrant_kfile = os.path.expanduser('~/.vagrant.d/insecure_private_key')
    vagrant_pkey = paramiko.RSAKey.from_private_key_file(vagrant_kfile)

    # minify the VM disk as much as possible
    task('prepare the VM for packaging')
    with paramiko.SSHClient() as ssh:
        """
        log('ensure {0} is running...'.format(host))
        v_up = CMD('vagrant up')
        debug(v_up.prompt)
        log(v_up.out)
        time.sleep(2)
        """
        try:
            ssh.load_system_host_keys()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=user, pkey=vagrant_pkey, timeout=10)
            whoami = SSHCMD(ssh, 'whoami', strip=True)
            log('{me}@{host}'.format(me=whoami, host=host))
            for command in commands:
                log(SSHCMD(ssh, command))
        except:
            raise
        """
        log('ensure {0} is halted...'.format(host))
        v_halt = CMD('vagrant halt')
        debug(v_halt.prompt)
        log(v_halt.out)
        """


def shrink(vmname, update=True, fake=False):
    task('condense VM hdd image')

    log('gathering required information...')
    """
    re_sctl = r'(?P<sctl>.{0,}?)\s*\((?P<device>\d+),\s*(?P<port>\d+)\)\s*:'
    re_vmdk = r'\s*(?P<vmdkfile>.{0,}?)\s*'
    re_uuid = r'\(UUID:\s*(?P<uuid>[\w\-]+)\)\s*'
    re_vm = re.compile(r'^{0}{1}{2}$'.format(re_sctl, re_vmdk, re_uuid))
    showvm = 'VBoxManage showvminfo {vmname}'
    command = CMD(showvm, vmname=vmname).grep(vmname).grep('vmdk')
    debug(command.prompt)
    debug(command)
    vminfomatch = re_vm.match(command.out)
    if vminfomatch is None:
        log('ERROR: cannot extract VM data')
        return
    vminfo = vminfomatch.groupdict()
    hddfile = vminfo['vmdkfile']
    basedir = os.path.dirname(hddfile)
    hdduuid = vminfo['uuid']
    hddsctl = vminfo['sctl']
    sctldev = vminfo['device']
    sctlport = vminfo['port']
    """
    vminfo = get_vm_info(vmname)
    if not vminfo:
        warning('warning: unable to retrieve VM info; attempting reset...')
        set_vm_hdd(vmname)
        vminfo = get_vm_info(vmname)
        if not vminfo:
            raise BoxBoxError('cannot get initial data for VM')
    hddfile = vminfo.hddfile
    basedir = vminfo.basedir
    hdduuid = vminfo.hdduuid
    hddsctl = vminfo.hddsctl
    sctldev = vminfo.sctldev
    sctlport = vminfo.sctlport
    log('hdd file: "{0}"'.format(hddfile))
    log('hdd uuid: "{0}"'.format(hdduuid))
    log('storagectl: {0}'.format(hddsctl))
    log('device {0} | port {1}'.format(sctldev, sctlport))
    if not os.path.exists(hddfile):
        log('ERROR: hdd file does not exist!')
        return boxname
    namefmt = '{vmname}.{isodate}'
    outfmt = '{fname}.{ext}'
    fname = namefmt.format(vmname=vmname, isodate=datetime.date.today())
    vmdkfile = outfmt.format(fname=fname, ext='vmdk')
    outvmdk = os.path.join(basedir, vmdkfile)
    tempvdi = os.path.join(basedir, 'tempclone.vdi')
    boxname = outfmt.format(fname=fname, ext='box')
    log('vdi temp: "{0}"'.format(tempvdi))
    log('vmdk out: "{0}"'.format(outvmdk))
    log('box name: "{0}"'.format(boxname))
    nl()
    if outvmdk == hddfile:
        warning('warning: input file matches output file!')

    # command will error if the file already exists
    if os.path.exists(tempvdi):
        warning('warning: temporary file already exists; removing...')
        command = CMD('rm "{0}"', tempvdi)
        debug(command.prompt)
        log(command.out)
        log('removed "{0}".\n'.format(tempvdi))

    # vbox clone the original to vdi format to reduce size
    log('cloning to vdi format...')
    clonevdi = 'VBoxManage clonehd "{invmdk}" "{outvdi}" --format vdi'
    command = CMD(clonevdi, invmdk=hddfile, outvdi=tempvdi)
    debug(command.prompt)
    if not fake:
        log(command.out)

    # later commands may error out if disk file is still registered
    showhdinfo = 'VBoxManage showhdinfo "{uuid}"'
    find_token = 'In use by VMs:'
    command = CMD(showhdinfo.format(uuid=hdduuid)).grep(find_token)
    debug(command.prompt)
    hdinfo = command.out.replace(find_token, '').strip()
    debug(hdinfo)

    re_vmsusing = re.compile(r'(?P<vm>.{1,}?)\s*\(UUID:\s*(?P<uuid>[\-\w]+)\)')
    vms = []
    for match in re_vmsusing.finditer(hdinfo):
        minfo = match.groupdict()
        vms.append((minfo['vm'], minfo['uuid']))
    debug(json.dumps(vms, indent=2))

    hdremove = 'VBoxManage storageattach {vm}'
    for vm in vms:
        try:
            log('unregistering {0} from {1}...'.format(hdduuid, vm[1]))
            vminfo = get_vm_info(vm[0])
            remove_vm_hdd(vm[1], vminfo, hdduuid)
            log('done.')
        except CalledProcessError as exc:
            raise
            log('------------------------------------------------------------')
            log(exc)
            log('------------------------------------------------------------')
            errstr = ''.join([
                'VBoxManage: error: No storage ',
                'device attached to device slot',
                ])
            excstr = '{0}'.format(exc)
            nodevice = excstr.find(errstr)

    nl()
    closemedium = 'VBoxManage closemedium disk "{uuid}"'
    command = CMD(closemedium.format(uuid=hdduuid))
    debug(command.prompt)
    log(command.out)
    log('closed medium "{0}"'.format(hdduuid))
    nl()

    # command will error if the file already exists
    if os.path.exists(outvmdk):
        warning('warning: output file already exists; removing...')
        command = CMD('rm "{0}"', outvmdk)
        debug(command.prompt)
        log(command.out)
        log('removed "{0}".'.format(outvmdk))

    nl()

    # revert the smaller image back to the vmdk format
    log('reverting clone to vmdk format...')
    clonevmdk = 'VBoxManage clonehd "{invdi}" "{outvmdk}" --format vmdk'
    command = CMD(clonevmdk, invdi=tempvdi, outvmdk=outvmdk)
    debug(command.prompt)
    if not fake:
        newvmdk = command.out
        debug(newvmdk)

    # if the filename is identical it will error, so get the UUID instead
    re_newuuid = re.compile(r'^.*UUID:\s*(?P<uuid>[\-\w]+)\s*$')
    uuidmatch = re_newuuid.match(newvmdk)
    if uuidmatch is None:
        error('ERROR: cannot extract new UUID for vmdk')
        return boxname
    uuidinfo = uuidmatch.groupdict()
    debug(json.dumps(uuidinfo, indent=2))
    newuuid = uuidinfo['uuid']

    # set new clone as hdd of current vm
    """
    https://forums.virtualbox.org/viewtopic.php?f=10&t=35119
    """
    if update:
        nl()
        log('updating {0} vm to use new hdd file...'.format(vmname))
        set_vm_hdd(vmname, hddsctl, newuuid, sctldev, sctlport)
        log('{0} is now using {1}.'.format(vmname, newuuid))

    # delete temp file
    nl()
    log('removing temp files...')
    command = CMD('rm "{tmp}"', tmp=tempvdi)
    debug(command.prompt)
    if not fake:
        log(command.out)
        log('removed "{0}".'.format(tempvdi))

    return boxname
