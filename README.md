# Sistema ERP - Módulo de Gestão de Pedidos

API desenvolvida para gestão de pedidos de alta performance, com foco em integridade de dados, arquitetura limpa e controle de concorrência.

## Tecnologias

- **Python 3.11 + Django REST Framework**
- **MySQL 8** (Persistência de Dados)
- **Redis 7** (Cache & Idempotência)
- **Docker & Docker Compose** (Infraestrutura e Orquestração)
- **Pytest** (Testes Automatizados)

## Como Rodar (Ambiente Local)

### Pré-requisitos
- Docker e Docker Compose instalados na máquina.

### Passo a Passo

1. **Clone o repositório:**
   git clone git clone https://github.com/Paraoxx/desafio_erp.git
   cd desafio_erp

2. **Configure as variáveis de ambiente:**
Certifique-se de que o arquivo .env na raiz do projeto contenha as credenciais configuradas no docker-compose.yml.

3. **Suba a infraestrutura dos containers:**
O projeto utiliza um script de inicialização (scripts/init_db.sql) para configurar automaticamente as permissões do banco de dados:

docker compose up --build -d

4. **Aplique as migrações do banco de dados:**
docker compose run --rm api python manage.py migrate

A API estará disponível em: http://localhost:8000/api/v1/

5. **Banco de dados de teste**
Utilize o comando abaixo para criar um cliente e produtos, com estoque inicial:

docker compose run --rm api python manage.py seed_db

A API estará disponível em: http://localhost:8000/api/v1/

**O projeto conta com uma suíte de testes focada em cenários críticos de negócio. Para executar os testes automatizados, incluindo o teste avançado de concorrência e race conditions:**
docker compose run --rm api pytest -s

**Estrutura das pastas**
src/
├── core/             # Configurações centrais do projeto Django
├── orders/           # App principal do desafio (Pedidos, Clientes, Produtos)
│   ├── dtos/         # Data Transfer Objects para desacoplamento da camada de View
│   ├── services/     # Camada de regras de negócio e serviços
│   ├── tests/        # Testes unitários e de integração (concorrência)
│   ├── urls.py       # Definição das rotas v1
│   └── views.py      # Viewsets da API
├── scripts/          # Scripts sql de inicialização do Banco de Dados
├── docker-compose.yml
└── pytest.ini        # Configurações da suíte de testes

**Decisões Arquiteturais**
Pessimistic Locking (select_for_update): Escolhido para garantir a integridade do estoque em ambientes de alta concorrência, impedindo que dois pedidos processem o mesmo item simultaneamente.

Service Layer: Implementada para isolar a lógica de negócio das Views do Django, facilitando a manutenção e os testes automatizados.

Atomicidade: Uso de transaction.atomic para assegurar que falhas parciais em pedidos com múltiplos itens não corrompam os dados do banco.

Idempotência com Redis: Preparado para evitar o reprocessamento de requisições duplicadas.

CI/CD: Integração contínua via GitHub Actions para validar cada novo commit.