#!/usr/bin/env python

PROJECT = 'cld'

# Change docs/sphinx/conf.py too!
VERSION = '0.0.1'

from setuptools import setup, find_packages

try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''

setup(
    name=PROJECT,
    version=VERSION,

    description='CloudARK command-line tool',
    long_description=long_description,

    author='Devdatta Kulkarni',
    author_email='devdattakulkarni@gmail.com',

    url='',
    download_url='',

    classifiers=['Development Status :: 3 - Alpha',
                 'License :: OSI Approved :: Apache Software License',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.2',
                 'Intended Audience :: Developers',
                 'Environment :: Console',
                 ],

    platforms=['Any'],

    scripts=[],

    provides=[],
    install_requires=['cliff'],

    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'cld = fmcmds.main:main'
        ],
        'cld.cmds': [
            'app delete = fmcmds.app_delete:AppDelete',
            'app deploy = fmcmds.app_deploy:AppDeploy',
            'app redeploy = fmcmds.app_redeploy:AppRedeploy',
            'app list = fmcmds.app_list:AppList',
            'app show = fmcmds.app_show:AppShow',
            #'resource create = fmcmds.resource_create:ResourceCreate',
            'resource show = fmcmds.resource_show:ResourceShow',
            'resource list = fmcmds.resource_list:ResourceList',
            #'resource delete = fmcmds.resource_delete:ResourceDelete',
            #'resource-stack create = fmcmds.resource_stack_create:ResourceStackCreate',
            #'resource-stack show = fmcmds.resource_stack_show:ResourceStackShow',
            #'resource-stack list = fmcmds.resource_stack_list:ResourceStackList',
            #'resource-stack delete = fmcmds.resource_stack_delete:ResourceStackDelete',
            'environment create = fmcmds.environment_create:EnvironmentCreate',
            'environment delete = fmcmds.environment_delete:EnvironmentDelete',
            'environment show = fmcmds.environment_show:EnvironmentShow',
            'environment list = fmcmds.environment_list:EnvironmentList',
        ],
    },

    zip_safe=False,
)
