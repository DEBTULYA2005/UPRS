from django.contrib import admin

from .models import Content


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ("content_id", "title", "category", "client", "is_active")
    list_filter = ("client", "category", "is_active")
    search_fields = ("content_id", "title")
