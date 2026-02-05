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
st.subheader("🏃‍♂️ Jouw run")

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

# -------------------------------------------------
# Looptijd-overlap
# -------------------------------------------------
def overlapt(uur_start, start, einde):
    return uur_start < einde and (uur_start + timedelta(hours=1)) > start

df["looptijd"] = df["tijd"].apply(lambda t: overlapt(t, start_dt, eind_dt))

# -------------------------------------------------
# Emoji + betekenis
# -------------------------------------------------
df["nacht"] = df["tijd"] >= sunset
df["emoji"] = df.apply(lambda r: weer_emoji(r["weer_code"], r["nacht"]), axis=1)
df["weer"] = df.apply(
    lambda r: f"{r['emoji']} {weer_betekenis(r['weer_code'])}",
    axis=1
)

# -------------------------------------------------
# Score
# -------------------------------------------------
def loop_score(feels, rain, wind):
    s = 10
    if feels < 0: s -= 3
    elif feels < 5: s -= 2
    elif feels > 20: s -= 2
    if rain > 1: s -= 3
    elif rain > 0: s -= 1
    if wind > 25: s -= 2
    elif wind > 15: s -= 1
    return max(1, min(10, s))

df["score"] = df.apply(lambda r: loop_score(r["gevoel"], r["neerslag"], r["wind"]), axis=1)

# -------------------------------------------------
# Midden van de run (voor advies)
# -------------------------------------------------
mid_row = df.iloc[(df["tijd"] - mid_dt).abs().argsort().iloc[0]]

gevoel = mid_row["gevoel"]
neerslag = mid_row["neerslag"]
wind = mid_row["wind"]
score = int(mid_row["score"])

# -------------------------------------------------
# ⭐ Score
# -------------------------------------------------
st.subheader("⭐ Loop-geschiktheid (midden van de run)")

kleur = "🟥" if score <= 4 else "🟧" if score <= 6 else "🟩"

st.markdown(
    f"<div style='text-align:center; font-size:64px; font-weight:bold;'>{kleur} {score}</div>",
    unsafe_allow_html=True
)

st.write(f"🌡️ Gevoelstemperatuur: **{gevoel:.1f} °C**")
st.write(f"🌧️ Neerslag: **{neerslag:.1f} mm/u**")
st.write(f"💨 Wind: **{wind:.0f} km/u**")
st.write(f"🌤️ Weer: **{mid_row['weer']}**")

# -------------------------------------------------
# 👕 KLEDINGADVIES (EXPLICIET AANWEZIG)
# -------------------------------------------------
st.subheader("👕 Kledingadvies (midden van de run)")

advies = {}

advies["Thermisch ondershirt"] = (
    "Ja (extra laag)" if (gevoel <= -2 or (gevoel <= 0 and wind >= 15)) else "Nee"
)

if gevoel <= 2:
    advies["Shirt"] = "Long sleeve"
elif 3 <= gevoel <= 8:
    advies["Shirt"] = "Long sleeve (of korte mouw bij hoge intensiteit)"
elif 9 <= gevoel <= 14:
    advies["Shirt"] = "Korte mouw"
else:
    advies["Shirt"] = "Singlet"

if gevoel <= 0:
    advies["Broek"] = "Winter tight"
elif 1 <= gevoel <= 7:
    advies["Broek"] = "Long tight"
else:
    advies["Broek"] = "Korte broek"

if gevoel <= -3:
    advies["Handen"] = "Wanten"
elif -2 <= gevoel <= 4:
    advies["Handen"] = "Dunne handschoenen"
else:
    advies["Handen"] = "Geen"

if neerslag > 1:
    advies["Jack"] = "Regenjas"
elif gevoel <= -5:
    advies["Jack"] = "Dikkere jas"
elif wind >= 15 and gevoel <= 5:
    advies["Jack"] = "Licht jack"
else:
    advies["Jack"] = "Geen"

if gevoel <= 0:
    advies["Hoofd"] = "Muts"
elif neerslag > 0:
    advies["Hoofd"] = "Pet"
else:
    advies["Hoofd"] = "Geen"

for k, v in advies.items():
    st.write(f"**{k}:** {v}")

# -------------------------------------------------
# 📊 Weersverwachting – rest van vandaag
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
