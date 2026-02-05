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

# -------------------------------------------------
# Filter: resterende uren vandaag
# -------------------------------------------------
now = datetime.now().replace(minute=0, second=0)
df = df[(df["tijd"].dt.date == today) & (df["tijd"] >= now)].copy()

# -------------------------------------------------
# Overlap-logica voor looptijd (correct!)
# -------------------------------------------------
def overlapt_met_run(uur_start, start, einde):
    uur_einde = uur_start + timedelta(hours=1)
    return uur_start < einde and uur_einde > start

df["looptijd"] = df["tijd"].apply(
    lambda t: overlapt_met_run(t, start_dt, eind_dt)
)

# -------------------------------------------------
# Weer interpretatie
# -------------------------------------------------
def weer_label(code):
    if code == 0:
        return "Helder ☀️"
    if code in [1, 2]:
        return "Licht bewolkt ⛅"
    if code == 3:
        return "Bewolkt ☁️"
    if code in [51, 53, 55, 61, 63, 65]:
        return "Regen 🌧️"
    if code in [71, 73, 75]:
        return "Sneeuw ❄️"
    return "Onbekend"

df["weer"] = df["weer_code"].apply(weer_label)

# -------------------------------------------------
# Score (1–10)
# -------------------------------------------------
def running_score(feels, rain, wind):
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

    if wind > 25:
        score -= 2
    elif wind > 15:
        score -= 1

    return max(1, min(10, score))

df["score"] = df.apply(
    lambda r: running_score(r["gevoel"], r["neerslag"], r["wind"]),
    axis=1
)

# -------------------------------------------------
# Weer op midden van de run
# -------------------------------------------------
mid_row = df.iloc[(df["tijd"] - mid_dt).abs().argsort().iloc[0]]

gevoel = mid_row["gevoel"]
neerslag = mid_row["neerslag"]
wind = mid_row["wind"]
score = int(mid_row["score"])

# -------------------------------------------------
# Grote score
# -------------------------------------------------
st.subheader("⭐ Loop-geschiktheid (midden van de run)")

kleur = "🟥" if score <= 4 else "🟧" if score <= 6 else "🟩"

st.markdown(
    f"""
    <div style="text-align:center; font-size:64px; font-weight:bold;">
        {kleur} {score}
    </div>
    """,
    unsafe_allow_html=True
)

st.write(f"🌡️ Temperatuur: **{mid_row['temperatuur']:.1f} °C**")
st.write(f"🥶 Gevoelstemperatuur: **{gevoel:.1f} °C**")
st.write(f"🌧️ Neerslag: **{neerslag:.1f} mm/u**")
st.write(f"💨 Wind: **{wind:.0f} km/u**")
st.write(f"🌤️ Weer: **{mid_row['weer']}**")

# -------------------------------------------------
# KLEDINGADVIES (jouw afgesproken logica)
# -------------------------------------------------
st.subheader("👕 Kledingadvies")

advies = {}

# Thermisch ondershirt
if gevoel <= -2 or (gevoel <= 0 and wind >= 15):
    advies["Thermisch ondershirt"] = "Ja (extra laag)"
else:
    advies["Thermisch ondershirt"] = "Nee"

# Shirt
if gevoel <= 2:
    advies["Shirt"] = "Long sleeve"
elif 3 <= gevoel <= 8:
    advies["Shirt"] = "Long sleeve (of korte mouw bij hoge intensiteit)"
elif 9 <= gevoel <= 14:
    advies["Shirt"] = "Korte mouw"
else:
    advies["Shirt"] = "Singlet"

# Broek
if gevoel <= 0:
    advies["Broek"] = "Winter tight"
elif 1 <= gevoel <= 7:
    advies["Broek"] = "Long tight"
else:
    advies["Broek"] = "Korte broek"

# Handen
if gevoel <= -3:
    advies["Handen"] = "Wanten"
elif -2 <= gevoel <= 4:
    advies["Handen"] = "Dunne handschoenen"
else:
    advies["Handen"] = "Geen"

# Jack
if neerslag > 1:
    advies["Jack"] = "Regenjas"
elif gevoel <= -5:
    advies["Jack"] = "Dikkere jas"
elif wind >= 15 and gevoel <= 5:
    advies["Jack"] = "Licht jack"
else:
    advies["Jack"] = "Geen"

# Hoofd
if gevoel <= 0:
    advies["Hoofd"] = "Muts"
elif neerslag > 0:
    advies["Hoofd"] = "Pet"
else:
    advies["Hoofd"] = "Geen"

for k, v in advies.items():
    st.write(f"**{k}:** {v}")

# -------------------------------------------------
# VISUELE "GRAFIEK" – REST VAN VANDAAG (BLIJFT!)
# -------------------------------------------------
st.subheader("📊 Weersverwachting – rest van vandaag")

def score_bar(s):
    return "🟩" * s + "⬜" * (10 - s)

display_df = df.copy()
display_df["score_visueel"] = display_df["score"].apply(score_bar)
display_df["looptijd"] = display_df["looptijd"].apply(lambda x: "🟢" if x else "")

st.dataframe(
    display_df[
        [
            "uur",
            "weer",
            "temperatuur",
            "gevoel",
            "neerslag",
            "score_visueel",
            "looptijd"
        ]
    ],
    hide_index=True
)

st.caption("🟢 = uur overlapt (gedeeltelijk) met jouw looptijd")

# -------------------------------------------------
# Footer
# -------------------------------------------------
st.caption(
    f"📍 {plaats} • 🕒 {start_dt.strftime('%H:%M')}–{eind_dt.strftime('%H:%M')} "
    f"(midden: {mid_dt.strftime('%H:%M')}) • ⏱️ {duur_min} min"
)
