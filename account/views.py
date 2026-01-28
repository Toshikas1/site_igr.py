from django.shortcuts import render
from account.forms import LoginForm, RegisterForm
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout
from django.shortcuts import redirect

def login_page(request):
    form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.cleaned_data.get("user")
            login(request, user)
            return render(request, "main/index.html")
    return render(request, "account/login.html", context={"form": form})

def register_page(request):
    form = RegisterForm()
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data.get("password1")
            user.set_password(password)
            user.save()
            user = authenticate(
                request,
                username=form.cleaned_data.get("username"),
                password=password,
            )
            if user is not None:
                login(request, user)
                return render(request, "main/index.html")
    return render(request, "account/register.html", context={"form": form})


def logout_view(request):
    logout(request)
    return redirect('main')
# Create your views here.
