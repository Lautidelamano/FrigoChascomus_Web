from orders.models import Order

def admin_context(request):
    """Inyecta datos globales en todos los templates del admin."""
    if request.user.is_authenticated and request.user.is_staff:
        return {'nuevos_count': Order.objects.filter(status='nuevo').count()}
    return {}
