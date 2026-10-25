from django.contrib import admin, messages

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "key_prefix", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "key_prefix")
    readonly_fields = ("key_prefix", "created_at")
    fields = ("name", "is_active", "key_prefix", "created_at")
    actions = ["rotate_api_key"]

    def save_model(self, request, obj, form, change):
        if not change:
            raw_key = obj.set_new_api_key()
            super().save_model(request, obj, form, change)
            messages.warning(
                request,
                f"API key for '{obj.name}' (copy it now, it is shown only once): {raw_key}",
            )
        else:
            super().save_model(request, obj, form, change)

    @admin.action(description="Rotate API key (old key stops working immediately)")
    def rotate_api_key(self, request, queryset):
        for client in queryset:
            raw_key = client.set_new_api_key()
            client.save()
            messages.warning(
                request,
                f"New API key for '{client.name}' (shown only once): {raw_key}",
            )
