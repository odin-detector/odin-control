from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

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
    install_requires=required,
)
