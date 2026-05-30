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
    list_display = ['title', 'start_time', 'end_time', 'location', 'tbc', 'initiative']
    list_filter = ['tbc']
    list_select_related = ['initiative']
    search_fields = ['title']
    autocomplete_fields = ['initiative']

@admin.register(EventRSVP)
class EventRSVPAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'email', 'event', 'created_at']
    list_filter = ['event']
    search_fields = ['first_name', 'last_name', 'email']
    autocomplete_fields = ['event', 'member']

@admin.register(MemberRole)
class MemberRoleAdmin(admin.ModelAdmin):
    list_display = ['member', 'committee', 'title']
    list_editable = ['committee', 'title']
    list_filter = ['committee']
    list_select_related = ['member']
    search_fields = ['member__first_name', 'member__last_name']
    autocomplete_fields = ['member']

@admin.register(Initiative)
class InitiativeAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'hidden']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title']
    inlines = [EventInline]
    autocomplete_fields = ['director']

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
