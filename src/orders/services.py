import logging
from typing import Optional
from django.db import transaction
from django.core.cache import cache
from django.core.exceptions import ValidationError
from .models import Order, OrderItem, Product, OrderStatusHistory
from .dtos import CreateOrderDTO, UpdateOrderStatusDTO
from .interfaces import IProductRepository, ICustomerRepository, IOrderRepository

logger = logging.getLogger(__name__)

class CreateOrderService:
    def __init__(self, product_repo: IProductRepository, customer_repo: ICustomerRepository, order_repo: IOrderRepository):
        self.product_repo = product_repo
        self.customer_repo = customer_repo
        self.order_repo = order_repo

    def execute(self, dto: CreateOrderDTO, idempotency_key: Optional[str] = None) -> Order:
       
        # Se a chave existe no redis retorna o pedido original sem processar nada novo
        if idempotency_key:
            cache_key = f"idempotency_{idempotency_key}"
            existing_order_id = cache.get(cache_key)
            if existing_order_id:
                logger.info(f"Idempotency hit: returning existing order {existing_order_id}")
                return self.order_repo.get_by_id(existing_order_id)

        with transaction.atomic():
            # Validar Cliente
            customer = self.customer_repo.get_by_cpf(dto.customer_cpf)
            if not customer:
                raise ValidationError({"customer": "Cliente não encontrado."})
            if not customer.is_active:
                raise ValidationError({"customer": "Cliente inativo."})

            # Validar se tem itens
            if not dto.items:
                raise ValidationError({"items": "O pedido deve conter pelo menos um item."})
            # ciclo de espera 
            dto.items.sort(key=lambda x: x.product_sku)

            total_amount = 0
            order_items_objects = []

            # Cria o cabeçalho do pedido 
            order = Order(
                customer=customer,
                status=Order.Status.PENDING,
                total_amount=0
            )
            # Salvar id e associar os itens
            order = self.order_repo.create(order)

            # Loop de estoque 
            for item_dto in dto.items:
                try:
                    product = Product.objects.select_for_update().get(sku=item_dto.product_sku)
                except Product.DoesNotExist:
                    raise ValidationError({"product": f"Produto {item_dto.product_sku} não encontrado."})

                if not product.is_active:
                    raise ValidationError({"product": f"Produto {product.name} está inativo."})

                if product.stock_quantity < item_dto.quantity:
                    raise ValidationError({
                        "stock": f"Estoque insuficiente para {product.name}. Restam {product.stock_quantity}."
                    })

                # Baixa o estoque
                product.stock_quantity -= item_dto.quantity
                product.save()

                # Snapshot do preço 
                item_total = product.price * item_dto.quantity
                total_amount += item_total

                order_items_objects.append(OrderItem(
                    order=order,
                    product=product,
                    quantity=item_dto.quantity,
                    unit_price=product.price, # Preço do momento da compra
                    subtotal=item_total
                ))

            # Bulk create dos itens para performance
            OrderItem.objects.bulk_create(order_items_objects)

            # Atualiza o total do pedido
            order.total_amount = total_amount
            order.save()

            # 5. Histórico inicial 
            OrderStatusHistory.objects.create(
                order=order,
                old_status=None,
                new_status=Order.Status.PENDING,
                observation="Pedido criado via API"
            )

            # Grava a chave de idempotência no Redis 
            if idempotency_key:
                cache.set(cache_key, order.id, timeout=60*60*24)

            return order


class UpdateOrderStatusService:
    def __init__(self, order_repo: IOrderRepository):
        self.order_repo = order_repo
    
    VALID_TRANSITIONS = {
        Order.Status.PENDING: [Order.Status.CONFIRMED, Order.Status.CANCELED],
        Order.Status.CONFIRMED: [Order.Status.SEPARATED, Order.Status.CANCELED],
        Order.Status.SEPARATED: [Order.Status.SHIPPED],
        Order.Status.SHIPPED: [Order.Status.DELIVERED],
        Order.Status.DELIVERED: [],
        Order.Status.CANCELED: [],  
    }

    def execute(self, dto: UpdateOrderStatusDTO) -> Order:
        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().get(id=dto.order_id)
            except Order.DoesNotExist:
                raise ValidationError("Pedido não encontrado.")

            old_status = order.status
            new_status = dto.new_status

            # Validação da Transição
            allowed_next_statuses = self.VALID_TRANSITIONS.get(old_status, [])
            if new_status not in allowed_next_statuses:
                raise ValidationError(f"Transição inválida: de {old_status} para {new_status}.")

            # Regra de Devolução de Estoque ao Cancelar 
            if new_status == Order.Status.CANCELED:
                self._restore_stock(order)

            # Atualiza status
            order.status = new_status
            order.save()

            # Grava Histórico
            OrderStatusHistory.objects.create(
                order=order,
                old_status=old_status,
                new_status=new_status,
                user_id=dto.user_id,
                observation=f"Status alterado manualmente."
            )

            return order

    def _restore_stock(self, order: Order):

        # Itera sobre os itens e devolve ao estoque
        for item in order.items.all():
            product = Product.objects.select_for_update().get(id=item.product.id)
            product.stock_quantity += item.quantity
            product.save()