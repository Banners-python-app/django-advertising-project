from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.contrib import messages
from agency.models import Product, ProductVariant, Category
from .forms import ContactForm
import io, requests, json
from orders.models import Invoice, InvoiceItem
from django.http import FileResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

# Importing ReportLab components
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def home_page(request):
    # Fetch only hoardings marked as active in your admin panel
    # (Assuming your Product model has an 'is_active' boolean field)
    hoardings = Product.objects.filter(is_active=True).order_by('id')
    
    context = {
        'hoardings': hoardings
    }
    return render(request, 'website/home.html', context)

def contact_page(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # If the captcha passes and data is good, save it to the database
            form.save()
            # Send a success flash message to the frontend
            messages.success(request, "Your message has been sent successfully! We will contact you soon.")
            return redirect('contact') # Refresh the page to clear the form
    else:
        # Pre-select a product if the user clicked "Request Quote" from the home page
        initial_data = {}
        if 'product_id' in request.GET:
            initial_data['interested_product'] = request.GET.get('product_id')
            
        form = ContactForm(initial=initial_data)

    return render(request, 'website/contact.html', {'form': form})

class ProductDetailView(DetailView):
    model = Product 
    template_name = 'website/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the default context
        context = super().get_context_data(**kwargs)
        
        # Get the current product instance being viewed
        product_instance = self.get_object()
        
        # 1. Keep your existing logic for online_prices
        context['online_prices'] = ProductVariant.objects.filter(
            product=product_instance, 
            is_active=True
        ).values_list('online_price', flat=True)
        
        # 2. NEW LOGIC: Fetch FUTURE bookings to disable on the calendar
        today = timezone.now().date()
        
        future_bookings = InvoiceItem.objects.filter(
            product_variant__product=product_instance,
            end_date__gte=today
        ).values('start_date', 'end_date')
        
        # 3. Format them into a list so JavaScript can read them easily
        disabled_dates = []
        for booking in future_bookings:
            # Quick safety check to ensure both dates exist before adding them
            if booking['start_date'] and booking['end_date']:
                disabled_dates.append({
                    "from": str(booking['start_date']),
                    "to": str(booking['end_date'])
                })
        
        # 4. Pass the JSON string safely to the template
        context['disabled_dates_json'] = json.dumps(disabled_dates)
        
        return context
    
class CategoryProductListView(ListView):
    model = Product
    template_name = 'website/category_prod.html'
    context_object_name = 'products'

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Product.objects.filter(category=self.category)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context
    
def aboutUs(request):
    return render(request, 'website/about.html')
        