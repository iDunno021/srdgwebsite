import json
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template

from .models import Member, Initiative, Event, Seminar, MemberRole, BlogPost, BlogImage, BlogAttachment
from .forms import MemberForm, BlogPostForm
from django.views import generic

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
        'Board of Directors': [r for r in roles if r.committee == 'general'],
        'Administrative Committee': [r for r in roles if r.committee == 'administrative'],
        'Technical Committee': [r for r in roles if r.committee == 'technical'],
        'Outreach Department': [r for r in roles if r.committee == 'outreach'],
        'Finance Department': [r for r in roles if r.committee == 'finance'],
    }
    return render(request, 'pages/about.html', {'committees': committees})

def contact(request):
    return render(request, 'pages/contact.html')

def calendar(request):
    status_colors = {'upcoming': '#C8391A', 'active': '#2e7d32', 'completed': '#1a4a7a'}

    events = [
        {
            'title': e.title,
            'start': e.start_time.isoformat(),
            'end': e.end_time.isoformat(),
            'color': status_colors[e.get_status],
        }
        for e in Event.objects.all()
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

class BlogView(generic.ListView):
    model = BlogPost
    template_name = 'pages/blog.html'
    context_object_name = 'posts'
    queryset = BlogPost.objects.filter(hidden=False).order_by('-published_at')

def blog_detail(request, id):
    post = get_object_or_404(BlogPost, id=id, hidden=False)
    return render(request, 'pages/blog_detail.html', {'post': post})

def create_blog(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save()
            for image in request.FILES.getlist('images'):
                BlogImage.objects.create(post=post, image=image)
            for attachment in request.FILES.getlist('attachments'):
                BlogAttachment.objects.create(post=post, file=attachment, name=attachment.name)
            return redirect('blog')
    else:
        form = BlogPostForm()
    return render(request, 'pages/create_blog.html', {'form': form})
