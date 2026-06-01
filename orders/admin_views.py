from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils.text import slugify
from functools import wraps
from django.contrib import admin
from .models import Order, Product, Category, ZonaEntrega


@admin.register(ZonaEntrega)
class ZonaEntregaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo')
    
    class Media:
        css = {
            'all': (
                'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
                'https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css',
            )
        }
        js = (
            'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
            'https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js',
            'js/admin_mapa_zonas.js', # El mismo script de JS que te pase en la respuesta anterior
        )


def staff_required(fn):
    @wraps(fn)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect(f'/admin/login/?next={request.path}')
        return fn(request, *args, **kwargs)
    return wrapper


# ── AUTH ───────────────────────────────────────────────────────────────────────

def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin_pedidos')
    if request.method == 'POST':
        user = authenticate(request,
            username=request.POST.get('username','').strip(),
            password=request.POST.get('password',''))
        if user and user.is_staff:
            login(request, user)
            return redirect(request.GET.get('next', 'admin_pedidos'))
        messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'admin/login.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


# ── DASHBOARD ──────────────────────────────────────────────────────────────────

@staff_required
def admin_dashboard(request):
    ctx = {
        'total_pedidos':     Order.objects.count(),
        'nuevos':            Order.objects.filter(status='nuevo').count(),
        'contactados':       Order.objects.filter(status='contactado').count(),
        'cerrados':          Order.objects.filter(status='cerrado').count(),
        'total_productos':   Product.objects.count(),
        'productos_activos': Product.objects.filter(active=True).count(),
        'total_categorias':  Category.objects.count(),
        'pedidos_recientes': Order.objects.all()[:8],
    }
    return render(request, 'admin/dashboard.html', ctx)


# ── PEDIDOS ────────────────────────────────────────────────────────────────────

@staff_required
def admin_pedidos(request):
    qs = Order.objects.all()
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '').strip()
    if status_filter:
        qs = qs.filter(status=status_filter)
    if search:
        qs = qs.filter(
            Q(customer_name__icontains=search) |
            Q(customer_phone__icontains=search) |
            Q(customer_email__icontains=search)
        )
    page = Paginator(qs, 25).get_page(request.GET.get('page', 1))
    return render(request, 'admin/pedidos.html', {
        'page': page,
        'counts': {
            'todos':      Order.objects.count(),
            'nuevo':      Order.objects.filter(status='nuevo').count(),
            'contactado': Order.objects.filter(status='contactado').count(),
            'cerrado':    Order.objects.filter(status='cerrado').count(),
            'cancelado':  Order.objects.filter(status='cancelado').count(),
        },
        'status_filter': status_filter,
        'search':        search,
        'status_choices': Order.Status.choices,
    })


@staff_required
def admin_pedido_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            s = request.POST.get('status')
            if s in dict(Order.Status.choices):
                order.status = s
                order.save(update_fields=['status', 'updated_at'])
                messages.success(request, f'Estado → {order.get_status_display()}')
        elif action == 'save_notes':
            order.seller_notes = request.POST.get('seller_notes', '')
            order.assigned_to  = request.POST.get('assigned_to', '')
            order.save(update_fields=['seller_notes', 'assigned_to', 'updated_at'])
            messages.success(request, 'Notas guardadas.')
        return redirect('admin_pedido_detail', order_id=order_id)
    return render(request, 'admin/pedido_detail.html', {
        'order':          order,
        'status_choices': Order.Status.choices,
    })


# ── PRODUCTOS ──────────────────────────────────────────────────────────────────

@staff_required
def admin_productos(request):
    qs = Product.objects.select_related('category').all()
    search     = request.GET.get('q', '').strip()
    cat_filter = request.GET.get('cat', '')
    act_filter = request.GET.get('active', '')
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
    if cat_filter:
        qs = qs.filter(category__slug=cat_filter)
    if act_filter == '1':
        qs = qs.filter(active=True)
    elif act_filter == '0':
        qs = qs.filter(active=False)
    return render(request, 'admin/productos.html', {
        'page':       Paginator(qs, 30).get_page(request.GET.get('page', 1)),
        'categories': Category.objects.all(),
        'search': search, 'cat_filter': cat_filter, 'act_filter': act_filter,
        'total':   Product.objects.count(),
        'activos': Product.objects.filter(active=True).count(),
    })


@staff_required
def admin_producto_form(request, pk=None):
    product    = get_object_or_404(Product, pk=pk) if pk else None
    categories = Category.objects.all()
    is_new     = product is None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'El nombre es obligatorio.')
        else:
            if is_new:
                product = Product()
            product.name        = name
            product.emoji       = request.POST.get('emoji', '🥩').strip() or '🥩'
            product.description = request.POST.get('description', '').strip()
            product.price_label = request.POST.get('price_label', 'Consultar').strip()
            product.unit        = request.POST.get('unit', 'kg').strip()
            product.tag         = request.POST.get('tag', '').strip()
            product.active      = 'active' in request.POST
            product.order       = int(request.POST.get('order', 0) or 0)
            cat_id              = request.POST.get('category', '')
            product.category    = Category.objects.filter(pk=cat_id).first() if cat_id else None

            # ── Imagen ────────────────────────────────────────────────────────
            if request.FILES.get('image'):
                product.image = request.FILES['image']
            elif request.POST.get('remove_image') == '1':
                # El usuario tildó "eliminar imagen actual"
                product.image = None

            product.save()
            verb = 'creado' if is_new else 'actualizado'
            messages.success(request, f'Producto "{product.name}" {verb} correctamente.')
            return redirect('admin_productos')

    return render(request, 'admin/producto_form.html', {
        'product': product, 'categories': categories, 'is_new': is_new,
    })


@staff_required
def admin_producto_toggle(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.active = not product.active
    product.save(update_fields=['active', 'updated_at'])
    messages.success(request, f'"{product.name}" {"activado" if product.active else "desactivado"}.')
    return redirect(request.META.get('HTTP_REFERER', 'admin_productos'))


@staff_required
def admin_producto_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        nombre = str(product)
        product.delete()
        messages.success(request, f'{nombre} eliminado.')
        return redirect('admin_productos')
    return render(request, 'admin/confirm_delete.html', {
        'object':   product,
        'titulo':   f'Eliminar producto: {product}',
        'back_url': '/admin/productos/',
    })


# ── CATEGORÍAS ─────────────────────────────────────────────────────────────────

@staff_required
def admin_categorias(request):
    cats = Category.objects.annotate(num_products=Count('products')).all()
    return render(request, 'admin/categorias.html', {'categories': cats})


@staff_required
def admin_categoria_form(request, pk=None):
    cat    = get_object_or_404(Category, pk=pk) if pk else None
    is_new = cat is None

    if request.method == 'POST':
        name  = request.POST.get('name', '').strip()
        slug  = request.POST.get('slug', '').strip() or slugify(name)
        order = int(request.POST.get('order', 0) or 0)
        if not name:
            messages.error(request, 'El nombre es obligatorio.')
        elif Category.objects.filter(slug=slug).exclude(pk=pk).exists():
            messages.error(request, f'Ya existe una categoría con el slug "{slug}".')
        else:
            if is_new:
                cat = Category()
            cat.name  = name
            cat.slug  = slug
            cat.order = order
            cat.save()
            messages.success(request, f'Categoría "{name}" {"creada" if is_new else "actualizada"}.')
            return redirect('admin_categorias')

    return render(request, 'admin/categoria_form.html', {
        'cat': cat, 'is_new': is_new,
    })


@staff_required
def admin_categoria_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        nombre = cat.name
        cat.delete()
        messages.success(request, f'Categoría "{nombre}" eliminada.')
        return redirect('admin_categorias')
    return render(request, 'admin/confirm_delete.html', {
        'object':   cat,
        'titulo':   f'Eliminar categoría: {cat.name}',
        'back_url': '/admin/categorias/',
        'warning':  f'Se va a desasignar la categoría de {cat.products.count()} productos.',
    })

## ADMINISTRADOR PARA ZONAS
def admin_zonas(request):
    """Muestra el listado de todas las zonas de entrega en una tabla"""
    zonas = ZonaEntrega.objects.all().order_by('nombre')
    return render(request, 'admin/zonas_list.html', {
        'zonas': zonas,
        'nav_zonas': 'active'  # Activa el botón en el sidebar de tu base.html
    })

def admin_zona_form(request, pk=None):
    """Maneja la creación y edición de zonas utilizando el tipo de zona del modelo"""
    zona = get_object_or_400(ZonaEntrega, pk=pk) if pk else None

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        tipo = request.POST.get("tipo")  # Captura 'verde', 'amarillo' o 'rojo'
        poligono_geojson = request.POST.get("poligono_geojson")

        if not nombre or not poligono_geojson:
            messages.error(request, "El nombre y la delimitación en el mapa son obligatorios.")
            return render(request, 'admin/zonas_form.html', {'zona': zona})

        if zona:
            zona.nombre = nombre
            zona.tipo = tipo
            zona.poligono_geojson = poligono_geojson
            zona.save()
            messages.success(request, f"Zona '{nombre}' actualizada con éxito.")
        else:
            ZonaEntrega.objects.create(
                nombre=nombre,
                tipo=tipo,
                poligono_geojson=poligono_geojson
            )
            messages.success(request, f"Zona '{nombre}' creada con éxito.")

        return redirect('admin_zonas')

    return render(request, 'admin/zonas_form.html', {
        'zona': zona,
        'nav_zonas': 'active'
    })

def admin_zona_delete(request, pk):
    """Elimina la zona de entrega"""
    zona = get_object_or_400(ZonaEntrega, pk=pk)
    nombre = zona.nombre
    
    if request.method == "POST":
        zona.delete()
        messages.success(request, f"La zona '{nombre}' fue eliminada.")
        return redirect('admin_zonas')
        
    # Fallback por si ejecutan un GET directo (así machea con tus otros views de eliminar)
    zona.delete()
    messages.success(request, f"La zona '{nombre}' fue eliminada.")
    return redirect('admin_zonas')

    return render(request, "admin/zonas_form.html", {"zona": zona})