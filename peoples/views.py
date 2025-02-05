from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView, DeleteView, View
from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect
from .models import Member
from .forms import MemberForm
from organization.models import Branch, Team
from journal.repositories.journal_reposity import GeneralJournalRepository
from .services.member_services import MemberService


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


class MemberDetailView(DetailView):
    model = Member
    template_name = 'people/member_detail.html'
    context_object_name = 'member'


    # Add context to pass members GeneralJournal entries
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = self.object
        member_service = MemberService(branch=self.request.user.branch)
        context['member_transactions'] = member_service.get_member_transactions(member.id)
        return context


class MemberUpdateView(UpdateView):
    model = Member
    form_class = MemberForm
    template_name = 'people/member_update.html'
    context_object_name = 'member'

    def form_valid(self, form):
        return super().form_valid(form)


class MemberDeleteView(View):
    template_name = 'people/member_confirm_delete.html'

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        return render(request, self.template_name, {'member': member})

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        member.is_active = False  # Soft delete by setting is_active to False
        member.save()
        messages.success(request, f"Member '{member.name}' has been deactivated.")
        return redirect(reverse_lazy('deposit_list'), args={'team_id': member.team.id})
