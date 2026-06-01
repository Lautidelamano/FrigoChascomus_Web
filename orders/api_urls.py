import json, logging
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import path
from .models import Order, ZonaEntrega
from .emails import send_order_emails
from django.utils import timezone
from django.template.loader import render_to_string
from shapely.geometry import shape, Point



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

        for f in ['customer_name', 'customer_phone', 'customer_email', 'items', 'latitud', 'longitud']:
            if not data.get(f):
                if not data.get(f.latitud or f.longitud):
                    msg = 'Por favor marcá tu ubicación en el mapa.' if f in ['latitud', 'longitud'] else f'Falta el campo: {f}'
                    return jresp({'error': msg}, 400)
                return jresp({'error': f'Falta el campo: {f}'}, 400)

        if not data['items']:
            return jresp({'error': 'El pedido no tiene productos'}, 400)
        
        # ── LÓGICA DE MAPAS Y ZONAS ──
        lat = float(data.get('latitud'))
        lng = float(data.get('longitud'))
        punto_cliente = Point(lng, lat)
        zona_asignada = None

        for zona in ZonaEntrega.objects.all():
            try:
                poligono = shape(json.loads(zona.poligono_geojson))
                if poligono.contains(punto_cliente):
                    zona_asignada = zona
                    break
            except Exception as e:
                logger.error(f'Error parseando GeoJSON zona {zona.id}: {e}')
                continue

        if not zona_asignada:
            return jresp({'error': 'Tu ubicación está fuera de nuestra área de cobertura.'}, 400)
        
        if zona_asignada.tipo == 'rojo':
            return jresp({'error': f'Lo sentimos, no realizamos entregas en la zona: {zona_asignada.nombre}.'}, 400)

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
                customer_zone  = zona_asignada.nombre,
                latitud        = lat,
                longitud       = lng,
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

# ── Contacto ───────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
class ContactoView(View):

    def post(self, request):
        try:
            data = json.loads(request.body)
        except Exception:
            return jresp({'error': 'JSON inválido'}, 400)

        for f in ['nombre', 'email']:
            if not data.get(f):
                return jresp({'error': f'Falta el campo: {f}'}, 400)

        nombre   = str(data['nombre'])[:200].strip()
        email    = str(data['email'])[:254].strip()
        telefono = str(data.get('telefono', ''))[:50].strip()
        mensaje  = str(data.get('mensaje', ''))[:2000].strip()

        # Fecha y hora actuales para el template
        ahora = timezone.localtime(timezone.now())

        # Contexto para el template HTML
        context = {
            'nombre':   nombre,
            'email':    email,
            'telefono': telefono,
            'mensaje':  mensaje,
            'fecha':    ahora.strftime('%d/%m/%Y'),
            'hora':     ahora.strftime('%H:%M'),
        }

        txt  = f"Consulta de {nombre} — {email} — Tel: {telefono or 'no indicado'}\n\n{mensaje or '(sin mensaje)'}"
        html = render_to_string('orders/email_contacto_vendor.html', context)

        msg = EmailMultiAlternatives(
            subject    = f'📩 Consulta web — {nombre}',
            body       = txt,
            from_email = settings.DEFAULT_FROM_EMAIL,
            to         = [settings.VENTAS_EMAIL],
            reply_to   = [email],
        )
        msg.attach_alternative(html, 'text/html')

        try:
            msg.send()
        except Exception as e:
            logger.error(f'Error enviando consulta: {e}')
            return jresp({'error': 'Error interno al enviar el email'}, 500)

        return jresp({'success': True}, 201)

urlpatterns = [
    path('orders/', OrderCreateView.as_view(), name='api_orders'),
    path('contacto/', ContactoView.as_view(),    name='api_contacto'),

]
