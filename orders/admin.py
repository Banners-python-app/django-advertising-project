from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import display
from django.utils.html import format_html
from django.urls import reverse
from decimal import Decimal
from .models import Invoice, InvoiceItem
from django.http import JsonResponse
from agency.models import ProductVariant

class InvoiceItemInline(TabularInline):
    model = InvoiceItem
    extra = 1 # Shows 1 blank row by default, click "Add another" for more
    fields = ('product_variant', 'start_date', 'end_date', 'amount', 'printing_price', 'mounting_price')

@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    class Media:
        js = ('js/invoice_auto_price.js',)
    list_display = ('id', 'document_actions', 'customer', 'campaign_period', 'subtotal', 'gst_amount', 'grand_total', 'is_paid', 'created_at', )
    list_filter = ('is_paid', 'created_at')
    search_fields = ('customer__name', 'customer__company_name', 'id')
    
    # Protect the financial totals from being typed manually!
    readonly_fields = ('subtotal', 'gst_amount', 'grand_total')
    
    inlines = [InvoiceItemInline]

# CUSTOM FUNCTION TO SHOW DATES ON THE MAIN PAGE
    def campaign_period(self, obj):
        # Grabs the first and last item to show the full date range
        first_item = obj.items.first() # Note: 'items' is the related_name from your model
        last_item = obj.items.last()
        
        if first_item and last_item and first_item.start_date and last_item.end_date:
            start = first_item.start_date.strftime("%d %b %Y")
            end = last_item.end_date.strftime("%d %b %Y")
            return f"{start} to {end}"
        return "No dates set"
    
    campaign_period.short_description = "Billing Period"

    # ==========================================
    # THE AUTO-CALCULATOR ENGINE
    # ==========================================
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        
        invoice = form.instance
        # 1. Sum up the 'amount' from all line items attached to this invoice
        total_sub = sum(
            (item.amount or Decimal('0.00')) + 
            (item.printing_price or Decimal('0.00')) + 
            (item.mounting_price or Decimal('0.00')) 
            for item in invoice.items.all()
        )
        
        # 2. Calculate 18% GST
        gst = total_sub * Decimal('0.18')
        
        # 3. Update and save the parent Invoice record
        invoice.subtotal = total_sub
        invoice.gst_amount = gst
        invoice.grand_total = total_sub + gst
        invoice.save()

    @display(description='Quotation & Bills')
    def document_actions(self, obj):
        bill_url = reverse('download_invoice_pdf', args=[obj.id])
        quote_url = reverse('download_quotation_pdf', args=[obj.id])
        
        # Renders two nice Tailwind buttons side-by-side in the admin panel
        return format_html(
            '<div style="display: flex; gap: 8px;">'
            '<a href="{}" class="bg-gray-600 text-white px-3 py-1.5 rounded-md font-semibold text-xs hover:bg-gray-700 transition-colors">📄 Quote</a>'
            '<a href="{}" class="bg-blue-600 text-white px-3 py-1.5 rounded-md font-semibold text-xs hover:bg-blue-700 transition-colors">↓ Bill</a>'
            '</div>',
            quote_url, bill_url
        )
    
    
    
    