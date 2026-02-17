from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.cache import cache
from .models import Customer, Product, Order
from .serializers import CustomerSerializer, ProductSerializer, OrderSerializer
from .services import CreateOrderService, UpdateOrderStatusService
from .dtos import CreateOrderDTO, OrderItemDTO

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @action(detail=True, methods=['patch'], url_path='stock')
    def update_stock(self, request, pk=None):
        product = self.get_object()
        new_stock = request.data.get('stock_quantity')
        
        if new_stock is None:
            return Response({'error': 'O campo stock_quantity é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            product.stock_quantity = int(new_stock)
            product.save()
            return Response({'status': 'Estoque atualizado', 'stock_quantity': product.stock_quantity}, status=status.HTTP_200_OK)
        except ValueError:
            return Response({'error': 'Quantidade inválida.'}, status=status.HTTP_400_BAD_REQUEST)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        # captura a chave de idempotencia do cabecalho da requisicao
        idempotency_key = request.headers.get('Idempotency-Key')
        
        # Se a chave existir, verifica a resposta no redis
        if idempotency_key:
            cache_key = f"idempotency_order_{idempotency_key}"
            cached_response = cache.get(cache_key)
            
            # Retorna exatamente o pedido criado antes (Status 200)
            if cached_response:
                return Response(cached_response, status=status.HTTP_200_OK)

        try:
            customer_id = request.data.get('customer')
            items_data = request.data.get('items', [])
            
            item_dtos = [
                OrderItemDTO(product_id=item['product'], quantity=item['quantity'])
                for item in items_data
            ]
            
            dto = CreateOrderDTO(customer_id=customer_id, items=item_dtos)
            
            service = CreateOrderService() 
            order = service.create_order(dto)
            
            serializer = self.get_serializer(order)
            response_data = serializer.data
            
            # Pedido criado 
            if idempotency_key:
                cache.set(cache_key, response_data, timeout=86400) 
                
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Erro interno no servidor'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'], url_path='status')
    def change_status(self, request, pk=None):
        """
        Endpoint dedicado para alterar status do pedido e gravar histórico.
        Rota: PATCH /api/v1/orders/{id}/status/
        """
        new_status = request.data.get('status')
        observation = request.data.get('observation', '')
        
        if not new_status:
            return Response({'error': 'O campo status é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # Pega o usuário logado para registrar na auditoria
            user = request.user if request.user.is_authenticated else None
            
            service = UpdateOrderStatusService()
            order = service.update_status(
                order_id=pk,
                new_status=new_status,
                user=user,
                observation=observation
            )
            
            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Order.DoesNotExist:
            return Response({'error': 'Pedido não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Erro interno no servidor'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def destroy(self, request, *args, **kwargs):
        """
        No ERP, 'deletar' um pedido significa Cancelá-lo.
        """
        try:
            order = self.get_object()
            user = request.user if request.user.is_authenticated else None
            
            service = UpdateOrderStatusService()
            service.update_status(
                order_id=order.id,
                new_status='CANCELADO',
                user=user,
                observation='Cancelado via chamada DELETE na API'
            )
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)