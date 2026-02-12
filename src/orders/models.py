from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator

User = get_user_model()

# Abstract Models 

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        # Por padrão esconde os deletados
        return super().get_queryset().filter(deleted_at__isnull=True)

class GlobalManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

class BaseModel(models.Model):
    """
    Base model que implementa timestamps e Soft Delete.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = GlobalManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super().delete()


# Domain Models 

class Customer(BaseModel):
    name = models.CharField(max_length=255)
    cpf_cnpj = models.CharField(max_length=14, unique=True, db_index=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.cpf_cnpj})"


class Product(BaseModel):
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock_quantity = models.IntegerField(default=0)  # Controle crítico
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.sku} - {self.name}"


class Order(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'PENDENTE', 'Pendente'
        CONFIRMED = 'CONFIRMADO', 'Confirmado'
        SEPARATED = 'SEPARADO', 'Separado'
        SHIPPED = 'ENVIADO', 'Enviado'
        DELIVERED = 'ENTREGUE', 'Entregue'
        CANCELED = 'CANCELADO', 'Cancelado'

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.PENDING,
        db_index=True
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} - {self.status}"


class OrderItem(models.Model):
    # Itens não precisam de soft delete individualmente, model simples para performance.
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    # Snapshot do preço no momento da compra 
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        # Garante cálculo automático
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity}x {self.product.sku}"


class OrderStatusHistory(models.Model):
    """
    Tabela de auditoria para mudanças de status.
    Não usamos Soft Delete aqui, histórico é imutável.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='history')
    old_status = models.CharField(max_length=20, null=True, blank=True)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)

    # Usuário pode ser null se for mudança 
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    observation = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"Order {self.order_id}: {self.old_status} -> {self.new_status}"