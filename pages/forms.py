from django import forms
from .models import Member, BlogPost, EventRSVP

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'school', 'year_level', 'email']
    
    

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'author', 'cover_image', 'body']


class EventRSVPForm(forms.ModelForm):
    class Meta:
        model = EventRSVP
        fields = ['first_name', 'last_name', 'email']
