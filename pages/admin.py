from django.contrib import admin
from .models import Member, Initiative, Seminar, Event

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'school', 'year_level', 'email']
    search_fields = ['first_name', 'last_name', 'email']

class EventInline(admin.TabularInline):
    model = Event
    extra = 1

@admin.register(Seminar)
class SeminarAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_time', 'end_time', 'hidden']
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_time', 'end_time', 'location', 'initiative']

@admin.register(Initiative)
class InitiativeAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'hidden']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [EventInline]