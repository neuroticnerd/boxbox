
"""
http://abhishek-tiwari.com/hacking/creating-a-new-vagrant-base-box-from-an-existing-vm?ModPagespeed=noscript
https://blog.engineyard.com/2014/building-a-vagrant-box
https://meta.discourse.org/t/how-can-we-make-our-vagrant-vm-image-smaller/5938
http://www.willdurness.com/post/101278039635/compacting-shrinking-a-virtualbox-image-when-using
http://stackoverflow.com/questions/17845637/vagrant-default-name
http://www.pythonforbeginners.com/code-snippets-source-code/ssh-connection-with-python
http://stackoverflow.com/questions/2715847/python-read-streaming-input-from-subprocess-communicate
http://stackoverflow.com/questions/2804543/read-subprocess-stdout-line-by-line
http://log.ooz.ie/2013/02/interactive-subprocess-communication-in.html
http://stackoverflow.com/questions/19880190/interactive-input-output-using-python
http://stackoverflow.com/questions/1606795/catching-stdout-in-realtime-from-subprocess
http://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python
"""


def use_pty():
    """
    http://stackoverflow.com/questions/5411780/python-run-a-daemon-sub-process-read-stdout
    http://fleckenzwerg2000.blogspot.com/2011/10/running-and-controlling-gnu-screen-from.html
    """
    import subprocess as sp
    import pty
    import os
    import sys

    master, slave = pty.openpty()
    stdout = os.fdopen(master, 'r')

    ssh = sp.Popen(
        ['vagrant', 'ssh'],
        shell=False,
        stdin=sp.PIPE,
        stdout=slave,
        stderr=slave,
        close_fds=True
        )

    try:
        line = stdout.readline()
        while line:
            if line != '\n':
                print ''.join(line.split('\n'))
            line = stdout.readline()
    except KeyboardInterrupt:
        print 'END PROGRAM'

    ssh.stdin.write('exit\n')
    ssh.stdin.flush()

    try:
        line = stdout.readline()
        while line:
            if line != '\n':
                print ''.join(line.split('\n'))
            line = stdout.readline()
    except KeyboardInterrupt:
        print 'END PROGRAM'

    stdout.close()
    sys.exit(0)


def use_non_blocking():
    import os
    import fcntl
    import subprocess as sp


    def non_blocking(fd):
        """set the given file descriptor to non blocking."""
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        flags = flags | os.O_NONBLOCK
        fcntl.fcntl(fd, fcntl.F_SETFL, flags)


    def send(proc, cmd):
        proc.stdin.write(cmd)
        proc.stdin.flush()


    def getline(proc, prompt=None):
        out = ''
        try:
            while True:
                try:
                    latest = proc.stdout.read()
                    if latest == '':
                        return out
                    out += latest
                    if out == '\n':
                        continue
                    return out
                except IOError:
                    continue
        except KeyboardInterrupt:
            return out


    ssh = sp.Popen(
        ['vagrant', 'ssh'],
        shell=False,
        bufsize=0,
        stdin=sp.PIPE,
        stdout=sp.PIPE,
        stderr=sp.STDOUT
        )
    non_blocking(ssh.stdout)
    #non_blocking(ssh.stderr)


    r = getline(ssh, '\n')
    print r
    send(ssh, 'exit\n')
    r = getline(ssh, '\n')
    print r

    sys.exit(0)



def use_ipopen():
    import sys
    import subprocess as sp
    from threading  import Thread
    from Queue import Queue, Empty
    ON_POSIX = 'posix' in sys.builtin_module_names


    # prepare the box
    class IPopen(object):
        def __init__(self, command, shell=False):
            self.proc = sp.Popen(
                command,
                shell=shell,
                bufsize=0,
                stdin=sp.PIPE,
                stdout=sp.PIPE,
                stderr=sp.STDOUT,
                close_fds=ON_POSIX
                )
            self.queue = Queue()
            self.push = Thread(
                target=self.enqueue_output,
                args=(self.proc.stdout, self.queue)
                )
            self.push.daemon = True # thread dies with the program
            self.push.start()
            self.pop = Thread(
                target=self.dequeue_output,
                args=(self.queue,)
                )
            self.pop.daemon = True
            self.pop.start()

        def __getattr__(self, attr):
            return getattr(self.proc, attr)

        def get(self):
            # read line without blocking
            try: 
                line = self.queue.get_nowait()
            except Empty:
                return True
            else:
                logging.info(line)
            return False

        def send(self, msg):
            self.proc.stdin.write(msg)
            self.proc.stdin.flush()

        def cmd(self, cmd):
            if not cmd.endswith('\n'):
                cmd = cmd + '\n'
            self.send(cmd)

        def enqueue_output(self, out, queue):
            for line in iter(out.readline, b''):
                queue.put(line)
            out.close()

        def dequeue_output(self, queue):
            msg = queue.get()
            while msg != None:
                if msg == '':
                    break
                msg = ''.join(msg.split('\n'))
                logging.info(msg)
                msg = queue.get()

    commands = [
        'sudo apt-get clean',
        'sudo apt-get autoclean',
        'sudo apt-get autoremove',
        'dd if=/dev/zero of=zerofile',
        'rm zerofile',
    ]
    #ssh = IPopen('vagrant ssh', True)
    ssh = IPopen(['vagrant', 'ssh'])
    for com in commands:
        ssh.cmd(com)
    ssh.cmd('exit')
    ssh.wait()
    ssh.get()

    sys.exit(0)
