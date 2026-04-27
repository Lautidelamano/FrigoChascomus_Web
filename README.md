# Frigo Chascomús — Proyecto Django Completo

## Inicio rápido (desarrollo local)

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Copiar y configurar variables
cp .env.example .env
# Editar .env con tus datos (o dejar como está para SQLite local)

# 3. Crear tablas en la base de datos
python manage.py migrate

# 4. Cargar datos iniciales (categorías + 12 productos de ejemplo)
python manage.py loaddata orders/fixtures/initial_data.json

# 5. Crear usuario administrador
python manage.py createsuperuser
# Ingresar usuario, email y contraseña cuando lo pide

# 6. Correr el servidor
python manage.py runserver
```

## URLs del sistema

| URL | Descripción |
|-----|-------------|
| `http://localhost:8000/` | Sitio público |
| `http://localhost:8000/admin/` | Panel admin |
| `http://localhost:8000/admin/login/` | Login vendedores |
| `http://localhost:8000/admin/pedidos/` | Lista de pedidos |
| `http://localhost:8000/admin/productos/` | Gestión catálogo |
| `http://localhost:8000/admin/categorias/` | Gestión categorías |
| `http://localhost:8000/api/orders/` | API (POST pedidos) |

## Panel Admin — funcionalidades

- **Dashboard**: resumen de pedidos nuevos, activos, cerrados y productos
- **Pedidos**: ver todos los pedidos, filtrar por estado, buscar por cliente, cambiar estado (Nuevo → Contactado → Cerrado), agregar notas internas y asignar a un vendedor
- **Productos**: agregar, editar, eliminar y activar/desactivar productos del catálogo
- **Categorías**: crear categorías que aparecen como filtros en el sitio

## Agregar el logo real

Copiar el archivo del logo a:
```
static/img/logo.png
```

El sitio lo mostrará automáticamente en el hero. Si no existe, muestra el emoji 🐄.

## Notas importantes

- **SQLite**: funciona sin instalar PostgreSQL. Ideal para desarrollo.
- **PostgreSQL**: para producción, configurar `DB_NAME`, `DB_USER`, etc. en `.env`
- **Emails en desarrollo**: si no configurás `EMAIL_HOST_USER`, Django imprime los emails en la consola del servidor. Así podés verlos sin enviar nada real.
- **SENASA / habilitación**: el sitio incluye los textos correspondientes. Ajustar si es necesario.

## Estructura del proyecto

```
frigochascomus/
├── frigochascomus/          # Configuración Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── orders/                  # App principal
│   ├── models.py            # Category, Product, Order
│   ├── api_urls.py          # POST /api/orders/
│   ├── site_urls.py         # GET / (sitio público)
│   ├── admin_urls.py        # /admin/* (panel)
│   ├── admin_views.py       # Vistas del panel admin
│   ├── emails.py            # Envío de emails
│   ├── context_processors.py
│   └── fixtures/
│       └── initial_data.json
├── templates/
│   ├── site/
│   │   └── index.html       # Sitio público completo
│   ├── admin/
│   │   ├── base.html        # Layout base del panel
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── pedidos.html
│   │   ├── pedido_detail.html
│   │   ├── productos.html
│   │   ├── producto_form.html
│   │   ├── categorias.html
│   │   ├── categoria_form.html
│   │   └── confirm_delete.html
│   └── orders/
│       ├── email_client.html/txt
│       └── email_vendor.html/txt
├── static/
│   └── img/
│       └── logo.png         # Poner el logo acá
├── requirements.txt
├── .env.example
└── manage.py
```
