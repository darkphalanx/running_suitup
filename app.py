import streamlit as st
import requests
import pandas as pd
from datetime import datetime, time, timedelta

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Hardloop kledingadvies",
    page_icon="🏃‍♂️",
    layout="centered"
)

# -------------------------------------------------
# THEME-AWARE CSS
# -------------------------------------------------
st.markdown("""
<style>
:root {
    --card-dark: #1e1e1e;
    --card-light: #ffffff;
    --text-dark: #e6e6e6;
    --text-light: #1f1f1f;
    --muted-dark: #aaaaaa;
    --muted-light: #666666;
}
@media (prefers-color-scheme: dark) {
    .card { background: var(--card-dark); color: var(--text-dark); }
    .meta { color: var(--muted-dark); }
}
@media (prefers-color-scheme: light) {
    .card { background: var(--card-light); color: var(--text-light); }
    .meta { color: var(--muted-light); }
}
.card {
    border-radius: 18px;
    padding: 1.6rem 1.8rem;
    margin-bottom: 1.6rem;
    box-shadow: 0 6px 20px rgba(0,0,0,0.15);
}
.hero { text-align: center; padding: 2.4rem; }
.score { font-size: 72px; font-weight: 800; }
.meta { font-size: 0.95rem; margin-top: -6px; }
.section-title { font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem; }
.advice-item {
    padding: 0.7rem 0.9rem;
    border-radius: 14px;
    background: rgba(255,255,255,0.06);
    margin-bottom: 0.6rem;
}
.tooltip { position: relative; cursor: pointer; }
.tooltip .tooltiptext {
    visibility: hidden;
    min-width: 220px;
    background: rgba(0,0,0,0.85);
    color: #fff;
    padding: 0.6rem;
    border-radius: 8px;
    position: absolute;
    top: 50%;
    left: 120%;
    transform: translateY(-50%);
    opacity: 0;
    transition: 0.2s;
    font-size: 0.75rem;
    z-index: 20;
}
.tooltip:hover .tooltiptext,
.tooltip:focus-within .tooltiptext {
    visibility: visible;
    opacity: 1;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# Helpers
# -------------------------------------------------
def weer_emoji(code, nacht=False):
    if code == 0: return "🌙" if nacht else "☀️"
    if code == 1: return "🌙☁️" if nacht else "🌤️"
    if code == 2: return "☁️🌙" if nacht else "⛅"
    if code == 3: return "☁️"
    if code in [45, 48]: return "🌫️"
    if code in [51, 53]: return "🌦️"
    if code in [55, 61]: return "🌧️"
    if code == 63: return "🌧️🌧️"
    if code == 65: return "🌧️⛈️"
    if code in [71, 73, 75]: return "❄️"
    if code in [80, 81]: return "🌦️🌬️"
    if code in [82, 95]: return "⛈️"
    return "❔"

def weer_betekenis(code):
    return {
        0:"Helder",1:"Overwegend helder",2:"Licht bewolkt",3:"Bewolkt",
        45:"Mist",48:"Mist",51:"Motregen",53:"Motregen",55:"Zware motregen",
        61:"Lichte regen",63:"Matige regen",65:"Zware regen",
        71:"Sneeuw",73:"Sneeuw",75:"Sneeuw",
        80:"Regenbuien",81:"Regenbuien",82:"Zware buien",95:"Onweer"
    }.get(code,"Onbekend")

def score_calc(feels, rain, wind):
    s = 10
    if feels < 0: s -= 3
    elif feels < 5: s -= 2
    elif feels > 20: s -= 2
    if rain > 1: s -= 3
    elif rain > 0: s -= 1
    if wind > 25: s -= 2
    elif wind > 15: s -= 1
    return max(1, min(10, s))

# -------------------------------------------------
# Header
# -------------------------------------------------
st.title("🏃‍♂️ Hardloop kledingadvies")
st.caption("Slimme kledingkeuze op basis van weer en looptijd")

# -------------------------------------------------
# Locatie & run
# -------------------------------------------------
st.markdown("<div class='section-title'>📍 Locatie & run</div>", unsafe_allow_html=True)
plaats = st.text_input("Stad / plaats", value="Lelystad")

col1, col2 = st.columns(2)
with col1:
    starttijd = st.time_input("Starttijd", value=time(18, 0))
with col2:
    duur_min = st.slider("Duur (min)", 10, 180, 60, step=5)

if not plaats:
    st.stop()

# -------------------------------------------------
# Geocoding
# -------------------------------------------------
geo = requests.get(
    "https://geocoding-api.open-meteo.com/v1/search",
    params={"name": plaats, "count": 1, "language": "nl", "format": "json"},
    timeout=10
).json()

loc = geo["results"][0]
lat, lon = loc["latitude"], loc["longitude"]

# -------------------------------------------------
# Tijd
# -------------------------------------------------
now = datetime.now().replace(minute=0, second=0, microsecond=0)
start_dt = datetime.combine(now.date(), starttijd)
eind_dt = start_dt + timedelta(minutes=duur_min)
mid_dt = start_dt + (eind_dt - start_dt) / 2
end_24h = now + timedelta(hours=24)

# -------------------------------------------------
# Weer ophalen
# -------------------------------------------------
weather = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,apparent_temperature,precipitation,weathercode,wind_speed_10m,uv_index",
        "daily": "sunset",
        "timezone": "auto"
    },
    timeout=10
).json()

sunset = datetime.fromisoformat(weather["daily"]["sunset"][0])

df = pd.DataFrame({
    "tijd": [datetime.fromisoformat(t) for t in weather["hourly"]["time"]],
    "temperatuur": weather["hourly"]["temperature_2m"],
    "gevoel": weather["hourly"]["apparent_temperature"],
    "neerslag": weather["hourly"]["precipitation"],
    "wind": weather["hourly"]["wind_speed_10m"],
    "weer_code": weather["hourly"]["weathercode"],
    "uv": weather["hourly"]["uv_index"]
})

df = df[(df["tijd"] >= now) & (df["tijd"] < end_24h)].copy()
df["nacht"] = df["tijd"] >= sunset
df["weer"] = df.apply(lambda r: f"{weer_emoji(r['weer_code'], r['nacht'])} {weer_betekenis(r['weer_code'])}", axis=1)
df["score"] = df.apply(lambda r: score_calc(r["gevoel"], r["neerslag"], r["wind"]), axis=1)

mid_row = df.iloc[(df["tijd"] - mid_dt).abs().argsort().iloc[0]]

# -------------------------------------------------
# HERO SCORE
# -------------------------------------------------
kleur = "🟥" if mid_row["score"] <= 4 else "🟧" if mid_row["score"] <= 6 else "🟩"

st.markdown(f"""
<div class="card hero">
    <div class="score">{kleur} {int(mid_row['score'])}</div>
    <div class="meta">
        {mid_row['weer']} • Gevoel {mid_row['gevoel']:.1f} °C • Wind {mid_row['wind']:.0f} km/u
    </div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------
# WEEROVERZICHT 24U
# -------------------------------------------------
st.markdown("<div class='section-title'>📊 Weersverwachting – komende 24 uur</div>", unsafe_allow_html=True)

df["uur"] = df["tijd"].dt.strftime("%a %H:%M")
df["temp / gevoel"] = df.apply(lambda r: f"{r['temperatuur']:.1f} / {r['gevoel']:.1f} °C", axis=1)

st.dataframe(
    df[["uur", "weer", "temp / gevoel", "neerslag", "wind", "uv", "score"]],
    hide_index=True
)
