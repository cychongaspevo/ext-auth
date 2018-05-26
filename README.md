User External Auth
-----------

User External Auth is a wrapper Django app for 3rd Party token auth, and convert it to Django OAuth2 token (django-oauth-toolkit). 

For now only focus on Firebase Auth ID Token. 

More feature and convenient methods will include in the future.

Register and Login Apiview is ready and it is using Django Rest Framework library.

Requirements
------------

1. django >= 1.7.7

2. django-oauth-toolkit >= 0.10.0

3. django-rest-framework >= 3.1.1

4. firebase-admin

Installation
------------

1. Install using pip

    `pip install ext-auth`

Usage
-----

1. Add `ext_auth` to your INSTALLED_APPS.
    
    > INSTALLED_APPS = [
    >   ...
    >   'ext_auth',
    > ]
    

2. Run `python manage.py migrate` to create the ext_auth models.

** The register and login Apiview sample is under `ext_auth.rest-framework.firebase`
