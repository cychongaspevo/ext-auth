=====
User External Auth
=====

User External Auth is a wrapper Django app for 3rd Party token auth, and convert it to Django OAuth2 token (django-oauth-toolkit). 

For now only focus on Firebase Auth ID Token. 

More feature and convenient methods will include in the future.

Register and Login Apiview is ready and it is using Django Rest Framework library.

Requirement:
1. django
2. django-oauth-toolkit
3. django-rest-framework
4. firebase-admin

Quick start
-----------

1. Add "ext_auth" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'ext_auth',
    ]

2. The register and login Apiview is under 'ext-auth.rest-framework.firebase'

3. Run `python manage.py migrate` to create the ext-auth models.
