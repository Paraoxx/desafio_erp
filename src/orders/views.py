from rest_framework import viewsets, status
from rest_framework.response import Response
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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': 'Erro interno no servidor'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)