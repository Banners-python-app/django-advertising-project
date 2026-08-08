from django.contrib import admin
from unfold.admin import ModelAdmin  # Import Unfold's Admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(ModelAdmin):     # Inherit from Unfold's ModelAdmin
    list_display = ('name', 'company_name', 'mobile_number', 'due_amount', 'is_active')
    list_filter = ('is_active',) 
    search_fields = ('name', 'company_name', 'mobile_number', 'gst_number')
    readonly_fields = ('created_at', 'updated_at')