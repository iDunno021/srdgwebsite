from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify
from io import BytesIO
from PIL import Image
import uuid


def optimize_image_file(image_field, max_dimension=1200, quality=82):
    """Resize/recompress an uploaded image to keep page weight down."""
    img = Image.open(image_field)
    has_alpha = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
    if has_alpha:
        img = img.convert('RGBA')
        has_alpha = img.split()[-1].getextrema()[0] < 255

    img.thumbnail((max_dimension, max_dimension), Image.LANCZOS)

    buffer = BytesIO()
    if has_alpha:
        img.save(buffer, format='PNG', optimize=True)
        ext = 'png'
    else:
        img.convert('RGB').save(buffer, format='JPEG', quality=quality, optimize=True)
        ext = 'jpg'
    buffer.seek(0)
    return ContentFile(buffer.read(), name=f'{uuid.uuid4().hex}.{ext}')

class Member(models.Model):
    SCHOOLS = [
        ('AGS', 'Auckland Grammar School'),
        ('STC', 'St Cuthbert\'s College'),
        ('STK', 'St Kent\'s College'),
        ('BAR', 'Baradene College'),
        ('EGGS', 'Epsom Girl\'s Grammar School'),
        ('KC', 'King\'s College'),
        ('GDC', 'Glendowie College'),
        ('selwyn', 'Selwyn College'),
        ('DIO', 'Diocesan School For Girls'),
        ('RGT', 'Rangitoto College'),
        ('DIL', 'Dilworth School'),
        ('ACGP', 'ACG Parnell College'),
        ('ACGS', 'ACG Sunderland'),
        ('WBC', 'Westlake Boys\' College'),
        ('WGC', 'Westlake Girls\' College'),
        ('MAC', 'Maclean\'s College'),
        ('SDCC', 'St Dominic\'s Catholic College'),
        ('GBHS', 'Green Bay High School'),
        ('other', 'Other'),
        ('SJC', 'St John\'s College')
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
    photo = models.ImageField(upload_to = "member_photos/", blank=True, null = True)
    discord_username = models.CharField(max_length=100, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.pk:
            old = Member.objects.filter(pk=self.pk).first()
            if old.photo and old.photo != self.photo:
                old.photo.delete(save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.first_name + " " + self.last_name


class Initiative(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    summary = models.CharField(max_length=150, blank=True)
    hidden = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    director = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='initiatives')
    

    def __str__(self):
        return self.title


class Event(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    location = models.CharField(max_length=100, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    initiative = models.ForeignKey(Initiative, on_delete=models.SET_NULL, related_name='events', null=True, blank=True)
    tbc = models.BooleanField(default=False, verbose_name='TBC')
    ticketed = models.BooleanField(default=False)

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError('End time must be after start time.')

    @property
    def get_status(self):
        if not self.start_time or not self.end_time:
            return 'upcoming'
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
    description = models.TextField()
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
        ('general', 'General Committee'),
        ('ea', 'EduUnlocked'),
        ('ype', 'Youth Political Engagement'),
        ('yac', 'Young Artists Collective'),
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
    
def about_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'about/{uuid.uuid4().hex}.{ext}'


class AboutPhoto(models.Model):
    SLOT_CHOICES = [
        ('side', 'Side Photo'),
        ('middle', 'Middle Photo'),
    ]
    image = models.ImageField(upload_to=about_photo_path)
    slot = models.CharField(max_length=10, choices=SLOT_CHOICES, default='side')
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'pk']

    def save(self, *args, **kwargs):
        if self.image and not self.image._committed:
            optimized = optimize_image_file(self.image, max_dimension=900)
            self.image.save(optimized.name, optimized, save=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_slot_display()} #{self.pk}"


def art_piece_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'yac/art/{uuid.uuid4().hex}.{ext}'


def blog_cover_path(instance, filename):
    ext = filename.split('.')[-1]
    return f'blog/covers/{uuid.uuid4().hex}.{ext}'

def blog_image_path(instance, filename):
    return f'blog/images/{instance.post.slug}/{filename}'

def blog_attachment_path(instance, filename):
    return f'blog/attachments/{instance.post.slug}/{filename}'


class ArtPiece(models.Model):
    title = models.CharField(max_length=200, blank=True)
    artist = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to=art_piece_path)
    order = models.PositiveIntegerField(default=0)
    hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ['order', 'pk']

    def __str__(self):
        return self.title


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    author = models.CharField(max_length=100, default="anonymous")
    body = models.TextField()
    cover_image = models.ImageField(
        upload_to=blog_cover_path, blank=True, null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])],
    )
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


class BlogReaction(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'
    REACTION_CHOICES = [
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike'),
    ]

    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='reactions')
    ip_address = models.GenericIPAddressField()
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('post', 'ip_address')]

    def __str__(self):
        return f"{self.ip_address} {self.reaction}d {self.post.title}"


class EventRSVP(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='rsvps', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('event', 'email'), ('event', 'member')]

    def __str__(self):
        return f"{self.first_name} {self.last_name} — {self.event.title}"


class Seat(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='seats')
    row = models.CharField(max_length=2)
    number = models.PositiveIntegerField()
    is_accessible = models.BooleanField(default=False)

    class Meta:
        ordering = ['row', 'number']
        unique_together = [('event', 'row', 'number')]

    def __str__(self):
        return f"{self.row}{self.number}"


class Ticket(models.Model):
    PENDING = 'pending'
    PAID = 'paid'
    STATUS_CHOICES = [(PENDING, 'Pending'), (PAID, 'Paid')]

    seat = models.OneToOneField(Seat, on_delete=models.CASCADE, related_name='ticket')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    hold_expires_at = models.DateTimeField(null=True, blank=True)
    stripe_session_id = models.CharField(max_length=255, blank=True)
    name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.seat} — {self.status}"


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

