from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify
import uuid

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
        ('RGT', 'Rangitoto College'),
        ('other', 'Other')
    ]

    YEAR_CHOICES=[
        (9 , '9'),
        (10, '10'),
        (11, '11'),
        (12, '12'),
        (13, '13'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    school = models.CharField(max_length=100, choices=SCHOOLS)
    year_level = models.IntegerField(choices=YEAR_CHOICES)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.first_name + " " + self.last_name


class Initiative(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    hidden = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Event(models.Model):
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    location = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    initiative = models.ForeignKey(Initiative, on_delete=models.CASCADE, related_name='events')

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError('End time must be after start time.')

    @property
    def get_status(self):
        now = timezone.now()
        if self.end_time < now:
            return 'completed'
        if self.start_time <= now:
            return 'active'
        return 'upcoming'

    def __str__(self):
        return self.title


class Seminar(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=1000)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    hidden = models.BooleanField(default=False)

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError('End time must be after start time.')

    @property
    def get_status(self):
        now = timezone.now()
        if self.end_time < now:
            return 'completed'
        if self.start_time <= now:
            return 'active'
        return 'upcoming'

    def __str__(self):
        return self.title


class MemberRole(models.Model):
    COMMITTEES = [
        ('general', 'Board of Directors'),
        ('administrative', 'Administrative Committee'),
        ('technical', 'Technical Committee'),
        ('outreach', 'Outreach Department'),
        ('finance', 'Finance Department'),
    ]
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='roles')
    committee = models.CharField(max_length=20, choices=COMMITTEES)
    title = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.member} — {self.get_committee_display()}"
    
def blog_cover_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'blog/covers/{uuid.uuid4().hex}.{ext}'

def blog_image_path(instance, filename):
    return f'blog/images/{instance.post.slug}/{filename}'

def blog_attachment_path(instance, filename):
    return f'blog/attachments/{instance.post.slug}/{filename}'


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    author = models.CharField(max_length=100, default="anonymous")
    body = models.TextField()
    cover_image = models.ImageField(upload_to=blog_cover_path, blank=True, null=True)
    published_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            slug = base
            n = 1
            while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base}-{n}'
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class BlogAttachment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to=blog_attachment_path)
    name = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or self.file.name


class BlogImage(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=blog_image_path)
    caption = models.CharField(max_length=300, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.caption or f"Image for {self.post.title}"

