# EMR — Facilitador de Separação

Painel web para acompanhamento em tempo real de robôs separadores de medicamentos e gestão das ordens de serviço (OS). O sistema foi construído para o **Software Challenge 3EMR** em parceria com **Apsen**, cobrindo o fluxo completo: atribuição de OS aos separadores, acompanhamento da operação, histórico, relatórios exportáveis (CSV / Excel / PDF) e auditoria.

> Stack: **FastAPI + SQLAlchemy + SQLite** no backend; **HTML + CSS + JavaScript puro (ES6)** com Chart.js e Flatpickr no frontend.

---

## Sumário

- [Principais funcionalidades](#principais-funcionalidades)
- [Arquitetura](#arquitetura)
- [Requisitos](#requisitos)
- [Instalação e execução](#instalação-e-execução)
- [Credenciais iniciais](#credenciais-iniciais)
- [Configuração (variáveis de ambiente)](#configuração-variáveis-de-ambiente)
- [Estrutura de pastas](#estrutura-de-pastas)
- [API REST](#api-rest)
- [Relatórios](#relatórios)
- [Migrações automáticas do SQLite](#migrações-automáticas-do-sqlite)
- [Segurança](#segurança)
- [Troubleshooting](#troubleshooting)

---

## Principais funcionalidades

### Operação em tempo real
- Cadastro de **separadores (robôs)** com código, nome, modelo, localização, especificações e capacidade por hora.
- Atribuição **automática ou manual** de OS aos separadores, com validação de conflito de código, reabertura de OS cancelada (continuação ou retrabalho completo) e bloqueio anti-duplicidade.
- Estados do separador: `offline`, `idle`, `running`, `paused`, `error`, `maintenance`, com transições controladas pelo `AssignmentService` / `RobotService`.
- **Pausar / retomar** a execução acumulando corretamente o tempo de pausa para descontar do tempo líquido de separação.
- **Cancelamento de OS** com motivo estruturado (código + descrição), preservando métricas parciais (unidades separadas, tempo médio por unidade, tempo total).

### Relatórios e histórico
- Histórico por separador com totais do período, gráfico de barras (Chart.js) e lista paginada.
- Relatório por OS filtrável por período, OS, cliente, separador (nome/código) e situação (concluída / cancelada).
- **Exportação individual** em CSV, Excel (XLSX) ou **PDF** (template Jinja2 + xhtml2pdf com logo Apsen, cabeçalho estilizado e paginação).
- **Exportação em lote**: seleção acumulativa ao alterar filtros e três formatos disponíveis:
  - **CSV**: tudo numa folha única.
  - **Excel**: com auto filtro e primeira linha congelada.
  - **PDF**: ZIP contendo um PDF por OS (nomes desambiguados automaticamente).
- Coluna *"Tempo Médio por Remédio"* só é preenchida se a linha do medicamento estiver concluída.

### Administração
- Aba **Logs** com auditoria completa (login, alterações de OS, criação/edição/exclusão de separadores, exportações, alterações em usuários).
- Gestão de **usuários** (criação, alteração de senha, toggle admin) apenas para administradores.
- **Clear logs** controlado com motivo obrigatório e registo auditado da própria limpeza.

### Autenticação e permissões
- Login baseado em **sessão** (cookie HttpOnly) via `starlette.SessionMiddleware`.
- Proteção **CSRF** via token em header `X-CSRF-Token` (endpoint `/api/csrf-token`).
- Conta comum e conta administrativa pré-provisionadas no arranque.
- Rate limiting em rotas sensíveis (`limit_sensitive`).

---

## Arquitetura

```
┌─────────────────────────────┐        HTTP/JSON        ┌──────────────────────────────┐
│  Frontend (HTML/JS/CSS)     │  ─────────────────────▶ │  FastAPI  (prefix /api)      │
│  static em /                │   ◀─── cookies de       │  routers: auth, robots,      │
│  Chart.js + Flatpickr       │       sessão + CSRF     │  service_orders, admin,      │
└─────────────────────────────┘                         │  notifications, csrf, health │
                                                        └──────────────┬───────────────┘
                                                                       │ SQLAlchemy ORM
                                                                       ▼
                                                        ┌──────────────────────────────┐
                                                        │  SQLite (backend/data/emr.db)│
                                                        │  migrações idempotentes em   │
                                                        │  bootstrap/sqlite_migrations │
                                                        └──────────────────────────────┘
```

Camadas do backend:

- **`api/routers/`** — endpoints finos; apenas orquestração e validação.
- **`services/`** — regras de negócio (atribuição, histórico, relatórios, auditoria, usuários).
- **`repositories/`** — acesso a dados (queries SQLAlchemy compostas reutilizadas entre serviços).
- **`models/entities.py`** — modelo ORM (`Robot`, `ServiceOrder`, `User`, `AuditLog`).
- **`schemas/`** — contratos Pydantic expostos na API.
- **`bootstrap/`** — *seed* de dados iniciais e migrações manuais do SQLite.
- **`middleware/security_headers.py`** — CSP, `X-Frame-Options`, `Referrer-Policy`, etc.

O frontend é servido como conteúdo **estático** pelo próprio FastAPI (montado em `/` via `StaticFiles`), então uma única porta atende tanto o app quanto a API.

---

## Requisitos

- **Python 3.11+** (desenvolvido em 3.13).
- **pip** recente.
- Navegador moderno (Chrome / Edge / Firefox).

Dependências Python listadas em `requirements.txt`:

```
fastapi, uvicorn[standard], sqlalchemy, pydantic, pydantic-settings,
python-multipart, passlib, openpyxl, jinja2, xhtml2pdf, reportlab,
pypdf, svglib
```

---

## Instalação e execução

### Windows (PowerShell)

```powershell
# 1) Clonar
git clone <url-do-repo> Software-Challenge-3EMR
cd Software-Challenge-3EMR

# 2) Ambiente virtual (opcional mas recomendado)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3) Dependências
pip install -r requirements.txt

# 4) Subir em modo dev (reload ativo, escuta em 127.0.0.1:8765)
python run_dev.py
```

### macOS / Linux

```bash
git clone <url-do-repo> Software-Challenge-3EMR
cd Software-Challenge-3EMR
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_dev.py
```

Depois acesse:

- Aplicação: <http://127.0.0.1:8765>
- Docs interativos (Swagger UI): <http://127.0.0.1:8765/docs>
- Docs alternativos (ReDoc): <http://127.0.0.1:8765/redoc>

Para alterar a porta, defina `EMR_PORT`:

```powershell
$env:EMR_PORT = "9000"; python run_dev.py
```

### Produção (uvicorn direto)

```bash
uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --workers 2
```

> Sempre sobreponha `EMR_SECRET_KEY`, `EMR_AUTH_DEFAULT_PASSWORD` e `EMR_ADMIN_PASSWORD` em produção.

---

## Credenciais iniciais

Na primeira subida o backend cria automaticamente (apenas se as contas não existirem):

| Usuário | Senha padrão | Papel              |
| ------- | ------------ | ------------------ |
| `teste` | `123456`     | Operador (padrão)  |
| `admin` | `admin123`   | Administrador      |

As três contas podem ser sobrescritas pelas variáveis descritas abaixo.

---

## Configuração (variáveis de ambiente)

Todas começam com o prefixo `EMR_` e podem ser definidas via arquivo `.env` na raiz (lido automaticamente pelo `pydantic-settings`) ou no ambiente do shell.

| Variável                      | Default                                                                 | Descrição                                           |
| ----------------------------- | ----------------------------------------------------------------------- | --------------------------------------------------- |
| `EMR_DATABASE_URL`            | `sqlite:///.../backend/data/emr.db`                                     | URL SQLAlchemy do banco.                            |
| `EMR_SECRET_KEY`              | `change-me-in-production-use-openssl-rand-hex-32`                       | Chave usada pelo `SessionMiddleware`.               |
| `EMR_CORS_ORIGINS`            | `http://127.0.0.1:8765,http://localhost:8765,...:8000`                  | Lista separada por vírgulas de origens permitidas.  |
| `EMR_ENVIRONMENT`             | `development`                                                           | Rótulo informativo.                                 |
| `EMR_AUTH_DEFAULT_USERNAME`   | `teste`                                                                 | Usuário comum de bootstrap.                         |
| `EMR_AUTH_DEFAULT_PASSWORD`   | `123456`                                                                | Senha do usuário comum.                             |
| `EMR_ADMIN_USERNAME`          | `admin`                                                                 | Nome do administrador.                              |
| `EMR_ADMIN_PASSWORD`          | `admin123`                                                              | Senha do administrador.                             |
| `EMR_PORT`                    | `8765`                                                                  | Porta usada por `run_dev.py`.                       |

Exemplo de `.env`:

```env
EMR_SECRET_KEY=troque-por-uma-chave-de-32-bytes
EMR_ADMIN_PASSWORD=uma-senha-forte
EMR_AUTH_DEFAULT_PASSWORD=outra-senha-forte
EMR_CORS_ORIGINS=http://meu-dominio.com
```

---

## Estrutura de pastas

```
Software-Challenge-3EMR-main/
├── run_dev.py                  # Inicia o uvicorn em modo dev (reload).
├── requirements.txt
├── .gitignore
├── backend/
│   ├── data/                   # Banco SQLite (emr.db) - ignorado em git em produção.
│   └── app/
│       ├── main.py             # create_app(), lifespan (seed + migrações).
│       ├── config.py           # Settings (pydantic-settings).
│       ├── database.py         # engine + SessionLocal.
│       ├── api/
│       │   ├── router.py       # Agrupa todos os sub-routers em /api.
│       │   ├── dependencies.py # Autenticação, CSRF, rate limit.
│       │   └── routers/        # auth, robots, service_orders, admin, ...
│       ├── services/           # Regras de negócio.
│       ├── repositories/       # Camada de acesso a dados.
│       ├── models/             # ORM + enums.
│       ├── schemas/            # Pydantic I/O.
│       ├── bootstrap/          # seed.py e sqlite_migrations.py.
│       ├── middleware/         # Cabeçalhos de segurança.
│       ├── security/           # Password hash, CSRF token.
│       ├── templates/reports/  # os_report.html (Jinja2 do PDF).
│       └── img/                # Logos usados pelo relatório PDF.
└── frontend/
    ├── index.html              # Aplicação principal (Operação, Histórico, Relatório, Logs).
    ├── login.html              # Tela de login.
    ├── app.js                  # SPA (fetch + DOM puro).
    ├── login.js
    ├── styles.css
    └── vendor/                 # chart.js e flatpickr (bundled).
```

---

## API REST

Base: `/api`. Todas as rotas exceto `/health`, `/login` e `/csrf-token` exigem sessão válida. Rotas que alteram estado exigem também o header `X-CSRF-Token`.

### Autenticação
- `POST /api/login` — inicia sessão (`username`, `password`).
- `POST /api/logout` — encerra sessão.
- `GET  /api/me` — dados do usuário autenticado.
- `PATCH /api/me/password` — troca de senha.
- `GET  /api/csrf-token` — emite token CSRF para as próximas mutações.

### Separadores (robôs)
- `GET    /api/robots` — lista resumida.
- `POST   /api/robots` — cria novo.
- `GET    /api/robots/{id}` / `PATCH /api/robots/{id}` / `DELETE /api/robots/{id}`.
- `POST   /api/robots/{id}/assign-order` — atribui OS.
- `POST   /api/robots/{id}/concluir-os` — conclui a OS atual.
- `POST   /api/robots/{id}/cancelar-os` — cancela a OS atual (com motivo).
- `POST   /api/robots/{id}/pausar` / `POST /api/robots/{id}/retomar`.
- `PATCH  /api/robots/{id}/units` — atualiza unidades separadas (progresso).
- `GET    /api/robots/{id}/historico` — agregados por período.
- `GET    /api/robots/cancellation-reasons` — opções de motivo de cancelamento.

### Ordens de serviço
- `GET    /api/service-orders` — OS atribuíveis (pendentes).
- `GET    /api/service-orders/completed` — relatório paginado (concluídas + canceladas) com vários filtros.
- `POST   /api/service-orders/manual` — cria OS manual e atribui diretamente.
- `DELETE /api/service-orders/{id}` — remove OS não iniciada.
- `GET    /api/service-orders/{id}/export?format=csv|xlsx|pdf` — exporta uma OS.
- `POST   /api/service-orders/export-batch` — exporta várias OS (CSV/XLSX) ou **ZIP com PDFs** (`format=pdf`).

### Administração
- `GET    /api/audit-logs` — lista paginada.
- `DELETE /api/audit-logs` — limpa com motivo auditado.
- `GET    /api/users` / `POST /api/users` / `PATCH /api/users/{id}` — gestão de contas (admin).

### Outros
- `GET /api/health` — status simples para health checks.
- `GET /api/notifications/os-completions` — feed de OS recém-concluídas (polling da UI).

---

## Relatórios

| Formato | Export individual                     | Export em lote                          |
| ------- | -------------------------------------- | ---------------------------------------- |
| CSV     | Separador `;`, BOM UTF-8.              | Uma folha única, uma linha por medicamento. |
| Excel   | Primeira linha em negrito + auto filtro. | Auto filtro + `freeze_panes` em A2.      |
| PDF     | Template Jinja2 com cabeçalho azul + logo Apsen (SVG rasterizado via `svglib`). Paginação estampada em todas as folhas pelo `reportlab`. | **ZIP** contendo um PDF por OS; nomes desambiguados automaticamente. |

Regras específicas implementadas em `order_report_export_service.py`:

- *"Tempo Médio por Remédio"* só é preenchido para linhas de medicamento com `situacao_coleta == "concluida"`.
- Colunas de erro (`erro_descricao`, `erro_codigo`) só aparecem quando a OS está cancelada.
- Em exports de lote a coluna *Situação* é sempre incluída para permitir o filtro do Excel.

---

## Migrações automáticas do SQLite

O arquivo `backend/app/bootstrap/sqlite_migrations.py` aplica, no arranque, mudanças **idempotentes** que cobrem cenários onde `Base.metadata.create_all` não é suficiente:

- Adição de colunas que foram introduzidas depois (ex.: `pause_count`, `total_pause_seconds`, `cancel_error_*`, `cancelled_wall_seconds`).
- `_cleanup_orphan_robot_refs` — zera `completed_by_robot_id` / `cancelled_by_robot_id` de OS que referenciam um separador inexistente ou um ID reciclado (comparando `completed_at/cancelled_at` com `robots.created_at`).
- `_ensure_robots_autoincrement` — recria a tabela `robots` com `INTEGER PRIMARY KEY AUTOINCREMENT` preservando os dados, evitando o reuso de IDs após exclusões.

Não é necessário rodar manualmente — as migrações executam dentro do `lifespan` do FastAPI.

---

## Segurança

- **Sessão**: cookie de sessão `SameSite=Lax`, `HttpOnly`, com TTL de 14 dias.
- **CSRF**: token gerado por sessão, validado em toda rota mutante (`require_csrf_token`).
- **Senhas**: hash com `passlib` (PBKDF2 SHA-256 por padrão).
- **Rate limit**: `limit_sensitive` protege login, criação de OS, criação de usuários.
- **Headers**: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: same-origin`, `Content-Security-Policy` restritiva (ver `middleware/security_headers.py`).
- **CORS**: lista explícita via `EMR_CORS_ORIGINS`.
- **Auditoria**: toda ação relevante é gravada em `audit_logs` com usuário e metadados.

Em produção lembre-se de:

1. Definir `EMR_SECRET_KEY` com um valor aleatório de 32 bytes (`openssl rand -hex 32`).
2. Trocar `EMR_AUTH_DEFAULT_PASSWORD` e `EMR_ADMIN_PASSWORD`.
3. Restringir `EMR_CORS_ORIGINS` ao domínio oficial.
4. Servir atrás de HTTPS e ativar `https_only=True` no `SessionMiddleware` (ajuste em `main.py`).

---

## Troubleshooting

| Sintoma                                                                 | Ação                                                                                             |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `ModuleNotFoundError: app`                                              | Use `python run_dev.py` (ele ajusta o `sys.path`) ou passe `--app-dir backend` ao uvicorn.        |
| PDF vem em branco / sem logo                                            | Verifique se `svglib` e `reportlab` estão instalados e se `backend/app/img/logo_apsen.svg` existe.|
| 403 em rotas de escrita                                                 | Chame `GET /api/csrf-token` e envie o header `X-CSRF-Token`; verifique se o cookie de sessão está presente. |
| `OperationalError: database is locked`                                  | Feche clientes externos do SQLite ou reinicie o servidor; em produção considere Postgres via `EMR_DATABASE_URL`. |
| Export em lote retorna 400 "Nenhuma ordem encerrada"                    | Os filtros não casam com nenhuma OS concluída/cancelada — revise datas, situação e seleção.      |
| Separador "reciclado" mostrando OS antigas                              | As migrações idempotentes já corrigem. Basta reiniciar o backend uma vez após a atualização.     |

---

## Licença

Projeto desenvolvido para o **Software Challenge 3EMR (Apsen)**. Uso conforme o regulamento da competição.
