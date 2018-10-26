from django.contrib import admin

from rest_api.models import *


class UserAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'email', 'phone', 'institute', 'social_id', 'team']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'institute', 'social_id', 'team']
    list_filter = ['institute', 'team']
    fields = ['first_name', 'last_name', 'email', 'phone', 'institute', 'social_id', 'team']


class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'member1', 'member2', 'member3']
    search_fields = ['name']


admin.site.register(User, UserAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Settings)
