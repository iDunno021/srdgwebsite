from django import forms
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from django.template.response import TemplateResponse
from .models import Member, Initiative, Event, Seminar, MemberRole, BlogPost, BlogImage, BlogAttachment, EventRSVP

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'school', 'year_level', 'email']
    search_fields = ['first_name', 'last_name', 'email']
    list_filter = ['school', 'year_level']
    actions = ['add_to_committee']

    def add_to_committee(self, request, queryset):
        ids = ','.join(str(pk) for pk in queryset.values_list('pk', flat=True))
        return HttpResponseRedirect(
            reverse('admin:pages_member_add_to_committee') + f'?ids={ids}'
        )
    add_to_committee.short_description = 'Add selected members to a committee'

    def get_urls(self):
        return [
            path(
                'add-to-committee/',
                self.admin_site.admin_view(self.add_to_committee_view),
                name='pages_member_add_to_committee',
            ),
        ] + super().get_urls()

    def add_to_committee_view(self, request):
        if request.method == 'POST':
            ids = request.POST.get('ids', '').split(',')
            committee = request.POST.get('committee')
            title = request.POST.get('title', '')
            members = Member.objects.filter(pk__in=ids)
            created = sum(
                1 for member in members
                if MemberRole.objects.get_or_create(member=member, committee=committee, defaults={'title': title})[1]
            )
            skipped = len(ids) - created
            msg = f'Added {created} role(s).'
            if skipped:
                msg += f' {skipped} already had this committee and were skipped.'
            self.message_user(request, msg)
            return HttpResponseRedirect(reverse('admin:pages_memberrole_changelist'))

        ids = request.GET.get('ids', '')
        members = Member.objects.filter(pk__in=ids.split(','))
        context = {
            **self.admin_site.each_context(request),
            'title': 'Add members to committee',
            'members': members,
            'ids': ids,
            'committees': MemberRole.COMMITTEES,
        }
        return TemplateResponse(request, 'admin/add_to_committee.html', context)

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
