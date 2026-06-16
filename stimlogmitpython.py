import streamlit as st
import json
import os
import math
from datetime import datetime, date, timedelta
import emoji

# ── Einstellungen ──────────────────────────────────────────────
TAGESLIMIT    = 400
HALBWERTSZEIT = 5.5
LOG_DATEI     = "logs.json"

# ── Listen ─────────────────────────────────────────────────────
# Format: [name, emoji, mg]
getraenke = [
    ["Pre Workout",     "\U0001F608", 300],
    ["Espresso",   "\u2615", 63 ],
    ["Filter",     "\u2615", 95 ],
    ["Cappuccino", "\u2615", 63 ],
    ["Energy",     "\U0001F964\u26A1", 80 ],
    ["Matcha",     "\U0001F375", 35 ],
    ["Cola",       "\U0001F964", 34 ],
    ["Doppel",     "\u2615", 126],
]

# ── Daten laden und speichern ──────────────────────────────────
def logs_laden():
    if not os.path.exists(LOG_DATEI):
        return []
    with open(LOG_DATEI, "r") as f:
        return json.load(f)

def logs_speichern(logs):
    with open(LOG_DATEI, "w") as f:
        json.dump(logs, f)

# ── Berechnungen ───────────────────────────────────────────────
def heute():
    return date.today().isoformat()

def aktive_mg(logs):
    total = 0
    jetzt = datetime.now()
    for log in logs:
        if log[0] != heute():
            continue
        aufgenommen = datetime.fromisoformat(log[1])
        stunden_her = (jetzt - aufgenommen).total_seconds() / 3600
        total += log[2] * math.pow(0.5, stunden_her / HALBWERTSZEIT)
    return round(total, 1)

def koffeinfrei_um(aktiv):
    if aktiv < 5:
        return None
    stunden = HALBWERTSZEIT * math.log2(aktiv / 5)
    return (datetime.now() + timedelta(hours=stunden)).strftime("%H:%M")

# ── Log hinzufügen / löschen ───────────────────────────────────
def log_hinzufuegen(name, emoji, mg):
    logs = logs_laden()
    # Jeder Log: [datum, zeitstempel, mg, name, emoji]
    logs.insert(0, [heute(), datetime.now().isoformat(), mg, name, emoji])
    logs_speichern(logs)

def log_loeschen(index):
    logs = logs_laden()
    logs.pop(index)
    logs_speichern(logs)

def alle_loeschen():
    logs = logs_laden()
    logs_speichern([log for log in logs if log[0] != heute()])

# ── Streamlit Seite ────────────────────────────────────────────
st.set_page_config(page_title="Stimlog", page_icon="☕")

logs       = logs_laden()
aktiv      = aktive_mg(logs)
frei       = koffeinfrei_um(aktiv)
heute_logs = [log for log in logs if log[0] == heute()]
total      = sum(log[2] for log in heute_logs)

st.markdown("<p style='font-family:monospace;color:#4a6080;letter-spacing:0.2em'>STIMLOG</p>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
col1.metric("Heute total", f"{total} mg")
col2.metric("Noch aktiv", f"{round(aktiv / total * 100) if total > 0 else 0}%")

if total > TAGESLIMIT:
    st.warning("⚠️ Tageslimit überschritten!")

st.divider()

namen = [f"{g[1]} {g[0]} ({g[2]} mg)" for g in getraenke]
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
    else:             farbe = "#ff4f4f"

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
