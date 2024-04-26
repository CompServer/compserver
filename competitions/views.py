from datetime import datetime
from logging import error
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import PermissionDenied
from django.contrib.auth.views import login_required
from django.db.models import Q, Count
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import SuspiciousOperation
from django.template.exceptions import TemplateDoesNotExist
from operator import attrgetter
import operator
import random
import zoneinfo
from typing import Union
from .forms import *
from .models import *
from .utils import *

def is_overflowed(list1: list, num: int):
  return all(x >= num for x in list1)

def get_tournament(request, tournament_id: int) -> Union[SingleEliminationTournament, RoundRobinTournament]:
    """Get a tournament by it's id, regardless of it's type.

    Args:
        tournament_id (int): The ID of the tournament.

    Raises:
        Http404: If the tournament does not exist or is not found.

    Returns:
        Union[SingleEliminationTournament, RoundRobinTournament]: The found tournament.
    """ 
    if SingleEliminationTournament.objects.filter(abstracttournament_ptr_id=tournament_id).exists():
        return get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    elif RoundRobinTournament.objects.filter(abstracttournament_ptr_id=tournament_id).exists():
        return get_object_or_404(RoundRobinTournament, pk=tournament_id)
    raise Http404


def generate_tournament_matches(request: HttpRequest, tournament_id: int):
    """View that calls the corresponding generate method for the tournament type."""
    tournament = get_tournament(request, tournament_id)
    if isinstance(tournament, SingleEliminationTournament):
        return generate_single_elimination_matches(request, tournament_id)
    elif isinstance(tournament, RoundRobinTournament):
        return generate_round_robin_matches(request, tournament_id)
    raise Http404


def generate_single_elimination_matches(request, tournament_id: int):
    #sort the list by ranking, then use a two-pointer alogrithm to make the starting matches
    tournament: SingleEliminationTournament = get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    arena_iterator = 0
    nmpt_iterator = 0
    arenas = [i for i in tournament.competition.arenas.filter(is_available=True)]
    if not arenas:
        raise SuspiciousOperation("No arenas available for this competition.")
    starting_time = tournament.start_time 
    team_ranks = []
    if tournament.prev_tournament == None or not tournament.prev_tournament.ranking_set.exists():
        teams = tournament.teams.all()
        for i, team in enumerate(teams, start=1):
            rank = Ranking.objects.create(tournament=tournament,team=team,rank=i)
            rank.save()
            team_ranks.append((rank.team, rank.rank))
    else:
        team_ranks = sorted([(rank.team, rank.rank) for rank in tournament.prev_tournament.ranking_set.all()], key=lambda x: x[1])
    #sort_list(teams, ranks)        
    rank_teams = {i+1: team_ranks[i][0] for i in range(len(team_ranks))}
    num_teams = len(rank_teams)
    num_matches, i = 1, 1
    extra_matches = []
    while num_matches * 2 < num_teams:
        num_matches *= 2
    while i <= num_matches - (num_teams - num_matches):
        extra_matches.append(i)
        i += 1
    j = num_teams
    while i < j:
        match = Match.objects.create(tournament=tournament)
        match.starting_teams.add(rank_teams[i], rank_teams[j])
        match.time = starting_time
        match.arena = arenas[arena_iterator]
        nmpt_iterator += 1
        if nmpt_iterator == arenas[arena_iterator].capacity:
            arena_iterator += 1
            nmpt_iterator = 0
            if arena_iterator >= len(arenas):
                arena_iterator = 0
                starting_time += tournament.event.match_time
        match.save()
        extra_matches.append(match)
        i += 1
        j -= 1

    #regular starting matches
    nmpt_iterator = 0
    if arena_iterator > 0:
        arena_iterator = 0
        starting_time += datetime.timedelta(minutes=10)
    i = 0
    j = len(extra_matches) - 1
    matches = []
    while i < j:
        match = Match.objects.create(tournament=tournament)
        if(isinstance(extra_matches[i], int)):
            match.starting_teams.add(rank_teams[extra_matches[i]])
        else:
            match.prev_matches.add(extra_matches[i])
        if(isinstance(extra_matches[j], int)):
            match.starting_teams.add(rank_teams[extra_matches[j]])
        else:
            match.prev_matches.add(extra_matches[j])
        match.time = starting_time
        match.arena = arenas[arena_iterator]
        nmpt_iterator += 1
        if nmpt_iterator == arenas[arena_iterator].capacity:
            arena_iterator += 1
            nmpt_iterator = 0
            if arena_iterator >= len(arenas):
                arena_iterator = 0
                starting_time += tournament.event.match_time 
        match.save()
        matches.append(match)
        i += 1
        j -= 1
    num_matches = len(matches)

    #2nd round
    nmpt_iterator = 0
    if arena_iterator > 0:
        arena_iterator = 0
        starting_time += tournament.event.match_time
    i = 0
    j = num_matches - 1
    new_matches = []
    while i < j:
        match = Match.objects.create(tournament=tournament)
        match.prev_matches.add(matches[i], matches[j])
        match.time = starting_time
        match.arena = arenas[arena_iterator]
        nmpt_iterator += 1
        if nmpt_iterator == arenas[arena_iterator].capacity:
            arena_iterator += 1
            nmpt_iterator = 0
            if arena_iterator >= len(arenas):
                arena_iterator = 0
                starting_time += tournament.event.match_time 
        match.save()
        new_matches.append(match)
        i += 2
        j -= 2
    i = 1
    j = num_matches - 2
    while i < j:
        match = Match.objects.create(tournament=tournament)
        match.prev_matches.add(matches[i], matches[j])
        match.time = starting_time
        match.arena = arenas[arena_iterator]
        nmpt_iterator += 1
        if nmpt_iterator == arenas[arena_iterator].capacity:
            arena_iterator += 1
            nmpt_iterator = 0
            if arena_iterator >= len(arenas):
                arena_iterator = 0
                starting_time += tournament.event.match_time
        match.save()
        new_matches.append(match)
        i += 2
        j -= 2
    matches = new_matches.copy()
    num_matches = len(matches)

    #rest of the matches
    while num_matches > 1:
        nmpt_iterator = 0
        if arena_iterator > 0:
            arena_iterator = 0
            starting_time += tournament.event.match_time
        new_matches = []
        for i in range(0, num_matches, 2):
            match = Match.objects.create(tournament=tournament)
            match.prev_matches.add(matches[i], matches[i+1])
            match.time = starting_time
            match.arena = arenas[arena_iterator]
            nmpt_iterator += 1
            if nmpt_iterator == arenas[arena_iterator].capacity:
                arena_iterator += 1
                nmpt_iterator = 0
                if arena_iterator >= len(arenas):
                    arena_iterator = 0
                    starting_time += tournament.event.match_time 
            match.save()
            new_matches.append(match)
        matches = []
        matches.extend(new_matches)
        num_matches = len(matches)
    return HttpResponseRedirect(reverse("competitions:single_elimination_tournament", args=(tournament_id,)))

def generate_round_robin_matches(request, tournament_id):
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    arena_iterator = 0
    nmpt_iterator = 0
    arenas = [i for i in tournament.competition.arenas.filter(is_available=True)]
    starting_time = tournament.start_time 
    teams = [team for team in tournament.teams.all()]
    for k in range(tournament.num_rounds):
        nmpt_iterator = 0
        if arena_iterator > 0:
            arena_iterator = 0
            starting_time += tournament.event.match_time
        num_participated = [0 for _ in range(len(teams))]
        while num_participated != [1 for _ in range(len(teams))]:
            match = Match.objects.create(tournament=tournament)
            for i in range(tournament.teams_per_match):
                j = random.randint(0, len(teams)-1)
                while(num_participated[j] > 0 or teams[j] in match.starting_teams.all()):
                    j = random.randint(0, len(teams)-1)          
                match.starting_teams.add(teams[j])
                num_participated[j] += 1 
                if num_participated == [1 for _ in range(len(teams))]:
                    break
            match.time = starting_time
            match.arena = arenas[arena_iterator]
            nmpt_iterator += 1
            if nmpt_iterator == arenas[arena_iterator].capacity:
                arena_iterator += 1
                nmpt_iterator = 0
                if arena_iterator >= len(arenas):
                    arena_iterator = 0
                    starting_time += tournament.event.match_time 
            match.round = k+1
            match.save()
    return HttpResponseRedirect(reverse("competitions:round_robin_tournament", args=(tournament_id,)))
    #still have a little bit of confusion with the ordering of matches.

def generate_round_robin_rankings(request, tournament_id):
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    team_wins = {team: 0 for team in tournament.teams.all()}
    matches = tournament.match_set.all()
    for match in matches:
        if match.advancers.all().count > 1:
            for team in match.advancers.all():
                team_wins[team] += tournament.points_per_tie
        else:
            for team in match.advancers.all():
                team_wins[team] += tournament.points_per_win
    sorted_team_wins = dict(sorted(team_wins.items(), key=lambda x:x[1]))
    i = len(sorted_team_wins)
    for i, kv in zip(range(len(sorted_team_wins), 1), sorted_team_wins.items()):
        key = kv[0]
        rank = Ranking.objects.create(tournament=tournament, team=key, rank=i)
        rank.save()
    pass

def swap_matches(request: HttpRequest, tournament_id: int):
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    form = None
    if request.method == 'POST':
        form = TournamentSwapForm(request.POST, tournament=tournament)
        if form.is_valid():
            team1 = form.cleaned_data.get('team1')
            team2 = form.cleaned_data.get('team2')
            round_num = form.cleaned_data.get('round_num')
            if round_num > tournament.num_rounds or round_num < 1:
                #print("Invalid round")
                return HttpResponseRedirect(reverse("competitions:swap_matches", args=(tournament_id,)))
            match1 = Match.objects.filter(tournament=tournament, starting_teams__in=[team1.id], round_num=round_num).first()
            match2 = Match.objects.filter(tournament=tournament, starting_teams__in=[team2.id], round_num=round_num).first()
            #print(match1, match2)
            match1.starting_teams.remove(team1)
            match2.starting_teams.remove(team2)
            match1.starting_teams.add(team2)
            match2.starting_teams.add(team1)
            match1.save()
            match2.save()
            #print(match1, match2)
            return HttpResponseRedirect(reverse("competitions:tournament", args=(tournament_id,)))
        else:
            for error_field, error_desc in form.errors.items():
                form.add_error(error_field, error_desc)
    if not form:
        form = TournamentSwapForm(tournament=tournament)
    return render(request, "competitions/swap_matches.html", {"form": form})

def home(request: HttpRequest):
    return render(request, "competitions/home.html")

def tournament(request: HttpRequest, tournament_id: int):
    tournament = get_tournament(request, tournament_id)
    if not tournament.match_set.exists():   
        return generate_tournament_matches(request, tournament_id)
    if isinstance(tournament, SingleEliminationTournament):
        #return HttpResponseRedirect(reverse("competitions:single_elimination_tournament", args=(tournament_id,)))
        return single_elimination_tournament(request, tournament_id)
    elif isinstance(tournament, RoundRobinTournament):
        #return HttpResponseRedirect(reverse("competitions:round_robin_tournament", args=(tournament_id,)))
        return round_robin_tournament(request, tournament_id)
    raise Http404

@login_required
def create_tournament(request: HttpRequest):
    competition_id = request.GET.get('competition_id',None)
    tournament_type = request.GET.get('tournament_type', None)

    if competition_id is None:
        messages.error(request, "No competition selected.")
        return HttpResponseRedirect(reverse("competitions:competitions"))
    try:
        competition = Competition.objects.get(pk=int(competition_id))
    except:
        messages.error(request, "Invalid competition.")
        return HttpResponseRedirect(reverse("competitions:competitions"))
    
    if not tournament_type:
        return render(request, "competitions/create_tournament.html", context={"competition": competition})
    
    tournament_type = str(tournament_type).lower().strip()

    if tournament_type == 'rr':
        FORM_CLASS = CreateRRTournamentForm
    elif tournament_type == 'se':
        FORM_CLASS = CreateSETournamentForm
    else:
        raise SuspiciousOperation

    form = None
    if request.method == 'POST':
        form = FORM_CLASS(request.POST, competition=competition)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("competitions:tournament", args=(form.instance.id,)))
        else:
            for error_field, error_desc in form.errors.items():
                form.add_error(error_field, error_desc)
    if not form:
        form = FORM_CLASS(competition=competition)
    return render(request, "FORM_BASE.html", {'form_title': "Create Tournament", 'action': f"?tournament_type={tournament_type}&competition_id={competition.id}" , "form": form})

def single_elimination_tournament(request: HttpRequest, tournament_id: int):
    redirect_to = request.GET.get('next', '')
    redirect_id = request.GET.get('id', None)
    if redirect_id:
        redirect_id = [redirect_id]
    tournament = get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    if request.method == 'POST':
        form = SETournamentStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            tournament.status = status
            tournament.save()
            if redirect_id == None:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}"))
            else:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}",args=redirect_id))
    if tournament.is_archived:
        return HttpResponseRedirect(reverse("competitions:competitions"))

    bracket_array = []

    def generate_competitor_data(match):
        output = []

        # T/F the match has a next match (is not the final)
        is_next = match.next_matches.exists()

        # loop through all the team playing in a match
        for team_index, team in enumerate(match.get_competing_teams()):

            # T/F the team advance from a previous match
            prev = team not in match.starting_teams.all()
            #set up variables
            connector_mult = 0
            connector = None

            if is_next:
                # the match the immediately follows our current match
                next_match = match.next_matches.all().first()
                # the set of matches that feed into next_match, which must include the current match
                feed_matches = next_match.prev_matches.all()
                # to determine wether connectors should go up or down
                midpoint = (feed_matches.count() - 1) / 2
                # where our current match is in the set of next matches
                match_index = list(feed_matches).index(match)
                # how many match heights away the connector is, used to calculate the heught
                connector_mult = abs(match_index - midpoint) + 0.5
                #class for the direction of the connector
                connector = "connector-down" if match_index < midpoint else "connector-up" if match_index > midpoint else "connector-straight"

                


            output.append({
                "name": team.name if team else "TBD",
                "won": team in match.advancers.all(),
                "is_next": is_next,
                "prev": prev and team,
                "match_id": match.id,
                "connector": connector,
                "connector_height": connector_mult,
            })
        return output
    
    def read_tree_from_node(curr_match, curr_round, base_index):
        if len(bracket_array) <= curr_round:
            bracket_array.append({})

        bracket_array[curr_round][base_index] = generate_competitor_data(curr_match) 
        
        prevs = curr_match.prev_matches.all()
        if prevs:
            for i, prev in enumerate(prevs):
                read_tree_from_node(prev, curr_round+1, 2*base_index+i)
        else:
            if len(bracket_array) <= curr_round+1:
                bracket_array.append({})
            bracket_array[curr_round+1][base_index] = None

    read_tree_from_node(Match.objects.filter(tournament=tournament_id).filter(next_matches__isnull=True).first(), 0, 0)

    bracket_array.pop()

    numRounds = len(bracket_array)

    mostTeamsInRound = max(sum(len(teams) if teams else 0 for teams in round.values()) for round in bracket_array)

    round_data = []
    matchWidth, connectorWidth, teamHeight = 200, 25, 25
    bracketWidth = (matchWidth + (connectorWidth * 2)) * numRounds
    bracketHeight = mostTeamsInRound * 50
    roundWidth = matchWidth + connectorWidth

    for round_matches in reversed(bracket_array):
        num_matches = len(round_matches)
        match_height = bracketHeight / num_matches
        match_data = []

        for team_data in round_matches.values():
            num_teams = len(team_data) if team_data else 0
            center_height = teamHeight * num_teams
            center_top_margin = (match_height - center_height) / 2

            match_data.append({
                "team_data": team_data,
                "match_height": match_height,
                "match_width": matchWidth,
                "center_height": center_height,
                "center_top_margin": center_top_margin,
            })

        round_data.append({"match_data": match_data})


    bracket_dict = {
        "bracketWidth": bracketWidth, 
        "bracketHeight": bracketHeight, 
        "roundWidth": roundWidth+connectorWidth, 
        "roundHeight": bracketHeight,
        "teamHeight": teamHeight,
        "connectorWidth": connectorWidth,
        "round_data": round_data,
    }
    
    tournament = get_object_or_404(SingleEliminationTournament, pk=tournament_id)
    context = {"tournament": tournament, "bracket_dict": bracket_dict}
    return render(request, "competitions/bracket.html", context)

def round_robin_tournament(request: HttpRequest, tournament_id: int):
    redirect_to = request.GET.get('next', '')
    redirect_id = request.GET.get('id', None)
    if redirect_id:
        redirect_id = [redirect_id]
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    if request.method == 'POST':
        form = TournamentStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            tournament.status = status
            tournament.save()
            if redirect_id == None:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}"))
            else:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}",args=redirect_id))
    if tournament.is_archived:
        return HttpResponseRedirect(reverse("competitions:competitions"))
    numRounds = tournament.num_rounds
    bracket_array =  [{i:[]} for i in range(numRounds)]
    for i in range(numRounds):
        rounds = sorted([match for match in Match.objects.filter(tournament=tournament, round=i+1)], key=lambda match : match.arena.id)
        for j in range(len(rounds)):
            team_data = []
            won = False
            is_next = True
            prev = False
            connector = None
            k = 0
            for team in rounds[j].starting_teams.all():
                if team in rounds[j].advancers.all():
                    won = True
                team_data.append({'name': team.name, 'won': won, 'is_next': is_next, 'prev': prev, 'match': rounds[j], 'connector': connector})
                won = False
                k += 1
            for q in range(k, tournament.teams_per_match):
                team_data.append({'name': 'TBD', 'won': won, 'is_next': is_next, 'prev': prev, 'match': rounds[j], 'connector': connector})
            bracket_array[i][j] = team_data
    
    num_matches = len(bracket_array)/numRounds
    mostTeamsInRound = tournament.teams_per_match

    round_data = []
    matchWidth, connectorWidth, teamHeight = 200, 25, 25
    bracketWidth = (matchWidth + (connectorWidth * 2)) * numRounds
    bracketHeight = mostTeamsInRound * 50
    roundWidth = matchWidth + connectorWidth

    for round_matches in bracket_array:
        match_height = bracketHeight / num_matches
        match_data = []

        for team_data in round_matches.values():
            num_teams = mostTeamsInRound if team_data else 0
            center_height = teamHeight * num_teams
            center_top_margin = (match_height - center_height) / 2

            match_data.append({
                "team_data": team_data,
                "match_height": match_height,
                "match_width": matchWidth,
                "center_height": center_height,
                "center_top_margin": center_top_margin,
                "arena": team_data[0].get('match').arena
             })

        round_data.append({"match_data": match_data})


    bracket_dict = {
        "bracketWidth": bracketWidth, 
        "bracketHeight": bracketHeight, 
        "roundWidth": roundWidth+connectorWidth, 
        "roundHeight": bracketHeight,
        "teamHeight": teamHeight,
        "connectorWidth": connectorWidth,
        "round_data": round_data,
    }
    tournament = get_object_or_404(RoundRobinTournament, pk=tournament_id)
    context = {"tournament": tournament, "bracket_dict": bracket_dict}
    return render(request, "competitions/round_robin_tournament.html", context)

def tournaments(request: HttpRequest):
    return render(request, "competitions/tournaments.html")

def competitions(request: HttpRequest):
    competition_list = Competition.objects.all().order_by("-status", "start_date")
    context = {"competition_list": competition_list, "form": CompetitionStatusForm()}
    return render(request, "competitions/competitions.html", context)

def competition(request: HttpRequest, competition_id: int):
    redirect_to = request.GET.get('next', '') #redirect to next after login
    redirect_id = request.GET.get('id', None) #redirect to page after id???
    if redirect_id:
        redirect_id = [redirect_id]
    competition = get_object_or_404(Competition, pk=competition_id)
    if request.method == 'POST':
        form = CompetitionStatusForm(request.POST)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            competition.status = status
            competition.save()
            if redirect_id:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}",args=redirect_id))
            elif redirect_to:
                return HttpResponseRedirect(reverse(f"competitions:{redirect_to}"))
            else:
                # if we don't know where they came from, just send them to the competition page
                return HttpResponseRedirect(reverse(f"competitions:competition", args=[competition_id]))
    if competition.is_archived:
        return HttpResponseRedirect(reverse("competitions:competitions"))
    elimination_tournaments = SingleEliminationTournament.objects.filter(competition__id = competition_id, status=Status.COMPLETE).order_by("-status", "-start_time")
    robin_tournaments = RoundRobinTournament.objects.filter(competition__id=competition_id, status=Status.COMPLETE).order_by("-status", "-start_time")
    context = {
        "competition": competition, 
        "form": SETournamentStatusForm(), 
        "robin_tournaments": robin_tournaments,
        "elimination_tournaments": elimination_tournaments,
    }
    return render(request, "competitions/competition.html", context)

def create_competition(request: HttpRequest):
    sport_id = request.GET.get('sport', None)
    if sport_id is None:
        return render(request, "competitions/create_competition.html", {"sports": Sport.objects.all()})
    try:
        sport_id = int(sport_id)
    except:
        raise Http404("Not a valid sport.")
    sport = get_object_or_404(Sport, pk=sport_id)

    form = None
    if request.method == 'POST':
        form = CreateCompetitionsForm(request.POST, sport=sport)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("competitions:competition", args=(form.instance.id,)))
        else:
            for error_field, error_desc in form.errors.items():
                form.add_error(error_field, error_desc)
    if not form:
        form = CreateCompetitionsForm(sport=sport)
    return render(request, "competitions/create_competition_form.html", {"form": form})

def credits(request: HttpRequest):
    return render(request, "competitions/credits.html")

@login_required
def judge_match(request: HttpRequest, match_id: int):
    instance: Match = get_object_or_404(Match, pk=match_id)
    user = request.user

    tournament: AbstractTournament = instance.tournament
    assert isinstance(tournament, AbstractTournament)
    competetion: Competition = tournament.competition
    assert isinstance(competetion, Competition)
    
    if not competetion.is_judgable or not tournament.is_judgable:
        messages.error(request, "This match is not judgable.")
        #print("This match is not judgable.")
        raise PermissionDenied("This match is not judgable.")
    # if the user is a judge for the tournament, or a plenary judge for the competition, or a superuser
    if not (user in tournament.judges.all() \
    or user in competetion.plenary_judges.all() \
    or user.is_superuser):
        messages.error(request, "You are not authorized to judge this match.")
        #print("You are not authorized to judge this match.")
        raise PermissionDenied("You are not authorized to judge this match.")
        #return HttpResponseRedirect(reverse('competitions:competition', args=[competetion.id]))

    winner_choices = []
    if instance.prev_matches.exists():
        winner_choice_ids = []
        for match in instance.prev_matches.all():
            if match.advancers.exists():
                winner_choice_ids.extend([x.id for x in match.advancers.all()])
            else:
                messages.error(request, "One or more previous matches have not been judged.")
                #print("One or more previous matches have not been judged.")
                raise SuspiciousOperation("One or more previous matches have not been judged.")
                #return HttpResponse(, reason="One or more previous matches have not been judged.")
        winner_choices = Team.objects.filter(id__in=winner_choice_ids)
    elif instance.starting_teams.exists():
        winner_choices = instance.starting_teams.all()
    else:
        messages.error(request, "This match has no starting teams or previous matches.")
        #print("This match has no starting teams or previous matches.")
        raise SuspiciousOperation("This match has no starting teams or previous matches.")
    
    # if instance.next_match is not None and instance.next_match.advancers.exists():
    #         messages.error(request, "The winner of the next match has already been decided.")
    #         #print("This match has already been judged.")
    #         return HttpResponseRedirect(reverse('competitions:tournament', args=[instance.tournament.id]))

    if request.method == 'POST':
        form = JudgeForm(request.POST, instance=instance, possible_advancers=winner_choices)
        if form.is_valid():
            form.save()
            messages.success(request, "Match judged successfully.")
            #print("Match judged successfully.")
            return HttpResponseRedirect(reverse('competitions:tournament', args=[instance.tournament.id]))

    form = JudgeForm(instance=instance, possible_advancers=winner_choices)
    return render(request, 'competitions/match_judge.html', {'form': form, 'match': instance, "teams": winner_choices})

def profile(request, user_id):
    #mpie charts
    #fix results page chart as well
    watch_competitions = Competition.objects.filter(status=Status.OPEN).order_by("-end_date", "-start_date", "-name")
    watch_tournaments = AbstractTournament.objects.filter(status=Status.OPEN).order_by("-start_time")
    newly_ended_competitions = Competition.objects.filter(status=Status.COMPLETE, end_date=datetime.date.today()).order_by("-end_date", "-start_date", "-name")
    user = User.objects.filter(id=user_id).first()
    if user_id in [user.id for user in [tournament.planeary_judges for tournament in SingleEliminationTournament.objects.all()]]:
        is_judge = True
        current_gigs = Match.objects.filter(planeary_judges__user__id == user_id, status = Status.OPEN).order_by("-time")
        upcoming_gigs = Match.objects.filter(planeary_judges__user__id == user_id, status = Status.SETUP).order_by("-status", "-time")
        judged_tournaments = AbstractTournament.ojbects.filter(Q(status = Status.COMPLETE) | Q(status = Status.CLOSED), planeary_judges__id == user_id).order_by("-start_time", "-competition")
    else:
        is_judge = False
    if user_id in [team.coach.id for team in Team.objects.all()]:
        is_coach = True
        coached_teams = Team.objects.filter(coach_id = user_id).order_by("-name")
        team_records = dict()
        team_names = list()
        team_wins = list()
        team_losses = list()
        for team in coached_teams:
            wins = AbstractTournament.objects.filter(competition__teams=team, status=Status.COMPLETE, match_set__last__advancers=team).order_by("-start_time", "-competition")
            if wins:
                wins_count = wins.count()
            else:
                wins_count = 0
            losses = AbstractTournament.objects.filter(competition__teams=team, status=Status.COMPLETE).exclude(match_set__last__advancers=team).order_by("-start_time", "-competition")
            if losses:
                losses_count = losses.count()
            else:
                losses_count = 0
            team_names.append(team.name)
            team_losess.append(losses_count)
            team_wins.append(wins_count)
            rankings = list()
            for ranking in Ranking.objects.filter(team=team).order_by("-tournament", "-rank"):
                line = ""
                line = line + "Ranked " + ranking.rank + " in " + ranking.tournament.event.name + " tournament at " + ranking.tournament.competition.name
                rankings.append((line, ranking.tournament))
            team_rankings[team] = rankings
    else:
        is_coach = False
    context = {
        'coached_teams': coached_teams,
        'watch_tournaments': watch_tournaments,
        'watch_competitions': watch_competitions,
        'newly_ended_competitions': newly_ended_competitions,
        'team_records': team_records,
        'team_rankings': team_rankings,
        'is_coach': is_coach,
        'is_judge': is_judge,
        'judged_tournaments': judged_tournaments,
        'current_gigs': current_gigs,
        'upcoming_gigs': upcoming_gigs,
        'team_wins': team_wins,
        'team_losses': team_losses,
        'team_names': team_names,
        'user': user,
    }
    return render(request, 'competitions/user_profile.html', context)


def organization(request, organization_id):
    organization = Organization.objects.filter(id = organization_id).first()
    associated_teams = Team.objects.filter(organization__id = organization_id).order_by("-name")
    results = dict()
    for team in associated_teams:
        wins_count = 0
        losses_count = 0
        if AbstractTournament.objects.filter(competition__teams=team):
            wins = AbstractTournament.objects.filter(competition__teams=team, match_set__last__advancers=team).order_by("-status", "-start_time")
            losses = wins = AbstractTournament.objects.filter(competition__teams=team).exclude(match_set__last__advancers=team).order_by("-status", "-start_time")
            wins_count = wins.count()
            losses_count = losses.count()
        results[team.name] = (wins_count, losses_count)
    context = {
        'organization': organization,
        'associated_teams': associated_teams,
        'results': results,
    }
    return render(request, 'organization.html', context)

def results(request, competition_id):
    competition = Competition.objects.get(id = competition_id)
    tournaments = [tournament for tournament in competition.tournament_set.order_by("points", "start_time", "competition").filter(status = Status.COMPLETE)]
    for robin_tournament in RoundRobinTournament.objects.filter(competition__id=competition_id, status = Status.COMPLETE).order_by("points", "-start_time", "-competition"):
        tournaments.append(robin_tournament)
    tournament_names = [tournament.event.name for tournament in tournaments]
    team_names = [team.name for team in competition.teams.order_by("name")]
    tournament_colors = [tournament.colors for tournament in tournaments]
    for tournament_name in tournament_names:
        tournament = AbstractTournament.objects.filter(event__name=tournament_name, competition__id=competition_id, status=Status.COMPLETE)
        scores = dict()
        for team_name in team_names:
            team = Team.objects.filter(name=team_name).first()
            if is_single_elimination(tournament):
                last_match = Match.objects.filter(tournament__id = tournament.id, next_matches__isnull = True).first()
                if team in last_match.advancers.all():
                    scores[tournament_name] = (team_name, tournament.points)
                else:
                    scores[tournament_name] = (team_name, 0)
            #each tournament name should have a team name and a scor ein a list
            else:
                robin_totals = dict()
                for match in tournament.match_set.all():
                    if team in match.advancers.all():
                        if match.advancers.count() == 1:
                            robin_totals[team_name] = tournament.points_per_win
                        if match.advancers.count() > 1:
                            robin_totals[team_name] = tournament.points_per_tie
                    else:
                        robin_totals[team_name] = tournament.points_per_loss
        #addd robin totals to scores
        #sum together results for each tournament team and display
    judge_names = ""
    #judge_names = [plenary_judge.first_name + " " + plenary_judge.last_name for plenary_judge in competition.plenary_judges.order_by("-username")]
    context = {
        'tournament_names': tournament_names,
        'team_names': team_names,
        'competition': competition,
        'tournaments': tournaments,
        'tournament_scorings': scores,
        'judge_names': judge_names,
        'team_and_total': totals,
    }
    return render(request, "competitions/results.html", context)

def team(request: HttpRequest, team_id: int):
    team = Team.objects.filter(id=team_id).first()
    today = timezone.now().date()
    upcoming_matches = Match.objects.filter(Q(starting_teams__id=team_id) | Q(prev_matches__advancers__id=team_id), tournament__competition__start_date__lte=today, tournament__competition__end_date__gte=today).exclude(advancers=None).order_by("-time")
    starter_matches = Match.objects.filter(Q(starting_teams__id=team_id)).exclude(advancers=None)
    previous_advancer_matches = Match.objects.filter(Q(prev_matches__advancers__id=team_id)).exclude(advancers=None)
    past_matches = [match for match in starter_matches]
    for match in previous_advancer_matches:
        past_matches.append(match)
    past_matches_dict = dict()
    for match in past_matches:
        past_matches_dict[match] = match.time
    sorted_past_matches = {k for k, v in sorted(past_matches_dict.items(), key=lambda item: past_matches_dict[1])}
    past_competitions = Competition.objects.filter(teams__id = team_id, status = Status.COMPLETE).order_by("end_date", "start_date", "name")
    past_tournaments_won = list()
    past_tournaments = SingleEliminationTournament.objects.filter(teams__id = team_id, status = Status.COMPLETE).order_by("start_time", "competition")
    if past_tournaments.exists():
        for past_tournament in past_tournaments:
            if team_id in [team.id for team in past_tournament.match_set.last().advancers.all()]:
                past_tournaments_won.append(past_tournament)
    losses = list()
    wins = list()
    draws = list()
    if past_matches:
        for match in past_matches:
            first_half = " in "
            second_half = " tournament @" + match.tournament.competition.name
            if match.starting_teams.exists():
                starting_teams_names = ",".join([team.name for team in match.starting_teams.exclude(id=team_id)])
            if match.prev_matches.exists():
                prev_advancing_names = ",".join([team.name for team in match.prev_matches.last().advancers.all().exclude(id=team_id)])
            if match.advancers.exists():
                advancers_names = ",".join([team.name for team in match.advancers.all().exclude(id=team_id)])
            if match.prev_matches.exists():
                if team_id in [team.id for team in match.advancers.all()]:
                    if match.advancers.count() == match.starting_teams.count() + len([advancer for advancer in match.prev_matches.last().advancers.all()]): 
                        draws.append((("Drew in match against " + ",".join(starting_teams_names) + ",".join(prev_advancing_names) + first_half), match.tournament, second_half, match))
                    else:
                        if match.advancers.count() == 1:
                            wins.append((("Won against " + ",".join(starting_teams_names) + ",".join(prev_advancing_names) + first_half), match.tournament, second_half, match))
                        elif match.advancers.count() > 2: 
                            wins.append((("Won with " + advancers_names + first_half), match.tournament, second_half, match))
                else:
                    if match.advancers.count() == 1:
                        losses.append((("Lost against " + match.advancers.first().name + first_half), match.tournament, second_half, match))
                    elif match.advancers.count() > 1: 
                        losses.append((("Lost against " + advancers_names + first_half), match.tournament, second_half, match))
            else:
                if team_id in [team.id for team in match.advancers.all()]:
                    if match.advancers.count() == match.starting_teams.count():
                        draws.append((("Drew with " + starting_teams_names + first_half), match.tournament, second_half))
                    else:
                        if match.advancers.count() == 1:
                            wins.append((("Won against " + starting_teams_names + first_half), match.tournament, second_half, match))
                        elif match.advancers.count() > 1:
                            wins.append((("Won with " + "," + advancers_names + first_half), match.tournament, second_half, match))
                else:
                    if match.advancers.count() == 1: 
                        losses.append((("Lost against " + match.advancers.first().name + first_half), match.tournament, second_half, match))
                    elif match.advancers.count() > 1: 
                        losses.append((("Lost against " + advancers_names + first_half), match.tournament, second_half, match))
    loss_dict = dict()
    for loss in losses:
        loss_dict[loss] = loss[-1].time
    sorted_losses = {k for k, v in sorted(loss_dict.items(), key=lambda item: loss_dict[1])}
    wins_dict = dict()
    for win in wins:
        wins_dict[win] = win[-1].time
    sorted_wins = {k for k, v in sorted(wins_dict.items(), key=lambda item: wins_dict[1])}
    draws_dict = dict()
    for draw in draws:
        draws_dict[draw] = draw[-1].time
    sorted_draws = {k for k, v in sorted(draws_dict.items(), key=lambda item: draws_dict[1])}
    byes = list()
    old_upcoming_matches = list(Match.objects.filter(Q(starting_teams__id=team_id) | Q(prev_matches__advancers__id=team_id), advancers=None).order_by("-time"))
    for match in old_upcoming_matches:
        if match.id in [match.id for match in upcoming_matches.all()]:
            old_upcoming_matches.remove(match)
    for match in past_matches:
        if team_id in [team.id for team in match.advancers.all()]:
            if match.starting_teams.all().exists():
                if match.prev_matches.last():
                    if team_id in [team.id for team in match.starting_teams.all()] or team_id in [team.id for team in match.prev_matches.last().starting_teams]:
                        if match.advancers.count() == 1:
                            if match.starting_teams.count() == 1 and match.prev_matches.last().starting_teams.count() == 1:
                                byes.append((("BYE" + first_half), match.tournament, second_half))
                            if match.starting_teams.count() == 0 and match.prev_matches.last().starting_teams.count() == 0:
                                byes.append((("BYE" + first_half), match.tournament, second_half))
    byes_dict = dict()
    for bye in byes:
        byes_dict[bye] = bye.time
    sorted_byes = {k for k, v in sorted(byes_dict.items(), key=lambda item: byes_dict[1])}
    context = {
        'team': team,
        'upcoming_matches': upcoming_matches,
        'old_upcoming_matches': old_upcoming_matches,
        'wins': sorted_wins,
        'byes': sorted_byes,
        'past_matches': sorted_past_matches,
        'draws': sorted_draws,
        'losses': sorted_losses,
        'won_tournaments': past_tournaments_won,
        'past_tournaments': past_tournaments,
        'past_competitions': past_competitions,
    }
    return render(request, "competitions/team.html", context)

def _raise_error_code(request: HttpRequest):
    try:
        error_code = int(request.GET.get('code', 0)) # type: ignore
    except:
        raise SuspiciousOperation

    # if error_code == 403:
    #     raise PermissionDenied
    # elif error_code == 404:
    #     raise Http404
    # else:
    try:
        return render(request, f'{error_code}.html', status=error_code)
    except TemplateDoesNotExist:
        try:
            return render(request, 'ERROR_BASE.html', context={"error_code": error_code, "error": f"{error_code} {http_codes.get(error_code, 'Unknown')}"}, status=error_code)
        except:
            return HttpResponse(status=error_code)

def not_implemented(request: HttpRequest, *args, **kwargs):
    """
    Base view for not implemented features. You can  use this view to show a message to the user that the feature is not yet implemented,
    or if you want to add a view for a URL to a page that doesn't exist yet.
    """
    messages.error(request, "This feature is not yet implemented.")
    #raise NotImplementedError()
    return render(request, 'skeleton.html')

def set_timezone_view(request: HttpRequest):
    """Please leave this view at the bottom. Create any new views you need above this one"""
    if request.method == "POST":
        if request.POST["timezone"]:
            request.session["timezone"] = request.POST["timezone"]
            messages.success(request, f"Timezone set successfully to {request.POST['timezone']}.")
            return redirect("/")
        else:   
            messages.error(request, "Invalid timezone.")
    timezones = sorted(zoneinfo.available_timezones())
    return render(request, "timezones.html", {"timezones": timezones})
