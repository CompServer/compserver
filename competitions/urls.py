from django.urls import path
from . import views
from django.views.generic.base import RedirectView

app_name = "competitions"
urlpatterns = [
    path('', views.home, name="home"),
    path("competition/", views.competitions, name="competitions"),
    path("competition/<int:competition_id>/", views.competition, name="competition"),
    path("team/<int:team_id>/", views.team, name="team"),
    path("tournament/", views.tournaments, name="tournaments"),
    path("tournament/<int:tournament_id>/", views.single_elimination_tournament, name="single_elimination_tournament"),
    # path("coach/<int:coach_id>/", views.coach, name="coach-page"),
    path("match/<int:match_id>/", views.match, name="match"),
    path('match/<int:pk>/judge/', views.judge_match, name='match_judge'),
    path('credits/', views.credits, name="credits"),
    path("match/<int:pk>/judge/", views.judge_match, name="match"),
    path('settings/timezone/',views.set_timezone_view, name='set_timezone'),
]
