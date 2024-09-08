
from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect
from .models import Member
from .forms import MemberForm
from organization.models import Branch, Team


def create_member(request, team_id):
    # Get the branch from the logged-in user (assuming user has a related branch)
    user_branch = request.user.branch
    team = get_object_or_404(Team, id=team_id)

    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            try:
                member = form.save(commit=False)
                member.branch = user_branch  # Set branch to logged-in user's branch
                member.team = team
                member.save()
                # Redirect or show success message
                messages.success(request, f'সদস্য ভর্তি সফল হয়েছে')
                return redirect(team)
            except IntegrityError:
                messages.error(request, f'এই সিরিয়ালে সদস্য ভর্তি আছে')

    else:
        form = MemberForm()

    return render(request, 'people/create_member.html', {'form': form, 'team': team})
