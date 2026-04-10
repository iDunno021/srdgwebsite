from django import forms
from .models import Member

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['first_name', 'last_name', 'school', 'year_level', 'email']
        widgets = {
            'year_level': forms.NumberInput(attrs={'min': 9, 'max': 13})
        }