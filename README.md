# SupplyChainOracle MCP Server v1.0.0

**Supply Chain Intelligence & ESG Compliance MCP Server — 12 tools for supplier risk scoring, LkSG compliance, Scope 3 emissions (GHG Protocol), CSRD/ESRS, CBAM, disruption detection, Incoterms 2020, TCO analysis.**

Port 12501 | Part of [ToolOracle](https://tooloracle.io) & [FeedOracle](https://feedoracle.io) Infrastructure

## Quick Connect

```bash
# Claude Desktop / Claude Code
claude mcp add supplychainoracle https://tooloracle.io/supplychain/mcp

# Or use directly
curl -X POST https://tooloracle.io/supplychain/mcp/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## 12 Tools

| `supplier_risk_score` | Tool 1 |
| `concentration_risk` | Tool 2 |
| `disruption_detector` | Tool 3 |
| `geopolitical_risk` | Tool 4 |
| `lksg_check` | Tool 5 |
| `scope3_estimate` | Tool 6 |
| `csrd_supply_check` | Tool 7 |
| `cbam_check` | Tool 8 |
| `lead_time_calc` | Tool 9 |
| `total_cost_ownership` | Tool 10 |
| `customs_hs_lookup` | Tool 11 |
| `incoterms_guide` | Tool 12 |

## Endpoints

| Endpoint | URL |
|----------|-----|
| MCP (StreamableHTTP) | `https://tooloracle.io/supplychain/mcp/` |
| MCP (FeedOracle) | `https://feedoracle.io/supplychain/mcp/` |
| Health | `https://tooloracle.io/supplychain/health` |

## Architecture

- **Transport**: StreamableHTTP + SSE (MCP Protocol 2025-03-26)
- **Auth**: x402 micropayments (USDC on Base) + Stripe subscriptions
- **Signing**: ECDSA ES256K — every response cryptographically signed
- **Platform**: Whitelabel MCP Platform v1.0

## Part of the ToolOracle Ecosystem

ToolOracle operates 81+ MCP servers with 824+ tools across:
- **Compliance & Regulation** — DORA, MiCA, NIS2, AMLR, GDPR, EU AI Act
- **Finance & Tax** — CFOCoPilot, TaxOracle, ISO20022Oracle
- **Legal** — LawOracle, LegalTechOracle, ContractOracle
- **Healthcare** — HealthGuard
- **Supply Chain** — SupplyChainOracle
- **Cybersecurity** — CyberShield, DORAOracle, TLPTOracle
- **HR** — HROracle
- **Blockchain** — 13 chains (ETH, BTC, Solana, Arbitrum, etc.)
- **Business Intelligence** — SEO, Leads, Reviews, E-Commerce

## License

Proprietary — © 2026 ToolOracle / FeedOracle. All rights reserved.
Contact: enterprise@feedoracle.io
