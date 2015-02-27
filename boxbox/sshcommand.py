

class SSHCommand(object):
    """
    simple class wrapper for executing commands over an ssh connection
    init has the same params as the .exec_command() function in SSHClient
    """
    def __init__(self, ssh, command, **kwargs):
        params = {
            'bufsize': -1,
            'timeout': None,
            'get_pty': False,
            'strip': False,
        }
        params.update(kwargs)
        self.stdin, self.stdout, self.stderr = ssh.exec_command(command)
        self._output = None
        self.ssh = ssh
        self.command = command
        self.bufsize = params['bufsize']
        self.timeout = params['timeout']
        self.get_pty = params['get_pty']
        self.strip = params['strip']

    def __str__(self):
        if not self._output:
            output = self.stdout.readlines()
            output.extend(self.stderr.readlines())
            self._output = ''.join(output)
            if self.strip:
                self._output = self._output.rstrip()
        return self._output

    def send(self, data):
        if not data.endswith('\n'):
            data = '{0}\n'.format(data)
        self.stdin.write(data)
        self.stdin.flush()
