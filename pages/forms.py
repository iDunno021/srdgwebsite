from django import forms
from .models import Member, BlogPost, EventRSVP

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'school', 'year_level', 'email']

    def clean_first_name(self):
        return self.cleaned_data['first_name'].lower()

    def clean_last_name(self):
        return self.cleaned_data['last_name'].lower()

    def clean_email(self):
        return self.cleaned_data['email'].lower()



class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'author', 'cover_image', 'body']

class EventRSVPForm(forms.ModelForm):
    class Meta:
        model = EventRSVP
        fields = ['first_name', 'last_name', 'email']

    def clean_email(self):
        return self.cleaned_data['email'].lower()
