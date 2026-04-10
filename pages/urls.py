from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name="signup"),
    path('signup/success/', views.signup_success, name='signup_success'),
    path('seminars/', views.seminars, name='seminars'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('calendar/', views.calendar, name='calendar'),
    path('initiatives/', views.initiatives, name='initiatives'),
    path('blog/', views.blog, name='blog')
]