import json
from django.shortcuts import render, redirect, get_object_or_404
from ratelimit.decorators import ratelimit
from django.template.loader import get_template
from django.contrib import messages
from django.db import IntegrityError
from .models import Member, Initiative, Event, Seminar, MemberRole, BlogPost, BlogImage, BlogAttachment, ArtPiece, AboutPhoto
from .forms import MemberForm, BlogPostForm, EventRSVPForm
from django.views import generic
import resend
from django.conf import settings

def home(request):
    total_members = Member.objects.count()
    total_initiatives = Initiative.objects.filter(hidden=False).count()
    schools_count = len([s for s in Member.SCHOOLS if s[0] != 'other'])
    total_activites = Seminar.objects.filter(hidden=False).count() + Event.objects.count()
    initiatives = Initiative.objects.filter(hidden=False)
    about_side_photos = list(AboutPhoto.objects.filter(slot='side'))
    about_middle_photos = list(AboutPhoto.objects.filter(slot='middle'))
    about_middle_photo = about_middle_photos[0] if about_middle_photos else None
    about_side_urls_json = json.dumps([p.image.url for p in about_side_photos])
    about_middle_urls_json = json.dumps([p.image.url for p in about_middle_photos])
    return render(request, 'pages/new_home.html', {
        'total_members': total_members,
        'total_initiatives': total_initiatives,
        'schools_count': schools_count,
        'total_activities': total_activites,
        'initiatives': initiatives,
        'about_side_photos': about_side_photos[:4],
        'about_middle_photo': about_middle_photo,
        'about_side_urls_json': about_side_urls_json,
        'about_middle_urls_json': about_middle_urls_json,
    })

def signup(request):
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            if member.school == 'other':
                other_school = request.POST.get('other_school')
                if not other_school:
                    form.add_error(None, 'Please enter your school name.')
                    return render(request, 'pages/signup.html', {'form': form})
                member.school = other_school
            member.save()
            return redirect('signup_success')
    else:
        form = MemberForm()
    return render(request, 'pages/signup.html', {'form': form})

def signup_success(request):
    return render(request, 'pages/signup_success.html')

def staff(request):
    roles = sorted(MemberRole.objects.select_related('member').all(), key=lambda r: (r.member.first_name.lower() != 'amber' or r.member.last_name.lower() != 'cai'))
    committees = {
        'General Committee': [r for r in roles if r.committee == 'general'],
        'Educational Advancement': [r for r in roles if r.committee == 'ea'],
        'Politics of Tomorrow': [r for r in roles if r.committee == 'ype'],
        'Young Artists Collective': [r for r in roles if r.committee == 'yac'],
        'Administrative Committee': [r for r in roles if r.committee == 'administrative'],
        'Technical Committee': [r for r in roles if r.committee == 'technical'],
        'Outreach Department': [r for r in roles if r.committee == 'outreach'],
        'Finance Department': [r for r in roles if r.committee == 'finance'],
    }
    return render(request, 'pages/staff.html', {'committees': committees})

def contact(request):
    return render(request, 'pages/contact.html')

def events(request):
    all_events = Event.objects.select_related('initiative').order_by('start_time')
    return render(request, 'pages/events.html', {'events': all_events})

def event_attend(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'pages/event_attend.html', {
        'event': event,
        'form': EventRSVPForm(),
    })

def event_rsvp(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventRSVPForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            member = Member.objects.filter(email=email).first()
            rsvp = form.save(commit=False)
            rsvp.event = event
            if member:
                rsvp.member = member
            try:
                rsvp.save()
            except IntegrityError:
                messages.error(request, "You've already registered for this event with that email.")
                return redirect('event_attend', event_id=event_id)
            messages.success(request, "You're registered! We'll see you there.")
            return redirect('event_attend', event_id=event_id)
    return redirect('events')

def calendar(request):
    status_colors = {'upcoming': '#C8391A', 'active': '#2e7d32', 'completed': '#1a4a7a'}

    events = [
        {
            'title': e.title,
            'start': e.start_time.isoformat(),
            'end': e.end_time.isoformat(),
            'color': status_colors[e.get_status],
            'url': f'/events/{e.id}/attend/',
        }
        for e in Event.objects.filter(start_time__isnull=False, end_time__isnull=False)
    ]
    seminars = [
        {
            'title': s.title,
            'start': s.start_time.isoformat(),
            'end': s.end_time.isoformat(),
            'url': f'/seminars/{s.slug}/',
            'color': status_colors[s.get_status],
        }
        for s in Seminar.objects.filter(hidden=False)
    ]
    return render(request, 'pages/calendar.html', {'calendar_events': json.dumps(events + seminars)})

class SeminarView(generic.ListView):
    model = Seminar
    template_name = 'pages/seminars.html'
    context_object_name = 'seminars'
    queryset = Seminar.objects.filter(hidden=False)

def seminar_detail(request, slug):
    seminar = get_object_or_404(Seminar, slug=slug, hidden=False)
    custom = f'pages/seminars/{slug}.html'
    default = 'pages/seminars/seminar_base.html'
    try:
        get_template(custom)
        template = custom
    except:
        template = default
    return render(request, template, {'seminar': seminar})

class InitiativeView(generic.ListView):
    model = Initiative
    template_name = 'pages/initiatives.html'
    context_object_name = 'initiatives'
    queryset = Initiative.objects.filter(hidden=False).order_by('order', 'pk')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['art_pieces'] = ArtPiece.objects.filter(hidden=False)
        return ctx

def initiative_detail(request, slug):
    initiative = get_object_or_404(Initiative, slug=slug, hidden=False)
    custom = f'pages/initiatives/{slug}.html'
    default = 'pages/initiatives/initiative_base.html'
    try:
        get_template(custom)
        template = custom
    except:
        template = default
    return render(request, template, {'initiative': initiative})

class BlogView(generic.ListView):
    model = BlogPost
    template_name = 'pages/blog.html'
    context_object_name = 'posts'
    queryset = BlogPost.objects.filter(approved=True).order_by('-published_at')

def blog_detail(request, id):
    post = get_object_or_404(BlogPost, id=id, approved=True)
    return render(request, 'pages/blog_detail.html', {'post': post})

@ratelimit(key='ip', rate='1/h', method='POST', block=True)
def create_blog(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('blog')
    else:
        form = BlogPostForm()
    return render(request, 'pages/create_blog.html', {'form': form})

def event_rsvp(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = EventRSVPForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            member = Member.objects.filter(email=email).first()
            rsvp = form.save(commit=False)
            rsvp.event = event
            if member:
                rsvp.member = member
            try:
                rsvp.save()
            except IntegrityError:
                messages.error(request, "You've already registered for this event with that email")
                return redirect('event_attend', event_id=event_id)
            try:
                resend.api_key = settings.RESEND_API_KEY
                resend.Emails.send({
                    "from": "noreply@srdg.co.nz",
                    "to": email,
                    "subject": "You've registered for the Youth Political Debate!",
                    "html": """
                        <h2> You're in! </h2>
                        <p>Thanks for registering for the <strong>Youth Political Debate</strong>.</p>
                        <p>We'll see you there!</p>
                    """
                })
            except Exception as e:
                print(f"Email failed: {e}")
            messages.success(request, "You're registered! We'll see you there.")
            return redirect('event_attend', event_id=event_id)
    return redirect('events')

def partners(request):
    total_members = Member.objects.count()
    schools_count = len([s for s in Member.SCHOOLS if s[0] != 'other'])

    return render(request, 'pages/partners.html', {
        'total_members': total_members,
        'schools_count': schools_count,
    })