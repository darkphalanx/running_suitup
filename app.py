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

st.title("🏃‍♂️ Hardloop kledingadvies")

# -------------------------------------------------
# Emoji helper
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
    if code in [45]:
        return "🌫️"
    if code in [48]:
        return "🌫️❄️"
    if code in [51, 53]:
        return "🌦️"
    if code == 55:
        return "🌧️"
    if code == 61:
        return "🌧️"
    if code == 63:
        return "🌧️🌧️"
    if code == 65:
        return "🌧️⛈️"
    if code == 71:
        return "🌨️"
    if code == 73:
        return "❄️"
    if code == 75:
        return "❄️❄️"
    if code == 77:
        return "🧊"
    if code == 80:
        return "🌦️🌬️"
    if code == 81:
        return "🌧️🌬️"
    if code == 82:
        return "⛈️"
    if code in [95, 96, 99]:
        return "⛈️🧊"
    return "❔"

def weer_betekenis(code):
    if code == 0:
        return "Helder"
    if code == 1:
        return "Overwegend helder"
    if code == 2:
        return "Licht bewolkt"
    if code == 3:
        return "Bewolkt"
    if code in [45, 48]:
        return "Mist"
    if code in [51, 53]:
        return "Motregen"
    if code == 55:
        return "Zware motregen"
    if code == 61:
        return "Lichte regen"
    if code == 63:
        return "Matige regen"
    if code == 65:
        return "Zware regen"
    if code in [71, 73, 75]:
        return "Sneeuw"
    if code == 77:
        return "IJskorrels"
    if code in [80, 81]:
        return "Regenbuien"
    if code == 82:
        return "Zware buien"
    if code in [95, 96, 99]:
        return "Onweer"
    return "Onbekend"

# -------------------------------------------------
# Locatie
# -------------------------------------------------
st.subheader("📍 Locatie")

plaats = st.text_input("Stad / plaats", value="Lelystad")
if not plaats:
    st.stop()

geo = requests.get(
    "https://geocoding-api.open-meteo.com/v1/search",
    params={"name": plaats, "count": 1, "language": "nl", "format": "json"},
    timeout=10
).json()

if "results" not in geo:
    st.error("❌ Locatie niet gevonden")
    st.stop()

loc = geo["results"][0]
lat, lon = loc["latitude"], loc["longitude"]

# -------------------------------------------------
# Run instellingen
# -------------------------------------------------
duur_min = st.slider("Duur van de run (minuten)", 10, 180, 60, step=5)
starttijd = st.time_input("Starttijd", value=time(18, 0))

today = datetime.now().date()
start_dt = datetime.combine(today, starttijd)
eind_dt = start_dt + timedelta(minutes=duur_min)
mid_dt = start_dt + (eind_dt - start_dt) / 2

# -------------------------------------------------
# Weer ophalen
# -------------------------------------------------
weather = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": lat,
        "longitude": lon,
        "hourly": (
            "temperature_2m,"
            "apparent_temperature,"
            "precipitation,"
            "weathercode,"
            "wind_speed_10m"
        ),
        "daily": "sunset",
        "timezone": "auto"
    },
    timeout=10
).json()

sunset = datetime.fromisoformat(weather["daily"]["sunset"][0])

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

def overlapt(uur_start, start, einde):
    return uur_start < einde and (uur_start + timedelta(hours=1)) > start

df["looptijd"] = df["tijd"].apply(lambda t: overlapt(t, start_dt, eind_dt))
df["nacht"] = df["tijd"] >= sunset
df["emoji"] = df.apply(lambda r: weer_emoji(r["weer_code"], r["nacht"]), axis=1)
df["weer"] = df.apply(
    lambda r: f"{r['emoji']} {weer_betekenis(r['weer_code'])}",
    axis=1
)

# -------------------------------------------------
# Score
# -------------------------------------------------
def score(feels, rain, wind):
    s = 10
    if feels < 0: s -= 3
    elif feels < 5: s -= 2
    elif feels > 20: s -= 2
    if rain > 1: s -= 3
    elif rain > 0: s -= 1
    if wind > 25: s -= 2
    elif wind > 15: s -= 1
    return max(1, min(10, s))

df["score"] = df.apply(lambda r: score(r["gevoel"], r["neerslag"], r["wind"]), axis=1)

# -------------------------------------------------
# Overzicht (grafiek/tabel)
# -------------------------------------------------
st.subheader("📊 Weersverwachting – rest van vandaag")

def score_bar(s):
    return "🟩" * s + "⬜" * (10 - s)

df["score_visueel"] = df["score"].apply(score_bar)
df["looptijd"] = df["looptijd"].apply(lambda x: "🟢" if x else "")

st.dataframe(
    df[
        ["uur", "weer", "temperatuur", "gevoel", "neerslag", "score_visueel", "looptijd"]
    ],
    hide_index=True
)

st.caption("🟢 = uur overlapt (gedeeltelijk) met jouw looptijd")
