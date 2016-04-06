from setuptools import setup, Extension

# define the extension module
fem_api = Extension('fem_api', sources=['fem_api_source/fem_api_wrapper.c', 'fem_api_source/femApi.cpp', 'fem_api_source/ExcaliburFemClient.cpp'])

setup(
    name="excalibur",
    version='0.1',
    description='EXCALIBUR detector plugin for ODIN framework',
    url='https://github.com/timcnicholls/odin',
    author='Tim Nicholls',
    author_email='tim.nicholls@stfc.ac.uk',
    setup_requires=['nose>=1.0'],
    ext_modules=[fem_api],
)
