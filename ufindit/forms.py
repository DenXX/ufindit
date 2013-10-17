from django import forms
from django.contrib.auth.models import User

class RegistrationForm(forms.ModelForm):
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs= \
        {'class':'form-control', 'placeholder': 'Confirm password'}))

    class Meta:
        model = User
        fields = ('email', 'password')
        widgets = {
            'email': forms.TextInput(attrs={'class':'form-control',
                'placeholder': 'Email'}),
            'password': forms.PasswordInput(attrs={'class':'form-control',
                'placeholder': 'Password'}),
        }

    def clean_password_confirm(self):
        password1 = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password_confirm')

        if password1 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")

        return password2