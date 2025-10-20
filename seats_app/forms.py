from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Only @nayatel.com emails are allowed",
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400',
            'placeholder': 'Enter your Nayatel email address'
        })
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400',
            'placeholder': 'Create a password'
        })
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-400',
            'placeholder': 'Confirm your password'
        })
    )

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()

        # ✅ Check if it's a Nayatel email
        if not email.endswith('@nayatel.com'):
            raise forms.ValidationError("Only @nayatel.com emails are allowed.")

        # ✅ Prevent duplicates
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data.get('email').strip().lower()

        # ✅ Derive username from email prefix
        username = email.split('@')[0]

        # ✅ Handle username conflicts (e.g., two users with same prefix)
        if User.objects.filter(username=username).exists():
            base_username = username
            counter = 1
            while User.objects.filter(username=f"{base_username}{counter}").exists():
                counter += 1
            username = f"{base_username}{counter}"

        user.username = username
        user.email = email

        if commit:
            user.save()
        return user



class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))