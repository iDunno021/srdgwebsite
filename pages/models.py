from django.db import models

class Member(models.Model):
    SCHOOLS = [
        ('AGS', 'Auckland Grammar School'),
        ('STC', 'St Cuthbert\'s College'),
        ('STK', 'St Kent\'s College'),
        ('BAR', 'Baradene College'),
        ('EGG', 'Epsom Girl\'s College'),
        ('KC', 'King\'s College'),
        ('GDC', 'Glendowie College'),
        ('Selwyn', 'Selwyn College'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    school = models.CharField(
        max_length=100,
        choices=SCHOOLS
    )
    year_level = models.IntegerField()
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.first_name + " " + self.last_name
    
class Seminars(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    date = models.DateField

class Initiatives(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)

