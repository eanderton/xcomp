# Copyright (c) 2020, Eric Anderton
# All rights reserved.
# Published under the BSD license.  See LICENSE For details.

import setuptools
import subprocess
from setuptools.command.develop import develop
from xcomp.version import __VERSION__

# shim to install dev depenedencies on 'setup.py develop'
class ExtDevelop(develop):
    def install_for_development(self):
        from distutils import log
        develop.install_for_development(self)
        if 'develop' in self.distribution.extras_require:
            log.info('\nInstalling development dependencies')
            requirements = ' '.join(self.distribution.extras_require['develop'])
            proc = subprocess.Popen('pip install ' + requirements, shell=True)
            proc.wait()


setuptools.setup(
    name='xcomp',
    version=__VERSION__,
    description='XComp 6502 assembler',
    long_description=open('README.md').read().strip(),
    author='Eric Anderton',
    author_email='eric.t.anderton@gmail.com',
    url='http://github.com/eanderton/xcomp',
    packages=['xcomp'],
    test_suite='tests',
    install_requires=[
        'ansicolor',
        'cbmcodecs',
    ],
    extras_require={
       'develop': [
           'hexdump',
           'pytest',
           'pytest-cov'
        ],
    },
    cmdclass= {
       'develop': ExtDevelop,
    },
    entry_points={
        'console_scripts': [
            'xcomp=xcomp.cli:main',
        ],
    },
    license='MIT License',
    zip_safe=False,
    keywords='compiler compilers 6502 6510',
    classifiers=[
        'Packages'
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
    ])
