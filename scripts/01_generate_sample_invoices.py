import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

raw_path = Path("data/raw")
raw_path.mkdir(parents=True, exist_ok=True)

months = ["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]

states = ["SP", "RJ", "MG", "PR", "RS", "BA", "PE", "GO", "SC", "ES"]
categories = ["Eletrônicos", "Serviços", "Peças", "Equipamentos", "Suprimentos"]
cfops = ["5102", "6102", "5405", "6404", "5933", "6933"]
csts = ["00", "20", "40", "41", "60"]

for month in months:
    rows = np.random.randint(420, 680)

    invoices = pd.DataFrame({
        "invoice_id": [f"NF-{month}-{i+1:05d}" for i in range(rows)],
        "issue_date": pd.date_range(start=f"{month}-01", periods=rows, freq="h"),
        "customer_state": np.random.choice(
            states,
            rows,
            p=[0.34, 0.13, 0.12, 0.09, 0.08, 0.07, 0.05, 0.05, 0.05, 0.02]
        ),
        "operation_type": np.random.choice(["Venda", "Devolução"], rows, p=[0.94, 0.06]),
        "cfop": np.random.choice(cfops, rows, p=[0.35, 0.24, 0.16, 0.10, 0.09, 0.06]),
        "cst": np.random.choice(csts, rows, p=[0.44, 0.18, 0.14, 0.10, 0.14]),
        "product_category": np.random.choice(
            categories,
            rows,
            p=[0.27, 0.21, 0.20, 0.18, 0.14]
        ),
        "gross_value": np.random.normal(1800, 650, rows).round(2),
        "discount_value": np.random.normal(80, 35, rows).round(2),
        "freight_value": np.random.normal(120, 50, rows).round(2)
    })

    invoices["gross_value"] = invoices["gross_value"].clip(lower=100)
    invoices["discount_value"] = invoices["discount_value"].clip(lower=0)
    invoices["freight_value"] = invoices["freight_value"].clip(lower=0)

    invoices["net_value"] = (
        invoices["gross_value"] - invoices["discount_value"] + invoices["freight_value"]
    ).round(2)

    invoices["icms_rate"] = np.where(invoices["customer_state"] == "SP", 0.18, 0.12)
    invoices["pis_rate"] = 0.0165
    invoices["cofins_rate"] = 0.076

    exempt_cst = invoices["cst"].isin(["40", "41", "60"])

    invoices["tax_base"] = np.where(exempt_cst, 0, invoices["net_value"]).round(2)
    invoices["icms_value"] = (invoices["tax_base"] * invoices["icms_rate"]).round(2)
    invoices["pis_value"] = (invoices["tax_base"] * invoices["pis_rate"]).round(2)
    invoices["cofins_value"] = (invoices["tax_base"] * invoices["cofins_rate"]).round(2)

    invoices["total_tax_value"] = (
        invoices["icms_value"] + invoices["pis_value"] + invoices["cofins_value"]
    ).round(2)

    invoices["estimated_tax_burden"] = np.where(
        invoices["net_value"] > 0,
        invoices["total_tax_value"] / invoices["net_value"] * 100,
        0
    ).round(2)

    invoices.loc[invoices.sample(frac=0.01, random_state=10).index, "cfop"] = np.nan
    invoices.loc[invoices.sample(frac=0.01, random_state=20).index, "cst"] = np.nan
    invoices.loc[invoices.sample(frac=0.005, random_state=30).index, "gross_value"] = -100

    file_name = f"invoices_{month}.xlsx"
    invoices.to_excel(raw_path / file_name, index=False)

print("Arquivos mensais de notas fiscais simuladas gerados com sucesso.")