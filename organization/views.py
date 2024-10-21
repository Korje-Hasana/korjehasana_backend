from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from .models import Team
from .forms import TeamForm
import logging
logger = logging.getLogger(__name__)


def home(request):
    return render(request, 'index.html')

# @login_required
# def team_create(request):
#     if request.method == 'POST':
#         form = TeamForm(request.POST)
#         if form.is_valid():
#             team = form.save(commit=False)
#             team.branch = request.user.branch
#             team.owner = request.user
#             team.save()
#             return redirect('team_list')


#     form = TeamForm(request.POST or None)
#     print(form.errors)
#     return render(request, 'org/team_form.html', {'form': form})


@login_required
def team_create(request):
    if request.user.role != 'BRANCH_OWNER':
        return redirect('permission_denied')  # Unauthorized users redirected

    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.branch = request.user.branch
            team.owner = request.user
            team.save()
            logger.info(f'Team {team.name} created by {request.user.username}')
            return redirect('team_list')

    form = TeamForm(request.POST or None)
    return render(request, 'org/team_form.html', {'form': form})


# Read/Display list of teams
@login_required
def team_list(request):
    teams = Team.objects.filter(branch=request.user.branch)
    return render(request, 'org/team_list.html', {'teams': teams})


# Update an existing team
# @login_required
# def team_update(request, pk):
#     team = get_object_or_404(Team, pk=pk)
#     if request.method == 'POST':
#         form = TeamForm(request.POST, instance=team)
#         if form.is_valid():
#             form.save()
#             return redirect('team_list')
#     else:
#         form = TeamForm(instance=team)
#     return render(request, 'team_form.html', {'form': form})

@login_required
def team_update(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == 'POST':
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            logger.info(f'Team {team.name} updated by {request.user.username}')
            return redirect('team_list')
    else:
        form = TeamForm(instance=team)
    return render(request, 'team_form.html', {'form': form})

# Delete a team
# @login_required
# def team_delete(request, pk):
#     team = get_object_or_404(Team, pk=pk)
#     if request.method == 'POST':
#         team.delete()
#         return redirect('team_list')
#     return render(request, 'team_confirm_delete.html', {'team': team})

@login_required
def team_delete(request, pk):
    team = get_object_or_404(Team, pk=pk)

    if team.members.count() > 1:  
        messages.error(request, "You cannot delete the team as it still has members.")
        return redirect('team_list')

    if request.method == 'POST':
        team.delete()
        messages.success(request, 'Team deleted successfully.')
        return redirect('team_list')

    return render(request, 'team_confirm_delete.html', {'team': team})