from abc import ABC, abstractmethod
from typing import List, Optional
from .models import Order, Product, Customer

class IProductRepository(ABC):
    @abstractmethod
    def get_by_sku(self, sku: str) -> Optional[Product]:
        pass

    @abstractmethod
    def list_active(self) -> List[Product]:
        pass

class ICustomerRepository(ABC):
    @abstractmethod
    def get_by_cpf(self, cpf: str) -> Optional[Customer]:
        pass

class IOrderRepository(ABC):
    @abstractmethod
    def create(self, order: Order) -> Order:
        pass
        
    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional[Order]:
        pass
        
    @abstractmethod
    def list(self) -> List[Order]:
        pass