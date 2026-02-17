from django.test import TestCase
from orders.models import Customer, Product, Order
from orders.services import CreateOrderService
from orders.dtos import CreateOrderDTO, OrderItemDTO

class AtomicityTestCase(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            name="Cliente Atomicidade", 
            cpf_cnpj="99988877766", 
            email="atom@teste.com"
        )
        # Produtos com estoque
        self.product_1 = Product.objects.create(sku="PROD-1", name="Produto 1", price=10.0, stock_quantity=10)
        self.product_2 = Product.objects.create(sku="PROD-2", name="Produto 2", price=20.0, stock_quantity=10)
        
        # Produto sem estoque 
        self.product_3 = Product.objects.create(sku="PROD-3", name="Produto Falha", price=30.0, stock_quantity=0)
        
        self.service = CreateOrderService()

    def test_atomic_partial_failure(self):
        """
        Cenário 6.3: Pedido com 3 itens. Item 1 e 2 têm estoque, item 3 não tem.
        Nenhum estoque deve ser reservado (Rollback completo).
        """
        dto = CreateOrderDTO(
            customer_id=self.customer.id,
            items=[
                OrderItemDTO(product_id=self.product_1.id, quantity=2), # OK
                OrderItemDTO(product_id=self.product_2.id, quantity=2), # OK
                OrderItemDTO(product_id=self.product_3.id, quantity=1), # VAI FALHAR
            ]
        )

        # Garante a exceção 
        with self.assertRaises(ValueError):
            self.service.create_order(dto)

        # Validações finais 
        self.product_1.refresh_from_db()
        self.product_2.refresh_from_db()

        # O estoque dos produtos 1 e 2 nao pode ter sido alterado
        self.assertEqual(
            self.product_1.stock_quantity, 10, 
            "ERRO: O estoque do Produto 1 foi abatido mesmo com a falha do pedido!"
        )
        self.assertEqual(
            self.product_2.stock_quantity, 10, 
            "ERRO: O estoque do Produto 2 foi abatido mesmo com a falha do pedido!"
        )
        
        # Nenhum pedido deve existir no banco
        self.assertEqual(Order.objects.count(), 0, "ERRO: Um pedido fantasma foi criado!")