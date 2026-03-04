from django import forms
from django.contrib.auth import get_user_model
from .models import Session, Games, GameImage
from django.core.exceptions import ValidationError

User = get_user_model()


class SessionForm(forms.ModelForm):
    players = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Игроки",
    )

    winner = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Победитель (опционально)",
    )

    class Meta:
        model = Session
        fields = ("game", "players", "winner")
        widgets = {
            "game": forms.Select(attrs={"class": "form-input"}),
        }

    def clean(self):
        cleaned = super().clean()
        players = cleaned.get("players")
        winner = cleaned.get("winner")
        if winner and players and winner not in players:
            raise ValidationError({"winner": "Победитель должен быть среди участников сессии"})
        return cleaned

class GameForm(forms.ModelForm):
    image = forms.FileField()
    class Meta:
        model = Games
        fields = ['name', 'description', 'rating', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea'}),
            'rating': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-input'}),
        }
    def clean(self):
        cleaned = super().clean()
        name = cleaned.get("name")
        description = cleaned.get("description")
        rating = cleaned.get("rating")
        image = cleaned.get("image")
        if name and description and rating is not None and image:
            return cleaned
        raise ValidationError({"name": "Пожалуйста, заполните все поля формы."})
    def save(self, commit = True):
        form_obj = super().save(commit = False)
        img_file = self.cleaned_data.get("image")
        if img_file:
            form_obj.image = img_file.read()
        if commit:
            form_obj.save()
        return form_obj




class GameImageForm(forms.ModelForm):
    image = forms.FileField()
    class Meta:
        model = GameImage
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'class': 'form-input'}),
        }
    def save(self,commit = True):
        obj = super().save(commit = False)
        img_file = self.cleaned_data.get("image")
        if img_file:
            obj.image = img_file.read()
        if commit:
            obj.save()
        return obj

