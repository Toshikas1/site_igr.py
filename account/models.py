from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    wins = models.IntegerField(default=0)
    games_played = models.IntegerField(default=0)
    



# Create your models here.
