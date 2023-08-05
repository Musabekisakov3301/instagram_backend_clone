import re
import threading
import phonenumbers
from rest_framework.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from decouple import config
from twilio.rest import Client 
from phonenumbers import geocoder

email_regex = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
phone_regex = re.compile(r"(\+[0-9]+\s*)?(\([0-9]+\))?[\s0-9\-]+[0-9]+")
username_regex = re.compile(r"^[a-zA-Z0-9_.-]+$")

def check_email_or_phone(email_or_phone):
    print(email_or_phone)
    phone_numbers = phonenumbers.parse(email_or_phone)
    #number_region = geocoder.description_for_number(phone_numbers, "en")


    if re.fullmatch(email_regex, email_or_phone):
           email_or_phone = "email"
         
    elif phonenumbers.is_valid_number(phone_numbers):
           email_or_phone = "phone"
           

    else:
        data = {
            'success': False,
            'message': 'Your email address or phone number is incorrect'
        }
        raise ValidationError(data)
    return email_or_phone

# this function(method) is for checking which type of user is logged in (usename,email, phone number)
def check_user_type(user_input): 
    #phone_numbers = phonenumbers.parse(user_input)
    if re.fullmatch(email_regex, user_input):
        user_input = 'email'
    elif re.fullmatch(phone_regex, user_input):
        user_input = 'phone'
    elif re.fullmatch(username_regex, user_input):
        user_input = 'username'
    else:
        data = {
            "success": True,
            "message": "Your email address,phone number,username is incorrect"
        }
        raise ValidationError(data)
    return user_input

class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()

class Email:
    @staticmethod
    def send_email(data):
        print(data)
        email = EmailMessage(
            subject=data['subject'],
            body=data['body'],
            to=[data['to_email']]
        )
        if data.get('content_type') == 'html':
            email.content_subtype = 'html'
        EmailThread(email).start()

def send_email(email, code):
    print(email)
    html_content = render_to_string( 
        'email/authentication/activate_account.html',
        {'code': code}
    )
    Email.send_email(
        {
            "subject":"Registration",
            "to_email":email,
            "body": html_content,
            "content_type": "html"
        }
    )

# Twilio
def send_phone_code(phone, code):
    account_sid = config('account_sid')
    auth_token = config('auth_token')
    client = Client(account_sid, auth_token)
    client.messages.create(
        body=f'Hi! Your verify code: {code}\n',
        from_='+998997346436',
        to=f'{phone}'
    )








