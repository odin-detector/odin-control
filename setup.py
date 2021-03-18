import sys
from setuptools import setup, find_packages
import versioneer

install_requires = [
    'tornado>=4.3',
    'pyzmq>=17.0',
    'future',
    'psutil>=5.0',
]

extras_require = {
    'test': [
        'pytest', 'pytest-cov', 'requests', 'tox'
    ]
}

if sys.version_info[0] == 2:
    install_requires.append('futures')
    extras_require['test'].append('mock')
else:
    extras_require['test'].append('pytest-asyncio')

setup(
    name="odin_control",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='ODIN detector control system',
    url='https://github.com/odin-detector/odin-control',
    author='Tim Nicholls',
    author_email='tim.nicholls@stfc.ac.uk',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    entry_points={
        'console_scripts': [
            'odin_server = odin.server:main',
        ],
    },
    install_requires=install_requires,
    extras_require=extras_require,
)
