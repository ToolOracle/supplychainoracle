#!/usr/bin/env python3
"""
SupplyChainOracle — Supply Chain Intelligence & ESG Compliance MCP v1.0.0
Port 12501 | Part of ToolOracle Whitelabel MCP Platform

12 Tools:
  ── Supply Chain Risk ──
  1.  supplier_risk_score   — Supplier risk assessment (multi-factor)
  2.  concentration_risk    — Single-source / geographic concentration analysis
  3.  disruption_detector   — Disruption early warning (based on risk factors)
  4.  geopolitical_risk     — Country supply chain risk score

  ── ESG & Compliance ──
  5.  lksg_check            — Lieferkettensorgfaltspflichtengesetz (LkSG) compliance
  6.  scope3_estimate       — Scope 3 GHG emissions estimation
  7.  csrd_supply_check     — CSRD/ESRS supply chain disclosure requirements
  8.  cbam_check            — Carbon Border Adjustment Mechanism applicability

  ── Operations ──
  9.  lead_time_calc        — Lead time & buffer stock calculator
 10.  total_cost_ownership  — TCO analysis for procurement decisions
 11.  customs_hs_lookup     — HS/CN customs tariff code lookup
 12.  incoterms_guide       — Incoterms 2020 quick reference

NO external API keys needed — computation + regulatory knowledge.
"""
import os, sys, json, logging, math
from datetime import datetime, timezone

sys.path.insert(0, "/root/whitelabel")
from shared.utils.mcp_base import WhitelabelMCPServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SupplyChainOracle] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("/root/whitelabel/logs/supplychainoracle.log", mode="a")])
logger = logging.getLogger("SupplyChainOracle")

PRODUCT_NAME = "SupplyChainOracle"
VERSION = "1.0.0"
PORT_MCP = 12501
PORT_HEALTH = 12502

def ts(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

COUNTRY_RISK_DB = {
    "DE":{"risk":15,"stability":90,"logistics":95,"corruption":80,"name":"Germany"},
    "US":{"risk":20,"stability":85,"logistics":92,"corruption":73,"name":"United States"},
    "CN":{"risk":45,"stability":60,"logistics":75,"corruption":45,"name":"China"},
    "IN":{"risk":40,"stability":55,"logistics":55,"corruption":40,"name":"India"},
    "TW":{"risk":55,"stability":50,"logistics":80,"corruption":65,"name":"Taiwan"},
    "JP":{"risk":18,"stability":88,"logistics":93,"corruption":73,"name":"Japan"},
    "KR":{"risk":22,"stability":78,"logistics":88,"corruption":62,"name":"South Korea"},
    "TR":{"risk":50,"stability":40,"logistics":60,"corruption":40,"name":"Turkey"},
    "RU":{"risk":80,"stability":20,"logistics":45,"corruption":29,"name":"Russia"},
    "UA":{"risk":85,"stability":15,"logistics":30,"corruption":33,"name":"Ukraine"},
    "VN":{"risk":35,"stability":60,"logistics":55,"corruption":42,"name":"Vietnam"},
    "BD":{"risk":50,"stability":45,"logistics":40,"corruption":26,"name":"Bangladesh"},
    "MX":{"risk":40,"stability":55,"logistics":65,"corruption":31,"name":"Mexico"},
    "PL":{"risk":20,"stability":75,"logistics":80,"corruption":56,"name":"Poland"},
    "CZ":{"risk":18,"stability":80,"logistics":82,"corruption":56,"name":"Czech Republic"},
    "AT":{"risk":12,"stability":92,"logistics":90,"corruption":79,"name":"Austria"},
    "CH":{"risk":10,"stability":95,"logistics":92,"corruption":84,"name":"Switzerland"},
    "NL":{"risk":13,"stability":90,"logistics":96,"corruption":82,"name":"Netherlands"},
    "FR":{"risk":18,"stability":80,"logistics":88,"corruption":71,"name":"France"},
    "IT":{"risk":25,"stability":70,"logistics":82,"corruption":56,"name":"Italy"},
    "GB":{"risk":20,"stability":82,"logistics":90,"corruption":78,"name":"United Kingdom"},
    "BR":{"risk":45,"stability":50,"logistics":55,"corruption":38,"name":"Brazil"},
}

async def handle_supplier_risk(args: dict) -> dict:
    """Supplier risk assessment."""
    supplier = args.get("supplier_name", "")
    country = args.get("country", "").upper()
    single_source = args.get("single_source", False)
    revenue_dependency = float(args.get("revenue_dependency_pct", 0))
    years_relationship = float(args.get("years_relationship", 0))
    has_audit = args.get("recent_audit", False)
    has_backup = args.get("backup_supplier", False)
    iso_certified = args.get("iso_certified", False)

    scores = {}
    geo = COUNTRY_RISK_DB.get(country, {"risk": 50, "stability": 50})
    scores["geographic"] = geo["risk"]
    scores["concentration"] = 80 if single_source else (revenue_dependency * 0.8 if revenue_dependency > 30 else 20)
    scores["relationship"] = max(10, 60 - years_relationship * 5) if years_relationship > 0 else 60
    scores["audit"] = 20 if has_audit else 60
    scores["backup"] = 20 if has_backup else 70
    scores["quality"] = 15 if iso_certified else 50

    overall = sum(scores.values()) / len(scores)
    rating = "LOW" if overall < 30 else "MEDIUM" if overall < 50 else "HIGH" if overall < 70 else "CRITICAL"

    return {
        "supplier": supplier, "country": country,
        "overall_risk_score": round(overall, 1), "rating": rating,
        "dimension_scores": scores,
        "recommendations": (
            ["Backup-Lieferant identifizieren und qualifizieren"] if not has_backup else []) +
            (["Lieferantenaudit durchführen (spätestens alle 2 Jahre)"] if not has_audit else []) +
            (["ISO 9001/14001 Zertifizierung anfragen"] if not iso_certified else []) +
            (["Abhängigkeit reduzieren — max. 30% Einkaufsvolumen bei einem Lieferanten"] if revenue_dependency > 30 else []),
        "legal_basis": "LkSG §5 (Risikoanalyse), DORA Art. 28 (Third-Party Risk)",
        "retrieved_at": ts(),
    }

async def handle_concentration(args: dict) -> dict:
    """Concentration risk analysis."""
    suppliers = args.get("suppliers", [])
    if isinstance(suppliers, str):
        try: suppliers = json.loads(suppliers)
        except: return {"error": "Provide 'suppliers' as JSON array [{name, country, share_pct}]"}

    if not suppliers:
        return {"error": "Provide 'suppliers' array with name, country, share_pct"}

    total_share = sum(float(s.get("share_pct", 0)) for s in suppliers)
    hhi = sum((float(s.get("share_pct", 0))/max(total_share,1)*100)**2 for s in suppliers)

    countries = {}
    for s in suppliers:
        c = s.get("country", "??")
        countries[c] = countries.get(c, 0) + float(s.get("share_pct", 0))

    single_source = any(float(s.get("share_pct", 0)) > 50 for s in suppliers)
    top_supplier = max(suppliers, key=lambda x: float(x.get("share_pct", 0))) if suppliers else {}

    return {
        "supplier_count": len(suppliers),
        "hhi_index": round(hhi, 1),
        "hhi_rating": "LOW" if hhi < 1500 else "MODERATE" if hhi < 2500 else "HIGH",
        "hhi_explanation": "Herfindahl-Hirschman Index: <1500=diversified, 1500-2500=moderate, >2500=concentrated",
        "single_source_risk": single_source,
        "top_supplier": {"name": top_supplier.get("name",""), "share": top_supplier.get("share_pct",0)},
        "geographic_concentration": countries,
        "recommendations": (
            ["CRITICAL: Single-source dependency detected — qualify backup supplier immediately"] if single_source else []) +
            (["Diversify geographic sourcing — >50% from one country"] if any(v > 50 for v in countries.values()) else []),
        "legal_basis": "LkSG §5, DORA Art.28 (CTPP concentration), CSRD ESRS S2",
        "retrieved_at": ts(),
    }

async def handle_disruption(args: dict) -> dict:
    """Disruption early warning."""
    country = args.get("country", "").upper()
    category = args.get("category", "general")  # semiconductors, raw_materials, energy, logistics, food
    lead_time_days = int(args.get("current_lead_time_days", 0))
    normal_lead_time = int(args.get("normal_lead_time_days", 0))

    geo = COUNTRY_RISK_DB.get(country, {"risk": 50, "stability": 50, "name": country})

    risk_factors = []
    if geo["risk"] > 60:
        risk_factors.append({"factor": "High geopolitical risk", "severity": "HIGH"})
    if geo.get("stability", 50) < 40:
        risk_factors.append({"factor": "Political instability", "severity": "HIGH"})

    category_risks = {
        "semiconductors": [{"factor": "Taiwan Strait tension", "severity": "HIGH"}, {"factor": "CHIPS Act reshoring ongoing", "severity": "MEDIUM"}],
        "raw_materials": [{"factor": "Critical mineral dependency (China 60%+ of processing)", "severity": "HIGH"}],
        "energy": [{"factor": "Oil price volatility", "severity": "MEDIUM"}, {"factor": "LNG supply constraints", "severity": "MEDIUM"}],
        "logistics": [{"factor": "Red Sea / Suez disruptions", "severity": "HIGH"}, {"factor": "Container shortage cycles", "severity": "MEDIUM"}],
        "food": [{"factor": "Climate events impact harvests", "severity": "MEDIUM"}, {"factor": "Export restrictions possible", "severity": "MEDIUM"}],
    }
    risk_factors.extend(category_risks.get(category, []))

    lead_time_alert = None
    if lead_time_days > 0 and normal_lead_time > 0:
        ratio = lead_time_days / normal_lead_time
        if ratio > 2.0:
            lead_time_alert = {"status": "CRITICAL", "ratio": round(ratio, 1), "note": f"Lead time {ratio:.1f}x normal — supply disruption likely"}
        elif ratio > 1.5:
            lead_time_alert = {"status": "WARNING", "ratio": round(ratio, 1), "note": f"Lead time {ratio:.1f}x normal — monitor closely"}

    overall = min(100, geo["risk"] + len(risk_factors) * 10 + (20 if lead_time_alert else 0))

    return {
        "country": country, "country_name": geo.get("name", country), "category": category,
        "disruption_risk_score": overall,
        "risk_level": "LOW" if overall < 30 else "MEDIUM" if overall < 50 else "HIGH" if overall < 70 else "CRITICAL",
        "risk_factors": risk_factors,
        "lead_time_alert": lead_time_alert,
        "mitigation": [
            "Safety stock aufbauen (min. 2-4 Wochen Verbrauch)",
            "Alternative Lieferanten in anderem Geografie-Cluster qualifizieren",
            "Rahmenverträge mit Mengenflexibilität abschließen",
            "Nearshoring-Optionen evaluieren (EU/EFTA)",
        ],
        "retrieved_at": ts(),
    }

async def handle_geopolitical(args: dict) -> dict:
    """Country supply chain risk score."""
    country = args.get("country", "").upper()
    geo = COUNTRY_RISK_DB.get(country)
    if not geo:
        return {"error": f"Country '{country}' not in database. Available: {', '.join(sorted(COUNTRY_RISK_DB.keys()))}"}

    return {
        "country": country, "name": geo["name"],
        "overall_risk": geo["risk"],
        "political_stability": geo["stability"],
        "logistics_performance": geo["logistics"],
        "corruption_perception": geo["corruption"],
        "risk_level": "LOW" if geo["risk"] < 25 else "MEDIUM" if geo["risk"] < 45 else "HIGH" if geo["risk"] < 65 else "CRITICAL",
        "eu_trade_agreement": country in {"CH","NO","IS","LI","GB","JP","KR","CA","MX","VN","NZ","AU","SG"},
        "sanctions_risk": country in {"RU","BY","IR","KP","SY","VE","MM","CU"},
        "sources": "Transparency International CPI, World Bank LPI, Fund for Peace FSI (composite scores)",
        "retrieved_at": ts(),
    }

async def handle_lksg(args: dict) -> dict:
    """LkSG compliance check."""
    employee_count = int(args.get("employee_count", 0))
    has_risk_analysis = args.get("risk_analysis", False)
    has_complaints_mechanism = args.get("complaints_mechanism", False)
    has_policy_statement = args.get("policy_statement", False)
    has_remediation = args.get("remediation_measures", False)
    has_reporting = args.get("annual_reporting", False)

    applicable = employee_count >= 1000

    checks = [
        {"obligation": "Risikoanalyse (§5 LkSG)", "met": has_risk_analysis, "priority": "CRITICAL"},
        {"obligation": "Grundsatzerklärung (§6 Abs.2 LkSG)", "met": has_policy_statement, "priority": "HIGH"},
        {"obligation": "Präventionsmaßnahmen (§6 LkSG)", "met": has_remediation, "priority": "HIGH"},
        {"obligation": "Beschwerdeverfahren (§8 LkSG)", "met": has_complaints_mechanism, "priority": "CRITICAL"},
        {"obligation": "Abhilfemaßnahmen (§7 LkSG)", "met": has_remediation, "priority": "HIGH"},
        {"obligation": "Dokumentation & Berichterstattung (§10 LkSG)", "met": has_reporting, "priority": "HIGH"},
    ]

    met = [c for c in checks if c["met"]]
    missing = [c for c in checks if not c["met"]]
    score = len(met) / len(checks) * 100

    return {
        "applicable": applicable,
        "threshold": "≥1.000 Mitarbeiter (seit 01.01.2024, vorher ≥3.000)",
        "employee_count": employee_count,
        "compliance_score": round(score),
        "obligations_met": met, "obligations_missing": missing,
        "penalties": {
            "bussgeld": "Bis zu 2% des weltweiten Jahresumsatzes",
            "ausschluss": "Ausschluss von öffentlichen Aufträgen bis 3 Jahre",
            "authority": "BAFA (Bundesamt für Wirtschaft und Ausfuhrkontrolle)",
        },
        "csddd_note": "EU Corporate Sustainability Due Diligence Directive (CSDDD) ab 2027 — erweitert LkSG auf EU-Ebene",
        "legal_basis": "Lieferkettensorgfaltspflichtengesetz (LkSG), in Kraft seit 01.01.2023",
        "retrieved_at": ts(),
    }

async def handle_scope3(args: dict) -> dict:
    """Scope 3 emissions estimation."""
    category = args.get("category", "")
    spend_eur = float(args.get("spend_eur", 0))
    weight_kg = float(args.get("weight_kg", 0))
    distance_km = float(args.get("distance_km", 0))
    transport_mode = args.get("transport_mode", "truck")

    # Emission factors (kgCO2e per unit — simplified DEFRA/GHG Protocol)
    EF_SPEND = {"electronics": 0.4, "chemicals": 0.6, "metals": 0.8, "textiles": 0.5,
                "food": 0.7, "services": 0.1, "logistics": 0.3, "packaging": 0.4, "default": 0.3}
    EF_TRANSPORT = {"truck": 0.062, "ship": 0.008, "air": 0.602, "rail": 0.022, "van": 0.115}

    emissions = {}
    if spend_eur > 0:
        ef = EF_SPEND.get(category.lower(), EF_SPEND["default"])
        emissions["spend_based"] = {"kgCO2e": round(spend_eur * ef, 1), "method": "Spend-based (DEFRA)",
                                    "emission_factor": f"{ef} kgCO2e/EUR"}

    if weight_kg > 0 and distance_km > 0:
        ef_t = EF_TRANSPORT.get(transport_mode, 0.062)
        transport_emissions = weight_kg / 1000 * distance_km * ef_t
        emissions["transport"] = {"kgCO2e": round(transport_emissions, 1), "method": "Distance-based",
                                  "emission_factor": f"{ef_t} kgCO2e/tkm", "mode": transport_mode}

    total = sum(e.get("kgCO2e", 0) for e in emissions.values())

    return {
        "total_kgCO2e": round(total, 1), "total_tCO2e": round(total / 1000, 3),
        "emissions_breakdown": emissions,
        "ghg_protocol_categories": {
            "Cat 1": "Purchased goods and services",
            "Cat 4": "Upstream transportation",
            "Cat 9": "Downstream transportation",
        },
        "note": "Simplified estimation — for certified reporting use supplier-specific data (GHG Protocol Scope 3 Standard)",
        "legal_basis": "CSRD/ESRS E1, GHG Protocol Scope 3 Standard, CBAM Regulation (EU) 2023/956",
        "retrieved_at": ts(),
    }

async def handle_csrd_supply(args: dict) -> dict:
    """CSRD/ESRS supply chain disclosure requirements."""
    return {
        "applicable_standards": [
            {"standard": "ESRS S2", "topic": "Workers in the value chain",
             "disclosures": ["Due diligence process", "Identified impacts/risks", "Actions taken", "Metrics"]},
            {"standard": "ESRS E1", "topic": "Climate Change (Scope 3)",
             "disclosures": ["Scope 3 GHG emissions", "Transition plan", "Targets"]},
            {"standard": "ESRS E2", "topic": "Pollution (supply chain)",
             "disclosures": ["Pollution in value chain", "Substances of concern"]},
            {"standard": "ESRS E5", "topic": "Resource use & circular economy",
             "disclosures": ["Resource inflows/outflows", "Waste in value chain"]},
            {"standard": "ESRS G1", "topic": "Business conduct",
             "disclosures": ["Anti-corruption in supply chain", "Payment practices"]},
        ],
        "timeline": {
            "2024_reports": "Large public-interest entities (>500 employees)",
            "2025_reports": "Large companies meeting 2 of 3 criteria (>250 employees, >€50M revenue, >€25M assets)",
            "2026_reports": "Listed SMEs (opt-out until 2028)",
        },
        "double_materiality": "Must assess both impact on supply chain AND supply chain risks to company",
        "legal_basis": "Directive (EU) 2022/2464 (CSRD), ESRS (Delegated Act 2023/2772)",
        "retrieved_at": ts(),
    }

async def handle_cbam(args: dict) -> dict:
    """CBAM applicability check."""
    product = args.get("product_category", "").lower()
    origin_country = args.get("origin_country", "").upper()
    value_eur = float(args.get("import_value_eur", 0))

    cbam_products = {
        "iron_steel": True, "aluminium": True, "cement": True, "fertiliser": True,
        "electricity": True, "hydrogen": True,
    }

    eu_ets_countries = {"EU", "IS", "NO", "LI", "CH"}
    exempt = origin_country in eu_ets_countries

    applicable = product in cbam_products and not exempt

    return {
        "product": product, "origin": origin_country, "value_eur": value_eur,
        "cbam_applicable": applicable,
        "exempt": exempt,
        "exempt_reason": "Origin country participates in EU ETS or equivalent" if exempt else None,
        "covered_products": list(cbam_products.keys()),
        "timeline": {
            "transitional_phase": "01.10.2023 — 31.12.2025 (reporting only, no financial adjustment)",
            "definitive_phase": "01.01.2026 — CBAM certificates required (financial adjustment)",
        },
        "obligations": [
            "Register as authorized CBAM declarant",
            "Quarterly CBAM reports (transitional phase)",
            "Annual CBAM declaration (definitive phase)",
            "Purchase CBAM certificates for embedded emissions",
            "Verify embedded emissions with accredited verifier",
        ],
        "cost_estimate": f"~€50-100/tCO2e (based on EU ETS price)" if applicable else "N/A",
        "legal_basis": "Regulation (EU) 2023/956 (CBAM), Commission Implementing Regulation 2023/1773",
        "retrieved_at": ts(),
    }

async def handle_lead_time(args: dict) -> dict:
    """Lead time & buffer stock calculator."""
    avg_lead_time = float(args.get("avg_lead_time_days", 0))
    lead_time_std = float(args.get("lead_time_std_days", 0))
    avg_daily_demand = float(args.get("avg_daily_demand", 0))
    demand_std = float(args.get("demand_std_daily", 0))
    service_level = float(args.get("service_level_pct", 95))

    if avg_lead_time <= 0 or avg_daily_demand <= 0:
        return {"error": "Provide avg_lead_time_days and avg_daily_demand"}

    z_scores = {90: 1.28, 95: 1.65, 97: 1.88, 98: 2.05, 99: 2.33, 99.5: 2.58, 99.9: 3.09}
    z = z_scores.get(service_level, 1.65)

    safety_stock = z * math.sqrt(avg_lead_time * demand_std**2 + avg_daily_demand**2 * lead_time_std**2)
    reorder_point = avg_daily_demand * avg_lead_time + safety_stock

    return {
        "avg_lead_time_days": avg_lead_time,
        "avg_daily_demand": avg_daily_demand,
        "service_level_pct": service_level,
        "z_score": z,
        "safety_stock_units": round(safety_stock, 1),
        "safety_stock_days": round(safety_stock / max(avg_daily_demand, 0.01), 1),
        "reorder_point_units": round(reorder_point, 1),
        "pipeline_stock": round(avg_daily_demand * avg_lead_time, 1),
        "formula": "Safety Stock = Z × √(LT × σ_d² + d² × σ_LT²)",
        "retrieved_at": ts(),
    }

async def handle_tco(args: dict) -> dict:
    """Total Cost of Ownership analysis."""
    unit_price = float(args.get("unit_price", 0))
    quantity = int(args.get("quantity", 1))
    shipping_cost = float(args.get("shipping_cost", 0))
    customs_duty_pct = float(args.get("customs_duty_pct", 0))
    quality_reject_pct = float(args.get("quality_reject_rate_pct", 0))
    lead_time_days = int(args.get("lead_time_days", 0))
    holding_cost_pct = float(args.get("annual_holding_cost_pct", 25))
    inspection_cost = float(args.get("inspection_cost", 0))
    tooling_cost = float(args.get("tooling_cost", 0))

    purchase = unit_price * quantity
    shipping = shipping_cost
    customs = purchase * customs_duty_pct / 100
    quality = purchase * quality_reject_pct / 100
    holding = purchase * holding_cost_pct / 100 * (lead_time_days / 365)
    total = purchase + shipping + customs + quality + holding + inspection_cost + tooling_cost
    tco_per_unit = total / max(quantity, 1)

    return {
        "breakdown": {
            "purchase_price": round(purchase, 2),
            "shipping": round(shipping, 2),
            "customs_duty": round(customs, 2),
            "quality_cost": round(quality, 2),
            "holding_cost": round(holding, 2),
            "inspection": round(inspection_cost, 2),
            "tooling": round(tooling_cost, 2),
        },
        "total_cost": round(total, 2),
        "tco_per_unit": round(tco_per_unit, 2),
        "hidden_cost_pct": round((total - purchase) / max(purchase, 1) * 100, 1),
        "note": "Hidden costs often add 15-40% to purchase price — TCO reveals true procurement cost",
        "retrieved_at": ts(),
    }

async def handle_hs_lookup(args: dict) -> dict:
    """HS code lookup (common codes)."""
    search = args.get("search", "").lower()
    code = args.get("code", "")

    HS_DB = {
        "8471": {"desc": "Automatic data processing machines (computers)", "duty_eu": "0%"},
        "8517": {"desc": "Telephone sets, smartphones", "duty_eu": "0%"},
        "8542": {"desc": "Electronic integrated circuits (semiconductors)", "duty_eu": "0%"},
        "7208": {"desc": "Flat-rolled products of iron/steel, hot-rolled", "duty_eu": "0-3.7%"},
        "7606": {"desc": "Aluminium plates, sheets", "duty_eu": "7.5%"},
        "2523": {"desc": "Portland cement", "duty_eu": "1.7%"},
        "3105": {"desc": "Mineral or chemical fertilisers", "duty_eu": "6.5%"},
        "8703": {"desc": "Motor cars for transport of persons", "duty_eu": "6.5-22%"},
        "6110": {"desc": "Jerseys, pullovers, cardigans (knitted)", "duty_eu": "12%"},
        "0901": {"desc": "Coffee", "duty_eu": "0-9%"},
        "3004": {"desc": "Medicaments (packaged for retail)", "duty_eu": "0%"},
        "9018": {"desc": "Medical instruments and appliances", "duty_eu": "0%"},
    }

    results = []
    if code:
        for hs, info in HS_DB.items():
            if hs.startswith(code[:4]):
                results.append({"hs_code": hs, **info})
    if search:
        for hs, info in HS_DB.items():
            if search in info["desc"].lower():
                results.append({"hs_code": hs, **info})

    return {
        "query": code or search, "results": results,
        "note": "Subset — full CN (Combined Nomenclature) contains 10,000+ codes. Check TARIC for binding classification.",
        "official_source": "https://ec.europa.eu/taxation_customs/dds2/taric/ (EU TARIC)",
        "retrieved_at": ts(),
    }

async def handle_incoterms(args: dict) -> dict:
    """Incoterms 2020 guide."""
    term = args.get("term", "").upper()

    INCOTERMS = {
        "EXW": {"name": "Ex Works", "risk_transfer": "At seller's premises", "transport": "Any",
                "seller_obligations": "Make goods available at premises", "buyer_obligations": "All transport, insurance, customs",
                "best_for": "Minimal seller obligation"},
        "FCA": {"name": "Free Carrier", "risk_transfer": "When delivered to carrier at named place", "transport": "Any",
                "seller_obligations": "Export clearance, delivery to carrier", "buyer_obligations": "Main carriage, import clearance",
                "best_for": "Most versatile — recommended default"},
        "FOB": {"name": "Free On Board", "risk_transfer": "When loaded on vessel at port of shipment", "transport": "Sea only",
                "seller_obligations": "Export clearance, loading on vessel", "buyer_obligations": "Main carriage, insurance, import",
                "best_for": "Sea freight — seller loads"},
        "CIF": {"name": "Cost, Insurance and Freight", "risk_transfer": "When loaded on vessel (but seller pays to destination)", "transport": "Sea only",
                "seller_obligations": "Freight + insurance to destination port", "buyer_obligations": "Import clearance, onward transport",
                "best_for": "Sea freight — seller arranges shipping + insurance"},
        "DAP": {"name": "Delivered At Place", "risk_transfer": "At named destination (before unloading)", "transport": "Any",
                "seller_obligations": "All transport to destination", "buyer_obligations": "Import clearance, unloading",
                "best_for": "Door delivery without import duties"},
        "DDP": {"name": "Delivered Duty Paid", "risk_transfer": "At destination (seller handles everything)", "transport": "Any",
                "seller_obligations": "All transport + import clearance + duties", "buyer_obligations": "Unloading only",
                "best_for": "Maximum seller obligation — full service"},
        "CPT": {"name": "Carriage Paid To", "risk_transfer": "When delivered to carrier", "transport": "Any",
                "seller_obligations": "Freight to destination", "buyer_obligations": "Insurance, import clearance"},
        "CIP": {"name": "Carriage and Insurance Paid To", "risk_transfer": "When delivered to carrier", "transport": "Any",
                "seller_obligations": "Freight + insurance to destination", "buyer_obligations": "Import clearance"},
        "FAS": {"name": "Free Alongside Ship", "risk_transfer": "Alongside vessel at port", "transport": "Sea only",
                "seller_obligations": "Deliver alongside vessel", "buyer_obligations": "Loading + main carriage"},
        "CFR": {"name": "Cost and Freight", "risk_transfer": "When loaded on vessel", "transport": "Sea only",
                "seller_obligations": "Freight to destination port", "buyer_obligations": "Insurance, import"},
        "DPU": {"name": "Delivered at Place Unloaded", "risk_transfer": "After unloading at destination", "transport": "Any",
                "seller_obligations": "All transport + unloading", "buyer_obligations": "Import clearance"},
    }

    if term and term in INCOTERMS:
        return {"term": term, **INCOTERMS[term], "version": "Incoterms® 2020 (ICC)", "retrieved_at": ts()}

    return {
        "all_terms": {k: {"name": v["name"], "transport": v["transport"], "best_for": v["best_for"]}
                      for k, v in INCOTERMS.items()},
        "recommendation": "FCA (most versatile) or DDP (full service) for most B2B transactions",
        "version": "Incoterms® 2020 (ICC — International Chamber of Commerce)",
        "retrieved_at": ts(),
    }


def main():
    server = WhitelabelMCPServer(product_name=PRODUCT_NAME, product_slug="supplychainoracle",
                                 version=VERSION, port_mcp=PORT_MCP, port_health=PORT_HEALTH)

    server.register_tool("supplier_risk_score", "Multi-factor supplier risk assessment. Geographic, concentration, relationship, audit, quality dimensions. Returns risk score 0-100 with LkSG/DORA compliance context.",
        {"supplier_name":{"type":"string"},"country":{"type":"string","description":"2-letter country code"},"single_source":{"type":"boolean"},"revenue_dependency_pct":{"type":"number"},"years_relationship":{"type":"number"},"recent_audit":{"type":"boolean"},"backup_supplier":{"type":"boolean"},"iso_certified":{"type":"boolean"}}, handle_supplier_risk, credits=2)

    server.register_tool("concentration_risk", "Supply chain concentration analysis using HHI (Herfindahl-Hirschman Index). Detects single-source and geographic dependencies.",
        {"suppliers":{"type":"string","description":"JSON array [{name, country, share_pct}]"}}, handle_concentration, credits=2)

    server.register_tool("disruption_detector", "Supply chain disruption early warning. Geopolitical risk, category-specific risks, lead time anomaly detection.",
        {"country":{"type":"string"},"category":{"type":"string","description":"semiconductors|raw_materials|energy|logistics|food|general"},"current_lead_time_days":{"type":"integer"},"normal_lead_time_days":{"type":"integer"}}, handle_disruption, credits=2)

    server.register_tool("geopolitical_risk", "Country supply chain risk score. Political stability, logistics performance, corruption, sanctions, trade agreements.",
        {"country":{"type":"string","description":"2-letter ISO country code"}}, handle_geopolitical, credits=1)

    server.register_tool("lksg_check", "German Supply Chain Due Diligence Act (LkSG) compliance assessment. Checks all 6 core obligations.",
        {"employee_count":{"type":"integer"},"risk_analysis":{"type":"boolean"},"complaints_mechanism":{"type":"boolean"},"policy_statement":{"type":"boolean"},"remediation_measures":{"type":"boolean"},"annual_reporting":{"type":"boolean"}}, handle_lksg, credits=2)

    server.register_tool("scope3_estimate", "Scope 3 GHG emissions estimation. Spend-based and distance-based methods per GHG Protocol.",
        {"category":{"type":"string","description":"electronics|chemicals|metals|textiles|food|services|logistics"},"spend_eur":{"type":"number"},"weight_kg":{"type":"number"},"distance_km":{"type":"number"},"transport_mode":{"type":"string","description":"truck|ship|air|rail"}}, handle_scope3, credits=2)

    server.register_tool("csrd_supply_check", "CSRD/ESRS supply chain disclosure requirements. ESRS S2, E1, E2, E5, G1 standards with timeline.",
        {}, handle_csrd_supply, credits=1)

    server.register_tool("cbam_check", "EU Carbon Border Adjustment Mechanism (CBAM) applicability. Covered products, timeline, obligations, cost estimate.",
        {"product_category":{"type":"string","description":"iron_steel|aluminium|cement|fertiliser|electricity|hydrogen"},"origin_country":{"type":"string"},"import_value_eur":{"type":"number"}}, handle_cbam, credits=2)

    server.register_tool("lead_time_calc", "Lead time & safety stock calculator. Uses service level Z-score method for optimal buffer stock.",
        {"avg_lead_time_days":{"type":"number"},"lead_time_std_days":{"type":"number"},"avg_daily_demand":{"type":"number"},"demand_std_daily":{"type":"number"},"service_level_pct":{"type":"number","description":"90, 95, 97, 98, 99 (default: 95)"}}, handle_lead_time, credits=1)

    server.register_tool("total_cost_ownership", "Total Cost of Ownership analysis. Reveals hidden procurement costs: shipping, customs, quality, holding, tooling.",
        {"unit_price":{"type":"number"},"quantity":{"type":"integer"},"shipping_cost":{"type":"number"},"customs_duty_pct":{"type":"number"},"quality_reject_rate_pct":{"type":"number"},"lead_time_days":{"type":"integer"},"annual_holding_cost_pct":{"type":"number","description":"Default 25%"},"inspection_cost":{"type":"number"},"tooling_cost":{"type":"number"}}, handle_tco, credits=1)

    server.register_tool("customs_hs_lookup", "HS/CN customs tariff code lookup. Common codes with EU duty rates. Search by code or product description.",
        {"code":{"type":"string","description":"HS code (4-6 digits)"},"search":{"type":"string","description":"Product search term"}}, handle_hs_lookup, credits=1)

    server.register_tool("incoterms_guide", "Incoterms 2020 quick reference. Risk transfer, obligations, best-for recommendations for all 11 terms.",
        {"term":{"type":"string","description":"EXW, FCA, FOB, CIF, DAP, DDP etc. (empty for all)"}}, handle_incoterms, credits=1)

    logger.info(f"🚀 {PRODUCT_NAME} v{VERSION} starting on port {PORT_MCP}")
    server.run()

if __name__ == "__main__":
    main()
