from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.db.models import Avg
from main.models import Games, Session, UserGameStats, GameRating
from .forms import GameImageForm
from django.contrib.auth.decorators import user_passes_test
User = get_user_model()
# Create your views here.
def main(request):
    user = request.user
    # Optional filter by game name via GET param `q`
    q = request.GET.get('q', '').strip()
    if q:
        sessions = Session.objects.filter(game__name__icontains=q).order_by('-created_at')
    else:
        sessions = Session.objects.all().order_by('-created_at')
    return render(request, "main/index.html", context={"sessions": sessions, "user": user, "q": q})

def top_igrokov(request):
    # Тестовые данные игроков (в будущем можно вытянуть из БД)
    players = User.objects.all().order_by('-wins')
    ranked_players = []
    for i, player in enumerate(players, start=1):
        player.rank = i
        ranked_players.append(player)
    return render(request, "main/top_igrokov.html", {"players": ranked_players})

def top_igr(request):
    # Тестовые данные игр (в будущем можно вытянуть из БД)
    games = Games.objects.all().order_by('-rating')
    ranked_games = []
    for i, game in enumerate(games, start=1):
        game.rank = i
        ranked_games.append(game)
    return render(request, "main/top_igr.html", {"games": ranked_games})

from .forms import SessionForm

@user_passes_test(lambda user : user.is_superuser)
def create_session(request):
    if request.method == "POST":
        form = SessionForm(request.POST)
        if form.is_valid():
            players = form.cleaned_data['players']
            winner = form.cleaned_data['winner']
            if winner:
                winner_stats, created = UserGameStats.objects.get_or_create(
                    user=winner,
                    game=form.cleaned_data['game'],
                    defaults={'games_played': 0, 'games_won': 0}
                )
                winner.wins += 1
                winner.save()
                winner_stats.games_won += 1
                winner_stats.save()
            game = Games.objects.get(id=form.cleaned_data['game'].id)
            played_games = game.played_games + 1
            game.played_games = played_games
            game.save()
            for player in players:
                stats, created = UserGameStats.objects.get_or_create(
                    user=player,
                    game=form.cleaned_data['game'],
                    defaults={'games_played': 0, 'games_won': 0}
                )
                stats.games_played += 1
                stats.save()
            session = form.save(commit=False)
            session.save()
            form.save_m2m()
            return render(request, "main/create_session.html", {"form": SessionForm(), "success": True})
    else:
        form = SessionForm()
    return render(request, "main/create_session.html", {"form": form})

def session_detail(request, session_id):
    try:
        session = Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        return render(request, "main/session_detail.html", {"error": "Сессия не найдена."})

    return render(request, "main/session_detail.html", {"session": session})

def game_detail(request, game_id):
    try:
        game = Games.objects.get(id=game_id)
        images = game.images.all()
    except Games.DoesNotExist:
        return render(request, "main/game_detail.html", {"error": "Игра не найдена."})

    # Prepare top players (user_stats) for this game, ordered by wins
    user_stats = list(UserGameStats.objects.filter(game=game).select_related('user').order_by('-games_won'))
    for i, s in enumerate(user_stats, start=1):
        s.rank = i
        s.win_rate = round((s.games_won / s.games_played) * 100, 1) if s.games_played else 0

    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = GameRating.objects.get(user=request.user, game=game).rating
        except GameRating.DoesNotExist:
            user_rating = None

    # Handle rating submission (AJAX or form POST)
    if request.method == 'POST' and 'rating' in request.POST:
        if not request.user.is_authenticated:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'auth_required'}, status=403)
            else:
                return render(request, "main/game_detail.html", {"game": game, "images": images, "error": "Пожалуйста, войдите, чтобы оценить игру.", "user_stats": user_stats if request.user.is_authenticated else None})
        try:
            val = int(request.POST.get('rating'))
            if val < 1 or val > 10:
                raise ValueError
        except (TypeError, ValueError):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': 'invalid_rating'}, status=400)
            else:
                return render(request, "main/game_detail.html", {"game": game, "images": images, "error": "Недопустимая оценка.","user_stats": user_stats if request.user.is_authenticated else None})

        GameRating.objects.update_or_create(user=request.user, game=game, defaults={'rating': val})
        # recalc and save average
        avg = GameRating.objects.filter(game=game).aggregate(avg=Avg('rating'))['avg'] or 0
        game.rating = round(avg, 1)
        game.save(update_fields=['rating'])
        user_rating = val
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'avg': game.rating, 'user_rating': user_rating})

    return render(request, "main/game_detail.html", {"game": game, "images": images, "user_rating": user_rating, "rating_range": list(range(1, 11)), "user_stats": user_stats})

@user_passes_test(lambda user : user.is_superuser)
def create_game(request):
    from .forms import GameForm
    if request.method == "POST":
        form = GameForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return render(request, "main/create_game.html", {"form": GameForm(), "success": True})
    else:
        form = GameForm()
    return render(request, "main/create_game.html", {"form": form})

def player_detail(request, player_id, game_id=None):
    try:
        player = User.objects.get(id=player_id)
    except User.DoesNotExist:
        return render(request, "main/player_detail.html", {"error": "Игрок не найден."})

    # Filter by game if provided
    if game_id:
        stats_qs = player.game_stats.filter(game_id=game_id).select_related('game')
    else:
        stats_qs = player.game_stats.select_related('game').all()

    # materialize queryset to compute aggregates and add per-row win rate
    stats = list(stats_qs)
    total_played = sum(s.games_played for s in stats)
    total_won = sum(s.games_won for s in stats)
    win_rate = round((total_won / total_played) * 100, 1) if total_played else 0

    for s in stats:
        s.win_rate = round((s.games_won / s.games_played) * 100, 1) if s.games_played else 0

    return render(request, "main/player_detail.html", {"player": player, "stats": stats, "total_played": total_played, "total_won": total_won, "win_rate": win_rate})
@user_passes_test(lambda user : user.is_superuser)
def add_images(request, game_id):
    try:
        game = Games.objects.get(id=game_id)
    except Games.DoesNotExist:
        return render(request, "main/add_images.html", {"error": "Игра не найдена."})

    if request.method == "POST":
        form = GameImageForm(request.POST, request.FILES)
        if form.is_valid():
            image_obj = form.save(commit=False)
            image_obj.game = game
            image_obj.save()
            return render(request, "main/add_images.html", {"form": GameImageForm(), "success": True, "game": game})
    else:
        form = GameImageForm()

    return render(request, "main/add_images.html", {"form": form, "game": game})