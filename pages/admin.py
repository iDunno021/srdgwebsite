from django.contrib import admin
from .models import Member, Initiative, Event, Seminar, MemberRole, BlogPost, BlogImage, BlogAttachment

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
    list_display = ['title', 'start_time', 'end_time', 'location', 'initiative']

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
    list_display = ['title', 'author', 'published_at', 'hidden']
    list_filter = ['hidden']
    search_fields = ['title', 'author']
    inlines = [BlogImageInline, BlogAttachmentInline]