# -*- coding: utf-8 -*-

from django import forms


class UserCreationForm(forms.Form):
    username = forms.RegexField(regex=r'^[\w.@+-]+$', max_length=30, label='Username')
    email = forms.EmailField(label="E-mail", required=False)
    password = forms.CharField(label="Password", required=False)
    password_retyped = forms.CharField(label="Retype Password", required=False)

    def __init__(self, *args, **kwargs):
        self.edit_mode = kwargs.pop('edit_mode', False)
        super(UserCreationForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(UserCreationForm, self).clean()
        password = cleaned_data.get("password")
        email = self.data.get("email", '')
        password_retyped = cleaned_data.get("password_retyped")

        if not email:
            raise forms.ValidationError("Enter an e-mail please.")

        if not self.edit_mode:
            if not password or len(password) <= 0:
                raise forms.ValidationError("Enter a password please.")

            if password != password_retyped:
                raise forms.ValidationError("Passwords do not match.")

        return cleaned_data
