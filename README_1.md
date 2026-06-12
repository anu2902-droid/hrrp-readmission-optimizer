# Hospital Readmission Penalty Optimizer

An interactive decision-support tool that allocates a fixed improvement budget across hospital-condition units to maximize impact under Medicare's Hospital Readmissions Reduction Program (HRRP), using linear-programming optimization on public CMS data.

**Live app:** https://hrrp-readmission-optimizer-s4cqdkyeo7uitx9aswapxc.streamlit.app/

---

## The problem

Under HRRP, CMS penalizes hospitals with higher-than-expected 30-day readmissions by reducing *all* Medicare reimbursement — up to 3% per hospital. A health system with a limited quality-improvement budget faces a real allocation question: **given a fixed budget, which hospitals and which conditions should we invest in to avoid the most readmissions (or the most penalty dollars)?**

This tool answers that as a constrained optimization, not a ranked list.

---

## How it works

1. **Data** — CMS FY2026 Hospital Readmissions Reduction Program file. For each hospital-condition unit (heart failure, pneumonia, COPD, AMI, CABG, hip/knee), it provides discharges, the Excess Readmission Ratio (ERR), and expected vs. actual readmission rates.
2. **Cleaning** — kept only penalized units (ERR > 1); computed *excess readmissions* (actual minus expected) as the avoidable pool. ~4,300 penalized units nationally.
3. **Optimization** — a linear program (PuLP) chooses what fraction of each unit's intervention to fund, maximizing total readmissions avoided (or dollars saved) subject to the budget constraint.
4. **App** — Streamlit front end: set the budget, pick an intervention preset, toggle between optimizing for readmissions vs. dollars, and see the optimal allocation update live.

---

## Key assumption (sourced)

Intervention cost and effectiveness default to published figures from a peer-reviewed comparison of discharge interventions:

| Intervention | Cost / patient | Readmission reduction |
|---|---|---|
| Care Transitions Intervention | $152.89 | 3.6% |
| Project RED | $327.03 | 5.5% |
| Transitional Care Model | $1,565.84 | 13.2% |

Users can override these with a custom slider.

---

## A real finding

At a mid-cost intervention applied across all discharges, **the budget spent exceeds the penalty dollars saved** — net benefit is negative. This is not a failure of the tool; it's the point. It shows blanket intervention isn't cost-effective, and the optimizer reveals the conditions under which it *does* pay off: cheaper interventions (CTI) or targeting only the highest-excess units. The tool is built to find that break-even, not to assume it.

---

## Limitations

- Intervention effectiveness is an assumption drawn from literature, not measured on this population — this is a prioritization aid, not a prediction.
- The dollar layer uses an estimated Medicare payment avoided per readmission; a future version would join the actual CMS payment-adjustment file.
- The model funds units fractionally; whole-unit funding would require an integer program (a one-line change).
- Observational data: ERR reflects correlation with hospital practice, not proven causal levers.

---

## Stack

Python · pandas · PuLP (linear programming) · Streamlit · CMS public data
