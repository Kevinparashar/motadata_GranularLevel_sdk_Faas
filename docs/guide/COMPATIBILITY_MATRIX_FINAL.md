# COMPATIBILITY_MATRIX.md
## Motadata Python AI SDK

This matrix defines **what is supported, validated, and recommended** for running and developing the SDK across environments.
It is intended for **platform teams, DevOps, QA, and engineering leadership**.

---

## 1) Support definitions (mandatory)

- **Supported**: validated in CI/release process (recommended for production)
- **Expected**: commonly compatible but not yet CI-validated for every release
- **Not validated**: not tested; may work but is not supported
- **Planned**: roadmap item; not production-ready

---

## 2) Python runtime compatibility

| Python version | Status | Notes |
|---|---|---|
| 3.8.x | ✅ Supported (Primary) | Matches current tooling baseline |
| 3.9.x | ⚠️ Expected | Validate via CI matrix for production |
| 3.10.x | ⚠️ Expected | Validate via CI matrix for production |
| 3.11.x | ⚠️ Expected | Common dev runtime |
| 3.12.x | ❌ Not validated | Do not use for production until CI adds it |

---

## 3) Operating system compatibility

| OS | Status | Notes |
|---|---|---|
| Ubuntu 20.04+ | ✅ Supported | Recommended baseline |
| RHEL/CentOS 8+ | ✅ Supported | Enterprise baseline |
| Debian 11+ | ⚠️ Expected | Validate in CI if used |
| macOS | ⚠️ Dev only | Supported for local development |
| Windows | ⚠️ Dev only | Use WSL2 recommended |

---

## 4) Database and cache dependencies

| Capability | Technology | Status | Notes |
|---|---|---|---|
| Relational store | PostgreSQL 14+ | ✅ Supported | Required for persistence |
| Vector store | pgvector | ✅ Supported | Required for vector operations |
| Cache | Redis 6+ | ✅ Supported | Optional depending on configuration |
| In-memory cache | Built-in | ✅ Supported | Dev/local use; not distributed |

---

## 5) Messaging and eventing

| System | Status | Notes |
|---|---|---|
| NATS | ⚠️ Planned / placeholder | Not production-ready until CI validates |
| Kafka | ❌ Not supported | Out of scope unless roadmap adds |

---

## 6) Observability

| Tool/Standard | Status | Notes |
|---|---|---|
| OpenTelemetry | ⚠️ Planned / placeholder | Enable when instrumentation is complete |
| Prometheus | External | Deploy separately; not bundled |
| Grafana | External | Deploy separately; not bundled |
| Structured logging | ✅ Supported | Use SDK logging conventions |

---

## 7) Deployment targets

| Target | Status | Notes |
|---|---|---|
| Docker | ✅ Supported | Recommended for services |
| Kubernetes | ✅ Supported | Recommended for multi-service deployments |
| AWS Lambda | ⚠️ Partial | Validate per service; not universal |
| VM/Bare metal | ⚠️ Expected | Ensure dependencies installed |

---

## 8) LLM provider compatibility

| Provider | Status | Notes |
|---|---|---|
| OpenAI | ✅ Supported | Through gateway configuration |
| Azure OpenAI | ✅ Supported | Through gateway configuration |
| Anthropic | ⚠️ Planned | Add once validated |
| Local models | ⚠️ Planned | Add once validated |

---

## 9) Organization rollout guidance (recommended)

For enterprise adoption:
- Standardize production on **Linux + Python 3.8.x**
- Run services using **Docker/Kubernetes**
- Ensure Postgres + Redis are provisioned via platform tooling
- Expand CI matrix to validate 3.9–3.11 if required by org standards

---

**End of file**
