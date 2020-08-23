from django import forms
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

class LoginForm(forms.Form):
    username=forms.CharField()
    password=forms.CharField(widget=forms.PasswordInput)
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = "学号/职工号"
        self.fields['password'].label = "密码"
