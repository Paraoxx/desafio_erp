from dataclasses import dataclass
from typing import List

@dataclass
class OrderItemDTO:
    product_id: int
    quantity: int

@dataclass
class CreateOrderDTO:
    customer_id: int
    items: List[OrderItemDTO]