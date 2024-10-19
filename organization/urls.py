from django.urls import path
from .views import *


urlpatterns = [
    path("teams", team_list, name="team_list"),
    path("teams/create", team_create, name="team_create"),
]