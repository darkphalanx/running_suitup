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

# -------------------------------------------------
# Weer ophalen (incl. zonsondergang)
# -------------------------------------------------
weather = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,apparent_temperature,precipitation,weathercode",
        "daily": "sunset",
        "timezone": "auto"
    },
    timeout=10
).json()

sunset = datetime.fromisoformat(weather["daily"]["sunset"][0])

hourly = weather["hourly"]
times = [datetime.fromisoformat(t) for t in hourly["time"]]

now = datetime.now().replace(minute=0, second=0)

rows = []
for i, t in enumerate(times):
    if t.date() == today and t >= now:
        rows.append({
            "tijd": t,
            "uur": t.strftime("%H:%M"),
            "temperatuur": hourly["temperature_2m"][i],
            "gevoel": hourly["apparent_temperature"][i],
            "neerslag": hourly["precipitation"][i],
            "weer_code": hourly["weathercode"][i],
            "nacht": t >= sunset,
            "looptijd": start_dt <= t <= eind_dt
        })

df = pd.DataFrame(rows)

# -------------------------------------------------
# Weer interpretatie
# -------------------------------------------------
def weer_label(code, nacht):
    if code == 0:
        return "Helder 🌙" if nacht else "Zonnig ☀️"
    if code in [1, 2]:
        return "Licht bewolkt 🌙" if nacht else "Licht bewolkt ⛅"
    if code == 3:
        return "Bewolkt ☁️"
    if code in [51, 53, 55, 61, 63, 65]:
        return "Regen 🌧️"
    if code in [71, 73, 75]:
        return "Sneeuw ❄️"
    return "Onbekend"

df["weer"] = df.apply(lambda r: weer_label(r["weer_code"], r["nacht"]), axis=1)

# -------------------------------------------------
# Score (1–10)
# -------------------------------------------------
def running_score(feels, rain):
    score = 10
    if feels < 0:
        score -= 3
    elif feels < 5:
        score -= 2
    elif feels > 20:
        score -= 2
    if rain > 1:
        score -= 3
    elif rain > 0:
        score -= 1
    return max(1, min(10, score))

df["score"] = df.apply(lambda r: running_score(r["gevoel"], r["neerslag"]), axis=1)

# -------------------------------------------------
# Weer + score op starttijd
# -------------------------------------------------
closest = df.iloc[(df["tijd"] - start_dt).abs().argsort().iloc[0]]

st.subheader("⭐ Loop-geschiktheid tijdens jouw run")

score = int(closest["score"])
kleur = "🟥" if score <= 4 else "🟧" if score <= 6 else "🟩"

st.markdown(
    f"<div style='text-align:center; font-size:64px; font-weight:bold;'>{kleur} {score}/10</div>",
    unsafe_allow_html=True
)

st.write(f"🌡️ Temperatuur: **{closest['temperatuur']:.1f} °C**")
st.write(f"🥶 Gevoelstemperatuur: **{closest['gevoel']:.1f} °C**")
st.write(f"🌧️ Neerslag: **{closest['neerslag']:.1f} mm/u**")
st.write(f"🌤️ Weer: **{closest['weer']}**")

# -------------------------------------------------
# Kledingadvies
# -------------------------------------------------
st.subheader("👕 Kledingadvies")

advies = []

if closest["gevoel"] <= 5:
    advies += ["👕 Thermisch ondershirt (lange mouw)", "👖 Lange hardlooptight"]
elif closest["gevoel"] <= 12:
    advies += ["👕 Longsleeve", "👖 Lange hardlooptight"]
else:
    advies += ["👕 Shirt korte mouw", "🩳 Korte broek"]

if closest["gevoel"] <= 3:
    advies += ["🧤 Dunne handschoenen", "🧣 Buff of dunne muts"]

if closest["neerslag"] > 0:
    advies.append("🧥 Licht waterafstotend jack")

for a in advies:
    st.write(a)

# -------------------------------------------------
# DUIDELIJKE WEERSGRAFIEK (native Streamlit)
# -------------------------------------------------
st.subheader("📊 Weersverwachting – rest van vandaag")

chart_df = df.set_index("uur")[["temperatuur", "gevoel", "neerslag"]]
st.line_chart(chart_df[["temperatuur", "gevoel"]])
st.bar_chart(chart_df[["neerslag"]])

# Highlight looptijd in tabel (visueel 100% duidelijk)
st.markdown("**🟩 Gemarkeerde uren = jouw looptijd**")
st.dataframe(
    df[["uur", "weer", "temperatuur", "gevoel", "neerslag", "score", "looptijd"]],
    hide_index=True
)

# -------------------------------------------------
# Footer
# -------------------------------------------------
st.caption(
    f"📍 {plaats} • 🕒 {start_dt.strftime('%H:%M')}–{eind_dt.strftime('%H:%M')} • "
    f"⏱️ {duur_min} min"
)
