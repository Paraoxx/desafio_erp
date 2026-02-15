Este documento detalha as decisões arquiteturais tomadas para garantir que a API do ERP seja escalável, testável e tolerante a falhas em cenários de alta concorrência.

## 1. Padrões Adotados (Design Patterns)

### Layered Architecture 
Para evitar o alto acoplamento, comum no padrão MVC tradicional do Django e respeitar o **Single Responsibility Principle (SRP)** do SOLID, o projeto foi estruturado em camadas lógicas:
- **Views (Controllers):** Responsáveis estritamente por receber requisições HTTP, delegar a lógica e retornar as respostas adequadas.
- **Services:** Camada que concentra TODA a regra de negócio como validações complexas, cálculos e orquestração de chamadas. As Views não possuem regras de negócio.
- **Repositories:** Abstraem o acesso a dados (ORM do Django). Isso centraliza as consultas ao banco, facilitando a manutenção e a criação de testes unitários, permitindo a injeção de dependências e uso de mocks.
- **DTOs (Data Transfer Objects):** Objetos simples (estruturas de dados) utilizados para transferir informações de forma tipada e segura entre as camadas (ex: da View para o Service), desacoplando a lógica de negócio dos *Serializers* do framework.

## 2. Soluções para Requisitos Críticos

### Controle de Concorrência (Race Conditions)
**Problema:** Em um cenário de alto volume (ex: Black Friday), dois ou mais usuários podem tentar comprar a última unidade de um produto no exato mesmo milissegundo, gerando estoque negativo.
**Solução:** Implementação de **Pessimistic Locking** utilizando `select_for_update()` atrelado a uma transação atômica (`transaction.atomic`). Isso garante que, no momento em que a primeira requisição lê o estoque, a linha daquele produto no banco de dados seja "travada". Qualquer outra requisição concorrente precisará aguardar a conclusão da transação atual, garantindo a integridade absoluta do estoque.

### Prevenção de Deadlocks
**Problema:** Transações concorrentes tentando bloquear múltiplos itens em ordens diferentes podem causar travamento mútuo no banco de dados (*Deadlock*).
**Solução:** Antes de aplicar o bloqueio no banco, os itens do pedido são sempre **ordenados pelo ID (ou SKU) do produto**. Isso garante que todas as transações concorrentes tentem adquirir os *locks* do banco de dados exatamente na mesma ordem estrutural, eliminando matematicamente o risco de *deadlocks* circulares.

### Idempotência
**Problema:** Retentativas de rede (o cliente achou que falhou e clicou em "comprar" duas vezes) podem acabar criando pedidos duplicados de forma acidental e cobrando o cliente duas vezes.
**Solução:** Utilização do **Redis** para controle de idempotência. A API espera um *header* único (`Idempotency-Key`). Antes de processar o pedido, o sistema verifica no Redis se essa chave já foi processada recentemente. Caso positivo, a API simplesmente retorna o resultado do pedido anterior, sem reexecutar a transação no banco de dados.

## 3. Qualidade e Testabilidade
A separação de conceitos através do `OrderService` permitiu a criação de um teste automatizado utilizando a biblioteca `threading` do Python em conjunto com o `TransactionTestCase`. Este teste simula múltiplos acessos simultâneos batendo na API no mesmo instante, provando de forma empírica que as regras de negócio e os locks do banco de dados funcionam conforme o planejado.