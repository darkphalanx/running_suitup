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
st.caption(f"Gevonden locatie: {loc['name']}, {loc['country']}")

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
# Weer ophalen (hourly)
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
        "timezone": "auto"
    },
    timeout=10
).json()

hourly = weather["hourly"]
times = [datetime.fromisoformat(t) for t in hourly["time"]]

df = pd.DataFrame({
    "tijd": times,
    "temperatuur": hourly["temperature_2m"],
    "gevoel": hourly["apparent_temperature"],
    "neerslag": hourly["precipitation"],
    "wind": hourly["wind_speed_10m"],
    "weer_code": hourly["weathercode"]
})

# Pak het uur dat het dichtst bij het midden van de run ligt
mid_row = df.iloc[(df["tijd"] - mid_dt).abs().argsort().iloc[0]]

gevoel = mid_row["gevoel"]
neerslag = mid_row["neerslag"]
wind = mid_row["wind"]

# -------------------------------------------------
# KLEDINGADVIES – JOUW LOGICA
# -------------------------------------------------
st.subheader("👕 Kledingadvies (midden van de run)")

advies = {}

# 1️⃣ Thermisch ondershirt
if gevoel <= -2 or (gevoel <= 0 and wind >= 15):
    advies["Thermisch ondershirt"] = "Ja (extra laag)"
else:
    advies["Thermisch ondershirt"] = "Nee"

# 2️⃣ Shirt
if gevoel <= 2:
    advies["Shirt"] = "Long sleeve"
elif 3 <= gevoel <= 8:
    advies["Shirt"] = "Long sleeve (of korte mouw bij hoge intensiteit)"
elif 9 <= gevoel <= 14:
    advies["Shirt"] = "Korte mouw"
else:
    advies["Shirt"] = "Singlet"

# 3️⃣ Broek
if gevoel <= 0:
    advies["Broek"] = "Winter tight"
elif 1 <= gevoel <= 7:
    advies["Broek"] = "Long tight"
else:
    advies["Broek"] = "Korte broek"

# 4️⃣ Handen
if gevoel <= -3:
    advies["Handen"] = "Wanten"
elif -2 <= gevoel <= 4:
    advies["Handen"] = "Dunne handschoenen"
else:
    advies["Handen"] = "Geen"

# 5️⃣ Jack
if neerslag > 1:
    advies["Jack"] = "Regenjas"
elif gevoel <= -5:
    advies["Jack"] = "Dikkere jas"
elif wind >= 15 and gevoel <= 5:
    advies["Jack"] = "Licht jack"
else:
    advies["Jack"] = "Geen"

# 6️⃣ Hoofd
if gevoel <= 0:
    advies["Hoofd"] = "Muts"
elif neerslag > 0:
    advies["Hoofd"] = "Pet"
else:
    advies["Hoofd"] = "Geen"

# -------------------------------------------------
# Output
# -------------------------------------------------
for item, keuze in advies.items():
    st.write(f"**{item}:** {keuze}")

st.caption(
    f"📍 {plaats} • 🕒 midden run: {mid_dt.strftime('%H:%M')} • "
    f"gevoel: {gevoel:.1f} °C"
)

# -------------------------------------------------
# Debug / transparantie (optioneel)
# -------------------------------------------------
with st.expander("🔍 Gebruikte weerswaarden"):
    st.write({
        "Gevoelstemperatuur": round(gevoel, 1),
        "Neerslag (mm/u)": neerslag,
        "Wind (km/u)": wind,
        "Referentietijd": mid_dt.strftime("%H:%M")
    })
