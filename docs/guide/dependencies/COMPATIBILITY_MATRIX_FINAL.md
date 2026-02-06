# MOTADATA - COMPATIBILITY MATRIX

**Compatibility matrix defining what is supported, validated, and recommended for running and developing the SDK across environments.**

---

## 📖 How to Read This Matrix

### Status Icons

| Icon | Meaning | Production Use |
|------|---------|----------------|
| ✅ **Supported** | Fully validated in CI/release, recommended | ✅ Yes - Recommended |
| ⚠️ **Expected** | Commonly compatible, not CI-validated | ⚠️ Use with caution |
| ❌ **Not Validated** | Not tested, may work but unsupported | ❌ No - Risky |
| 🔜 **Planned** | Roadmap item, not production-ready | ❌ No - Not ready |

### How to Use This Document

1. **Check Python Version** - Ensure you're using a supported Python version
2. **Verify OS Compatibility** - Confirm your OS is supported or expected
3. **Review Dependencies** - Check required infrastructure (PostgreSQL, Dragonfly)
4. **Plan for EOL** - Note upcoming end-of-life dates for version planning

### Quick Decision Guide

**For Production:**
- ✅ Use only "Supported" (✅) versions
- ✅ Use "Expected" (⚠️) only after validation in your environment

**For Development:**
- ✅ "Supported" and "Expected" versions are fine
- ⚠️ "Not Validated" may work but lacks official support

**For Planning:**
- 📅 Check "Version Lifecycle" section for EOL dates
- 🔜 Review "Planned" features for roadmap alignment

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
| Cache | Dragonfly 6+ | ✅ Supported | Optional depending on configuration |
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
- Ensure Postgres + Dragonfly are provisioned via platform tooling
- Expand CI matrix to validate 3.9–3.11 if required by org standards

---

## 10) Version Lifecycle & EOL Dates

### Python Runtime Lifecycle

| Version | Release Date | End of Support (EOL) | Status | Recommendation |
|---------|--------------|---------------------|--------|----------------|
| **3.8** | Oct 2019 | Oct 2024 (expired) | ⚠️ **EOL Reached** | Upgrade to 3.9+ recommended |
| **3.9** | Oct 2020 | Oct 2025 | ✅ **Active** | Recommended for new projects |
| **3.10** | Oct 2021 | Oct 2026 | ✅ **Active** | Recommended for new projects |
| **3.11** | Oct 2022 | Oct 2027 | ✅ **Active** | Recommended for new projects |
| **3.12** | Oct 2023 | Oct 2028 | ⚠️ **Not Validated** | Validate before production use |

**Note:** Python 3.8 has reached EOL (October 2024) but is still supported by the SDK for legacy compatibility. Plan migration to Python 3.9+ for continued Python security updates.

### PostgreSQL Lifecycle

| Version | Release Date | End of Support (EOL) | Status | Recommendation |
|---------|--------------|---------------------|--------|----------------|
| **12** | Oct 2019 | Nov 2024 (expired) | ⚠️ **EOL Reached** | Upgrade to 14+ recommended |
| **13** | Sep 2020 | Nov 2025 | ✅ **Active** | Supported |
| **14** | Sep 2021 | Nov 2026 | ✅ **Active** | Recommended |
| **15** | Oct 2022 | Nov 2027 | ✅ **Active** | Recommended |
| **16** | Sep 2023 | Nov 2028 | ✅ **Active** | Latest recommended |

### Dragonfly Lifecycle

| Version | Status | Recommendation |
|---------|--------|----------------|
| **6.x** | ✅ **Active** | Recommended |
| **5.x** | ⚠️ **Legacy** | Upgrade to 6.x recommended |

### SDK Version Support Policy

**Current SDK Version:** 0.1.0

**Support Policy:**
- **Major versions (x.0.0):** Supported for 12 months after next major release
- **Minor versions (0.x.0):** Supported for 6 months after next minor release
- **Patch versions (0.0.x):** Supported until next patch or minor release

**Deprecation Process:**
1. **3 months before EOL:** Deprecation notice in release notes
2. **1 month before EOL:** Warning logs in affected code
3. **EOL date:** Feature removed or made unsupported

### Deprecation Notices

**Current Deprecations:**
- **Python 3.8 Support** - Will be removed in SDK v0.3.0 (Q3 2026)
  - **Action:** Migrate to Python 3.9+
  - **Timeline:** 6 months notice
  
- **PostgreSQL 12 Support** - Will be removed in SDK v0.2.0 (Q2 2026)
  - **Action:** Upgrade to PostgreSQL 14+
  - **Timeline:** 3 months notice

**Planned Support Additions:**
- **Python 3.12** - Full validation planned for SDK v0.2.0 (Q2 2026)
- **Anthropic Claude 3** - Full support planned for SDK v0.2.0 (Q2 2026)
- **NATS Integration** - Production-ready in SDK v0.2.0 (Q2 2026)

### Migration Planning

**If you're on deprecated versions:**

1. **Check EOL dates** in the lifecycle tables above
2. **Plan upgrade path** at least 2 months before EOL
3. **Test in staging** environment before production upgrade
4. **Monitor SDK release notes** for migration guides

**Upgrade Priority:**

| Priority | Recommendation |
|----------|----------------|
| 🔴 **High** | Versions past EOL (Python 3.8, PostgreSQL 12) |
| 🟡 **Medium** | Versions EOL within 6 months |
| 🟢 **Low** | Versions supported > 12 months |

---

**Last Updated:** 2026-02-02
**Next Review:** 2026-05-02

**End of file**
