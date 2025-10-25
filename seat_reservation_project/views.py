from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views import View
from seats_app.forms import RegisterForm




def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "registration/register.html",{"form": form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/workspace')  # already logged in → redirect to dashboard/home
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/workspace')  # redirect to your dashboard view
        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    return redirect('/')