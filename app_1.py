import streamlit as st
import pandas as pd
import pulp

st.set_page_config(page_title="HRRP Readmission Optimizer", layout="wide")

st.title("Hospital Readmission Penalty Optimizer")
st.caption("Allocate a fixed budget across hospital-condition units to maximize impact under Medicare's HRRP. "
           "Linear-programming optimization on public CMS FY2026 data.")

# ---- load data ----
@st.cache_data
def load():
    return pd.read_csv("hrrp_clean.csv")

clean = load()

# ---- sidebar controls ----
st.sidebar.header("Scenario inputs")

budget = st.sidebar.number_input("Total budget ($)", min_value=100_000,
                                 max_value=50_000_000, value=5_000_000, step=500_000)

st.sidebar.subheader("Intervention assumption")
preset = st.sidebar.selectbox(
    "Preset (sourced: Hospital Discharge Interventions, 2015-adj.)",
    ["Care Transitions Intervention (CTI)",
     "Project RED",
     "Transitional Care Model (TCM)",
     "Custom"])

presets = {
    "Care Transitions Intervention (CTI)": (152.89, 0.036),
    "Project RED": (327.03, 0.055),
    "Transitional Care Model (TCM)": (1565.84, 0.132),
}
if preset == "Custom":
    cost = st.sidebar.slider("Cost per patient ($)", 50, 2000, 327)
    reduction = st.sidebar.slider("Readmission reduction (%)", 1, 25, 6) / 100
else:
    cost, reduction = presets[preset]
    st.sidebar.write(f"Cost/patient: ${cost:,.2f}  |  Reduction: {reduction*100:.1f}%")

pay_per_case = st.sidebar.number_input("Medicare payment avoided per readmission ($)",
                                       value=14000, step=1000)

objective = st.sidebar.radio("Optimize for", ["Readmissions avoided", "Dollars saved"])

# ---- build + solve LP ----
opt = clean.reset_index(drop=True).copy()
opt["unit_cost"] = opt["Number of Discharges"] * cost
opt["avoidable"] = opt["excess_readmissions"] * reduction
opt["dollar_value"] = opt["avoidable"] * pay_per_case

prob = pulp.LpProblem("opt", pulp.LpMaximize)
x = {i: pulp.LpVariable(f"x_{i}", 0, 1) for i in opt.index}

value_col = "avoidable" if objective == "Readmissions avoided" else "dollar_value"
prob += pulp.lpSum(x[i] * opt.loc[i, value_col] for i in opt.index)
prob += pulp.lpSum(x[i] * opt.loc[i, "unit_cost"] for i in opt.index) <= budget
prob.solve(pulp.PULP_CBC_CMD(msg=0))

opt["funded_fraction"] = [x[i].value() for i in opt.index]
opt["spend"] = opt["funded_fraction"] * opt["unit_cost"]
opt["readm_avoided"] = opt["funded_fraction"] * opt["avoidable"]
opt["dollars_saved"] = opt["readm_avoided"] * pay_per_case

funded = opt[opt["funded_fraction"] > 0.001].copy()

# ---- headline metrics ----
total_spend = opt["spend"].sum()
total_readm = opt["readm_avoided"].sum()
total_saved = opt["dollars_saved"].sum()
net = total_saved - total_spend

c1, c2, c3, c4 = st.columns(4)
c1.metric("Budget used", f"${total_spend:,.0f}")
c2.metric("Readmissions avoided", f"{total_readm:,.1f}")
c3.metric("Dollars saved", f"${total_saved:,.0f}")
c4.metric("Net benefit", f"${net:,.0f}")

st.divider()

# ---- allocation table + chart ----
left, right = st.columns([1, 1])

with left:
    st.subheader("Where the budget goes")
    show = funded.sort_values(value_col == "dollar_value" and "dollars_saved" or "readm_avoided",
                              ascending=False).head(15)
    st.dataframe(show[["Facility ID", "Measure Name", "Number of Discharges",
                       "Excess Readmission Ratio", "spend", "readm_avoided",
                       "dollars_saved"]].round(2), hide_index=True)

with right:
    st.subheader("Spend by condition")
    by_cond = funded.groupby("Measure Name")["spend"].sum().sort_values()
    st.bar_chart(by_cond)

st.caption(f"Units funded: {len(funded)} of {len(opt)} penalized hospital-condition units. "
           "Effectiveness and cost are assumptions; this is a decision-support tool, not a prediction.")
