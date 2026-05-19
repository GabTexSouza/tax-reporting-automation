import logging
from pathlib import Path

import pandas as pd


RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")
TABLES_PATH = Path("outputs/tables")
REPORTS_PATH = Path("outputs/reports")
LOG_PATH = Path("logs")

PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
TABLES_PATH.mkdir(parents=True, exist_ok=True)
REPORTS_PATH.mkdir(parents=True, exist_ok=True)
LOG_PATH.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH / "tax_pipeline.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def load_files():
    files = sorted(RAW_PATH.glob("invoices_*.xlsx"))

    if not files:
        raise FileNotFoundError("Nenhum arquivo de notas encontrado em data/raw.")

    frames = []

    for file in files:
        df = pd.read_excel(file)
        df["source_file"] = file.name
        frames.append(df)
        logging.info(f"Arquivo carregado: {file.name} | Linhas: {len(df)}")

    return pd.concat(frames, ignore_index=True)


def prepare_data(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    df["issue_date"] = pd.to_datetime(df["issue_date"])
    df["month"] = df["issue_date"].dt.to_period("M").astype(str)

    numeric_cols = [
        "gross_value",
        "discount_value",
        "freight_value",
        "net_value",
        "tax_base",
        "icms_rate",
        "pis_rate",
        "cofins_rate",
        "icms_value",
        "pis_value",
        "cofins_value",
        "total_tax_value",
        "estimated_tax_burden"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["calculated_net_value"] = (
        df["gross_value"] - df["discount_value"] + df["freight_value"]
    ).round(2)

    df["calculated_total_tax"] = (
        df["icms_value"] + df["pis_value"] + df["cofins_value"]
    ).round(2)

    df["tax_burden_check"] = (
        df["calculated_total_tax"] / df["calculated_net_value"] * 100
    ).round(2)

    return df


def find_inconsistencies(df):
    checks = []

    checks.append(df[df["cfop"].isna()].assign(inconsistency_type="CFOP ausente"))
    checks.append(df[df["cst"].isna()].assign(inconsistency_type="CST ausente"))
    checks.append(df[df["gross_value"] <= 0].assign(inconsistency_type="Valor bruto inválido"))
    checks.append(df[df["tax_base"] > df["net_value"]].assign(inconsistency_type="Base maior que valor líquido"))
    checks.append(df[df["customer_state"].isna()].assign(inconsistency_type="UF ausente"))

    inconsistencies = pd.concat(checks, ignore_index=True)

    if inconsistencies.empty:
        return pd.DataFrame(columns=list(df.columns) + ["inconsistency_type"])

    return inconsistencies


def create_summary_tables(df, inconsistencies):
    monthly_summary = (
        df
        .groupby("month")
        .agg(
            invoices=("invoice_id", "count"),
            gross_revenue=("gross_value", "sum"),
            discounts=("discount_value", "sum"),
            freight=("freight_value", "sum"),
            net_revenue=("calculated_net_value", "sum"),
            tax_base=("tax_base", "sum"),
            icms=("icms_value", "sum"),
            pis=("pis_value", "sum"),
            cofins=("cofins_value", "sum"),
            total_tax=("calculated_total_tax", "sum")
        )
        .reset_index()
    )

    monthly_summary["estimated_tax_burden"] = (
        monthly_summary["total_tax"] / monthly_summary["net_revenue"] * 100
    )

    monthly_summary = monthly_summary.round(2)

    tax_by_state = (
        df
        .groupby("customer_state")
        .agg(
            invoices=("invoice_id", "count"),
            net_revenue=("calculated_net_value", "sum"),
            total_tax=("calculated_total_tax", "sum")
        )
        .reset_index()
    )

    tax_by_state["estimated_tax_burden"] = (
        tax_by_state["total_tax"] / tax_by_state["net_revenue"] * 100
    )

    tax_by_state = tax_by_state.round(2)

    tax_by_cfop = (
        df
        .groupby("cfop", dropna=False)
        .agg(
            invoices=("invoice_id", "count"),
            net_revenue=("calculated_net_value", "sum"),
            total_tax=("calculated_total_tax", "sum")
        )
        .reset_index()
        .round(2)
    )

    inconsistency_summary = (
        inconsistencies
        .groupby("inconsistency_type")
        .agg(invoices=("invoice_id", "count"))
        .reset_index()
        .sort_values("invoices", ascending=False)
    )

    return monthly_summary, tax_by_state, tax_by_cfop, inconsistency_summary


def save_outputs(df, inconsistencies, monthly_summary, tax_by_state, tax_by_cfop, inconsistency_summary):
    df.to_csv(PROCESSED_PATH / "fiscal_consolidated.csv", index=False)

    inconsistencies.to_csv(TABLES_PATH / "inconsistency_report.csv", index=False)
    monthly_summary.to_csv(TABLES_PATH / "monthly_tax_summary.csv", index=False)
    tax_by_state.to_csv(TABLES_PATH / "tax_by_state.csv", index=False)
    tax_by_cfop.to_csv(TABLES_PATH / "tax_by_cfop.csv", index=False)
    inconsistency_summary.to_csv(TABLES_PATH / "inconsistency_summary.csv", index=False)

    total_invoices = len(df)
    total_net_revenue = df["calculated_net_value"].sum()
    total_tax = df["calculated_total_tax"].sum()
    tax_burden = total_tax / total_net_revenue * 100
    total_inconsistencies = len(inconsistencies)
    inconsistency_rate = total_inconsistencies / total_invoices * 100

    report = f"""
Relatório Fiscal Mensal - Base Consolidada

Arquivos processados: {df["source_file"].nunique()}
Total de notas fiscais: {total_invoices}
Faturamento líquido: {total_net_revenue:,.2f}
Total estimado de tributos: {total_tax:,.2f}
Carga tributária estimada: {tax_burden:.2f}%
Notas com inconsistência: {total_inconsistencies}
Percentual de inconsistências: {inconsistency_rate:.2f}%

Arquivos gerados:
- data/processed/fiscal_consolidated.csv
- outputs/tables/monthly_tax_summary.csv
- outputs/tables/tax_by_state.csv
- outputs/tables/tax_by_cfop.csv
- outputs/tables/inconsistency_report.csv
- outputs/reports/fiscal_report.txt
- logs/tax_pipeline.log
"""

    with open(REPORTS_PATH / "fiscal_report.txt", "w", encoding="utf-8") as file:
        file.write(report.strip())


def main():
    logging.info("Início da execução do pipeline fiscal")

    df = load_files()
    df = prepare_data(df)
    inconsistencies = find_inconsistencies(df)

    monthly_summary, tax_by_state, tax_by_cfop, inconsistency_summary = create_summary_tables(
        df,
        inconsistencies
    )

    save_outputs(
        df,
        inconsistencies,
        monthly_summary,
        tax_by_state,
        tax_by_cfop,
        inconsistency_summary
    )

    logging.info("Pipeline fiscal executado com sucesso")
    print("Pipeline fiscal executado com sucesso.")


if __name__ == "__main__":
    main()