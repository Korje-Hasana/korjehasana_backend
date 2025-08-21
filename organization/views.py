from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView

from blog.models import Blog
from peoples.models import Member
from transaction.repositories.loan_repo import LoanRepository
from .models import Team, Branch
from .forms import TeamForm
from .services import BranchService


def home(request):
    total_loan_count = LoanRepository.get_total_loan_count()
    total_loan_amount = LoanRepository.get_total_loan_amount()
    blogs = Blog.objects.all().order_by('-id')[:3]
    context = {
        'total_loan_count': total_loan_count,
        'total_loan_amount': total_loan_amount,
        'total_member': Member.objects.filter(is_active=True).count(),
        'blogs': blogs,
    }
    return render(request, 'index.html', context)

@login_required
def team_create(request):
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.branch = request.user.branch
            team.owner = request.user
            team.save()
            return redirect('team_list')


    form = TeamForm(request.POST or None)
    return render(request, 'org/team_form.html', {'form': form})


# Read/Display list of teams
@login_required
def team_list(request):
    teams = Team.objects.filter(branch=request.user.branch)
    return render(request, 'org/team_list.html', {'teams': teams})


# Update an existing team
@login_required
def team_update(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == 'POST':
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            return redirect('team_list')
    else:
        form = TeamForm(instance=team)
    return render(request, 'team_form.html', {'form': form})

# Delete a team
@login_required
def team_delete(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == 'POST':
        team.delete()
        return redirect('team_list')
    return render(request, 'team_confirm_delete.html', {'team': team})


class BranchStatisticsView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Admin view for branch statistics"""
    model = Branch
    template_name = 'org/branch_statistics.html'
    context_object_name = 'branch_stats'

    def test_func(self):
        # Only allow admin users (adjust this condition based on your user model)
        return self.request.user.is_superuser or getattr(self.request.user, 'is_admin', False)

    def get_queryset(self):
        # We don't use the default queryset, instead we use our service
        branch_service = BranchService()
        return branch_service.get_branch_statistics()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add overall statistics
        branch_service = BranchService()
        context['overall_stats'] = branch_service.get_overall_statistics()

        return context