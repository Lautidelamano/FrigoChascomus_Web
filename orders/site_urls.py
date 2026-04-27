from django.urls import path
from django.shortcuts import render
from .models import Product, Category


def home(request):
    products   = Product.objects.filter(active=True).select_related('category').order_by('order', 'name')
    categories = Category.objects.all()
    return render(request, 'site/index.html', {
        'products':   products,
        'categories': categories,
    })


urlpatterns = [
    path('', home, name='home'),
]
