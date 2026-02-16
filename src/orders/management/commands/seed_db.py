from django.core.management.base import BaseCommand
from orders.models import Customer, Product

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados iniciais para teste'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populando banco de dados...')

        # Clientes
        customer, created = Customer.objects.update_or_create(
            cpf_cnpj="12345678901",
            defaults={
                "name": "Cliente Teste Pleno",
                "email": "cliente@teste.com",
                "phone": "11988887777"
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Cliente {customer.name} criado.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Dados do cliente atualizados para: {customer.name}'))

        # Lista de Produtos para o seed
        products_data = [
            {"sku": "IPHONE15", "name": "iPhone 15 Pro", "price": 7000.00, "stock_quantity": 10},
            {"sku": "MACBOOK-M3", "name": "MacBook Air M3", "price": 12000.00, "stock_quantity": 5},
            {"sku": "AIRPODS-PRO", "name": "AirPods Pro", "price": 2000.00, "stock_quantity": 2},
        ]

        for p_data in products_data:
            product, created = Product.objects.get_or_create(
                sku=p_data["sku"],
                defaults={
                    "name": p_data["name"],
                    "price": p_data["price"],
                    "stock_quantity": p_data["stock_quantity"]
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Produto {product.name} criado com {product.stock_quantity} unidades.'))
            else:
                # Atualiza estoque se existir para facilitar re-testes manuais
                product.stock_quantity = p_data["stock_quantity"]
                product.price = p_data["price"]
                product.save()
                self.stdout.write(f'Estoque e preço do produto {product.name} resetados.')

        self.stdout.write(self.style.SUCCESS('Banco de dados pronto para uso!'))