

def vagrant_package(vmname, boxname):
    task('package the new base box')
    log('packaging {vm} to {box}'.format(vm=vmname, box=boxname))
    package = 'vagrant package --base {vm} --output {box}'
    command = CMD(package, vm=vmname, box=boxname)
    debug(command.prompt)
    log(command.out)
    return boxname


def package_lzma():
    # repackage it using lzma compression for smaller footprint
    cmd = 'bsdtar -c --lzma -f "$2.lz" @$2'
    # ^ probably not actually necessary
