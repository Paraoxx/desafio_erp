from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal

@dataclass
class OrderItemDTO:
    product_sku: str
    quantity: int

@dataclass
class CreateOrderDTO:
    customer_cpf: str
    items: List[OrderItemDTO]
    
@dataclass
class UpdateOrderStatusDTO:
    order_id: int
    new_status: str
    user_id: Optional[int] = None 