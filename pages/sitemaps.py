from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import BlogPost, Seminar, Initiative


class StaticViewSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return ['home', 'blog', 'seminars', 'events', 'calendar',
                'staff', 'contact', 'partners', 'signup', 'initiatives']

    def location(self, item):
        return reverse(item)


class BlogPostSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return BlogPost.objects.filter(approved=True).order_by('-published_at')

    def location(self, post):
        return reverse('blog_detail', args=[post.id])

    def lastmod(self, post):
        return post.published_at


class SeminarSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5

    def items(self):
        return Seminar.objects.filter(hidden=False)

    def location(self, seminar):
        return reverse('seminar_detail', args=[seminar.slug])


class InitiativeSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return Initiative.objects.filter(hidden=False)

    def location(self, initiative):
        return reverse('initiative_detail', args=[initiative.slug])
