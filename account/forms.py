from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError

User = get_user_model()


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Имя пользователя",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Логин", "autofocus": True, "class": "form-input"}),
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Пароль", "class": "form-input"}),
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            user = authenticate(self.request, username=username, password=password)
            if user is None:
                raise ValidationError("Неверный логин или пароль")
            if not user.is_active:
                raise ValidationError("Учётная запись неактивна")
            cleaned_data["user"] = user
        return cleaned_data


class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Пароль", "class": "form-input"}),
    )
    password2 = forms.CharField(
        label="Подтверждение пароля",
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Подтвердите пароль", "class": "form-input"}),
    )

    class Meta:
        model = User
        fields = ("username", "email")
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Логин", "class": "form-input"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email", "class": "form-input"}),
        }

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Пользователь с таким именем уже существует")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Пользователь с таким email уже существует")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password1")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError({"password2": "Пароли не совпадают"})
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        user.set_password(password)
        if commit:
            user.save()
        return user
