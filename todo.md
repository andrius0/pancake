## Task List for Implementing Pancake Order System

Each microservice must be independently executable and containerized with its own Dockerfile. The architecture is designed for modular deployment and scalable orchestration.

### General Setup

- [x] Set up monorepo structure for all services.
- [x] Create `venv` files and common config patterns.
- [x] Define shared folder `shared/` to hold:
  - [x] `interface.py`: Shared Pydantic models.
  - [x] `logging_config.py`: Common logging configuration.
- [x] Ensure `shared/` is imported correctly across services.
- [x] Add a `tests/` directory under each service/worker and shared/ for unit tests.
- [x] Factor out all hardcoded config/secrets to .env and load with dotenv in all entrypoints.

---

### Temporal Server Setup

- [x] Install Temporal via Docker.
- [x] Configure ports and UI access.
- [ ] Verify Temporal CLI and Web UI are functional.

---

### Order Service

- [x] Build FastAPI server with `/orders` endpoint.
- [x] Validate payload and convert to `OrderDetails` model.
- [x] Connect to Temporal and start workflow.
- [x] Log all major interactions using `shared/logging_config.py`.
- [x] Create Dockerfile.
- [x] Generate `requirements.txt` with FastAPI, temporalio.
- [x] All configuration and secrets loaded from .env using dotenv.

---

### Analyze Order Worker

- [x] Define `analyze_order` activity.
- [x] Use LangChain + OpenAI to parse order text.
- [x] Output structured `Ingredients` model.
- [x] Log inputs and outputs using `shared/logging_config.py`.
- [x] Import models from `shared/interface.py`.
- [x] Create Dockerfile.
- [x] Create `requirements.txt` with langchain, openai, pydantic, temporalio.
- [x] Remove unnecessary imports and refactor for clarity.
- [x] All configuration and secrets loaded from .env using dotenv.

---

### Inventory Check Worker

- [x] Define `inventory_check` activity.
- [x] Use LangChain agent with GPT-4.1 to make decisions.
- [x] Create database access tools (SQLAlchemy).
- [x] Return structured `InventoryResponse`.
- [x] Access shared models from `shared/interface.py`.
- [x] Create Dockerfile.
- [x] Create `requirements.txt` with sqlalchemy, langchain, psycopg2.
- [x] All configuration and secrets loaded from .env using dotenv.
- [ ] (Optional) Investigate and fix async/sync issues with agent.invoke in inventory_check.py (should agent.invoke be awaited or run in a thread for true async compatibility?).

---

### Kitchen Worker

- [x] Define `execute_order` activity (implemented in `src/execute_order.py`).
- [x] Implement logic to deduct ingredients from inventory (see `db_tools_kitchen.py`).
- [x] Log all major actions and errors using `shared/logging_config.py`.
- [x] Create Dockerfile.
- [x] Create `requirements.txt` with SQLAlchemy, temporalio, pydantic.
- [x] All configuration and secrets loaded from .env using dotenv.
- [x] Add and improve logging for all DB and business logic (recently completed).
- [ ] Add/expand unit and integration tests for kitchen worker (if not already present).
- [ ] Review and document error handling and edge cases (e.g., insufficient inventory).

---

### Notify Worker

- [x] Define `notify` activity (see `src/notify.py`).
- [x] Implement notification logic and return confirmation.
- [x] Log all major actions and errors using `shared/logging_config.py`.
- [x] Create Dockerfile.
- [x] Create `requirements.txt` with temporalio, pydantic.
- [x] All configuration and secrets loaded from .env using dotenv.
- [ ] Add/expand unit and integration tests for notify worker (if not already present).

---

### Workflow Worker

- [x] Implement central orchestration logic using Temporal workflow.
- [x] Manage the lifecycle of a pancake order from creation through fulfillment.
- [x] Log all major workflow steps and errors.
- [x] Create Dockerfile.
- [x] Create `requirements.txt` with temporalio, pydantic.
- [x] All configuration and secrets loaded from .env using dotenv.
- [ ] Add/expand unit and integration tests for workflow worker (if not already present).

---

### Shared

- [x] Define and maintain shared Pydantic models and logging config.
- [x] Ensure all services import shared code correctly.
- [ ] Add/expand unit tests for shared code.

---

### Status Service

- [x] Implement service to subscribe to Redis channel for order status events.
- [x] Log all received messages for monitoring and debugging.
- [x] Create Dockerfile and requirements.txt.
- [x] All configuration and secrets loaded from .env using dotenv.

---

### Eventing & Shared Code

- [x] Implement Redis event publishing in order_service and subscribing in status_service.
- [x] Use `sync_shared.sh` to synchronize shared code across all services.

---

### General Setup (Ongoing)

- [ ] (Ongoing) Keep `todo.md` up to date as work progresses.
- [ ] (Ongoing) Add/expand documentation for deployment, environment setup, and local development.
- [ ] (Ongoing) Add/expand monitoring and alerting setup (including event log monitoring for status_service).