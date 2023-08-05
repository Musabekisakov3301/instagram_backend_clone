from .models import User, UserConfirmation, VIA_EMAIL, VIA_PHONE, DONE, NEW, CODE_VERIFIED, PHOTO_STEP
from shared.utility import check_email_or_phone, check_user_type, send_phone_code,send_email
from rest_framework import exceptions
from django.db.models import Q
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer,TokenRefreshSerializer
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.generics import get_object_or_404
#from django.core.mail import send_mail
from django.core.validators import FileExtensionValidator
from django.contrib.auth import authenticate

class SignUpSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True) # read_only=True -> Only allowed to read (by default it is False)
                                               # required=True ->
    
    # auth_type = serializers.CharField(read_only=True, required=True)                         
    # auth_status = serializers.CharField(read_only=True, required=True)
    
    # initialization new field
    def __init__(self, *args, **kwargs):
        super(SignUpSerializer, self).__init__(*args, **kwargs)
        self.fields['email_phone_number'] = serializers.CharField(required=False) 
        
    class Meta:
        model = User
        fields = (
            'id',
            'auth_type',
            'auth_status'
        )
        extra_kwargs = {
            'auth_type': {'read_only': True, 'required': False},
            'auth_status':  {'read_only': True, 'required': False}
        }
    
    def create(self,validated_data):
        user = super(SignUpSerializer, self).create(validated_data)
        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            #send_phone_code(user.phone, code)
            send_email(user.phone_number, code)
        user.save()
        return user

    def validate(self, data):
        super(SignUpSerializer, self).validate(data)
        data = self.auth_validate(data)
        print(data)
        return data 

    @staticmethod # auth_validate is a simple function method
    def auth_validate(data):
        print(data)
        user_input = str(data.get('email_phone_number')).lower()
        input_type = check_email_or_phone(user_input) # to check -> email or phone
        
        if input_type == "email":
            data = {
                "email": user_input,
                "auth_type": VIA_EMAIL
            }
        elif input_type == "phone":
            data = {
                "phone_number": user_input,
                'auth_type': VIA_PHONE
            }
        else: 
            print(data)
            data = {
                'success': False,
                'message': 'You must send email or phone number'
            }
            raise ValidationError(data)
          
        return data

    def validate_email_phone_number(self, value):
        value = value.lower()
        print(value)
        if value and User.objects.filter(email=value).exists():
            data = {
                'success': False,
                'message': 'This Email address is already available in the database'
            }
            raise ValidationError(data)
        elif value and User.objects.filter(phone_number=value).exists():
            data = {
                'success': False,
                'message': 'This Phone number is already available in the database'
            }
            raise ValidationError(data)
        
          
        return value
    
    def to_representation(self, instance):
        data = super(SignUpSerializer, self).to_representation(instance)
        data.update(instance.token())
        return data
    
class ChangeUserInformation(serializers.ModelSerializer):
    first_name = serializers.CharField(write_only=True,required=True)
    last_name = serializers.CharField(write_only=True,required=True)
    username = serializers.CharField(write_only=True,required=True)
    password = serializers.CharField(write_only=True,required=True)
    confirm_password = serializers.CharField(write_only=True,required=True)

    class Meta:
       model = User
       fields = ('first_name', 'last_name', 'username', 'password', 'confirm_password')

    def validate(self, data): 
        #password = data['password']
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)
        if password != confirm_password:
            raise ValidationError(
                {
                    'message': 'Your password and the confirmation password do not match'
                }
            )
        if password:
            validate_password(password)
            validate_password(confirm_password)
        
        return data
    
    def validate_username(self, username):
        ''' if User.objects.filter(username=username).exists():
            raise ValidationError(
                {
                    'message': 'This username already exists'
                }
               )'''
        if len(username) < 5 or len(username) > 30:
                    data = {
                        'message': 'Username must be between 5 and 30 characters length'
                    }
                    raise ValidationError(data)
        if username.isdigit():
                    data = {
                        'message': 'This username is entirely numeric'
                    }
                    raise ValidationError(data)
            
        return username 
        
    def validate_full_name(self, data):
        first_name = data.get('first_name', None)
        last_name = data.get('last_name', None)
        if first_name.strip() == '':
            raise ValidationError(
                {
                    'message': 'First name is required'
                }
            )
        elif last_name.strip() == '':
            raise ValidationError(
                 {
                    'message': 'Last name is required'  
                 } 
            )
        
        return data
    
    def update(self, instance, validated_data):
        # intance -> This is an argument that get the first_name object from the User model 
        # validated -> This is an argument that passes validation and returns data like dict()
        instance.first_name = validated_data.get('first_name', instance.first_name) # this method means that if the 'first_name' (from validated_data) is empty,'instance.first_name' from the user model will be taken in its place
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.username = validated_data.get('username', instance.username)
        instance.password = validated_data.get('password', instance.password)
        # this method allow to hash the password (set_password) 
        if validated_data.get('password'):
            instance.set_password(validated_data.get('password'))
        if instance.auth_status == CODE_VERIFIED:
            instance.auth_status == DONE
        instance.save()
        return instance
    
class ChangeUserPhotoSerializer(serializers.Serializer):
    photo = serializers.ImageField(validators=[FileExtensionValidator(allowed_extensions=[
         'jpg','jpeg','png','heic','heif'
    ])])

    def update(self, instance, validated_data):
        photo = validated_data.get('photo')
        if photo:
            instance.photo = photo
            instance.auth_status = PHOTO_STEP
            instance.save()
        return instance 
    
class LoginSerializer(TokenObtainPairSerializer):
    
    # TokenObtainPairSerializer -> this class returns refresh and access token

    # initialization new field
    def __init__(self, *args, **kwagrs):
        super(LoginSerializer, self).__init__(*args, **kwagrs)
        self.fields['userinput'] = serializers.CharField(required=True)
        self.fields['username'] = serializers.CharField(required=False, read_only=True)
        
    def auth_validate(self, data):
        user_input = data.get('userinput') # login with(email,username,phone number)
        if check_user_type(user_input) == 'username':
            username = user_input
        elif check_user_type(user_input) == 'email': # Google@gmail.com -> google@gmail.com
            #user = User.objects.get(email__iexact=user_input) # using the user get method, the variable was bound to the user
            user = self.get_user(email__iexact=user_input) # usi
            username = user.username
        elif check_user_type(user_input) == 'phone':
            #user = User.objects.get(phone_number=user_input)
            user = self.get_user(phone_number=user_input)
            username = user.username
        else:
            data = {
                'success': True,
                'message': 'you have to send email, phone number, username'
            }
            raise ValidationError(data)
        
        # used to facilitate filling in arguments (username,password) in the authenticate(username=username, password=password) method
        authentication_kwargs = {
            self.username_field: username,
            'password': data['password']
        }
        
        # to check user status
        current_user = User.objects.filter(username__iexact=username).first() # first() -> returns the first element from the QuerySet.
        if current_user is not None and current_user.auth_status in [NEW, CODE_VERIFIED]:
            raise ValidationError(
                {
                    'success': False,
                    'message': 'you have not fully registered!'
                }
            )
        
        # authenticate() -> this method needed for verifify credentials.it takes credentials as keyword arguments(username, password) for default case
        # and check them against each authentication backend, and returns a User object if the credentials are valid for a backend. 
        # If the credentials aren't valid for any backend or if a backend raises PermissionDenied,it returns None 
        user = authenticate(**authentication_kwargs) # -> authenticate(username=username, password=data['password'])
        if user is not None:
            self.user = user
        else:
            raise ValidationError(
                {
                    'success': False,
                    'message': 'Sorry, login or password you entered is incorrect. Please check and try again!'
                }
            )
    
    def validate(self, data):
        self.auth_validate(data)
        if self.user.auth_status not in [DONE, PHOTO_STEP]:
            raise PermissionDenied("you can't log in, no permitted!")
        data = self.user.token()
        data['auth_status'] = self.user.auth_status
        data['full_name'] = self.user.full_name
        return data
      
    # this function(method) is used to replace or facilitate the User object call (User.objects.get())   
    def get_user(self, **kwargs):
        users = User.objects.filter(**kwargs)
        if not users.exists():
            raise ValidationError(
                {
                    'message': 'No active account found'
                }
           )
        return users.first() 

class LoginRefreshSerializer(TokenRefreshSerializer):
    
    def validate(self, attrs):
        data =  super().validate(attrs)
        access_token_instance = AccessToken(data['access'])
        user_id = access_token_instance['user_id']
        user = get_object_or_404(User, id=user_id)
        update_last_login(None, user)
        return data  

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField() 

class ForgotPasswordSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        email_or_phone = attrs.get('email_or_phone', None)
        if email_or_phone is None:
            raise ValidationError(
                {
                    'success': False,
                    'message': 'You must enter email or phone number required!'
                }
            )
        user = User.objects.filter(Q(phone_number=email_or_phone) | Q(email=email_or_phone)) # Query Set
        if not user.exists():
            raise NotFound(detail='User not found')
        attrs['user'] = user.first()
        return attrs

class ResetPasswordSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True) # read_only -> 
    password = serializers.CharField(max_length=8, required=True, write_only=True)
    confirm_password = serializers.CharField(max_length=8, required=True, write_only=True)
    
    class Meta:
        model = User
        fields = (
            'id',
            'password',
            'confirm_password'
        )
        
    def validate(self, data):
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)
        if password != confirm_password:
            raise ValidationError(
                {
                    'success': False,
                    'message': 'The values of your password do not match each other'
                }
            )
        elif (password is None) and (confirm_password is None):
            raise ValidationError(
                {
                    'success': False,
                    'message': 'The field is empty, you have to fill in the fields '
                }
            )
        elif password:
            validate_password(password)
        return data
    
    def update(self, instance, validated_data):
        
        """ The update method is used to update an instance of a model with validated data. It sets the password of the instance
            to the new password provided in the validated data and then calls the update method of the parent serializer to
            update the instance with the remaining validated data.
            
            The method takes two arguments(instance,validated_data)
            instance -> is the instance of the model that needs to be updated
            validated_data -> is the data that has been validated by the serializer
            
            This function updates the password of a user instance with the new password provided in the validated data.

            Args:
            self: The ResetPasswordSerializer instance.
            instance: The user instance to be updated.
            validated_data: The validated data containing the new password.

            Returns:
            updated_instance: The updated user instance with the new password.
        """
        # the get() and pop() methods correspond to the elements, but pop() removes them from the source dictionary, and the get() method remains there.
        # However, if you try to use the pop() method a second time, you will find that the elements have been removed from the dictionary, 
        # pop() removes the elements from the dictionary, so if it calls a second time for an already set one, it will give a response error (KeyError)
        
        # the first line of the method extracts the password field from the(validated_data) dictionary and removes it from the dictionary using the pop() method
        # the set_password() method is then called on the instance with the new password as an argument.This method hashes the password and sets ut as the new password for the instance
        # the last line of the method calls the update method of the parent serializer with the(instance, validated_data) arguments.This method updates the instance with the remaining validated_data
        
        # Extract the new password from the validated data 
        password = validated_data.pop('password') 
        # Set the new password for the user instance
        instance.set_password(password)
        # Call the update method of the parent class to update the user instance with the validated data
        return super(ResetPasswordSerializer, self).update(instance, validated_data)
       