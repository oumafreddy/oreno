# config/sitemaps.py

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone


class PublicSitemap(Sitemap):
    """
    Sitemap for public pages of the Hashrate Solutions website.
    """
    changefreq = 'weekly'
    priority = 0.8
    lastmod = timezone.now()

    def items(self):
        """
        Return list of public page names/identifiers.
        """
        return [
            'public-home',
            'public-privacy', 
            'public-cookies',
            'public-docs',
        ]

    def location(self, item):
        """
        Return the URL for each item.
        """
        return reverse(item)

    def lastmod(self, item):
        """
        Return the last modification date for each item.
        """
        return timezone.now()

    def priority(self, item):
        """
        Return priority for each item.
        """
        priorities = {
            'public-home': 1.0,  # Home page has highest priority
            'public-docs': 0.9,  # Documentation is important
            'public-privacy': 0.6,  # Legal pages are moderately important
            'public-cookies': 0.6,
        }
        return priorities.get(item, 0.5)


class StaticSitemap(Sitemap):
    """
    Sitemap for static pages that don't change often.
    """
    changefreq = 'monthly'
    priority = 0.5
    lastmod = timezone.now()

    def items(self):
        """
        Return list of static page URLs.
        """
        return [
            '/health/',
            '/api/docs/',
        ]

    def location(self, item):
        """
        Return the URL for each item.
        """
        return item
