from django.db import models
from django.utils import timezone

class Member(models.Model):
    SCHOOLS = [
        ('AGS', 'Auckland Grammar School'),
        ('STC', 'St Cuthbert\'s College'),
        ('STK', 'St Kent\'s College'),
        ('BAR', 'Baradene College'),
        ('EGG', 'Epsom Girl\'s College'),
        ('KC', 'King\'s College'),
        ('GDC', 'Glendowie College'),
        ('selwyn', 'Selwyn College'),
        ('DIO', 'Diocesan School For Girls'),
        ('other', 'Other')
    ]

    YEAR_CHOICES[
        (9 , '9'),
        (10, '10'),
        (11, '11'),
        (12, '12'),
        (13, '13'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    school = models.CharField(
        max_length=100,
        choices=SCHOOLS
    )
    year_level = models.IntegerField(
        choices=YEAR_CHOICES
    )
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.first_name + " " + self.last_name
    
class Seminar(models.Model):
    STATUS = [
        ('active', 'Active'),
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
    ]

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=timezone.now)
    hidden = models.BooleanField(default=False)

    def get_status(self):
        now = timezone.now()
        if now < self.start_time:
            return 'upcoming'
        elif now >= self.start_time and now <= self.end_time:
            return 'active'
        return 'completed'

    def __str__(self):
        return self.title

class Initiative(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    hidden = models.BooleanField(default=False)

    def __str__(self):
        return self.title
    
class Event(models.Model):
    STATUS = [
        ('active', 'Active'),
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
    ]

    title = models.CharField(max_length=100)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='events')

    def get_status(self):
        now = timezone.now()
        if now < self.start_time:
            return 'upcoming'
        elif now >= self.start_time and now <= self.end_time:
            return 'active'
        return 'completed'

    def __str__(self):
        return self.title
    
class MemberRole(models.Model):
    COMMITTEES = [
        ('general', 'General Committee'),
        ('administrative', 'Administrative Committee'),
        ('technical', 'Technical Committee'),
    ]
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='roles')
    committee = models.CharField(max_length=20, choices=COMMITTEES)
    title = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.member} — {self.get_committee_display()}"

