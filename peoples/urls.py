from django.urls import path
from .views import create_member, MemberDeleteView, MemberDetailView, MemberUpdateView, MyDetailView


urlpatterns = [
    path('members/<int:team_id>/crate/', create_member, name='create-member'),
    path('member/<int:pk>/', MemberDetailView.as_view(), name='member_detail'),
    path('member/me/', MyDetailView.as_view(), name='my-detail'),
    path('member/<int:pk>/update/', MemberUpdateView.as_view(), name='member_update'),
    path('member/<int:pk>/delete/', MemberDeleteView.as_view(), name='member_delete'),
]