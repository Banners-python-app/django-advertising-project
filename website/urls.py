from django.urls import path
from . import views
from .views import ProductDetailView, CategoryProductListView

urlpatterns = [
    path('', views.home_page, name='home'),
    path('contact/', views.contact_page, name='contact'),
    path('aboutus/', views.aboutUs, name='aboutus'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('category/<slug:slug>/', CategoryProductListView.as_view(), name='category_products')
]