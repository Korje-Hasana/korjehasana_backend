from django.contrib.admin.sites import AlreadyRegistered
from django.contrib import admin
from django.apps import apps

from peoples.models import Staff, Member


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['id', 'name',]
    list_display_links = ['name']
    ordering = ['id']


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'serial_number', 'team', 'is_active')
    search_fields = ('name',)
    list_filter = ('team', 'is_active', 'branch')