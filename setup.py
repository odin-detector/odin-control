import sys
from setuptools import setup, find_packages
import versioneer

install_requires = [
    'tornado>=4.3',
    'pyzmq>=17.0',
    'future',
    'psutil>=5.0',
]

if sys.version_info[0] == 2:
    install_requires.append('futures')

setup(
    name="odin",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='ODIN detector server',
    url='https://github.com/timcnicholls/odin',
    author='Tim Nicholls',
    author_email='tim.nicholls@stfc.ac.uk',
    packages=find_packages('src'),
    package_dir={'':'src'},
    entry_points={
        'console_scripts' : [
            'odin_server = odin.server:main',
        ],
    },
    install_requires=install_requires,
)
