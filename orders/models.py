from django.db import models
import uuid


class Category(models.Model):
    name  = models.CharField('Nombre', max_length=100)
    slug  = models.SlugField('Slug', unique=True)
    order = models.PositiveIntegerField('Orden', default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.name


class Product(models.Model):
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                    verbose_name='Categoría', related_name='products')
    name        = models.CharField('Nombre', max_length=200)
    emoji       = models.CharField('Emoji', max_length=10, default='🥩')
    description = models.TextField('Descripción', blank=True)
    price_label = models.CharField('Precio', max_length=100, default='Consultar',
                                   help_text='Ej: Consultar, $6.800, Precio mayorista')
    unit        = models.CharField('Unidad', max_length=50, default='kg',
                                   help_text='Ej: kg, pieza, unidad')
    tag         = models.CharField('Etiqueta', max_length=50, blank=True,
                                   help_text='Ej: Al Vacío, Mayorista, Nuevo')
    active      = models.BooleanField('Visible en catálogo', default=True)
    order       = models.PositiveIntegerField('Orden', default=0)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return f'{self.emoji} {self.name}'


class Order(models.Model):
    class Status(models.TextChoices):
        NUEVO      = 'nuevo',      'Nuevo'
        CONTACTADO = 'contactado', 'Contactado'
        CERRADO    = 'cerrado',    'Cerrado'
        CANCELADO  = 'cancelado',  'Cancelado'

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
    customer_name  = models.CharField('Nombre', max_length=200)
    customer_phone = models.CharField('Teléfono', max_length=50)
    customer_email = models.EmailField('Email')
    customer_zone  = models.CharField('Zona', max_length=200, blank=True)
    notes          = models.TextField('Comentarios', blank=True)
    items          = models.JSONField('Productos', default=list)
    status         = models.CharField('Estado', max_length=20,
                                      choices=Status.choices, default=Status.NUEVO, db_index=True)
    seller_notes   = models.TextField('Notas del vendedor', blank=True)
    assigned_to    = models.CharField('Asignado a', max_length=100, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'

    def __str__(self):
        return f'#{str(self.id)[:8]} — {self.customer_name}'

    @property
    def items_summary(self):
        return ', '.join(f"{i.get('name','?')} x{i.get('qty',1)}" for i in self.items)

    @property
    def total_items(self):
        return sum(i.get('qty', 1) for i in self.items)
