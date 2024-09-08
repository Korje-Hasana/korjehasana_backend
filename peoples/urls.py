from django.urls import path
from .views import create_member


urlpatterns = [
    path('members/<int:team_id>/crate/', create_member, name='create-member')
]