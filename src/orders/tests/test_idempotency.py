from rest_framework.test import APITestCase
from rest_framework import status
from django.core.cache import cache
from orders.models import Customer, Product, Order

class IdempotencyTestCase(APITestCase):
    def setUp(self):
        # Limpa o cache antes do teste 
        cache.clear()
        
        self.customer = Customer.objects.create(
            name="Cliente Idempotencia", 
            cpf_cnpj="12312312312", 
            email="idemp@teste.com"
        )
        self.product = Product.objects.create(
            sku="IDEMP-PROD", 
            name="Produto Idempotencia", 
            price=100.0, 
            stock_quantity=10
        )
        
        # URL do endpoint 
        self.url = '/api/v1/orders/' 

    def test_idempotency_multiple_requests(self):
        """
        Cenário 6.2: Cliente envia a mesma requisição 3 vezes.
        Apenas UM pedido deve ser criado. O resto deve retornar 200 OK.
        """
        payload = {
            "customer": self.customer.id,
            "items": [
                {"product": self.product.id, "quantity": 2}
            ]
        }
        
        # Header de Idempotência simulando a mesma chave
        headers = {'HTTP_IDEMPOTENCY_KEY': 'chave-unica-transacao-12345'}

        # 1ª Requisição (Deve criar o pedido e retornar 201)
        response1 = self.client.post(self.url, payload, format='json', **headers)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # 2ª Requisição idêntica (Deve retornar 200 do cache)
        response2 = self.client.post(self.url, payload, format='json', **headers)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # 3ª Requisição idêntica (Deve retornar 200 do cache)
        response3 = self.client.post(self.url, payload, format='json', **headers)
        self.assertEqual(response3.status_code, status.HTTP_200_OK)

        # Validações finais no Banco de Dados
        self.assertEqual(Order.objects.count(), 1, "ERRO: Mais de um pedido foi salvo no banco!")
        
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 8, "ERRO: O estoque foi abatido mais de uma vez!")