from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from orders.models import Invoice, InvoiceItem
from agency.models import Product
from customers.models import Customer  # Make sure this matches your actual Customer app/model
from django.core.paginator import Paginator

def dashboard_callback(request, context):
    """
    Calculates real-time business KPIs for the admin dashboard.
    """
    now = timezone.now().date()
    yesterday = now - timedelta(days=1)
    seven_days_from_now = now + timedelta(days=7)

    # ==========================================
    # REVENUE & SALES METRICS
    # ==========================================
    # 1. Today's Sales
    today_sales = Invoice.objects.filter(
        created_at__date=now
    ).aggregate(Sum('grand_total'))['grand_total__sum'] or 0

    # 2. Yesterday's Sales
    yesterday_sales = Invoice.objects.filter(
        created_at__date=yesterday
    ).aggregate(Sum('grand_total'))['grand_total__sum'] or 0

    # 3. Monthly Revenue
    this_month_invoices = Invoice.objects.filter(
        created_at__month=now.month, 
        created_at__year=now.year
    )
    monthly_revenue = this_month_invoices.aggregate(Sum('grand_total'))['grand_total__sum'] or 0

    # 4. Pending Dues (Unpaid Invoices)
    pending_dues = Invoice.objects.filter(
        is_paid=False
    ).aggregate(Sum('grand_total'))['grand_total__sum'] or 0

    # ==========================================
    # INVENTORY & CLIENT METRICS
    # ==========================================
    # 5. Total Customers
    total_customers = Customer.objects.count()

    # 6. Active Hoardings
    active_hoardings = Product.objects.filter(is_active=True).count()

    # 7. Expiring Campaigns
    seven_days_from_now = now + timedelta(days=30)
    expiring_soon = InvoiceItem.objects.filter(
        end_date__gte=now, 
        end_date__lte=seven_days_from_now
    ).count()

    expiring_qs = InvoiceItem.objects.filter(
        end_date__gte=now, 
        end_date__lte=seven_days_from_now
    ).select_related('invoice__customer', 'product_variant__product').order_by('end_date')

    # Paginate to 5 items per page
    expiring_paginator = Paginator(expiring_qs, 5) 
    expiring_page_num = request.GET.get('expiring_page', 1)
    expiring_page_obj = expiring_paginator.get_page(expiring_page_num)

    # 8. Expired Campaigns
    expired_qs = InvoiceItem.objects.filter(
        end_date__lt=now # Less than today
    ).select_related('invoice__customer', 'product_variant__product').order_by('-end_date') # Most recently expired first
    
    expired_paginator = Paginator(expired_qs, 5)
    expired_page_num = request.GET.get('expired_page', 1)
    expired_page_obj = expired_paginator.get_page(expired_page_num)

    # Inject all numbers into the dashboard
    context.update({
        "today_sales": today_sales,
        "yesterday_sales": yesterday_sales,
        "monthly_revenue": monthly_revenue,
        "pending_dues": pending_dues,
        "total_customers": total_customers,
        "active_hoardings": active_hoardings,
        "expiring_soon": expiring_soon,
        "expiring_campaigns": expiring_page_obj,
        "expired_campaigns": expired_page_obj,
    })
    
    return context