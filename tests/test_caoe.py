import os
import tempfile
from contextlib import contextmanager
import shutil
# Fix bug: http://bugs.python.org/issue15881
try:
    import multiprocessing
except ImportError:
    pass
from multiprocessing import Process
import time
from signal import SIGKILL
from glob import glob

from nose.tools import ok_, eq_

import caoe


@contextmanager
def mkdtmp():
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


def is_process_alive(pid):
    try:
        os.kill(pid, 0)
    except OSError, e:
        if e.errno == 3:  # process is dead
            return False
        elif e.errno == 1:  # no permission
            return True
        else:
            raise
    else:
        return True


def parent(path, pause=False, fork=True):
    caoe.install(fork=fork)
    open(os.path.join(path, 'parent-%d' % os.getpid()), 'w').close()
    for i in range(3):
        p = Process(target=child, args=(path,))
        p.daemon = True
        p.start()
    if pause:
        time.sleep(10)
    else:
        time.sleep(0.1)


def child(path):
    pid = os.getpid()
    open(os.path.join(path, 'child-%d' % pid), 'w').close()
    time.sleep(100)


def test_all_child_processes_should_be_killed_if_parent_quit_normally(fork=True):
    with mkdtmp() as tmpdir:
        p = Process(target=parent, args=(tmpdir,), kwargs={'fork': fork})
        p.start()
        p.join(1)
        cpids = [int(x.split('-')[1])
                 for x in os.listdir(tmpdir) if x.startswith('child-')]
        eq_(len(cpids), 3)
        ok_(all(not is_process_alive(pid) for pid in cpids))
        # ensure the parent logic is executed only once
        eq_(len(glob(os.path.join(tmpdir, 'parent-*'))), 1)


def test_nonfork_all_child_processes_should_be_killed_if_parent_quit_normally():
    test_all_child_processes_should_be_killed_if_parent_quit_normally(
        fork=False)


def test_all_child_processes_should_be_killed_if_parent_is_killed(fork=True):
    with mkdtmp() as tmpdir:
        p = Process(target=parent, args=(tmpdir,),
                    kwargs={'pause': True, 'fork': fork})
        p.start()
        time.sleep(1)  # wait for child processes spawned
        p.terminate()
        p.join()
        cpids = [int(x.split('-')[1])
                 for x in os.listdir(tmpdir) if x.startswith('child-')]
        eq_(len(cpids), 3)
        time.sleep(1)  # wait for killing children
        ok_(all(not is_process_alive(pid) for pid in cpids))
        # ensure the parent logic is executed only once
        eq_(len(glob(os.path.join(tmpdir, 'parent-*'))), 1)


def test_nonfork_all_child_processes_should_be_killed_if_parent_is_killed():
    test_all_child_processes_should_be_killed_if_parent_is_killed(fork=False)


def test_all_child_processes_should_be_killed_if_parent_is_killed_by_SIGKILL_in_fork_mode():
    with mkdtmp() as tmpdir:
        p = Process(target=parent, args=(tmpdir,), kwargs={'pause': True})
        p.start()
        time.sleep(1)  # wait for child processes spawned
        os.kill(p.pid, SIGKILL)
        p.join()
        time.sleep(5)  # wait for the parent status checking interval
        cpids = [int(x.split('-')[1])
                 for x in os.listdir(tmpdir) if x.startswith('child-')]
        eq_(len(cpids), 3)
        ok_(all(not is_process_alive(pid) for pid in cpids))
        # ensure the parent logic is executed only once
        eq_(len(glob(os.path.join(tmpdir, 'parent-*'))), 1)
