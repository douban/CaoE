import os, sys
from signal import signal, SIGINT, SIGQUIT, SIGTERM, SIGCHLD, SIGHUP, pause, SIG_DFL
import time

__all__ = ['install']

def install():
    print "parent: %d" % os.getpid()
    pid = os.fork()
    if pid == 0:
        # child process
        print "child: %d" % os.getpid()
        os.setpgrp()
        pid = os.fork()
        if pid != 0:
            exit_when_parent_or_child_dies()
        else:
            print "grand child: %d" % os.getpid()
    else:
        # parent process
        gid = pid
        handler = make_quit_signal_handler(gid)
        signal(SIGINT, handler)
        signal(SIGQUIT, handler)
        signal(SIGTERM, handler)
        signal(SIGCHLD, make_child_die_signal_handler(gid))
        pause()


def make_quit_signal_handler(gid, sig=SIGTERM):
    def handler(signum, frame):
        print "%d got signal %s for quit" % (os.getpid(), signum)
        signal(SIGTERM, SIG_DFL)
        os.killpg(gid, sig)
    return handler


def make_child_die_signal_handler(gid, sig=SIGTERM):
    def handler(signum, frame):
        print "%d got signal %s for child die" % (os.getpid(), signum)
        pid, status = os.wait()
        try:
            signal(SIGTERM, SIG_DFL)
            print "kill -%d" % gid
            os.killpg(gid, sig)
        finally:
            sys.exit((status & 0xff00) >> 8)
    return handler


def exit_when_parent_or_child_dies():
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
                print "%d: parent died, suicide" % os.getpid()
                signal(SIGTERM, SIG_DFL)
                os.killpg(gid, SIGTERM)
                sys.exit()
            time.sleep(5)
