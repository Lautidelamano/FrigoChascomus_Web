import json, logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.urls import path
from .models import Order
from .emails import send_order_emails

logger = logging.getLogger(__name__)


def jresp(data, status=200):
    return JsonResponse(data, status=status, json_dumps_params={'ensure_ascii': False})


@method_decorator(csrf_exempt, name='dispatch')
class OrderCreateView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
        except Exception:
            return jresp({'error': 'JSON inválido'}, 400)

        for f in ['customer_name', 'customer_phone', 'customer_email', 'items']:
            if not data.get(f):
                return jresp({'error': f'Falta el campo: {f}'}, 400)

        if not data['items']:
            return jresp({'error': 'El pedido no tiene productos'}, 400)

        clean_items = [{
            'id':    item.get('id'),
            'name':  str(item.get('name', ''))[:200],
            'qty':   int(item.get('qty', 1)),
            'unit':  str(item.get('unit', 'kg'))[:50],
            'price': str(item.get('price', 'Consultar'))[:100],
            'emoji': str(item.get('emoji', '🥩'))[:10],
        } for item in data['items']]

        try:
            order = Order.objects.create(
                customer_name  = str(data['customer_name'])[:200],
                customer_phone = str(data['customer_phone'])[:50],
                customer_email = str(data['customer_email'])[:254],
                customer_zone  = str(data.get('customer_zone', ''))[:200],
                notes          = str(data.get('notes', ''))[:2000],
                items          = clean_items,
            )
        except Exception as e:
            logger.error(f'Error creando pedido: {e}')
            return jresp({'error': 'Error interno'}, 500)

        try:
            send_order_emails(order)
        except Exception as e:
            logger.error(f'Error enviando emails: {e}')

        return jresp({'success': True, 'order_id': str(order.id)}, 201)


urlpatterns = [
    path('orders/', OrderCreateView.as_view(), name='api_orders'),
]
