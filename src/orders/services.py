from django.core.exceptions import ValidationError
from django.db import transaction
from .interfaces import IProductRepository, ICustomerRepository, IOrderRepository
from .dtos import CreateOrderDTO, OrderItemDTO
from .models import Order, OrderItem

class CreateOrderService:
    def __init__(
        self, 
        product_repo: IProductRepository,
        customer_repo: ICustomerRepository,
        order_repo: IOrderRepository
    ):
        # Injeção de dependência 
        self.product_repo = product_repo
        self.customer_repo = customer_repo
        self.order_repo = order_repo

    def execute(self, dto: CreateOrderDTO) -> Order:

        # Validar Cliente
        customer = self.customer_repo.get_by_cpf(dto.customer_cpf)
        if not customer:
            raise ValidationError(f"Cliente com CPF {dto.customer_cpf} não encontrado.")
        if not customer.is_active:
            raise ValidationError("Cliente inativo.")

        # A lógica pesada de estoque transaction + lock
        
        # Mock temporário para testar a estrutura:
        order = Order(customer=customer, total_amount=0)
        return self.order_repo.create(order)