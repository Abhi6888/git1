import streamlit as st
import pandas as pd
import re
import plotly.express as px

# ------------------------------
# DATA
# ------------------------------

cost_rates = {
    "Mumbai": {"residential": 2800, "commercial": 3200, "school": 3000},
    "Pune": {"residential": 2400, "commercial": 2900, "school": 2700},
    "Delhi": {"residential": 2600, "commercial": 3100, "school": 2900},
}

floor_factor = {i: 1 + 0.05 * (i - 1) for i in range(1, 31)}

activity_norms = [
    {"activity": "Excavation", "days_per_1000sqft": 10},
    {"activity": "Foundation", "days_per_1000sqft": 20},
    {"activity": "Structure", "days_per_1000sqft": 45},
    {"activity": "Finishing", "days_per_1000sqft": 40},
]

resource_norms = [
    {"activity": "Excavation", "workers": 6, "equipment": "Excavator"},
    {"activity": "Structure", "workers": 12, "equipment": "Concrete Mixer"},
    {"activity": "Finishing", "workers": 10, "equipment": "Tools"},
]

# ------------------------------
# MODELS
# ------------------------------


def estimate_cost(building_type, area_sqft, floors, city):
    rate = cost_rates.get(city, {}).get(building_type, 2500)
    ff = floor_factor.get(floors, 1.5)
    total_cost = area_sqft * rate * ff
    return rate, ff, int(total_cost)


def generate_schedule(area_sqft, floors):
    scale = area_sqft / 1000
    phases = []
    total_days = 0

    for act in activity_norms:
        days = act["days_per_1000sqft"] * scale * (1 + 0.05 * (floors - 1))
        phases.append({"Activity": act["activity"], "Days": int(days)})
        total_days += days

    months = total_days / 30
    return int(total_days), round(months, 1), phases


def plan_resources(area_sqft, floors):
    scale = area_sqft / 1000
    workers = 0
    equipment = set()

    for r in resource_norms:
        workers += int(r["workers"] * scale * (1 + 0.05 * (floors - 1)))
        equipment.add(r["equipment"])

    return workers, list(equipment)


# ------------------------------
# NLP PARSER
# ------------------------------


def parse_user_input(text):
    text = text.lower()

    if "commercial" in text or "office" in text:
        btype = "commercial"
    elif "school" in text:
        btype = "school"
    else:
        btype = "residential"

    floors = 1
    g_match = re.search(r"g\+?(\d+)", text)
    if g_match:
        floors = int(g_match.group(1)) + 1

    area = 1000
    area_match = re.search(r"(\d{3,6})", text)
    if area_match:
        area = int(area_match.group(1))

    city = "Mumbai"
    for c in cost_rates.keys():
        if c.lower() in text:
            city = c
            break

    return btype, area, floors, city


# ------------------------------
# PAGE CONFIG & STYLE
# ------------------------------

st.set_page_config(page_title="DAC Construction Planner", layout="wide")

st.markdown(
    """
    <style>
    body { background-color:#0e1117; }
    .metric {
        background: linear-gradient(135deg,#1f2937,#111827);
        padding:22px;
        border-radius:14px;
        color:white;
        box-shadow:0 4px 18px rgba(0,0,0,0.35);
    }
    .section {
        background:#111827;
        padding:24px;
        border-radius:16px;
        margin-bottom:20px;
        box-shadow:0 4px 20px rgba(0,0,0,.35);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# TITLE
# ------------------------------

st.markdown("<br><br>", unsafe_allow_html=True)

st.markdown(
    "<h1 style='text-align:center;'>DAC Construction Planner</h1>",
    unsafe_allow_html=True,
)

st.markdown(
    "<p style='text-align:center;color:#9ca3af;'>AI-driven cost, schedule, and resource planning</p>",
    unsafe_allow_html=True,
)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    user_text = st.text_input(
        "",
        placeholder="Describe project (e.g., G+3 commercial 5000 sqft Mumbai)",
    )

# ------------------------------
# SIDEBAR
# ------------------------------

with st.sidebar:
    st.header("Project Parameters")
    s_type = st.selectbox("Building Type", ["residential", "commercial", "school"])
    s_area = st.number_input("Area (sqft)", 500, 100000, 2000, 100)
    s_floors = st.slider("Floors", 1, 30, 3)
    s_city = st.selectbox("City", list(cost_rates.keys()))
    run = st.button("Run Planning AI")

# ------------------------------
# INPUT SELECTION
# ------------------------------

if user_text:
    btype, area, floors, city = parse_user_input(user_text)
else:
    btype, area, floors, city = s_type, s_area, s_floors, s_city

# ------------------------------
# RESULTS
# ------------------------------

if user_text or run:
    rate, ff, total_cost = estimate_cost(btype, area, floors, city)
    days, months, phases = generate_schedule(area, floors)
    workers, equipment = plan_resources(area, floors)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f'<div class="metric"><p>Estimated Cost</p><h2>₹ {total_cost:,}</h2><p>₹{rate}/sqft</p></div>',
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f'<div class="metric"><p>Duration</p><h2>{months} mo</h2><p>{days} days</p></div>',
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f'<div class="metric"><p>Peak Workforce</p><h2>{workers}</h2><p>{", ".join(equipment)}</p></div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("Construction Schedule")

    df = pd.DataFrame(phases)
    st.dataframe(df, use_container_width=True)

    fig = px.bar(df, x="Days", y="Activity", orientation="h")
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("Project Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Type:** {btype}")
        st.write(f"**City:** {city}")

    with col2:
        st.write(f"**Area:** {area} sqft")
        st.write(f"**Floors:** {floors}")

    st.markdown('</div>', unsafe_allow_html=True)