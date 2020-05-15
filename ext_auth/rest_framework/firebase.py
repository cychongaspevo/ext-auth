import json
import operator
import functools
from datetime import timedelta
import firebase_admin
from firebase_admin import credentials, auth
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Q
from django.shortcuts import render
from django.utils import timezone

#django-rest
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
#django-oauth-toolkit
from oauthlib import common
from oauth2_provider.models import Grant, AccessToken, RefreshToken, get_application_model
from oauth2_provider.settings import oauth2_settings

from ext_auth.models import ExternalUserIdentifier
from ext_auth.settings import ext_auth_settings
from .exceptions import APIErrorException
from .serializers import UserSerializer
from .mixins import ErrorMixin
#### firebase setup

# init
cred = credentials.Certificate(ext_auth_settings.FIREBASE_ADMIN_CERT)
default_app = firebase_admin.initialize_app(cred)

#### Firebase View
## Auth
class FirebaseAuthMixin(ErrorMixin):
    decoded_token = None
    id_token = None
    
    #get 
    def get_expire_seconds(self):
        return oauth2_settings.ACCESS_TOKEN_EXPIRE_SECONDS
    
    def get_ext_user_by_decoded_token(self, decoded_token):
        uid = decoded_token.get('uid', None)
        ext_user = ExternalUserIdentifier.objects.filter(uid=uid).first()
        return ext_user
    
    def get_user_by_decoded_token(self, decoded_token):
        uid = decoded_token.get('uid', None)
        firebase_dict = decoded_token.get('firebase', None)
        identities = firebase_dict.get('identities', None)
        
        uid_list = ('username', uid)
        q_list = [Q(uid_list)]
        
        for item in identities:
            value_array = identities.get(item, [])
            if value_array:
                new_list = ('username', value_array[0])
                print("new_list:", new_list)
                q_list.append(Q(new_list))
                #extra check on email
                if item == 'email':
                    new_list = ('email', value_array[0])
                    q_list.append(Q(new_list))
        
        user = User.objects.filter(functools.reduce(operator.or_, q_list)).first()

        return user
    
    def get_auto_link(self):
        #determine it will perform link user with current uid if found
        return True

    def get_decoded_token(self, id_token, **kwargs):
        if self.decoded_token:
            return self.decoded_token

        try:
            decoded_token = auth.verify_id_token(id_token, app=default_app)
        except Exception as e:
            err_msg = "[firebase] {0}".format(e)
            self.error_firebase_admin(err_msg)

        self.decoded_token = decoded_token
        return self.decoded_token

    def get_username_from_decode_token(self, decoded_token):
        username = decoded_token.get('email', None)
        
        if not username:
            username = decoded_token.get('phone_number', None)
        
        if not username:
            username = decoded_token.get('uid', None)

        return username
    
    def get_email_from_decode_token(self, decoded_token):
        email = decoded_token.get('email', None)

        if not email:
            provider_info = decoded_token.get('providerUserInfo', [])
            for info in provider_info:
                email = info.get('email', None)
                if email:
                    break
                
        return email
    
    def get_oauth2_app_by_client_id(self, client_id):
        Application = get_application_model()
        oauth_app = Application.objects.filter(client_id=client_id).first()

        return oauth_app

    def get_remove_old_token(self):
        return False

    def create_oauth2_token(self, user, client_id, old_token=None):
        oauth_app = self.get_oauth2_app_by_client_id(client_id)
        
        remove_old_token = self.get_remove_old_token()

        if remove_old_token is True:
            #this field to remove all token associate with this user and the application
            AccessToken.objects.filter(user=user, application=oauth_app).delete()
        
        if old_token:
            AccessToken.objects.filter(user=user, token=old_token).delete()

        expire_seconds = self.get_expire_seconds()
        
        expires = timezone.now() + timedelta(seconds=expire_seconds)
        scopes = oauth2_settings.DEFAULT_SCOPES
        access_token = AccessToken(
            user=user,
            scope=scopes,
            expires=expires,
            token=common.generate_token(),
            application=oauth_app
        )

        access_token.save()
        refresh_token = RefreshToken(
            user=user,
            token=common.generate_token(),
            application=oauth_app,
            access_token=access_token
        )
        refresh_token.save()

        results = {
            "access_token": access_token.token,
            "refresh_token": refresh_token.token,
            "token_type": "Bearer",
            "expires_in": expire_seconds,
            "scope": scopes,
            "user_id": user.id,
        }
        return results

    def validate_oauth2_app_by_client_id(self, client_id, **kwargs):
        app = self.get_oauth2_app_by_client_id(client_id)
        raise_error = kwargs.get('raise_error', True)
        if not app and raise_error is True:
            err_msg = kwargs.get('err_msg', 'Client ID is not valid')
            self.error_basic_requirement(err_msg)
        
        return app

    #others
    def link_user_with_ext(self, user, decoded_token, **kwargs):
        print("link existing user to ext identifier")
        uid = decoded_token.get('uid', None)
        obj, created = ExternalUserIdentifier.objects.update_or_create(
            user=user, uid=uid,
            defaults={'platform': 'firebase'},
        )

class RegisterUserApiView(APIView, FirebaseAuthMixin):
    serializer = UserSerializer
    
    def post(self, request):
        id_token = request.data.get('id_token', None)
        if not id_token:
            self.error_missing_field()
        
        self.id_token = id_token

        decoded_token = self.get_decoded_token(id_token)
        
        print("decoded_token:", decoded_token)
        ext_user = self.get_ext_user_by_decoded_token(decoded_token)
        if ext_user:
            self.error_exists('User with this identifier already signup')
        
        user = self.get_user_by_decoded_token(decoded_token)
        if user:
            if self.get_auto_link() is True:
                self.link_user_with_ext(user, decoded_token)
                err_msg = "User with uid/email/phone number found, since auto link enabled, system will link use with this identifier"
            else:
                err_msg = "User with uid/email/phone number in use by another account."
            
            self.error_exists(err_msg)
        
        user = self.perform_create(request, decoded_token)
        
        #return access_token
        serializer = self.serializer(user)
        return Response(serializer.data)

    def perform_create(self, request, decoded_token):
        first_name = request.data.get('first_name', decoded_token.get('name', ""))
        last_name = request.data.get('last_name', "")
        email = request.data.get('email', decoded_token.get('email', ""))
        username = request.data.get('username', None)
        if not username:
            username = self.get_username_from_decode_token(decoded_token)

        #create user
        user = User.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        #link user
        self.link_user_with_ext(user, decoded_token)
        
        return user

    def get(self, request):
        return Response({'description':'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

class RegisterUserTokenApiView(RegisterUserApiView):
    def post(self, request):
        client_id = request.data.get('client_id', None)
        id_token = request.data.get('id_token', None)
        if not id_token or not client_id:
            self.error_missing_field()
        
        self.validate_oauth2_app_by_client_id(client_id)
        
        self.id_token = id_token

        decoded_token = self.get_decoded_token(id_token)
        
        print("decoded_token:", decoded_token)
        ext_user = self.get_ext_user_by_decoded_token(decoded_token)
        if ext_user:
            self.error_exists('User with this identifier already signup')
        
        user = self.get_user_by_decoded_token(decoded_token)
        if user:
            if self.get_auto_link() is True:
                self.link_user_with_ext(user, decoded_token)
                err_msg = "User with uid/email/phone number found, since auto link enabled, system will link user with this identifier"
            else:
                err_msg = "User with uid/email/phone number in use by another account."
            
            self.error_exists(err_msg)
        
        user = self.perform_create(request, decoded_token)
        
        #create token
        token_results = self.create_oauth2_token(user, client_id, request.data.get('old_token', None))
        return Response(token_results)

class LoginUserApiView(APIView, FirebaseAuthMixin):
    def get_auto_create(self):
        return True
    
    def get_extra_data(self, user, data={}, is_auto_create=False):
        return data
    
    def create_user_by_decoded_token(self, decoded_token):
        username = self.get_username_from_decode_token(decoded_token)
        email = self.get_email_from_decode_token(decoded_token)
        display_name = decoded_token.get('name', "")
        phone = decoded_token.get('phone_number', "")
        
        #create user
        user = User.objects.create(
            username=username,
            first_name=display_name,
            last_name="",
            email=email
        )
        #link user
        self.link_user_with_ext(user, decoded_token)
        return user

    def get(self, request):
        return Response({'description':'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        client_id = request.data.get('client_id', None)
        id_token = request.data.get('id_token', None)
        if not id_token or not client_id:
            self.error_missing_field()
        
        self.validate_oauth2_app_by_client_id(client_id)
        
        self.id_token = id_token

        decoded_token = self.get_decoded_token(id_token)
        
        print("decoded_token:", decoded_token)
        # get user from ext user by uid
        ext_user = self.get_ext_user_by_decoded_token(decoded_token)
        user = None

        if ext_user:
            user = ext_user.user
        # get user from using decoded_token, email, phone_num or other id
        if not user:
            user = self.get_user_by_decoded_token(decoded_token)
        is_auto_create = False
        if not user:
            if self.get_auto_create() is False:
                self.error_object_not_found('There is no user corresponding to this identifier.')
            else:
                # create user use decoded_token
                user = self.create_user_by_decoded_token(decoded_token)
                is_auto_create = True
        else:
            # user found, do extra stuff
            if self.get_auto_link() is True:
                self.link_user_with_ext(user, decoded_token)

        #create token
        token_results = self.create_oauth2_token(user, client_id, request.data.get('old_token', None))
        payload_results = self.get_extra_data(user, token_results, is_auto_create)
        return Response(payload_results)

## Firebase Functions
class FirebaseUserMixin(ErrorMixin):
    pass
        
class GetUserApiView(APIView, FirebaseUserMixin):
    def get(self, request, *args, **kwargs):
        uid = request.query_params.get('uid', None)
        email = request.query_params.get('email', None)
        phone = request.query_params.get('phone', None)
        
        if not uid and not email and not phone:
            self.error_missing_field()

        user_record = None
        try:
            if email:
                user_record = firebase_admin.auth.get_user_by_email(email)
                
            elif phone:
                user_record = firebase_admin.auth.get_user_by_phone_number(phone)
            else:
                user_record = firebase_admin.auth.get_user(uid)
        except ValueError as e:
            self.error_firebase_admin('firebase error', "{}".format(e))
        except firebase_admin.auth.AuthError as e:
            cause = e.detail
            if cause:
                error = json.loads(cause.response._content)
                raise APIErrorException(error.get('error'), 400)
            else:
                self.error_firebase_admin('firebase error', "{}".format(e))

        result = {
            'data': {}
        }

        if user_record:
            result['data'] = user_record._data

        return Response(result)
        
    def post(self, request, *args, **kwargs):
        return Response({'description':'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

class CreateUserApiView(APIView, FirebaseUserMixin):
    def get(self, request, *args, **kwargs):
        return Response({'description':'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        
    def post(self, request, *args, **kwargs):
        display_name = request.data.get('display_name', None)
        email = request.data.get('email', None)
        phone_number = request.data.get('phone_number', None)
        password = request.data.get('password', None)
        disabled = request.data.get('disabled', False)

        if not email or not password:
            self.error_missing_field()

        payload = {
            'email': email,
            'password': password,
        }

        if display_name:
            payload['display_name'] = display_name
        
        if phone_number:
            payload['phone_number'] = phone_number

        try:
            user_record = firebase_admin.auth.create_user(**payload)
        
        except ValueError as e:
            self.error_firebase_admin('firebase error', "{}".format(e))
        except auth.AuthError as e:
            cause = e.detail
            error = json.loads(cause.response._content)
            err_msg = error.get('message', None)
            if err_msg and not err_msg == 'EMAIL_EXISTS':
                raise APIErrorException(error.get('error'), 400)

        user_record = firebase_admin.auth.get_user_by_email(email)
        
        return Response(user_record._data)
    