# SADC Corridor Compliance & Traceability Engine — Prototype

A single-file Streamlit demo for the CCBA Group Sustainability pitch.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Your browser opens at `http://localhost:8501`. Nothing else to configure — the mock
data is embedded in the script.

## What it does (and the story to tell on camera)

1. **Regional KPIs** — dispatched vs received tonnage, computed transit variance, and total
   community injection in ZAR (with the FX rates shown, so the number is defensible).
2. **Shipments table** — the anomaly flag is *computed in-engine* (variance > 5%), not read
   from the spreadsheet. MW-8091 lights up red at ~18% loss. Narrate this as the intelligence.
3. **Bale drill-down**:
   - **Section A — Cross-Border Social Provenance:** ZAR injection for the bale, split by
     women-owned SMME / youth enterprise / informal sector, plus a flow diagram literally
     drawing the value crossing the border. This is the differentiated thesis — dwell here.
   - **Section B — Dual-Track Border Compliance:** each bale is classified (Basel B3011
     simplified vs full PIC), then the corridor-correct documents are listed and a real PDF
     compliance pack downloads. Pick BW-1042 (clean PET → simplified, SA dual-track) and then
     MW-8091 (mixed/contaminated → full PIC, Zambia ZEMA gate) to show the logic flexing.
4. **Platform Economics** — editable per-shipment + per-tonne fee model showing revenue
   scaling with corridor volume.

## Demo tips

- **BW-1042** shows the "everything clean, minimal paperwork" happy path (B3011).
- **MW-8091** shows the flagged, hazardous, full-PIC path — the contrast is the point.
- **NM-3011** is In-Transit (Received = Pending) — shows the tool handles incomplete data.

## Before any real use

- Update the `FX_TO_ZAR` rates at the top of `app.py` to live rates.
- The compliance document requirements are researched but illustrative — have a compliance
  specialist confirm current forms/turnarounds before this informs a real shipment.
