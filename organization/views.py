from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect

from blog.models import Blog
from peoples.models import Member
from transaction.repositories.loan_repo import LoanRepository
from .models import Team
from .forms import TeamForm, ContactUsForm


def contact_us(request):
    if request.method == "POST":
        contact_form = ContactUsForm(request.POST)
        if contact_form.is_valid():
            contact_form.save()
            messages.success(request, "আপনার বার্তা সফলভাবে পাঠানো হয়েছে!")
            return redirect("home")
        else:
            messages.error(request, "আপনার বার্তা পাঠাতে সমস্যা হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।")
            return redirect("home")
    else:
        return redirect("home")


def home(request):
    total_loan_count = LoanRepository.get_total_loan_count()
    total_loan_amount = LoanRepository.get_total_loan_amount()
    blogs = Blog.objects.all().order_by("-id")[:3]

    context = {
        "total_loan_count": total_loan_count,
        "total_loan_amount": total_loan_amount,
        "total_member": Member.objects.filter(is_active=True).count(),
        "blogs": blogs,
        "contact_form": ContactUsForm,
    }
    return render(request, "index.html", context)


@login_required
def team_create(request):
    if request.method == "POST":
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.branch = request.user.branch
            team.owner = request.user
            team.save()
            return redirect("team_list")

    form = TeamForm(request.POST or None)
    print(form.errors)
    return render(request, "org/team_form.html", {"form": form})


# Read/Display list of teams
@login_required
def team_list(request):
    teams = Team.objects.filter(branch=request.user.branch)
    return render(request, "org/team_list.html", {"teams": teams})


# Update an existing team
@login_required
def team_update(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == "POST":
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            return redirect("team_list")
    else:
        form = TeamForm(instance=team)
    return render(request, "team_form.html", {"form": form})


# Delete a team
@login_required
def team_delete(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if request.method == "POST":
        team.delete()
        return redirect("team_list")
    return render(request, "team_confirm_delete.html", {"team": team})
