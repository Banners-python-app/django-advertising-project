from django.db import models
from django.utils import timezone
from decimal import Decimal

class Invoice(models.Model):
    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='invoices')
    
    # Auto-calculated financial fields
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice #{self.id} - {self.customer.company_name or self.customer.name}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product_variant = models.ForeignKey('agency.ProductVariant', on_delete=models.PROTECT)
    
    # Each hoarding can have its own timeline
    start_date = models.DateField()
    end_date = models.DateField()
    mounting_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Cost for mounting the hoarding")
    printing_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Cost for printing the flex/vinyl")
    
    # The negotiated price for this specific hoarding timeline
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price for this hoarding timeline")

    def __str__(self):
        return f"{self.product_variant} on Invoice #{self.invoice.id}"

    @property
    def days_remaining(self):
        return (self.end_date - timezone.now().date()).days