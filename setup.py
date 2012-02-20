import sys, os
from setuptools import setup

install_requires = []
if sys.platform.startswith('linux'):
    install_requires.append('prctl')

setup(
    name = "CaoE",
    description = "Kill all children processes when the parent dies",
    long_description = open(os.path.join(os.path.dirname(__file__),
                                         'README.rst')).read(),
    version = "0.1.2",
    platforms = ['POSIX'],
    classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
    ],
    py_modules = ['caoe'],
    install_requires = install_requires,
    author = "Qiangning Hong",
    author_email = "hongqn@douban.com",
    keywords = "process management",
    url = "https://github.com/douban/caoe",
    test_suite = 'nose.collector',
    tests_require = ['nose'],
)
