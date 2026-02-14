from django.db import transaction
from .models import Order, OrderItem, Product
from .dtos import CreateOrderDTO

class OrderService:
    @transaction.atomic
    def create_order(self, dto: CreateOrderDTO) -> Order:
        # Travar os produtos no banco para concorrencia 
        product_ids = [item.product_id for item in dto.items]
        products = Product.objects.select_for_update().filter(id__in=product_ids)
        
        product_map = {p.id: p for p in products}
        
        # Validação e checagem de estoque
        for item in dto.items:
            product = product_map.get(item.product_id)
            if not product:
                raise ValueError(f"Produto ID {item.product_id} não encontrado.")
            if product.stock_quantity < item.quantity:
                raise ValueError(f"Estoque insuficiente para o produto {product.name}.")
            
        # Criar o Pedido 
        order = Order.objects.create(
            customer_id=dto.customer_id,
            status=Order.Status.PENDING,
            total_amount=0
        )
        
        total = 0
        
        # Criar os itens do pedido e abater o estoque
        for item in dto.items:
            product = product_map[item.product_id]
            subtotal = product.price * item.quantity
            
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                unit_price=product.price,
                subtotal=subtotal
            )
            
            # Abater o estoque do produto
            product.stock_quantity -= item.quantity
            product.save()
            
            total += subtotal
            
        # Atualizar o valor total do pedido
        order.total_amount = total
        order.save()
        
        return order