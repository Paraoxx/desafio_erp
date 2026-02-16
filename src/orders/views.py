from rest_framework import viewsets, status
from rest_framework.response import Response
from django.core.cache import cache
from .models import Customer, Product, Order
from .serializers import CustomerSerializer, ProductSerializer, OrderSerializer
from .services import CreateOrderService
from .dtos import CreateOrderDTO, OrderItemDTO

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        #captura a chave de idempotência do cabecalho da requisição
        idempotency_key = request.headers.get('Idempotency-Key')
        
        # Se a chave existir, verifica a resposta no Redis
        if idempotency_key:
            cache_key = f"idempotency_order_{idempotency_key}"
            cached_response = cache.get(cache_key)
            
            # Se achou no cache, retorna exatamente o pedido criado antes (Status 200)
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