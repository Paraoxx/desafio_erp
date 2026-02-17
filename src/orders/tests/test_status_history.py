from rest_framework.test import APITestCase
from rest_framework import status
from orders.models import Customer, Order, OrderStatusHistory

class TestOrderStatusHistory(APITestCase):
    def setUp(self):
        # Cria um cliente com todos os campos obrigatórios
        self.customer = Customer.objects.create(
            name="Cliente Teste Status", 
            cpf_cnpj="55566677788", 
            email="status@teste.com",
            phone="11999999999",         
            address="Rua dos Testes, 123" 
        )
        self.order = Order.objects.create(
            customer=self.customer,
            status=Order.Status.PENDING,
            total_amount=100.00
        )
        
        # Monta a URL dinâmica usando o ID do pedido gerado
        self.url = f'/api/v1/orders/{self.order.id}/status/'

    def test_change_status_creates_history(self):
        """
        Garante que a rota PATCH de mudança de status atualiza o pedido 
        e salva corretamente na tabela de auditoria (OrderStatusHistory).
        """
        payload = {
            "status": "CONFIRMADO",
            "observation": "Pagamento aprovado via PIX"
        }

        # Simula a requisição PATCH que o front-end faria
        response = self.client.patch(self.url, payload, format='json')
        
        # Valida se a API retornou Sucesso (200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Valida se o status mudou na tabela de Pedidos
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "CONFIRMADO")
        
        # Valida se a linha de histórico foi criada
        history_count = OrderStatusHistory.objects.filter(order=self.order).count()
        self.assertEqual(history_count, 1, "ERRO: O histórico de status não foi salvo no banco!")
        
        # Verifica se os dados do histórico estão corretos
        history_entry = OrderStatusHistory.objects.get(order=self.order)
        self.assertEqual(history_entry.old_status, "PENDENTE")
        self.assertEqual(history_entry.new_status, "CONFIRMADO")
        self.assertEqual(history_entry.observation, "Pagamento aprovado via PIX")

    def test_change_status_invalid_choice(self):
        """
        Garante que a API barra status que não existem.
        """
        payload = {"status": "STATUS_LOUCO"}
        response = self.client.patch(self.url, payload, format='json')
        
        # Deve retornar erro 400 
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)