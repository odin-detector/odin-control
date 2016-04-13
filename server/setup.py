from setuptools import setup
import os
setup(
    name="odin",
    version='0.1',
    description='ODIN detector server',
    url='https://github.com/timcnicholls/odin',
    author='Tim Nicholls',
    author_email='tim.nicholls@stfc.ac.uk',
    packages=[
        'odin',
    ],
    entry_points={
        'console_scripts' : [
            'odin_server = odin.server:main',
        ],
    },
    install_requires=
        open(os.path.join(os.path.dirname(__file__),
          'requirements.txt'
        ), 'rb').readlines(),
)
