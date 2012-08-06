import errno
import os, sys
from signal import signal, SIGINT, SIGQUIT, SIGTERM, SIGCHLD, SIGHUP, pause, SIG_DFL
import time

__all__ = ['install']

def install(fork=True, sig=SIGTERM):
    def _reg(gid):
        handler = make_quit_signal_handler(gid, sig)
        signal(SIGINT, handler)
        signal(SIGQUIT, handler)
        signal(SIGTERM, handler)
        signal(SIGCHLD, make_child_die_signal_handler(gid, sig))

    if not fork:
        _reg(os.getpid())
        return

    pid = os.fork()
    if pid == 0:
        # child process
        os.setpgrp()
        pid = os.fork()
        if pid != 0:
            exit_when_parent_or_child_dies(sig)
    else:
        # parent process
        gid = pid
        _reg(gid)
        while True:
            pause()


def make_quit_signal_handler(gid, sig=SIGTERM):
    def handler(signum, frame):
        signal(SIGTERM, SIG_DFL)
        try:
            os.killpg(gid, sig)
        except os.error, ex:
            if ex.errno != errno.ESRCH:
                raise
    return handler


def make_child_die_signal_handler(gid, sig=SIGTERM):
    def handler(signum, frame):
        try:
            pid, status = os.wait()
        except OSError:
            # sometimes there is no child processes already
            status = 0

        try:
            signal(SIGTERM, SIG_DFL)
            os.killpg(gid, sig)
        finally:
            sys.exit((status & 0xff00) >> 8)
    return handler


def exit_when_parent_or_child_dies(sig):
    gid = os.getpgrp()
    signal(SIGCHLD, make_child_die_signal_handler(gid))

    try:
        from prctl import prctl, PDEATHSIG
        signal(SIGHUP, make_quit_signal_handler(gid))
        # give me SIGHUP if my parent dies
        prctl(PDEATHSIG, SIGHUP)
        pause()

    except ImportError:
        # fallback to polling status of parent
        while True:
            if os.getppid() == 1:
                # parent died, suicide
                signal(SIGTERM, SIG_DFL)
                os.killpg(gid, sig)
                sys.exit()
            time.sleep(5)
