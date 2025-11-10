from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'your.email@example.com'}))
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'John'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'placeholder': 'Doe'}))
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')


class LoginForm(forms.Form):
    email = forms.EmailField(label='Email Address')
    password = forms.CharField(widget=forms.PasswordInput)
