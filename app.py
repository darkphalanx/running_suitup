import streamlit as st
import requests
import pandas as pd
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(
    page_title="Hardloop kledingadvies",
    page_icon="🏃‍♂️",
    layout="centered"
)

# =================================================
# CSS
# =================================================
st.markdown("""
<style>
.card {
    border-radius:18px;
    padding:1.6rem 1.8rem;
    margin-bottom:1.6rem;
    box-shadow:0 6px 20px rgba(0,0,0,.15);
}
.hero { text-align:center; padding:2.4rem; }
.score { font-size:72px; font-weight:800; }
.meta { font-size:.95rem; opacity:.8; }
.section-title { font-size:1.2rem; font-weight:600; margin-bottom:1rem; }
.advice-item {
    padding:.7rem .9rem;
    border-radius:14px;
    background:rgba(255,255,255,.06);
    margin-bottom:.6rem;
}
.tooltip { position:relative; cursor:pointer; }
.tooltip .tooltiptext {
    visibility:hidden;
    min-width:220px;
    background:rgba(0,0,0,.85);
    color:#fff;
    padding:.6rem;
    border-radius:8px;
    position:absolute;
    top:50%;
    left:120%;
    transform:translateY(-50%);
    opacity:0;
    transition:.2s;
    font-size:.75rem;
    z-index:20;
}
.tooltip:hover .tooltiptext,
.tooltip:focus-within .tooltiptext {
    visibility:visible;
    opacity:1;
}
</style>
""", unsafe_allow_html=True)

# =================================================
# HELPERS
# =================================================
def dichtstbijzijnde_tijd(interval_min, tz):
    now = datetime.now(tz)
    minutes = (now.minute + interval_min // 2) // interval_min * interval_min
    rounded = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=minutes)
    return rounded.time()

def weer_emoji(code, nacht=False):
    if code == 0: return "🌙" if nacht else "☀️"
    if code == 1: return "🌙☁️" if nacht else "🌤️"
    if code == 2: return "⛅"
    if code == 3: return "☁️"
    if code in [45,48]: return "🌫️"
    if code in [51,53,55]: return "🌦️"
    if code in [61,63,65]: return "🌧️"
    if code in [71,73,75]: return "❄️"
    if code in [80,81,82]: return "🌦️🌬️"
    if code == 95: return "⛈️"
    return "❔"

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

# =================================================
# HEADER
# =================================================
st.title("🏃‍♂️ Hardloop kledingadvies")
st.caption("Slimme kledingkeuze op basis van weer en looptijd")

# =================================================
# LOCATIE (autocomplete)
# =================================================
zoekterm = st.text_input("Plaats (min. 2 letters)", "Lelystad")

if len(zoekterm) < 2:
    st.stop()

geo = requests.get(
    "https://geocoding-api.open-meteo.com/v1/search",
    params={"name":zoekterm,"count":5,"language":"nl","format":"json"},
    timeout=10
).json()

if not geo.get("results"):
    st.info("Geen locaties gevonden")
    st.stop()

opties = [
    f"{r['name']}, {r.get('admin1','')}, {r['country']}".replace(" ,","")
    for r in geo["results"]
]

keuze = st.selectbox("Kies een plaats", opties)
loc = geo["results"][opties.index(keuze)]
lat, lon = loc["latitude"], loc["longitude"]

# =================================================
# WEER + TIJDZONE
# =================================================
weather = requests.get(
    "https://api.open-meteo.com/v1/forecast",
    params={
        "latitude":lat,
        "longitude":lon,
        "hourly":"temperature_2m,apparent_temperature,precipitation,weathercode,wind_speed_10m,uv_index",
        "daily":"sunset",
        "timezone":"auto"
    },
    timeout=10
).json()

tz = ZoneInfo(weather["timezone"])
now = datetime.now(tz).replace(minute=0, second=0, microsecond=0)
sunset = datetime.fromisoformat(weather["daily"]["sunset"][0]).astimezone(tz)

# =================================================
# RUN INPUT
# =================================================
c1, c2 = st.columns(2)
with c1:
    starttijd = st.time_input("Starttijd", value=dichtstbijzijnde_tijd(5, tz))
with c2:
    duur_min = st.slider("Duur (min)", 10, 180, 60, 5)

start_dt = datetime.combine(now.date(), starttijd, tzinfo=tz)
eind_dt = start_dt + timedelta(minutes=duur_min)
mid_dt = start_dt + (eind_dt - start_dt) / 2
end_24h = now + timedelta(hours=24)

# =================================================
# DATAFRAME
# =================================================
df = pd.DataFrame({
    "tijd":[datetime.fromisoformat(t).astimezone(tz) for t in weather["hourly"]["time"]],
    "temp":weather["hourly"]["temperature_2m"],
    "gevoel":weather["hourly"]["apparent_temperature"],
    "regen":weather["hourly"]["precipitation"],
    "wind":weather["hourly"]["wind_speed_10m"],
    "code":weather["hourly"]["weathercode"],
    "uv":weather["hourly"]["uv_index"]
})

df = df[(df["tijd"]>=now)&(df["tijd"]<end_24h)]
df["nacht"] = df["tijd"] >= sunset
df["weer"] = df.apply(lambda r:f"{weer_emoji(r['code'],r['nacht'])}",axis=1)
df["score"] = df.apply(lambda r:score_calc(r["gevoel"],r["regen"],r["wind"]),axis=1)

mid = df.iloc[(df["tijd"]-mid_dt).abs().argsort().iloc[0]]

# =================================================
# HERO
# =================================================
kleur = "🟥" if mid["score"]<=4 else "🟧" if mid["score"]<=6 else "🟩"
st.markdown(f"""
<div class="card hero">
  <div class="score">{kleur} {int(mid['score'])}</div>
  <div class="meta">{mid['weer']} • Gevoel {mid['gevoel']:.1f}°C • Wind {mid['wind']:.0f} km/u</div>
</div>
""", unsafe_allow_html=True)

# =================================================
# KLEDINGADVIES
# =================================================
st.markdown("<div class='section-title'>👕 Kledingadvies</div>", unsafe_allow_html=True)

gevoel, wind, regen, uv = mid["gevoel"], mid["wind"], mid["regen"], mid["uv"]
is_zonnig = mid["code"] in [0,1] and not mid["nacht"]
run_na_zonsondergang = eind_dt >= sunset

# Jack eerst
if regen > 1:
    jack = "Regenjas"
elif wind >= 15 and gevoel <= 6:
    jack = "Licht jack"
else:
    jack = "Geen"

# Thermisch pas daarna
thermisch = (
    gevoel <= -2 or
    (gevoel <= 0 and wind >= 15) or
    (gevoel <= 2 and jack != "Geen")
)

kleding = {
    "Hoofd": "Muts" if gevoel<=0 else "Pet" if (is_zonnig or regen>0) else "Geen",
    "Thermisch ondershirt": "Ja" if thermisch else "Nee",
    "Shirt": "Singlet" if gevoel>18 else "Korte mouw" if gevoel>12 else "Long sleeve",
    "Broek": "Korte broek" if gevoel>10 else "Long tight" if gevoel>-2 else "Winter tight",
    "Jack": jack,
    "Handen": "Wanten" if gevoel<0 else "Dunne handschoenen" if gevoel<=5 else "Geen"
}

accessoires = {
    "Verlichting": "Aanbevolen" if run_na_zonsondergang else "Niet nodig",
    "Zonnebril": "Aanbevolen" if is_zonnig else "Niet nodig",
    "Zonnebrand": "Aanbevolen (UV ≥ 3)" if uv>=3 else "Niet nodig"
}

cols = st.columns(2)
for i,(k,v) in enumerate(kleding.items()):
    with cols[i%2]:
        st.markdown(f"<div class='advice-item'><strong>{k}</strong><br>{v}</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### 🧢 Accessoires & veiligheid")

cols = st.columns(2)
for i,(k,v) in enumerate(accessoires.items()):
    with cols[i%2]:
        st.markdown(f"<div class='advice-item'><strong>{k}</strong><br>{v}</div>", unsafe_allow_html=True)

# =================================================
# WEEROVERZICHT
# =================================================
st.markdown("<div class='section-title'>📊 Weersverwachting – komende 24 uur</div>", unsafe_allow_html=True)
df["uur"] = df["tijd"].dt.strftime("%a %H:%M")
df["temp/gevoel"] = df.apply(lambda r:f"{r['temp']:.1f}/{r['gevoel']:.1f}",axis=1)

st.dataframe(
    df[["uur","weer","temp/gevoel","regen","wind","uv","score"]],
    hide_index=True
)
