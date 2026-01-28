from main.views import main,top_igrokov, top_igr, create_session, session_detail, game_detail, create_game, player_detail, add_images
from django.urls import path




urlpatterns = [
    path("", main, name="main"),
    path("top-igrokov/", top_igrokov, name="top_igrokov"),
    path("top-igr/", top_igr, name="top_igr"),
    path("create-session/", create_session, name="create_session"),
    path("session/<int:session_id>/", session_detail, name="session_detail"),
    path("game/<int:game_id>/", game_detail, name="game_detail"),
    path("create-game/", create_game, name="create_game"),
    path("player/<int:player_id>/", player_detail, name="player_detail"),
    path("player/<int:player_id>/<int:game_id>/", player_detail, name="player_detail"),
    path("game/<int:game_id>/add_images", add_images, name="add_images"),
]
