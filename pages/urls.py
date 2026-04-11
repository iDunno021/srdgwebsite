from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name="signup"),
    path('signup/success/', views.signup_success, name='signup_success'),
    path('seminars/<slug:slug>', views.seminar_detail, name='seminar_detail'),
    path('seminars/', views.SeminarView.as_view(), name='seminars'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('calendar/', views.calendar, name='calendar'),
    path('initiatives/<slug:slug>', views.initiative_detail, name='initiative_detail'),
    path('initiatives/', views.InitiativeView.as_view(), name='initiatives'),
    path('blog/', views.blog, name='blog'),
]