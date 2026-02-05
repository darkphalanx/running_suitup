import streamlit as st
import requests
import pandas as pd
from datetime import datetime, time, timedelta

# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="Hardloop Kledingadvies",
    page_icon="🏃‍♂️",
    layout="centered"
)

# -------------------------------------------------
# Custom CSS
# -------------------------------------------------
st.markdown(
    """
    <style>
    .card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    .score {
        font-size: 64px;
        font-weight: 700;
        text-align: center;
        margin: 0;
    }
    .score-sub {
        text-align: center;
        color: #666;
        margin-top: -10px;
    }
    .section-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.6rem;
    }
    .pill {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        background: #f0f2f6;
        margin-right: 0.4rem;
        margin-bottom: 0.4rem;
        font-size: 0.85rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------
# Helpers: emoji + betekenis
# -------------------------------------------------
def weer_emoji(code, nacht=False):
    if code == 0:
        return "🌙" if nacht else "☀️"
    if code == 1:
        return "🌙☁️" if nacht else "🌤️"
    if code == 2:
        return "☁️🌙" if nacht else "⛅"
    if code == 3:
        return "☁️"
    if code in [45, 48]:
        return "🌫️"
    if code in [51, 53]:
        return "🌦️"
    if code in [55, 61]:
        return "🌧️"
    if code in [63]:
        return "🌧️🌧️"
    if code in [65]:
        return "🌧️⛈️"
    if code in [71, 73, 75]:
        return "❄️"
    if code in [80, 81]:
        return "🌦️🌬️"
    if code in [82, 95]:
        return "⛈️"
    return "❔"

def weer_betekenis(code):
    mapping = {
        0: "Helder",
        1: "Overwegend helder",
        2: "Licht bewolkt",
        3: "Bewolkt",
        45: "Mist",
        48: "Mist",
        51: "Motregen",
        53: "Motregen",
        55: "Zware motregen",
        61: "Lichte regen",
        63: "Matige regen",
        65: "Zware regen",
        71: "Sneeuw",
        73: "Sneeuw",
        75: "Sneeuw",
        80: "Regenbuien",
        81: "Regenbuien",
        82: "Zware buien",
        95: "Onweer"
    }
    return mapping.get(code, "Onbekend")

# -------------------------------------------------
# Header
# -------------------------------------------------
st.title("🏃‍♂️ Hardloop kledingadvies")
st.caption("Slimme kledingkeuze op basis van weer en looptijd")

# -------------------------------------------------
# Locatie & run instellingen
# -------------------------------------------------
with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>📍 Locatie & run</div>", unsafe_allow_html=True)

    plaats = st.text_input("Stad / plaats", value="Lelystad")

    col1, col2 = st.columns(2)
    with col1:
        starttijd = st.time_input("Starttijd", value=time(18, 0))
    with col2:
        duur_min = st.slider("Duur (min)", 10, 180, 60, step=5)

    st.markdown("</div>", unsafe_allow_html=True)

if not plaats:
    st.stop()

# -------------------------------------------------
# Data ophalen
# -------------------------------------------------
geo = requests.get(
    "https://geocoding-api.open-meteo.com/v1/search",
    params={"name": plaats, "count": 1, "language": "nl", "format": "json"},
    timeout=10
).json()

loc = geo["results"][0]
lat, lon = loc["latitude"], loc["longitude"]

today = datetime.now().date()
start_dt = datetime.combine(today, starttijd)
eind_dt = start_dt + timedelta(minutes=duur_min)
mid_dt = start_dt + (eind_dt - start_dt) / 2

weather = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,apparent_temperature,precipitation,weathercode,wind_speed_10m",
        "timezone": "auto"
    },
    timeout=10
).json()

hourly = weather["hourly"]
times = [datetime.fromisoformat(t) for t in hourly["time"]]

df = pd.DataFrame({
    "tijd": times,
    "uur": [t.strftime("%H:%M") for t in times],
    "temperatuur": hourly["temperature_2m"],
    "gevoel": hourly["apparent_temperature"],
    "neerslag": hourly["precipitation"],
    "wind": hourly["wind_speed_10m"],
    "weer_code": hourly["weathercode"]
})

now = datetime.now().replace(minute=0, second=0)
df = df[(df["tijd"].dt.date == today) & (df["tijd"] >= now)].copy()

# -------------------------------------------------
# Score + midden run
# -------------------------------------------------
mid_row = df.iloc[(df["tijd"] - mid_dt).abs().argsort().iloc[0]]

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

score = score_calc(mid_row["gevoel"], mid_row["neerslag"], mid_row["wind"])
kleur = "🟥" if score <= 4 else "🟧" if score <= 6 else "🟩"

# -------------------------------------------------
# Score card
# -------------------------------------------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown(f"<div class='score'>{kleur} {score}</div>", unsafe_allow_html=True)
st.markdown(
    f"<div class='score-sub'>Gevoel: {mid_row['gevoel']:.1f} °C • "
    f"Wind: {mid_row['wind']:.0f} km/u • "
    f"{weer_emoji(mid_row['weer_code'])} {weer_betekenis(mid_row['weer_code'])}</div>",
    unsafe_allow_html=True
)
st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# Kledingadvies
# -------------------------------------------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>👕 Kledingadvies</div>", unsafe_allow_html=True)

gevoel = mid_row["gevoel"]
wind = mid_row["wind"]
regen = mid_row["neerslag"]

advies = {
    "Thermisch ondershirt": "Ja" if (gevoel <= -2 or (gevoel <= 0 and wind >= 15)) else "Nee",
    "Shirt": "Long sleeve" if gevoel <= 8 else "Korte mouw" if gevoel <= 14 else "Singlet",
    "Broek": "Winter tight" if gevoel <= 0 else "Long tight" if gevoel <= 7 else "Korte broek",
    "Handen": "Wanten" if gevoel <= -3 else "Dunne handschoenen" if gevoel <= 4 else "Geen",
    "Jack": "Regenjas" if regen > 1 else "Licht jack" if wind >= 15 and gevoel <= 5 else "Geen",
    "Hoofd": "Muts" if gevoel <= 0 else "Pet" if regen > 0 else "Geen"
}

cols = st.columns(2)
items = list(advies.items())
for i, (k, v) in enumerate(items):
    with cols[i % 2]:
        st.markdown(f"<div class='pill'><strong>{k}:</strong> {v}</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------------------------
# Weer-overzicht
# -------------------------------------------------
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>📊 Weersverwachting (rest van vandaag)</div>", unsafe_allow_html=True)

df["weer"] = df.apply(lambda r: f"{weer_emoji(r['weer_code'])} {weer_betekenis(r['weer_code'])}", axis=1)

st.dataframe(
    df[["uur", "weer", "temperatuur", "gevoel", "neerslag"]],
    hide_index=True
)

st.markdown("</div>", unsafe_allow_html=True)
