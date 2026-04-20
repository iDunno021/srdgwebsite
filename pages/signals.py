from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import BlogPost, BlogImage, BlogAttachment


@receiver(post_delete, sender=BlogPost)
def delete_cover_image(_sender, instance, **_kwargs):
    if instance.cover_image:
        instance.cover_image.delete(save=False)


@receiver(post_delete, sender=BlogImage)
def delete_blog_image(_sender, instance, **_kwargs):
    if instance.image:
        instance.image.delete(save=False)


@receiver(post_delete, sender=BlogAttachment)
def delete_blog_attachment(_sender, instance, **_kwargs):
    if instance.file:
        instance.file.delete(save=False)
