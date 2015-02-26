
import logging
import paramiko
import datetime
import time
import re
import json
import os

from subprocess import CalledProcessError
from .utils import task, log, warning, debug, nl, yesno
from .shellcommand import ShellCommand as CMD


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
        commands.extend([
            'dd if=/dev/zero of=zerofile',
            'rm zerofile',
        ])
    vagrant_kfile = os.path.expanduser('~/.vagrant.d/insecure_private_key')
    vagrant_pkey = paramiko.RSAKey.from_private_key_file(vagrant_kfile)

    # minify the VM disk as much as possible
    task('prepare the VM for packaging')
    with paramiko.SSHClient() as ssh:
        log('ensure {0} is running...'.format(host))
        v_up = CMD('vagrant up')
        debug(v_up.prompt)
        log(v_up.out)
        time.sleep(2)
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
        log('ensure {0} is halted...'.format(host))
        v_halt = CMD('vagrant halt')
        debug(v_halt.prompt)
        log(v_halt.out)


def shrink(vmname, update=True, fake=False):
    task('condense VM hdd image')

    log('gathering required information...')
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
        # get required info for storageattach
        # remove the medium from the storagectl
        pass
    nl()
    return boxname

    closemedium = 'VBoxManage closemedium disk "{uuid}"'
    command = CMD(closemedium.format(uuid=hdduuid))
    debug(command.prompt)
    log(command.out)

    # command will error if the file already exists
    if os.path.exists(outvmdk):
        warning('warning: output file already exists; removing...')
        command = CMD('rm "{0}"', outvmdk)
        debug(command.prompt)
        log(command.out)
        log('removed "{0}".'.format(outvmdk))

    # revert the smaller image back to the vmdk format
    log('reverting clone to vmdk format...')
    clonevmdk = 'VBoxManage clonehd "{invdi}" "{outvmdk}" --format vmdk'
    command = CMD(clonevmdk, invdi=tempvdi, outvmdk=outvmdk)
    debug(command.prompt)
    if not fake:
        newvmdk = command.out
        log(newvmdk)

    # if the filename is identical command will error, so get the UUID instead
    re_newuuid = re.compile(r'^.*UUID:\s*(?P<uuid>[\-\w]+)\s*$')
    uuidmatch = re_newuuid.match(newvmdk)
    if uuidmatch is None:
        log('ERROR: cannot extract new UUID for vmdk')
        log(newvmdk)
        return boxname
    uuidinfo = uuidmatch.groupdict()
    log(json.dumps(uuidinfo, indent=2))
    return boxname

    # set new clone as hdd of current vm
    """
    https://forums.virtualbox.org/viewtopic.php?f=10&t=35119
    """
    if update:
        log('updating {0} vm to use new hdd file...'.format(vmname))
        cmdparts = [
            'VBoxManage',
            'storageattach {vm}',
            '--storagectl {sctl}',
            '--medium "{vmdk}"',
            '--device {dev}',
            '--port {port}',
            '--type hdd',
            #'--comment "{comment}"',
        ]
        setstorage = ' '.join(cmdparts)
        command = CMD(
            setstorage,
            vm=vmname,
            sctl=hddsctl,
            vmdk=outvmdk,
            dev=sctldev,
            port=sctlport
            )
        debug(command.prompt)
        if not fake:
            log(command.out)

    # delete temp file
    log('removing temp files...')
    command = CMD('rm "{tmp}"', tmp=tempvdi)
    debug(command.prompt)
    if not fake:
        log(command.out)

    return boxname
