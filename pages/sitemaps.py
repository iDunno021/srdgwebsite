from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import BlogPost, Seminar, Initiative


class StaticViewSitemap(Sitemap):
    priority = 0.6
    changefreq = 'monthly'

    def items(self):
        return ['home', 'signup', 'staff', 'contact', 'calendar', 'initiatives', 'events', 'partners']

    def location(self, item):
        return reverse(item)


class BlogSitemap(Sitemap):
    changefreq = 'never'
    priority = 0.5

    def items(self):
        return BlogPost.objects.filter(approved=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('blog_detail', args=[obj.id])


class SeminarSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return Seminar.objects.filter(hidden=False)

    def location(self, obj):
        return reverse('seminar_detail', args=[obj.slug])


class InitiativeSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return Initiative.objects.filter(hidden=False)

    def location(self, obj):
        return reverse('initiative_detail', args=[obj.slug])
