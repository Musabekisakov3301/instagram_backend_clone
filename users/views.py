from django.shortcuts import render
from django.utils.datetime_safe import datetime
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.decorators import permission_classes
from rest_framework.generics import CreateAPIView,UpdateAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import SignUpSerializer,ChangeUserInformation,ChangeUserPhotoSerializer,LoginSerializer,LoginRefreshSerializer,LogoutSerializer,ForgotPasswordSerializer,ResetPasswordSerializer
from .models import User,DONE,CODE_VERIFIED,NEW,VIA_EMAIL,VIA_PHONE
from shared.utility import send_email, check_email_or_phone


class CreateUserView(CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny, )
    serializer_class = SignUpSerializer

class VerifyAPIView(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        user = self.request.user
        code = self.request.data.get('code')
          
        self.check_verify(user, code)
        return Response(
            data= {
                'success': True,
                'auth_status': user.auth_status,
                'access': user.token()['access'],
                'refresh': user.token()['refresh_token']

            }
        )
    
    @staticmethod
    def check_verify(user, code):
        verifies = user.verify_codes.filter(expiration_time__gte=datetime.now(), code=code, is_confirmed=False)
        if not verifies.exists():
            data = {
                'message': 'Your verification code is incorrect or outdated'
            }
            raise ValidationError(data)
        else:
            verifies.update(is_confirmed=True)
        if user.auth_status == NEW:  #user.auth_status not in DONE:
            user.auth_status = CODE_VERIFIED
            user.save()
        return True
    
class GetNewVerification(APIView):
    permission_classes = [IsAuthenticated, ]

    def get(self, request, *args, **kwagrs):
        user = self.request.user
        self.check_verification(user)

        if user.auth_type == VIA_EMAIL:
            code = user.create_verify_code(VIA_EMAIL)
            send_email(user.email, code)
        elif user.auth_type == VIA_PHONE:
            code = user.create_verify_code(VIA_PHONE)
            send_email(user.phone_number, code)
        else:
            data = {
                'message': 'Your email address or phone number is incorrect'
            }
            raise ValidationError(data)
        
        return Response( 
            {
               'success': True,
               'message': 'Your code has been sent again'
            }           
        )

    @staticmethod
    def check_verification(user):
        verifies = user.verify_codes.filter(expiration_time__gte=datetime.now(), is_confirmed=False)
        if verifies.exists():
            data = {
                'message': f"Your code is still available. Please wait a bit\nYou have to send the request within 2 minutes.To get the verification code again"
            }
            raise ValidationError(data)

class ChangeUserInformationView(UpdateAPIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = ChangeUserInformation
    http_method_names = ['patch','put'] # put - this is a method of updating an object in all parameters
                                        # patch - this is a method of updating an object by only one parameter
   
    # this function(method) is used to change the user request data without id
    def get_object(self):
        return self.request.user
    
    # this update function(method) is used to 'put' request
    def update(self, request, *args, **kwargs):
        super(ChangeUserInformationView, self).update(request, *args, **kwargs)
        data = {
            'success': True,
            'message': 'User updated successfully',
            'auth_status': self.request.user.auth_status,
        }
        return Response(data, status=200)
    
    def partial_update(self, request, *args, **kwargs):
        super(ChangeUserInformationView, self).partial_update(request, *args, **kwargs)
        data = {
            'success': True,
            'message': 'User updated successfully',
            'auth_statu': self.request.user.auth_status,
        }
        return Response(data, status=200) 

class ChangeUserPhotoView(APIView):
    permission_classes = [IsAuthenticated, ]

    def put(self, request, *args, **kwagrs):
        serializer = ChangeUserPhotoSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            serializer.update(user, serializer.validated_data)
            return Response({
                'message': 'the photo has been successfully changed'
            }, status=200)
        return Response(
            serializer.errors, status=400
        )

class LoginView(TokenObtainPairView):
    # it is not possible to use the permission class here, because during login the user does not have access and refresh token
    serializer_class = LoginSerializer

class LoginRefreshView(TokenRefreshView):
    serializer_class = LoginRefreshSerializer

class LogoutView(APIView):
    serializer_class = LogoutSerializer
    permission_classes = [IsAuthenticated, ]
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        try:
            refresh_token = self.request.data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            data = {
                'success': True,
                'message': 'You are logout'
            }
            return Response(data, status=205)
        except TokenError:
            return Response(status=400)
        
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny, ] # in this class if in permission classes will (isauthenticated) it will be error,
    serializer_class = ForgotPasswordSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data) # this variable gets from the serializer class what the user gets from the request (data)
        serializer.is_valid(raise_exception=True) # the serializer is first checked for validation if not, it will output an error(raise_exception)   
        email_or_phone = serializer.validated_data.get('email_or_phone') # this field from the verified serializer data gets the entered value through the user(because this field is entered from the user)
        user = serializer.validated_data.get('user') # this veriable gets from validated data
        if check_email_or_phone(email_or_phone) == 'phone':
            code = user.create_verify_code(VIA_PHONE)
            send_email(email_or_phone, code)
        elif check_email_or_phone(email_or_phone) == 'email':
            code = user.create_verify_code(VIA_EMAIL)
            send_email(email_or_phone, code)
        
        return Response(
            {
                'success': True,
                'message': 'Verify code has been successfully sent',
                'access': user.token()['access'],
                'refresh': user.token()['refresh_token'],
                'user_status': user.auth_status,
            }, status=200
        )

class ResetPasswordView(UpdateAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [IsAuthenticated, ]
    http_method_names = ['pathc, put']

    # this function is used to find out which user changed the password
    def get_object(self):
       return self.request.user 
    
    def updata(self, request, *args, **kwargs):
        response = super(ResetPasswordSerializer, self).update(request, *args, **kwargs)
        try:
            user = User.objects.get(id=response.data.get('id'))
        except ObjectDoesNotExist as e:
            raise NotFound(detail='User not found')
        return Response(
            {
                'success': True,
                'message': 'The password has been successfully changed',
                'access': user.token()['access'],
                'refresh': user.token()['refresh_token'],
            }
        )