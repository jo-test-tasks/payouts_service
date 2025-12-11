from django.contrib import admin
from .models import Recipient, Payout

@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "type", "account_number", "is_active", "country")
    search_fields = ("id", "name", "account_number")
    list_filter = ("type", "is_active", "country")

@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "amount", "currency", "status", "created_at")
    search_fields = ("id", "recipient__name")
    list_filter = ("status", "currency")


# Register your models here.
