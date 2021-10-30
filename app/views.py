from django.shortcuts import redirect, render, HttpResponse
from django.template.loader import render_to_string
from django.views import View
from django.contrib.auth import login, authenticate, logout
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from django.conf import settings

from app.models import Account
from .forms import Registration, AccountAuthenticationForm
from .utils import generate_token
# Create your views here.

def send_email(user, request):
    current_site = get_current_site(request)
    email_subject = "Activate your account"
    email_body = render_to_string('activate.html',{
            'user':user,
            'domain':current_site,
            'uid':urlsafe_base64_encode(force_bytes(user.pk)),
            'token':generate_token.make_token(user)
        })

    email = EmailMessage(subject=email_subject, body=email_body, 
            from_email=settings.EMAIL_FROM_USER,
            to=[user.email])
    email.send()
        

def activate_user(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = Account.objects.get(pk=uid)
    except Exception as e:
        user = None
    if user and generate_token.check_token(user, token):
        user.is_verified = True
        user.save()
        return redirect("login")


class MyView(View):
    form_class = Registration
    template_name = 'register.html'

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save()
            #user.save()

            send_email(user, request)
            return HttpResponse("success")

        return render(request, self.template_name, {'form': form})
    

class Login(View):
    form_class = AccountAuthenticationForm
    template_name = 'login.html'

    def get(self, request):
        return render(request, 'login.html')
    
    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            email = request.POST['email']
            password = request.POST['password']
            user = authenticate(email=email, password=password)
            if user:
                login(request, user)
                if not user.is_verified:
                    return HttpResponse("Verify email")
                return render(request, 'dashboard.html')

        return render(request, self.template_name, {'form': form})


class Logout(View):
    def get(self, request):
        logout(request)
        return redirect("login")
