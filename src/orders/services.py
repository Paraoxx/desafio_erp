from django.db import transaction
from .models import Order, OrderItem, Product, OrderStatusHistory, Customer
from .dtos import CreateOrderDTO

class CreateOrderService:
    @transaction.atomic
    def create_order(self, dto: CreateOrderDTO) -> Order:
        # Validacao do Cliente 
        try:
            customer = Customer.objects.get(id=dto.customer_id)
        except Customer.DoesNotExist:
            raise ValueError("Cliente não encontrado.")
            
        if not customer.is_active:
            raise ValueError("Cliente inativo não pode realizar pedidos.")

        # Travar os produtos no banco para concorrencia 
        product_ids = [item.product_id for item in dto.items]
        products = Product.objects.select_for_update().filter(id__in=product_ids)
        
        product_map = {p.id: p for p in products}
        
        # Validação de Produtos, quantidade e estoque 
        for item in dto.items:
            if item.quantity <= 0:
                raise ValueError("A quantidade do item deve ser maior que zero.")
                
            product = product_map.get(item.product_id)
            if not product:
                raise ValueError(f"Produto ID {item.product_id} não encontrado.")
            if not product.is_active:
                raise ValueError(f"O produto {product.name} está inativo e não pode ser vendido.")
            if product.stock_quantity < item.quantity:
                raise ValueError(f"Estoque insuficiente para o produto {product.name}.")
            
        # 4. Criar o Pedido 
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
            
            # Abater o estoque do produto atomicamente
            product.stock_quantity -= item.quantity
            product.save()
            
            total += subtotal
            
        # 6. Atualizar o valor total do pedido
        order.total_amount = total
        order.save()
        
        return order


class UpdateOrderStatusService:
    # Transicoes válidas de status 
    ALLOWED_TRANSITIONS = {
        Order.Status.PENDING: [Order.Status.CONFIRMED, Order.Status.CANCELED],
        Order.Status.CONFIRMED: [Order.Status.SEPARATED, Order.Status.CANCELED],
        Order.Status.SEPARATED: [Order.Status.SHIPPED],
        Order.Status.SHIPPED: [Order.Status.DELIVERED],
        Order.Status.DELIVERED: [],  
        Order.Status.CANCELED: []    
    }

    @transaction.atomic
    def update_status(self, order_id: int, new_status: str, user=None, observation: str = "") -> Order:
        # Trava a linha do pedido para evitar atualizações concorrentes
        order = Order.objects.select_for_update().get(id=order_id)
        
        old_status = order.status
        
        # Se o status for o mesmo, não faz nada
        if old_status == new_status:
            return order
            
        # Valida se o status enviado existe no sistema
        if new_status not in dict(Order.Status.choices):
            raise ValueError(f"Status '{new_status}' inválido.")
            
        # Bloqueia transições invalidas 
        if new_status not in self.ALLOWED_TRANSITIONS.get(old_status, []):
            raise ValueError(f"Transição de status inválida: de '{old_status}' para '{new_status}'.")
            
        # Ao cancelar um pedido, o estoque deve ser devolvido
        if new_status == Order.Status.CANCELED:
            items = order.items.all()
            # Trava as linhas dos produtos especificos desse pedido
            product_ids = [item.product_id for item in items]
            products_to_update = Product.objects.select_for_update().filter(id__in=product_ids)
            product_map = {p.id: p for p in products_to_update}
            
            for item in items:
                product = product_map[item.product_id]
                product.stock_quantity += item.quantity 
                product.save()
                
        # Atualiza o pedido
        order.status = new_status
        order.save()
        
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status=new_status,
            user=user,
            observation=observation
        )
        
        return order