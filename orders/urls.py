from django.urls import path
from . import views

urlpatterns = [
    path('download-invoice/<int:invoice_id>/', views.download_invoice_pdf, name='download_invoice_pdf'),
    path('download-quotation/<int:invoice_id>/', views.download_quotation_pdf, name='download_quotation_pdf'),
    path('api/get-price/<int:variant_id>/', views.get_variant_price, name='get_variant_price'),
]