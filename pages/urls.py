from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('signup/success/', views.signup_success, name='signup_success'),
    path('seminars/', views.SeminarView.as_view(), name='seminars'),
    path('seminars/<slug:slug>/', views.seminar_detail, name='seminar_detail'),
    path('staff/', views.staff, name='staff'),
    path('contact/', views.contact, name='contact'),
    path('calendar/', views.calendar, name='calendar'),
    path('initiatives/', views.InitiativeView.as_view(), name='initiatives'),
    path('initiatives/<slug:slug>/', views.initiative_detail, name='initiative_detail'),
    path('events/', views.events, name='events'),
    path('events/<int:event_id>/attend/', views.event_attend, name='event_attend'),
    path('events/<int:event_id>/rsvp/', views.event_rsvp, name='event_rsvp'),
    path('blog/', views.BlogView.as_view(), name='blog'),
    path('blog/<int:id>/', views.blog_detail, name='blog_detail'),
    path('blog/<int:id>/react/<str:reaction>/', views.blog_react, name='blog_react'),
    path('blog/create/', views.create_blog, name='create_blog'),
    path('partners/', views.partners, name='partners'),
<<<<<<< HEAD
    path('tumbleweed/', views.family_page, name='family_page'),


=======
    path('robots.txt', TemplateView.as_view(template_name='pages/robots.txt', content_type='text/plain')),
    path('network263/', views.network263, name='network263'),
>>>>>>> 20c60cbd5f3d2079d227715b17bb3a5b195089a9
]