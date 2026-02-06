# -------------------------------------------------
# KLEDINGADVIES
# -------------------------------------------------
st.markdown("<div class='section-title'>👕 Kledingadvies</div>", unsafe_allow_html=True)

# Waarden midden van de run
gevoel = mid_row["gevoel"]
wind = mid_row["wind"]
regen = mid_row["neerslag"]
uv = mid_row["uv"]

# Context
is_zonnig = mid_row["weer_code"] in [0, 1] and not mid_row["nacht"]
run_na_zonsondergang = eind_dt >= sunset

# -----------------------------
# Jack (eerst)
# -----------------------------
if regen > 1:
    jack = "Regenjas"
elif wind >= 15 and gevoel <= 6:
    jack = "Licht jack"
else:
    jack = "Geen"

# -----------------------------
# Thermisch ondershirt (pas daarna)
# -----------------------------
thermisch_ondershirt = False
if gevoel <= -2:
    thermisch_ondershirt = True
elif gevoel <= 0 and wind >= 15:
    thermisch_ondershirt = True
elif gevoel <= 2 and jack != "Geen":
    thermisch_ondershirt = True

# -----------------------------
# Overige kleding
# -----------------------------
# Hoofd
if gevoel <= 0:
    hoofd = "Muts"
elif is_zonnig or regen > 0:
    hoofd = "Pet"
else:
    hoofd = "Geen"

# Shirt
if gevoel > 18:
    shirt = "Singlet"
elif gevoel > 12:
    shirt = "Korte mouw"
else:
    shirt = "Long sleeve"

# Broek
if gevoel > 10:
    broek = "Korte broek"
elif gevoel > -2:
    broek = "Long tight"
else:
    broek = "Winter tight"

# Handen
if gevoel < 0:
    handen = "Wanten"
elif gevoel <= 5:
    handen = "Dunne handschoenen"
else:
    handen = "Geen"

# -----------------------------
# Structuren
# -----------------------------
kleding = {
    "Hoofd": hoofd,
    "Thermisch ondershirt": "Ja" if thermisch_ondershirt else "Nee",
    "Shirt": shirt,
    "Broek": broek,
    "Jack": jack,
    "Handen": handen,
}

accessoires = {
    "Verlichting": "Aanbevolen" if run_na_zonsondergang else "Niet nodig",
    "Zonnebril": "Aanbevolen" if is_zonnig else "Niet nodig",
    "Zonnebrand": "Aanbevolen (UV ≥ 3)" if uv >= 3 else "Niet nodig",
}

# -----------------------------
# Tooltips (waarom)
# -----------------------------
waarom = {
    "Hoofd": (
        "Muts voorkomt warmteverlies bij kou."
        if gevoel <= 0
        else "Pet beschermt tegen zon en regen."
        if is_zonnig or regen > 0
        else "Geen hoofdbedekking nodig."
    ),
    "Thermisch ondershirt": (
        "Extra isolatie omdat het jack alleen wind/regen tegenhoudt."
        if thermisch_ondershirt
        else "Niet nodig bij deze gevoelstemperatuur."
    ),
    "Shirt": "Bepaald op basis van gevoelstemperatuur tijdens het lopen.",
    "Broek": "Benen warmen sneller op dan romp; daarom andere drempels.",
    "Jack": (
        "Beschermt tegen wind en/of regen."
        if jack != "Geen"
        else "Geen extra bescherming nodig."
    ),
    "Handen": (
        "Handen koelen snel af bij lage temperatuur."
        if handen != "Geen"
        else "Geen extra bescherming nodig."
    ),
    "Verlichting": (
        "Je loopt (deels) in het donker: zichtbaarheid is belangrijk."
        if run_na_zonsondergang
        else "Je loopt volledig bij daglicht."
    ),
    "Zonnebril": (
        "Beschermt je ogen tegen fel zonlicht."
        if is_zonnig
        else "Niet nodig zonder zon."
    ),
    "Zonnebrand": (
        "UV-index is hoog genoeg om huid te beschadigen."
        if uv >= 3
        else "UV-index is laag."
    ),
}

# -----------------------------
# Render kleding
# -----------------------------
st.markdown("#### 🎽 Kleding")

cols = st.columns(2)
for i, (k, v) in enumerate(kleding.items()):
    with cols[i % 2]:
        st.markdown(
            f"""
            <div class="advice-item">
                <strong>{k}</strong>
                <span class="tooltip" tabindex="0"> ⓘ
                    <span class="tooltiptext">{waarom[k]}</span>
                </span>
                <br>{v}
            </div>
            """,
            unsafe_allow_html=True
        )

# -----------------------------
# Render accessoires
# -----------------------------
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### 🧢 Accessoires & veiligheid")

cols = st.columns(2)
for i, (k, v) in enumerate(accessoires.items()):
    with cols[i % 2]:
        st.markdown(
            f"""
            <div class="advice-item">
                <strong>{k}</strong>
                <span class="tooltip" tabindex="0"> ⓘ
                    <span class="tooltiptext">{waarom[k]}</span>
                </span>
                <br>{v}
            </div>
            """,
            unsafe_allow_html=True
        )
