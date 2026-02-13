from typing import List, Optional
from django.db import transaction
from .models import Product, Customer, Order
from .interfaces import IProductRepository, ICustomerRepository, IOrderRepository

class ProductRepository(IProductRepository):
    def get_by_sku(self, sku: str) -> Optional[Product]:
        try:
            return Product.objects.get(sku=sku)
        except Product.DoesNotExist:
            return None

    def list_active(self) -> List[Product]:
        return list(Product.objects.filter(is_active=True))

class CustomerRepository(ICustomerRepository):
    def get_by_cpf(self, cpf: str) -> Optional[Customer]:
        try:
            return Customer.objects.get(cpf_cnpj=cpf)
        except Customer.DoesNotExist:
            return None

class OrderRepository(IOrderRepository):
    def create(self, order: Order) -> Order:
        order.save()
        return order
        
    def get_by_id(self, order_id: int) -> Optional[Order]:
        try:
            return Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return None
            
    def list(self) -> List[Order]:
        return list(Order.objects.all().order_by('-created_at'))