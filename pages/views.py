from django.shortcuts import render,redirect, get_object_or_404
from django.template.loader import get_template
from .models import Member, Initiative, Seminar
from .forms import MemberForm
from django.views import generic

def home(request):
    total_members = Member.objects.count()
    total_initiatives = Initiative.objects.count()
    return render(request, 'pages/home.html', {'total_members' : total_members, 'total_initiatives' : total_initiatives})

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
    return render(request, 'pages/about.html')

def contact(request):
    return render(request, 'pages/contact.html')

def calendar(request):
    return render(request, 'pages/calendar.html')

class SeminarView(generic.ListView):
    model = Seminar
    template_name = 'pages/seminars.html'
    context_object_name = 'seminars'

def seminar_detail(request, slug):
    seminar = get_object_or_404(Seminar, slug=slug)
    custom = f'pages/seminars/{slug}.html'
    default = 'pages/semiars/seminar_base.html'

    try:
        get_template(custom)
        template = custom
    except:
        template = default

    return render(request, template, {'seminar' : seminar})


class InitiativeView(generic.ListView):
    model = Initiative
    template_name = 'pages/initiatives.html'
    context_object_name = 'initiatives'

def initiative_detail(request, slug):
    initiative = get_object_or_404(Initiative, slug=slug)
    custom = f'pages/initiatives/{slug}.html'
    default = 'pages/initiatives/initiative_base.html'

    try:
        get_template(custom)
        template = custom
    except:
        template = default

    return render(request, template, {'initiative' : initiative})

def blog(request):
    return render(request, 'pages/blog.html')