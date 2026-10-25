from django.contrib import admin

from .models import Interaction, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("external_user_id", "client", "created_at")
    list_filter = ("client",)
    search_fields = ("external_user_id",)


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ("client", "user", "content", "event_type", "weight", "timestamp")
    list_filter = ("client", "event_type")
