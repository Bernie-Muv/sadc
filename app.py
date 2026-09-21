"""
SADC Regional Corridor Compliance & Traceability Engine
--------------------------------------------------------
Sandbox demo for CCBA Group Sustainability.

THESIS: This tool occupies the layer the incumbent domestic collector-ledger does
NOT cover -- the legal and financial auditability of recycled plastic moving ACROSS
SADC borders, and the proof that economic inclusion (women / youth / SMME) travels
with the material across that border.

Single-file app. Runs out-of-the-box:  streamlit run app.py
"""

import io
import datetime as dt

import pandas as pd
import streamlit as st
from fpdf import FPDF  # fpdf2

# --------------------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------------------
st.set_page_config(
    page_title="SADC Corridor Compliance & Traceability Engine",
    layout="wide",
    page_icon="♻️",
)

# ILLUSTRATIVE placeholder FX rates -> update to LIVE rates before any real use.
FX_TO_ZAR = {
    "BWP": 1.32,    # 1 Botswana Pula  ~ R1.32
    "MWK": 0.0105,  # 1 Malawi Kwacha  ~ R0.0105
    "ZAR": 1.0,
}
FX_CAPTION = "FX (illustrative): 1 BWP = R1.32 · 1 MWK = R0.0105 · update to live rates before real use"

VARIANCE_THRESHOLD = 0.05  # 5% mass-balance variance flags a shipment

# --------------------------------------------------------------------------------------
# DATA
# --------------------------------------------------------------------------------------
SHIPMENTS_CSV = """Bale_ID,Origin,Destination,Date_Dispatched,Dispatched_kg,Received_kg,Transport_Cost_ZAR,Material_Type,Contamination_Level,Status
BW-1042,Botswana,South Africa,2026-09-15,24500,24480,18500,PET (sorted),Low,Cleared
BW-1043,Botswana,South Africa,2026-09-16,24000,23950,18500,PET (sorted),Low,Cleared
MW-8091,Malawi,Zambia,2026-09-18,22000,18000,24000,Mixed PP/PET,High,Flagged - Variance
NM-3011,Namibia,South Africa,2026-09-20,25000,Pending,19000,HDPE (sorted),Low,In Transit
"""

FIRST_MILE_CSV = """Log_ID,Bale_ID,Buy_Back_Centre,Collector_Demographic,Weight_kg,Payout_Local,Local_Currency
FM-991,BW-1042,Gaborone Women's Co-op,Women-Owned SMME,520,750,BWP
FM-992,BW-1042,Naledi Youth Recyclers,Youth Enterprise,310,450,BWP
FM-993,BW-1042,Independent Pickers (Cash),Informal Sector,120,175,BWP
FM-994,MW-8091,Lilongwe Youth Hub,Youth Enterprise,1000,450000,MWK
FM-995,MW-8091,Lake Shore Women,Women-Owned SMME,2000,900000,MWK
"""


@st.cache_data
def load_data():
    ship = pd.read_csv(io.StringIO(SHIPMENTS_CSV))
    fm = pd.read_csv(io.StringIO(FIRST_MILE_CSV))

    # Safe numeric coercion. "Pending" -> NaN so it is excluded from sums/variance.
    ship["Received_kg_num"] = pd.to_numeric(ship["Received_kg"], errors="coerce")
    ship["Dispatched_kg"] = pd.to_numeric(ship["Dispatched_kg"], errors="coerce")
    ship["Transport_Cost_ZAR"] = pd.to_numeric(ship["Transport_Cost_ZAR"], errors="coerce")
    ship["Corridor"] = ship["Origin"] + " \u2192 " + ship["Destination"]

    # Variance is COMPUTED, not read from the CSV label (deliberate: this is the intelligence).
    ship["Variance_kg"] = ship["Dispatched_kg"] - ship["Received_kg_num"]
    ship["Variance_pct"] = ship["Variance_kg"] / ship["Dispatched_kg"]
    ship["Flagged"] = ship["Variance_pct"] > VARIANCE_THRESHOLD  # NaN (pending) -> False

    # First-mile payouts converted to a single reporting currency (ZAR).
    fm["Payout_Local"] = pd.to_numeric(fm["Payout_Local"], errors="coerce")
    fm["Payout_ZAR"] = fm.apply(
        lambda r: r["Payout_Local"] * FX_TO_ZAR.get(r["Local_Currency"], float("nan")),
        axis=1,
    )
    return ship, fm


ship, fm = load_data()

# --------------------------------------------------------------------------------------
# HELPERS
# --------------------------------------------------------------------------------------
def rand(x):
    """Format a number as ZAR."""
    return f"R{x:,.0f}"


def classify_basel(material: str, contamination: str):
    """
    Basel plastic-waste classification.
    Clean, sorted single-polymer PET/HDPE/PE/PP with low contamination is presumed
    NON-hazardous under entry B3011 -> simplified path.
    Mixed / high-contamination streams are presumed hazardous -> full Prior Informed
    Consent (PIC) control procedure.
    """
    sorted_single = any(p in material.upper() for p in ["PET", "HDPE", "PE ", "PP "]) \
        and "MIXED" not in material.upper()
    if contamination.strip().lower() == "low" and sorted_single:
        return "B3011", "Presumed non-hazardous (sorted, low contamination) \u2013 simplified path, PIC not required."
    return "PIC", "Presumed hazardous (mixed / contaminated) \u2013 full Prior Informed Consent control procedure required."


def compliance_docs(origin: str, destination: str, basel_class: str):
    """Return the corridor- and classification-specific document checklist."""
    docs = []

    # ---- EXPORT SIDE (origin country) ----
    if origin == "Botswana":
        docs.append(("EXPORT \u2013 Botswana",
                     "Transboundary Movement of Waste Permit (Dept. of Waste Management & "
                     "Pollution Control). Requires: service agreement with receiving disposer, "
                     "liability insurance, motivational letter, receiving-facility certification, "
                     "Material Safety Data Sheet. ~15 working-day turnaround."))
    else:
        docs.append((f"EXPORT \u2013 {origin}",
                     f"Origin-country transboundary export authorisation from the {origin} "
                     "environmental authority (notification + consent before dispatch)."))

    # ---- IMPORT SIDE (destination country) ----
    if destination == "South Africa":
        docs.append(("IMPORT \u2013 South Africa (Track 1: Customs)",
                     "ITAC Import Permit, Form IE 461 (commercial import). "
                     "Plastic/municipal waste under tariff heading 38.25."))
        docs.append(("IMPORT \u2013 South Africa (Track 2: Environmental)",
                     "NEM: Waste Act transboundary process \u2013 movement document submitted "
                     "\u22657 days before the shipment reaches the port; Consent presented at the "
                     "port by the transporter; Safe Disposal Certificate due within 30 days of recycling."))
    elif destination == "Zambia":
        docs.append(("IMPORT \u2013 Zambia (ZEMA \u2013 conditional gate)",
                     "ZEMA approval granted ONLY IF the waste is destined for reuse/recycling/"
                     "recovery AND the receiving facility has the capacity to handle it. "
                     "Treated as an approval gate, not an automatic stamp."))
    else:
        docs.append((f"IMPORT \u2013 {destination}",
                     f"Destination-country environmental import approval from the {destination} authority."))

    # ---- BASEL PIC (only if hazardous) ----
    if basel_class == "PIC":
        docs.append(("BASEL \u2013 Prior Informed Consent",
                     "Full Basel PIC notification: exporting + importing (and transit) states "
                     "must give written consent before movement."))
    else:
        docs.append(("BASEL \u2013 B3011 (simplified)",
                     "Bale qualifies as presumed non-hazardous (B3011). Full PIC NOT required \u2013 "
                     "simplified documentation only. (The engine avoids unnecessary paperwork.)"))
    return docs


def _ascii(text: str) -> str:
    """FPDF core fonts are latin-1 only; swap the unicode glyphs we use for ASCII."""
    return (str(text)
            .replace("\u2192", "->")   # arrow
            .replace("\u2013", "-")     # en dash
            .replace("\u2014", "-")     # em dash
            .replace("\u2265", ">=")    # >=
            .replace("\u2019", "'"))    # curly apostrophe


def build_pdf(row, fm_bale, basel_class, basel_note, docs):
    """Generate the mock compliance pack into an in-memory buffer."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 10, "SADC CROSS-BORDER COMPLIANCE PACK", ln=True)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(150, 30, 30)
    pdf.cell(0, 6, "SIMULATED DEMO DOCUMENT - not a legal instrument", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Consignment", ln=True)
    pdf.set_font("Helvetica", "", 10)
    recv = "Pending" if pd.isna(row["Received_kg_num"]) else f"{row['Received_kg_num']:,.0f} kg"
    lines = [
        f"Bale ID:            {row['Bale_ID']}",
        f"Corridor:           {row['Corridor']}",
        f"Dispatch date:      {row['Date_Dispatched']}",
        f"Dispatched:         {row['Dispatched_kg']:,.0f} kg",
        f"Received:           {recv}",
        f"Transport cost:     R{row['Transport_Cost_ZAR']:,.0f}",
        f"Material:           {row['Material_Type']}  (contamination: {row['Contamination_Level']})",
    ]
    for ln in lines:
        pdf.cell(0, 6, _ascii(ln), ln=True)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, f"Basel classification: {basel_class}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(190, 6, _ascii(basel_note))
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Required documents", ln=True)
    pdf.set_font("Helvetica", "", 9)
    for title, body in docs:
        pdf.set_font("Helvetica", "B", 9)
        pdf.multi_cell(190, 5, _ascii(f"- {title}"))
        pdf.set_font("Helvetica", "", 9)
        pdf.multi_cell(190, 5, _ascii(f"  {body}"))
    pdf.ln(2)

    # First-mile social summary (ZAR)
    if not fm_bale.empty:
        total_zar = fm_bale["Payout_ZAR"].sum()
        by_dem = fm_bale.groupby("Collector_Demographic")["Payout_ZAR"].sum()
        women = by_dem.get("Women-Owned SMME", 0.0)
        youth = by_dem.get("Youth Enterprise", 0.0)
        wp = (women / total_zar * 100) if total_zar else 0
        yp = (youth / total_zar * 100) if total_zar else 0
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Cross-border social provenance", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(
            0, 6,
            _ascii(
                f"Sourced via {len(fm_bale)} first-mile enterprise(s); "
                f"R{total_zar:,.0f} community injection; "
                f"{wp:.0f}% women-owned SMME, {yp:.0f}% youth enterprise."
            ),
        )

    out = pdf.output()  # fpdf2 returns bytearray
    return bytes(out)


# --------------------------------------------------------------------------------------
# HEADER + REGIONAL KPIs
# --------------------------------------------------------------------------------------
st.title("SADC Regional Corridor Compliance & Traceability Engine")
st.markdown(
    "Making the **cross-border** movement of recycled plastic legally and financially "
    "auditable \u2014 permit by permit, on both sides of every border \u2014 and proving that "
    "economic inclusion of women, youth and SMMEs travels with the material across that border."
)
st.divider()

total_dispatched = ship["Dispatched_kg"].sum()
total_received = ship["Received_kg_num"].sum(skipna=True)
variance_completed = ship.loc[ship["Received_kg_num"].notna(), "Variance_kg"].sum()
total_injection_zar = fm["Payout_ZAR"].sum()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Tonnage Dispatched", f"{total_dispatched/1000:,.2f} t")
k2.metric("Total Tonnage Received", f"{total_received/1000:,.2f} t")
k3.metric(
    "Transit Variance (completed)",
    f"{variance_completed/1000:,.2f} t",
    delta=f"-{variance_completed:,.0f} kg lost",
    delta_color="inverse",
)
k4.metric("Direct Community Injection", rand(total_injection_zar))
k4.caption(FX_CAPTION)

# --------------------------------------------------------------------------------------
# SHIPMENTS TABLE (computed flag + conditional styling)
# --------------------------------------------------------------------------------------
st.subheader("Live Cross-Border Shipments")
st.caption(f"Anomaly flag is computed in-engine: mass-balance variance > {VARIANCE_THRESHOLD:.0%} on completed shipments.")

view = ship[[
    "Bale_ID", "Corridor", "Date_Dispatched", "Dispatched_kg", "Received_kg",
    "Variance_kg", "Variance_pct", "Material_Type", "Contamination_Level", "Status", "Flagged",
]].copy()


def _highlight(r):
    color = "background-color: #FFD98A" if r["Flagged"] else ""
    return [color] * len(r)


styled = (
    view.style
    .apply(_highlight, axis=1)
    .format({"Dispatched_kg": "{:,.0f}", "Variance_kg": "{:,.0f}", "Variance_pct": "{:.1%}"}, na_rep="\u2013")
)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.divider()

# --------------------------------------------------------------------------------------
# DRILL-DOWN
# --------------------------------------------------------------------------------------
st.subheader("Bale Drill-Down")
bale_id = st.selectbox("Select a Bale ID to inspect", ship["Bale_ID"].tolist())
row = ship.loc[ship["Bale_ID"] == bale_id].iloc[0]
fm_bale = fm.loc[fm["Bale_ID"] == bale_id].copy()

colA, colB = st.columns(2)

# ---- SECTION A: CROSS-BORDER SOCIAL PROVENANCE ----
with colA:
    st.markdown("### A · Cross-Border Social Provenance")
    if fm_bale.empty:
        st.info("No first-mile provenance recorded for this bale yet.")
    else:
        total_zar = fm_bale["Payout_ZAR"].sum()
        a1, a2 = st.columns(2)
        a1.metric("Buy-back centres", f"{fm_bale['Buy_Back_Centre'].nunique()}")
        a2.metric("Community injection (this bale)", rand(total_zar))
        st.caption(FX_CAPTION)

        by_dem = fm_bale.groupby("Collector_Demographic")["Payout_ZAR"].sum()
        st.markdown("**Injection by demographic (ZAR)**")
        st.bar_chart(by_dem, horizontal="#E4002B")

        st.dataframe(
            fm_bale[["Buy_Back_Centre", "Collector_Demographic", "Weight_kg", "Payout_ZAR"]]
            .rename(columns={"Payout_ZAR": "Payout (ZAR)"})
            .style.format({"Payout (ZAR)": "R{:,.0f}", "Weight_kg": "{:,.0f}"}),
            use_container_width=True, hide_index=True,
        )

        # "Survives the border" flow: Buy-Back Centre -> Bale -> Origin -> Destination
        st.markdown("**Economic value crossing the border**")
        dot = 'digraph { rankdir=LR; node [shape=box style=rounded fontsize=10];'
        for i, c in enumerate(fm_bale["Buy_Back_Centre"].unique()):
            dot += f'"c{i}" [label="{c}"]; "c{i}" -> "{bale_id}";'
        dot += f'"{bale_id}" [style="rounded,filled" fillcolor="#e8f0fe"];'
        dot += f'"{row["Origin"]}" [shape=oval fillcolor="#e6f4ea" style=filled];'
        dot += f'"{row["Destination"]}" [shape=oval fillcolor="#fef7e0" style=filled];'
        dot += f'"{bale_id}" -> "{row["Origin"]}" -> "{row["Destination"]}" [label="  border"]; }}'
        st.graphviz_chart(dot, use_container_width=True)

# ---- SECTION B: DUAL-TRACK BORDER COMPLIANCE ----
with colB:
    st.markdown("### B · Dual-Track Border Compliance")

    basel_class, basel_note = classify_basel(row["Material_Type"], row["Contamination_Level"])
    if basel_class == "B3011":
        st.success(f"**Basel: B3011 \u2013 Simplified.** {basel_note}")
    else:
        st.warning(f"**Basel: PIC \u2013 Full Control.** {basel_note}")

    docs = compliance_docs(row["Origin"], row["Destination"], basel_class)

    if st.button("Generate SADC Compliance Pack", type="primary"):
        with st.spinner("Compiling corridor-specific documents\u2026"):
            pdf_bytes = build_pdf(row, fm_bale, basel_class, basel_note, docs)
        st.session_state[f"pdf_{bale_id}"] = pdf_bytes  # survive reruns
        st.success("Compliance pack compiled.")

    st.markdown("**Documents for this corridor & classification:**")
    for title, body in docs:
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(body)

    pdf_bytes = st.session_state.get(f"pdf_{bale_id}")
    if pdf_bytes:
        st.download_button(
            "\u2b07\ufe0f Download compliance pack (PDF)",
            data=pdf_bytes,
            file_name=f"compliance_pack_{bale_id}.pdf",
            mime="application/pdf",
        )

st.divider()

# --------------------------------------------------------------------------------------
# MONETISATION PANEL
# --------------------------------------------------------------------------------------
with st.expander("Platform Economics \u2014 how the engine earns as corridor volume grows", expanded=False):
    m1, m2 = st.columns(2)
    flat_fee = m1.number_input("Flat fee per consignment cleared (R)", value=750, step=50)
    per_tonne = m2.number_input("Per-tonne fee on received material (R/t)", value=15, step=1)

    completed = ship[ship["Received_kg_num"].notna()]
    n_cleared = len(completed)
    tonnes_received = completed["Received_kg_num"].sum() / 1000
    revenue = n_cleared * flat_fee + tonnes_received * per_tonne

    r1, r2, r3 = st.columns(3)
    r1.metric("Consignments cleared", f"{n_cleared}")
    r2.metric("Tonnes cleared", f"{tonnes_received:,.2f} t")
    r3.metric("Platform revenue (this dataset)", rand(revenue))

    st.caption(
        "Framing: small per-shipment revenue now, scaling with the corridor volume the platform "
        "helps unlock \u2014 positioned as the operational layer beneath the SADC regional policy "
        "framework CCBA is lobbying governments to create. Revenue and volume rise together."
    )

st.caption("Simulated sandbox demo for CCBA Group Sustainability. Figures and documents are illustrative.")
