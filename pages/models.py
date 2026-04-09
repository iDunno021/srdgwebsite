from django.db import models

class Member():
    first_name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    school = models.CharField(max_length=100)
    year_level = models.IntegerField()
    email = models.EmailField(unique=True)

