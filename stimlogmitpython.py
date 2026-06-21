import streamlit as st
import json
import os
import math
from datetime import datetime, date, timedelta
import emoji

# ── Einstellungen 
TAGESLIMIT    = 400
HALBWERTSZEIT = 5.5
LOG_DATEI     = "logs.json"

# ── Listen 
# Formatt [name, emoji, mg]
getraenke = [
    ["Pre Workout",     "\U0001F608", 300],
    ["Espresso",   "\u2615", 63 ],
    ["Filter",     "\u2615", 95 ],
    ["Cappuccino", "\u2615", 63 ],
    ["Energy",     "\U0001F964\u26A1", 80 ],
    ["Matcha",     "\U0001F375", 35 ],
    ["Cola",       "\U0001F964", 34 ],
    ["Doppel",     "\u2615", 126],
    ["Dunkle Schokolade",     "\U0001F36B", 60],
    ["Koffein Pille",     "\U0001F48A", 200],
]

def logs_laden():
    datei_existiert = os.path.exists(LOG_DATEI)
    
    if datei_existiert == False:
        leere_liste = []
        return leere_liste
    datei = open(LOG_DATEI, "r")
    datei_inhalt_text = datei.read()
    datei.close()
    geladene_logs = json.loads(datei_inhalt_text)
    return geladene_logs


def logs_speichern(logs):
    logs_als_text = json.dumps(logs)
    datei = open(LOG_DATEI, "w")
    datei.write(logs_als_text)
    datei.close()

# ── Berechnungen 
def heute():
    return date.today().isoformat()

def aktive_mg(logs):
    total = 0
    jetzt = datetime.now()
    
    for log in logs:
        if log[0] == heute():
            aufgenommen = datetime.fromisoformat(log[1])
            zeit_differenz = jetzt - aufgenommen
            stunden_her = zeit_differenz.total_seconds() / 3600
            
            faktor = 0.5 ** (stunden_her / HALBWERTSZEIT)
            total = total + (log[2] * faktor)
            
    return round(total, 1)

def koffeinfrei_um(aktiv):
    if aktiv < 5:
        return None
    
    stunden = 0
    aktueller_wert = aktiv
    while aktueller_wert > 5:
        aktueller_wert = aktueller_wert * 0.9
        stunden = stunden + 0.5
        
    zeitpunkt = datetime.now() + timedelta(hours=stunden)
    uhrzeit_text = zeitpunkt.strftime("%H:%M")
    return uhrzeit_text

# ── Log hinzufügen und auch löschen
def log_hinzufuegen(name, emoji, mg):
    logs = logs_laden()
    logs.insert(0, [heute(), datetime.now().isoformat(), mg, name, emoji])
    logs_speichern(logs)

def log_loeschen(index):
    logs = logs_laden()
    logs.pop(index)
    logs_speichern(logs)

def alle_loeschen():
    alle_logs = logs_laden()
    logs_die_bleiben = []
    for log in alle_logs:
        if log[0] != heute():
            logs_die_bleiben.append(log)
    logs_speichern(logs_die_bleiben)

# ── Streamlit Seite
st.set_page_config(page_title="Stimlog", page_icon="\u26A1")
def splash_zeigen():
    st.html("""
    <style>
      header, footer { display: none; }
      .stApp { background: #070b14; }
      div[data-testid="stVerticalBlock"] { background: #070b14; }
    </style>
    <div style="
        position: fixed; inset: 0; z-index: 999;
        background: #070b14;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        gap: 16px; pointer-events: none;
      ">
      <p style="font-family:monospace; font-size:28px; letter-spacing:0.4em; color:#6eaaff; margin:0;">
        STIMLOG
      </p>
      <p style="font-family:monospace; font-size:11px; letter-spacing:0.2em; color:#4a6080; margin:0;">
        klicken zum starten
      </p>
    </div>
    """)
    st.markdown("""
    <style>
      /* Button komplett unsichtbar aber klickbar */
      div[data-testid="stButton"] button {
        position: fixed;
        inset: 0;
        width: 100vw;
        height: 100vh;
        background: transparent;
        border: none;
        cursor: pointer;
        z-index: 9999;
        color: transparent;
      }
    </style>
    """, unsafe_allow_html=True)
    if st.button("start"):
        st.session_state.splash_fertig = True
        st.rerun()
    st.stop()
# ── App starten ────────────────────────────────────────────────
st.set_page_config(page_title="Stimlog", page_icon="\u26A1", layout="centered")

if "splash_fertig" not in st.session_state:
    st.session_state.splash_fertig = False

if not st.session_state.splash_fertig:
    splash_zeigen()

logs       = logs_laden()
aktiv      = aktive_mg(logs)
frei       = koffeinfrei_um(aktiv)

heute_logs = []
for log in logs:
    if log[0] == heute():
        heute_logs.append(log)

total = 0
for log in heute_logs:
    total = total + log[2]

st.markdown("<p style='font-family:monospace;color:#4a6080;letter-spacing:0.2em'>STIMLOG</p>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
col1.metric("Heute total", f"{total} mg")

prozent_wert = 0
if total > 0:
    prozent_wert = round(aktiv / total * 100)
col2.metric("Noch aktiv", f"{prozent_wert}%")

#warunung für imitüberschreittung
if total > TAGESLIMIT:
    st.warning("⚠️Tageslimit überschritten!")

st.divider()

namen = []
for g in getraenke:
    namen.append(f"{g[1]} {g[0]} ({g[2]} mg)")

wahl  = st.selectbox("Getränk", namen, label_visibility="collapsed")
index = namen.index(wahl)
mg    = st.number_input("mg", value=getraenke[index][2], min_value=1, max_value=999)

if st.button("➕ Tracken", use_container_width=True):
    log_hinzufuegen(getraenke[index][0], getraenke[index][1], mg)
    st.rerun()

st.divider()

if not heute_logs:
    st.caption("— noch keine logs heute —")
else:
    for i, log in enumerate(heute_logs):
        uhrzeit = datetime.fromisoformat(log[1]).strftime("%H:%M")
        a, b, c = st.columns([3, 1, 1])
        a.write(f"{log[4]} {log[3]} — {uhrzeit}")
        b.write(f"**{log[2]} mg**")
        if c.button("✕", key=f"del_{i}"):
            log_loeschen(i)
            st.rerun()

    if st.button("Alle löschen"):
        alle_loeschen()
        st.rerun()

# ── HTML Ring mit py befehl versuch 
def ring_html(aktiv, frei):
    offset = 628.3 * (1 - min(aktiv / TAGESLIMIT, 1.0))

    if   aktiv < 100: farbe = "#00c9a7"
    elif aktiv < 250: farbe = "#ffb347"
    else:              farbe = "#ff4f4f"

    untertitel = f"frei ~{frei}" if frei else (" kein Koffein im Blut" if aktiv < 5 else "")

    return f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&display=swap');
      .wrap  {{ position:relative; width:240px; height:240px; margin:0 auto; }}
      .wrap svg {{ transform:rotate(-90deg); }}
      .bg    {{ fill:none; stroke:#131d30; stroke-width:12; }}
      .arc   {{ fill:none; stroke-width:12; stroke-linecap:round; }}
      .mitte {{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:2px; }}
      .klein {{ font-family:'DM Mono',monospace; font-size:10px; color:#4a6080; }}
      .gross {{ font-family:'DM Mono',monospace; font-size:48px; font-weight:500; color:{farbe}; }}
    </style>
    <div class="wrap">
      <svg width="240" height="240" viewBox="0 0 240 240">
        <circle class="bg"  cx="120" cy="120" r="100"/>
        <circle class="arc" cx="120" cy="120" r="100"
          stroke="{farbe}" stroke-dasharray="628.3" stroke-dashoffset="{offset:.1f}"/>
      </svg>
      <div class="mitte">
        <div class="klein">AKTIV IM BLUT</div>
        <div class="gross">{round(aktiv)}</div>
        <div class="klein">/ {TAGESLIMIT} mg</div>
        <div class="klein">{untertitel}</div>
      </div>
    </div>
    """

st.html(ring_html(aktiv, frei))
