from django.urls import path
from .admin_views import *

urlpatterns = [
    path('login/',   admin_login,   name='admin_login'),
    path('logout/',  admin_logout,  name='admin_logout'),
    path('',         admin_dashboard, name='admin_dashboard'),

    # Pedidos
    path('pedidos/',                         admin_pedidos,       name='admin_pedidos'),
    path('pedidos/<uuid:order_id>/',         admin_pedido_detail, name='admin_pedido_detail'),

    # Productos
    path('productos/',                       admin_productos,        name='admin_productos'),
    path('productos/nuevo/',                 admin_producto_form,    name='admin_producto_nuevo'),
    path('productos/<int:pk>/editar/',       admin_producto_form,    name='admin_producto_editar'),
    path('productos/<int:pk>/toggle/',       admin_producto_toggle,  name='admin_producto_toggle'),
    path('productos/<int:pk>/eliminar/',     admin_producto_delete,  name='admin_producto_delete'),

    # Categorías
    path('categorias/',                      admin_categorias,       name='admin_categorias'),
    path('categorias/nueva/',                admin_categoria_form,   name='admin_categoria_nueva'),
    path('categorias/<int:pk>/editar/',      admin_categoria_form,   name='admin_categoria_editar'),
    path('categorias/<int:pk>/eliminar/',    admin_categoria_delete, name='admin_categoria_delete'),

    # Mapa
    path('zonas/',                           admin_zonas,            name='admin_zonas'),
    path('zonas/nueva/',                     admin_zona_form,        name='admin_zona_nueva'),
    path('zonas/<int:pk>/editar/',           admin_zona_form,        name='admin_zona_editar'),
    path('zonas/<int:pk>/eliminar/',         admin_zona_delete,      name='admin_zona_eliminar'),
]
