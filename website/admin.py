from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Inquiry

@admin.register(Inquiry)
class InquiryAdmin(ModelAdmin):
    list_display = ('name', 'email', 'phone_number', 'interested_product', 'is_resolved', 'created_at')
    list_filter = ('is_resolved', 'created_at', 'interested_product')
    search_fields = ('name', 'email', 'message')
    list_editable = ('is_resolved',)