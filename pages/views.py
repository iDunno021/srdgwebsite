from django.shortcuts import render,redirect
from .models import Member
from .forms import MemberForm

def home(request):
    totalMembers = Member.objects.count()
    return render(request, 'pages/home.html', {'totalMembers' : totalMembers})

def signup(request):
    if request.method == 'POST':
        form = MemberForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('signup_success')
    else:
        form = MemberForm()
    return render(request, 'pages/signup.html', {'form': form})

def signup_success(request):
    return render(request, 'pages/signup_success.html')

def seminars(request):
    return render(request, 'pages/seminars.html')

def about(request):
    return render(request, 'pages/about.html')

def contact(request):
    return render(request, 'pages/contact.html')

def calendar(request):
    return render(request, 'pages/calendar.html')

def initiatives(request):
    return render(request, 'pages/initiatives.html')

def blog(request):
    return render(request, 'pages/blog.html')