from setuptools import setup, find_packages, Extension
import os

# Import requirements from file
with open('requirements.txt') as f:
    required = f.read().splitlines()

# Define the extension module
fem_api_source_path='fem_api_source'
fem_api_sources = ['fem_api_wrapper.c', 'femApi.cpp', 'ExcaliburFemClient.cpp', 'FemApiError.cpp']

fem_api = Extension('excalibur.fem_api', sources=[
    os.path.join(fem_api_source_path, source) for source in fem_api_sources
])

setup(
    name='excalibur',
    version='0.1',
    description='EXCALIBUR detector plugin for ODIN framework',
    url='https://github.com/timcnicholls/odin',
    author='Tim Nicholls',
    author_email='tim.nicholls@stfc.ac.uk',
    ext_modules=[fem_api],
    packages = find_packages(),
    install_requires=required,
)
