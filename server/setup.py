#!/usr/bin/env python

PROJECT = 'cld-server'

VERSION = '0.0.1'

from setuptools import setup, find_packages

try:
    long_description = open('README.rst', 'rt').read()
except IOError:
    long_description = ''

setup(
    name=PROJECT,
    version=VERSION,

    description='CloudARK server',
    long_description=long_description,

    author='Devdatta Kulkarni',
    author_email='kulkarni.devdatta@gmail.com',

    url='',
    download_url='',

    classifiers=['Development Status :: 3 - Alpha',
                 'License :: OSI Approved :: Apache Software License',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Intended Audience :: Developers',
                 'Environment :: Console',
                 ],

    platforms=['Any'],

    scripts=[],

    provides=[],

    namespace_packages=[],
    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'server.server_plugins.aws.resource': [
            'rds = server.server_plugins.aws.resource.rds_handler:RDSResourceHandler',
            'dynamodb = server.server_plugins.aws.resource.dynamodb_handler:DynamoDBResourceHandler',
        ],
        'server.server_plugins.aws.coe': [
            'ecs = server.server_plugins.aws.coe.ecs:ECSHandler',
        ],
    },

    zip_safe=False,
)
