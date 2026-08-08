from django.db import models
from django.utils.text import slugify

class Customer(models.Model):
    # --- Your Requested Fields ---
    name = models.CharField(max_length=255, help_text="Contact person's name")
    gst_number = models.CharField(max_length=15, blank=True, help_text="15-character alphanumeric GSTIN")
    mobile_number = models.CharField(max_length=15, unique=True, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, blank=True, null=True, help_text="Total pending amount to be paid")
    company_name = models.CharField(max_length=255, blank=True, help_text="Legal name for the PDF Bill")

    # Financial safeguards
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00, blank=True, null=True, help_text="Max allowed due amount before rejecting new orders")
    is_active = models.BooleanField(default=True, help_text="Uncheck to blacklist/block this customer")
    
    # Audit trails
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.company_name:
            return f"{self.company_name} ({self.name})"
        return self.name

    # A helper method to easily check if they are allowed to book a new hoarding
    def can_book_order(self, new_order_amount):
        return (self.due_amount + new_order_amount) <= self.credit_limit