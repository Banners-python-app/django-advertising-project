import sys
import re  # Added for YouTube ID extraction
from io import BytesIO
from PIL import Image
from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.core.files.uploadedfile import InMemoryUploadedFile

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True) 
    image = models.ImageField(upload_to='category_images/', max_length=500, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories', null=True, blank=True)
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.category:
            return f"{self.category.name} -> {self.name}"
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255) 
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    description = models.TextField(blank=True, null=True, help_text="Supports HTML for bold, lists, tables, etc.") 
    
    # --- NEW YOUTUBE FIELD ---
    youtube_link = models.URLField(max_length=500, blank=True, null=True, help_text="Paste a YouTube video link. Used as a fallback if no images are uploaded.")
    
    slug = models.SlugField(unique=True, blank=True)
    is_active = models.BooleanField(default=True, help_text="Uncheck to hide from the website")
    location_address = models.TextField(blank=True, null=True, help_text="Physical address of the hoarding")
    map_coordinates = models.CharField(max_length=100, blank=True, null=True, help_text="Lat/Long for Google Maps integration")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    # --- NEW YOUTUBE ID EXTRACTOR ---
    @property
    def youtube_id(self):
        """Automatically extracts the 11-character YouTube video ID from various URL formats."""
        if not self.youtube_link:
            return None
        # Regex catches standard links, youtu.be shortlinks, and embed links
        match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11}).*', self.youtube_link)
        return match.group(1) if match else None

    def __str__(self):
        return self.name
    
    # showing booked/available
    @property
    def is_currently_booked(self):
        """Checks if there is an active invoice for this hoarding today."""
        # We import here to avoid circular import errors
        from orders.models import InvoiceItem 
        
        today = timezone.now().date()
        
        # Check if any variant of this product has an invoice item overlapping today
        is_booked = InvoiceItem.objects.filter(
            product_variant__product=self, # Assuming InvoiceItem links to ProductVariant
            start_date__lte=today,
            end_date__gte=today
        ).exists()
        
        return is_booked

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    
    length = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Length in feet/meters")
    height = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, help_text="Height in feet/meters")
    
    stock = models.IntegerField(default=1, null=True, blank=True)
    hsn_code = models.CharField(max_length=20, null=True, blank=True)
    gst_percentage = models.DecimalField(max_digits=4, decimal_places=2, default=18.00, null=True, blank=True)
    color = models.CharField(max_length=50, blank=True, null=True, help_text="Frame or background color, if applicable")
    
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    offline_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Price for walk-in/direct clients")
    online_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Visible on the showcase website")
    
    sku = models.CharField(max_length=50, unique=True, null=True, blank=True, help_text="Stock Keeping Unit / Unique ID for this specific size")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        if self.length and self.height:
            return f"{self.product.name} ({self.length}x{self.height})"
        return f"{self.product.name} (Variant)"

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/', max_length=500)
    is_primary = models.BooleanField(default=False, help_text="Check this to make it the main thumbnail")
    alt_text = models.CharField(max_length=100, blank=True, null=True, help_text="Good for SEO on the showcase site")

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_obj = ProductImage.objects.get(pk=self.pk)
                if old_obj.image == self.image:
                    return super().save(*args, **kwargs)
            except ProductImage.DoesNotExist:
                pass

        if self.image:
            img = Image.open(self.image)

            if img.mode != 'RGB':
                img = img.convert('RGB')

            img.thumbnail((1920, 1920), Image.Resampling.LANCZOS)

            output = BytesIO()
            img.save(output, format='JPEG', quality=70, optimize=True)
            output.seek(0)

            original_filename = self.image.name.split('.')[0]
            self.image = InMemoryUploadedFile(
                output,
                'ImageField',
                f"{original_filename}_optimized.jpg",
                'image/jpeg',
                sys.getsizeof(output),
                None
            )

        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Image for {self.product.name}"
    
class VendorExpense(models.Model):
    vendor_name = models.CharField(max_length=255, help_text="Name of the vendor or land owner")
    location = models.CharField(max_length=255, blank=True, null=True, help_text="Physical location or hoarding associated with this cost")
    
    start_date = models.DateField(blank=True, null=True,help_text="When does this vendor contract/booking start?")
    end_date = models.DateField(blank=True, null=True,help_text="When does it end?")
    
    cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, help_text="Total cost to be paid to the vendor")
    
    # Keeping track of when this record was created
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Vendor Expense"
        verbose_name_plural = "Vendor Expenses"
        ordering = ['-start_date'] # Shows the newest contracts at the top by default

    def __str__(self):
        return f"{self.vendor_name} - {self.location} (₹{self.cost})"