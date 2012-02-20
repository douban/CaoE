import sys
from setuptools import setup

install_requires = []
if sys.platform.startswith('linux'):
    install_requires.append('prctl')

setup(
    name = "CaoE",
    description = "Kill all children processes when the parent dies",
    version = "0.1",
    py_modules = ['caoe'],
    install_requires = install_requires,
    author = "Qiangning Hong",
    author_email = "hongqn@douban.com",
    license = "PSF",
    keywords = "process management",
    url = "https://github.com/douban/caoe",
    test_suite = 'nose.collector',
    tests_require = ['nose'],
)
