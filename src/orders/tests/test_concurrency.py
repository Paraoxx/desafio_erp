import pytest
import threading
from django.db import connection
from orders.models import Product, Customer, Order
from orders.services import CreateOrderService
from orders.dtos import CreateOrderDTO, OrderItemDTO

# TransactionTestCase para permitir threads no teste e isolamento de banco
from django.test import TransactionTestCase

class ConcurrencyTestCase(TransactionTestCase):
    def setUp(self):
        # Cria dados iniciais
        self.customer = Customer.objects.create(
            name="Tester", 
            cpf_cnpj="11122233344", 
            email="t@t.com", 
            phone="11999999999"
        )
        # Produto com APENAS 1 unidade em estoque para forçar a disputa
        self.product = Product.objects.create(
            sku="IPHONE15", 
            name="iPhone 15", 
            price=5000, 
            stock_quantity=1
        )
        
        # Instancia o serviço 
        self.service = CreateOrderService()

    def test_race_condition_buy_last_item(self):
        """
        Cenário 6.1: Dois pedidos simultâneos tentam comprar o último item.
        Apenas UM deve conseguir. O outro deve falhar com erro de estoque.
        """
        results = []
        errors = []

        def place_order():
            # Tenta comprar o último item usando os nomes de atributos 
            dto = CreateOrderDTO(
                customer_id=self.customer.id,
                items=[OrderItemDTO(product_id=self.product.id, quantity=1)]
            )
            try:
                # Chama o método create_order 
                order = self.service.create_order(dto)
                results.append(order)
            except Exception as e:
                errors.append(e)
            finally:
                # Fecha conexões de thread para evitar travamento do banco no teste
                connection.close()

        # Criar 2 threads simulando acessos exatamente ao mesmo tempo
        t1 = threading.Thread(target=place_order)
        t2 = threading.Thread(target=place_order)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Logs para conferência no terminal (visíveis com a flag -s)
        print(f"\nPedidos processados: {len(results)}")
        print(f"Erros de estoque capturados: {len(errors)}")

        # VALIDAÇÕES TÉCNICAS:
        
        # bloqueio (apenas 1 pedido criado)
        self.assertEqual(len(results), 1, "ERRO: Mais de um pedido foi criado para apenas 1 item em estoque!")
        
        # Garante que a segunda thread recebeu a exceção de estoque insuficiente
        self.assertEqual(len(errors), 1, "ERRO: A segunda thread deveria ter falhado por falta de estoque!")
        
        # Garante que o estoque final no banco de dados é zero 
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 0, "ERRO: O estoque deveria ser exatamente 0!")