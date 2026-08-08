from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from django import forms
from django.forms.widgets import TextInput
from .models import Category, SubCategory, Product, ProductVariant, ProductImage, VendorExpense
from unfold.contrib.forms.widgets import WysiwygWidget
from django.db import models
# 1. Create a custom form to override the color field
class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = '__all__'
        widgets = {
            # This forces the browser to show a native color picker
            # The style attributes make it match Unfold's modern field heights
            'color': TextInput(attrs={
                'type': 'color', 
                'style': 'height: 38px; width: 100%; padding: 2px; cursor: pointer; border-radius: 6px;'
            }),
        }

# 2. Attach the custom form to the Inline
class ProductVariantInline(TabularInline):
    model = ProductVariant
    form = ProductVariantForm  # <--- Attached here
    extra = 1 

class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'created_at')
    # ==========================================
    # DYNAMIC RICH TEXT EDITOR
    # ==========================================
    formfield_overrides = {
        models.TextField: {
            "widget": WysiwygWidget,
        }
    }
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'location_address')
    inlines = [ProductVariantInline, ProductImageInline]
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Category)
admin.site.register(SubCategory)

@admin.register(VendorExpense)
class VendorExpenseAdmin(ModelAdmin):
    # This controls exactly which columns show up on the main list page
    list_display = ('vendor_name', 'location', 'start_date', 'end_date', 'cost')
    
    # Adds a search bar so you can quickly find a vendor or location
    search_fields = ('vendor_name', 'location')
    
    # Adds a filter sidebar so you can filter by date
    list_filter = ('start_date', 'end_date')
    
    # Optional: If you are using Unfold for your admin theme, this makes the date boxes look great
    date_hierarchy = 'start_date'