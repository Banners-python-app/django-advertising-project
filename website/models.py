from django.db import models
from agency.models import Product

class Inquiry(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Links to the specific hoarding they selected!
    interested_product = models.ForeignKey(
        Product, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="inquiries"
    )
    
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lead: {self.name} - {self.interested_product or 'General Inquiry'}"
    
    class Meta:
        verbose_name_plural = "Inquiries"