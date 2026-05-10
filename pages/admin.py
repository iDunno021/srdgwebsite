from django import forms
from django.contrib import admin
from .models import Member, Initiative, Event, Seminar, MemberRole, BlogPost, BlogImage, BlogAttachment, EventRSVP

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'school', 'year_level', 'email']
    search_fields = ['first_name', 'last_name', 'email']
    list_filter = ['school', 'year_level']

class EventInline(admin.TabularInline):
    model = Event
    extra = 1

@admin.register(Seminar)
class SeminarAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_time', 'end_time', 'hidden']
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_time', 'start_tbc', 'end_time', 'end_tbc', 'location', 'initiative']
    list_filter = ['start_tbc', 'end_tbc']
    fieldsets = [
        (None, {'fields': ['title', 'description', 'location', 'initiative']}),
        ('Start time', {'fields': [('start_time', 'start_tbc')]}),
        ('End time', {'fields': [('end_time', 'end_tbc')]}),
    ]

@admin.register(EventRSVP)
class EventRSVPAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'event', 'created_at']
    list_filter = ['event']
    search_fields = ['first_name', 'last_name', 'email']

@admin.register(MemberRole)
class MemberRoleAdmin(admin.ModelAdmin):
    list_display = ['member', 'committee', 'title']
    list_filter = ['committee']

@admin.register(Initiative)
class InitiativeAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'hidden']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [EventInline]

class BlogImageInline(admin.TabularInline):
    model = BlogImage
    extra = 1

class BlogAttachmentInline(admin.TabularInline):
    model = BlogAttachment
    extra = 1

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'published_at', 'approved']
    list_filter = ['approved']
    search_fields = ['title', 'author']
    inlines = [BlogImageInline, BlogAttachmentInline]