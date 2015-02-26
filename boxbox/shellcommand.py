
import subprocess as sp
import traceback as tb
import sys
import os
import shlex


class ShellCommand(object):
    def __init__(self, cmd, *args, **kwargs):
        self._cmd = cmd
        if args or kwargs:
            self._cmd = cmd.format(*args, **kwargs)
        self._input = None
        self._output = None

    def _exec(self, pipe=False):
        # nothing fancy, just use check_output
        if not pipe and not self._input:
            try:
                self._output = sp.check_output(shlex.split(self._cmd))
                self._output = '{0}'.format(self._output)
            except CalledProcessError:
                exc_type, exc_value, exc_tb = sys.exc_info()
                exc_info = tb.format_exception(exc_type, exc_value, exc_tb)
                self._output = ''.join(exc_info)
                raise
            except:
                raise
            return

        # pipe or input required, use Popen instead of check_output
        pin = None
        params = {'stdout': sp.PIPE, 'stderr': sp.PIPE}
        if self._input:
            pin = self._input._exec(pipe=True)
            params['stdin'] = pin.stdout
        proc = sp.Popen(shlex.split(self._cmd), **params)
        if pin:
            pin.stdout.close()
        if pipe:
            return proc
        stdout, stderr = proc.communicate()
        if stderr:
            raise ValueError(stderr)
        self._output = stdout

    def pipe(self, cmd, *args, **kwargs):
        pcmd = ShellCommand(cmd, *args, **kwargs)
        pcmd._input = self
        return pcmd

    def grep(self, find, options=None):
        opts = ' {0}'.format(options) if options else ''
        return self.pipe('grep{0} "{1}"', opts, find)

    @property
    def out(self):
        return self.__str__()

    @property
    def cmd(self):
        incmd = ''
        if self._input:
            incmd = '{0} | '.format(self._input.cmd)
        return '{0}{1}'.format(incmd, self._cmd)

    @property
    def prompt(self):
        user = os.path.split(os.path.expanduser('~'))[1]
        prefix = ''
        return '{0}: {1}$ {2}'.format(prefix, user, self.cmd)

    def __str__(self):
        if not self._output:
            self._exec()
        return self._output
