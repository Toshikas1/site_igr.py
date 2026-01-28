from django.db import models
from django.db.models import Avg
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from PIL import Image

User = get_user_model()

class Games(models.Model):
    name = models.CharField(max_length=50)
    played_games = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    rating = models.FloatField(default=0.0)
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    def __str__(self):
        return self.name

class Session(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    game = models.ForeignKey(Games, on_delete=models.CASCADE)
    players = models.ManyToManyField(User, related_name='sessions')
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_sessions')
# Create your models here.




class GameImage(models.Model):
    game = models.ForeignKey(
        Games,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='games/')
    def __str__(self):
        return f"Image for {self.game.name}"
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.image.path)
        if img.height != 450 or img.width != 450:
            output_size = (450, 450)
            img = img.resize(output_size, Image.LANCZOS)
            img.save(self.image.path)

            
class UserGameStats(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='game_stats'
    )
    game = models.ForeignKey(
        Games,
        on_delete=models.CASCADE,
        related_name='user_stats'
    )
    rating = models.FloatField(default = None, blank = True, null = True)
    games_played = models.IntegerField(default=0)
    games_won = models.IntegerField(default=0)
    def __str__(self):
        return f"Stats for {self.user.username} in {self.game.name}"


class GameRating(models.Model):
    """A user's rating for a game (1..10)."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    game = models.ForeignKey(Games, on_delete=models.CASCADE, related_name='ratings')
    rating = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'game')

    def __str__(self):
        return f"Rating {self.rating} by {self.user.username} for {self.game.name}"


@receiver(post_save, sender=GameRating)
@receiver(post_delete, sender=GameRating)
def update_game_avg_rating(sender, instance, **kwargs):
    """Recompute and update the average rating for the game."""
    avg = GameRating.objects.filter(game=instance.game).aggregate(avg=Avg('rating'))['avg'] or 0
    instance.game.rating = round(avg, 1)
    instance.game.save(update_fields=['rating'])




