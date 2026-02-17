# Sistema ERP - Módulo de Gestão de Pedidos

API REST desenvolvida para gestão de pedidos de alta performance, com foco em integridade de dados, arquitetura limpa e controle de concorrência.

## Tecnologias

**Backend: Python 3.11 + Django REST Framework 3.14**

**Banco de Dados: MySQL 8.0 (Persistência com ACID)**

**Cache & Resiliência: Redis 7.0 (Idempotência e Throttling)**

**DevOps: Docker & Docker Compose (Multi-stage Build)**

**Documentação: OpenAPI 3 / Swagger (drf-spectacular)**

**Testes: Pytest (Suíte de testes de integração e concorrência)**

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

5. **Seed de dados(opcional)**
docker compose run --rm api python manage.py seed_db

6. **Acesse a documentação Swagger**
http://localhost:8000/api/v1/docs/


7. **O projeto conta com um suíte de testes com focco em TDD (Test Driven Development) para cenários críticos de ERP:**

7.1. **Para todos os testes, use o comando:**
docker compose run --rm api pytest -s

7.2. **Para teste de race conditions, use o comando:**
docker compose run --rm api pytest orders/tests/test_concurrency.py

7.3. **Para teste de Idempotência, use o comando:**
docker compose run --rm api pytest orders/tests/test_idempotency.py

7.4. **Para teste de atomicidade, use o comando:**
docker compose run --rm api pytest orders/tests/test_atomicity.py

7.5. **Para cobertura de código:**
docker compose run --rm api pytest --cov=orders

8. **Estrutura das pastas**
src/
├── core/             # Configurações do Django e Swagger
├── orders/           # App principal (Negócio)
│   ├── dtos/         # Camada de transporte de dados
│   ├── services/     # O "Coração" do projeto (Regras de Negócio)
│   ├── tests/        # Testes de Integração e Stress
│   ├── signals.py    # Disparo de Eventos de Domínio
│   └── views.py      # Viewsets e Actions customizadas

9. **Decisões Arquiteturais**
**Consistência e Concorrência (Pessimistic Locking):**
No ERP, o erro de "venda sem estoque" é crítico. Para mitigar isso, utilizei o select_for_update() do Django (Pessimistic Locking). Essa minha escolha garante que, durante a transação de criação do pedido, a linha do produto no banco de dados seja travada, impedindo que requisições simultâneas causem race conditions e vendam o mesmo item duas vezes.

**Service Layer (Arquitetura em Camadas):**
Seguindo os principios de Clean Architecture, isolei a lógica de negócio das Views. Isso garante um:

**Desacoplamento**, A view lida apenas com HTTP (request/response).

**Testabilidade**, As regras de negócio podem ser testadas isoladamente sem subir o servidor.

**Single Responsibility (SOLID)**, Cada serviço tem uma única missão clara.

**Idempotência com Redis:**
Para garantir a resiliência em cenários de instabilidade de rede (retries do cliente), implementei uma camada de Idempotência. Através de uma Idempotency-Key enviada no header e armazenada no redis, o sistema evita o reprocessamento de pedidos duplicados, garantindo que o cliente não seja cobrado duas vezes.

**Integridade Atômica:**
Todas as operações de criação e atualização de pedidos são envolvidas em transaction.atomic. Isso assegura o principio ACID do banco de dados: ou o pedido é salvo com todos os seus itens e o estoque é baixado, ou nada acontece, o rollback. Não existe estado de "erro parcial".

**Soft Delete e Auditoria:**
Implementei via deleted_at para garantir que registros históricos não sejam perdidos fisicamente, mantendo a integridade referencial.

**Histórico de Status**: Cada mudança de estado do pedido gera uma entrada imutável na tabela de auditoria, registrando quem mudou, quando e por que.