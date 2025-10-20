from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

# ✅ Allowed email list
ALLOWED_EMAILS = [
    "umar.farooq@nayatel.com",
    "saif.zameer@nayatel.com",
    "fahad.zafar@nayatel.com",
    "tehseen.ahmed@nayatel.com",
    "umer.rizwan@nayatel.com",
    "akash.gir@nayatel.com",
    "muhammad.umer@nayatel.com",
    "waqas.rafique@nayatel.com",
    "hassan.raza@nayatel.com",
    "touqeer.malik@nayatel.com",
    "hamail.ashraf@nayatel.com",
    "faizan.bakhsh@nayatel.com",
    "samia.ahmed@nayatel.com",
    "lalain.aamir@nayatel.com",
    "zeenia.khan@nayatel.com",
    "hammad.yousaf@nayatel.com",
    "muhammad.azeem@nayatel.com",
    "iqra.ibrar@nayatel.com",
    "afshan.liaquat@nayatel.com",
    "hannan.afzal@nayatel.com",
    "raahim.fareed@nayatel.com",
    "zain.abideen@nayatel.com",
    "ahmad.uzzam@nayatel.com",
    "abdullah.nazar@nayatel.com",
    "muhammad.anees@nayatel.com",
    "arslanali.irshad@nayatel.com",
    "hasham.rizwan@nayatel.com",
    "aqdas.ayyaz@nayatel.com",
    "waleed.mahmood@nayatel.com",
    "aiman.badshah@nayatel.com",
    "muhammad.aqas@nayatel.com",
    "malik.danyal@nayatel.com",
    "asad.siddique@nayatel.com",
    "anas.bashir@nayatel.com",
    "aashar.mehmood@nayatel.com",
    "areeba.qadeer@nayatel.com",
    "saad.zafar@nayatel.com",
    "hira.liaqat@nayatel.com",
    "afaq.malik@nayatel.com",
    "muhammad.sabih@nayatel.com",
    "usama.zahid@nayatel.com",
    "muneeb.ashraf@nayatel.com",
    "muhammad.hassaan@nayatel.com",
    "momna.hassan@nayatel.com",
    "intern.jibran@nayatel.com",
    "abdullah.ashraf@nayatel.com",
    "syed.farhan@nayatel.com",
    "ahsan.raza@nayatel.com",
    "kainat.naseer@nayatel.com",
    "raheel.ghauri@nayatel.com",
    "waleed.ahmed@nayatel.com",
    "muhammad.shahmeer@nayatel.com",
    "malaika.ghayur@nayatel.com",
    "alyan.quddoos@nayatel.com",
    "saif.zameer@nayatel.com",
    "masooma.rubab@nayatel.com",
    "muzzamil.hussain@nayatel.com",
    "uzair.abdullah@nayatel.com",
    "anum.rafaqat@nayatel.com",
    "sohaib.ahsan@nayatel.com",
    "furqan.tariq@nayatel.com",
    "aksam.javed@nayatel.com",
    "sehrish.naseer@nayatel.com",
    "saqib.kamran@nayatel.com",
    "tahreem.saeed@nayatel.com",
    "hanif.muhammad@nayatel.com",
    "shiza.noor@nayatel.com",
]

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text="Only @nayatel.com emails are allowed",
        widget=forms.EmailInput(attrs={
            'class': "w-full px-4 py-2.5 rounded-lg border border-gray-700 bg-gray-800 text-gray-100 placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all duration-200",
            'placeholder': 'Enter your Nayatel email address'
        })
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': "w-full px-4 py-2.5 rounded-lg border border-gray-700 bg-gray-800 text-gray-100 placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all duration-200",
            'placeholder': 'Create a password'
        })
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            'class': "w-full px-4 py-2.5 rounded-lg border border-gray-700 bg-gray-800 text-gray-100 placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all duration-200",
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
        

        if email not in ALLOWED_EMAILS:
            raise ValidationError("You are not authorised for NTL-ES Workspace")

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