from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from .models import Member, Initiative, Seminar, MemberRole
from .forms import MemberForm
from django.views import generic
import requests
import os


# ── Google Calendar integration ──────────────────────────────────────────────

CALENDAR_ID = 'socialresearchanddiscourse@gmail.com'

class CalendarEvent:
    """Wraps a Google Calendar event to look like a Seminar for the template."""
    is_calendar_event = True

    def __init__(self, title, description, start_time, end_time, html_link):
        self.title = title
        self.start_time = start_time
        self.end_time = end_time
        self.html_link = html_link
        self.slug = slugify(title)
        self.detail_url = html_link  # link out to Google Calendar

        # Use only the first non-empty line as the short description
        raw = (description or '').strip()
        first_line = next((l.strip() for l in raw.splitlines() if l.strip()), '')
        self.description = first_line

    @property
    def get_status(self):
        now = timezone.now()
        if not self.end_time:
            return 'upcoming'
        if self.end_time < now:
            return 'completed'
        if self.start_time and self.start_time <= now:
            return 'active'
        return 'upcoming'


def fetch_calendar_events():
    api_key = os.getenv('GOOGLE_CALENDAR_API_KEY')
    if not api_key:
        return []

    url = f'https://www.googleapis.com/calendar/v3/calendars/{CALENDAR_ID}/events'
    params = {
        'key': api_key,
        'singleEvents': True,
        'orderBy': 'startTime',
        'maxResults': 100,
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f'[SRDG] Google Calendar fetch error: {e}')
        return []

    events = []
    for item in data.get('items', []):
        start = item.get('start', {})
        end = item.get('end', {})
        start_str = start.get('dateTime') or start.get('date')
        end_str = end.get('dateTime') or end.get('date')

        if not start_str:
            continue

        from django.utils.dateparse import parse_datetime
        from django.utils.timezone import make_aware
        from datetime import datetime as dt

        def parse_gcal_dt(s):
            if not s:
                return None
            if 'T' in s:
                parsed = parse_datetime(s)
                if parsed and timezone.is_naive(parsed):
                    import pytz
                    parsed = make_aware(parsed, pytz.timezone('Pacific/Auckland'))
                return parsed
            else:
                import pytz
                auckland = pytz.timezone('Pacific/Auckland')
                return make_aware(dt.strptime(s, '%Y-%m-%d'), auckland)

        start_time = parse_gcal_dt(start_str)
        end_time = parse_gcal_dt(end_str)

        events.append(CalendarEvent(
            title=item.get('summary', 'Untitled Event'),
            description=item.get('description', ''),
            start_time=start_time,
            end_time=end_time,
            html_link=item.get('htmlLink', ''),
        ))

    return events


def build_seminars_list():
    """
    Merge Google Calendar events with DB seminars.
    DB seminars take priority (they have custom detail pages).
    Calendar events not matched to a DB seminar link out to Google Calendar.
    """
    db_seminars = {slugify(s.title): s for s in Seminar.objects.filter(hidden=False)}

    # Give each DB seminar a detail_url and mark it
    for s in db_seminars.values():
        s.is_calendar_event = False
        s.detail_url = reverse('seminar_detail', args=[s.slug])

    calendar_events = fetch_calendar_events()

    merged = {}
    for event in calendar_events:
        if event.slug in db_seminars:
            # Use the richer DB seminar instead
            merged[event.slug] = db_seminars[event.slug]
        else:
            merged[event.slug] = event

    # Add any DB seminars not on the calendar
    for slug, seminar in db_seminars.items():
        if slug not in merged:
            merged[slug] = seminar

    result = list(merged.values())
    result.sort(key=lambda x: x.start_time or timezone.now())
    return result


# ── Views ─────────────────────────────────────────────────────────────────────

def home(request):
    total_members = Member.objects.count()
    total_initiatives = Initiative.objects.filter(hidden=False).count()
    schools_count = len([s for s in Member.SCHOOLS if s[0] != 'other'])
    return render(request, 'pages/home.html', {
        'total_members': total_members,
        'total_initiatives': total_initiatives,
        'schools_count': schools_count,
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

def about(request):
    roles = MemberRole.objects.select_related('member').all()
    committees = {
        'General Committee': [r for r in roles if r.committee == 'general'],
        'Administrative Committee': [r for r in roles if r.committee == 'administrative'],
        'Technical Committee': [r for r in roles if r.committee == 'technical'],
    }
    return render(request, 'pages/about.html', {'committees': committees})

def contact(request):
    return render(request, 'pages/contact.html')

def calendar(request):
    return render(request, 'pages/calendar.html')

def seminars(request):
    seminar_list = build_seminars_list()
    return render(request, 'pages/seminars.html', {'seminars': seminar_list})

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
    queryset = Initiative.objects.filter(hidden=False)

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

def blog(request):
    return render(request, 'pages/blog.html')
