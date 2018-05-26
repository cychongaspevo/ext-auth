
import os
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='ext_auth',
    version='0.1.3',
    packages=['ext_auth'],
    package_data={'migrations': ['*'], 'rest_framework':['*']},
    include_package_data=True,
    license='BSD License',  # example license
    description='A simple Django app register and login via 3rd party Auth',
    long_description_content_type="text/markdown",
    long_description=long_description,
    url='https://github.com/cychongaspevo/ext-auth.git',
    author='notfair',
    author_email='cy.chong@aspevo.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License', # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        # Replace these appropriately if you are stuck on Python 2.
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'Django>=1.7.7',
        'djangorestframework>=3.1.1',
        'django-oauth-toolkit>=0.10.0',
        'firebase-admin>=2.10.0',
    ]
)
