from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from competitions.forms import RRTournamentForm, SETournamentForm
from crispy_forms.utils import render_crispy_form
import html
from competitions.views import competition
from competitions.models import Competition, Sport, Team

# Create your views here.

def teams(request: HttpRequest):
    sport = request.GET.get('sport')
    response = ''

    sport = get_object_or_404(Sport, pk=sport)

    for team in Team.objects.filter(sport=sport):
        response += f'<option value="{team.id}">{team.name}</option>\n'
    
    return HttpResponse(content=response)

def new_team(request: HttpRequest):
    sport_id = request.POST.get('sport')
    name = html.escape(request.POST.get('new_team'))
    name = name.strip()

    sport = Sport.objects.get(id=sport_id)
    response = ''
    if sport:
        if name != "":
            team = Team(name=name, sport=sport)
            team.save()
        for team in Team.objects.filter(sport=sport):
            response += f'<option value="{team.id}">{team.name}</option>\n'
    
    return HttpResponse(content=response)

def tournament_form(request: HttpRequest, competition_id: int):
    if request.method == 'GET':
        tournament_type = str(request.GET.get('tournament_type','')).lower().strip()
    elif request.method == 'POST':
        tournament_type = str(request.POST.get('tournament_type')).lower().strip()
    else:
        raise ValueError("Invalid request method")

    competition = get_object_or_404(Competition, pk=competition_id)

    FORM_CLASS = None

    if tournament_type == 'rr':
        FORM_CLASS = RRTournamentForm
    
    elif tournament_type == 'se':
        FORM_CLASS = SETournamentForm
    else:
        raise ValueError("Invalid tournament type")

    form = FORM_CLASS(competition=competition)

    return render(request, 'CSRF_FORM.html', {'form': form, 'action': f"?competition_id={competition_id}&tournament_type={tournament_type}"})

