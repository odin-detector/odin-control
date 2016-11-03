import sys
from setuptools import setup, find_packages
import versioneer

with open('requirements.txt') as f:
    required = f.read().splitlines()

if sys.version_info[0] == 2:
    required.append('futures>=3.0.0')

setup(
    name="odin",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='ODIN detector server',
    url='https://github.com/timcnicholls/odin',
    author='Tim Nicholls',
    author_email='tim.nicholls@stfc.ac.uk',
    packages=find_packages(),
    entry_points={
        'console_scripts' : [
            'odin_server = odin.server:main',
        ],
    },
    install_requires=required,
)
