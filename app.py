"""
evento/app.py — Streamlit event info & food request app
"""

import streamlit as st
import tomllib
import pandas as pd
from pathlib import Path
from datetime import datetime
import hashlib

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent
CONFIG_PATH = ROOT / "config.toml"
DATA_PATH   = ROOT / "data" / "requests.csv"
LOG_PATH    = ROOT / "data" / "visits.csv"
SW_JS       = ROOT / "static" / "sw.js"

# ── Config ───────────────────────────────────────────────────────────────────
@st.cache_data
def load_config():
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)

cfg = load_config()

# ── Theme presets ─────────────────────────────────────────────────────────────
PRESETS = {
    "spring": {
        "bg":      "linear-gradient(135deg, #e8f4e8 0%, #d0eaf7 50%, #f5f9d0 100%)",
        "sun":     "rgba(255,240,80,0.55)",
        "blob1":   "rgba(180,230,160,0.35)",
        "blob2":   "rgba(200,230,255,0.4)",
    },
    "summer": {
        "bg":      "linear-gradient(135deg, #fff8d6 0%, #ffe0a0 50%, #ffd0c0 100%)",
        "sun":     "rgba(255,220,50,0.7)",
        "blob1":   "rgba(255,190,80,0.3)",
        "blob2":   "rgba(255,240,180,0.4)",
    },
    "autumn": {
        "bg":      "linear-gradient(135deg, #f5e8d0 0%, #e8d0a8 50%, #d4b080 100%)",
        "sun":     "rgba(220,140,40,0.5)",
        "blob1":   "rgba(200,120,60,0.25)",
        "blob2":   "rgba(240,200,100,0.3)",
    },
    "night": {
        "bg":      "linear-gradient(135deg, #0d1b2a 0%, #1a2c44 50%, #0a1520 100%)",
        "sun":     "rgba(180,200,255,0.3)",
        "blob1":   "rgba(80,120,200,0.2)",
        "blob2":   "rgba(40,80,160,0.15)",
    },
    "custom": {
        "bg":      cfg["theme"].get("bg_color", "#f0f4e8"),
        "sun":     "rgba(255,240,80,0.4)",
        "blob1":   "rgba(180,210,160,0.3)",
        "blob2":   "rgba(200,220,255,0.3)",
    },
}

theme_key = cfg["theme"].get("bg_style", "spring")
T = PRESETS.get(theme_key, PRESETS["spring"])

c_modus  = cfg["theme"].get("card_modus_color",  "#c9a227")
c_locus  = cfg["theme"].get("card_locus_color",  "#4a8c40")
c_musica = cfg["theme"].get("card_musica_color", "#7c6c5a")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{cfg['event']['title']} — {cfg['event']['subtitle']}",
    page_icon="🌿",
    layout="centered",
)

# ── Inject service worker + global CSS ───────────────────────────────────────
is_night = theme_key == "night"
text_main   = "#e8f0ff" if is_night else "#2c3e1f"
text_muted  = "#8090b0" if is_night else "#5a7a4a"
card_bg_alpha = "rgba(20,35,55,0.85)" if is_night else "rgba(255,255,255,0.72)"

st.markdown(f"""
<script>
if ('serviceWorker' in navigator) {{
  navigator.serviceWorker.register('/app/static/sw.js', {{scope: '/'}})
    .catch(e => console.warn('SW:', e));
}}
</script>

<style>
  /* ── Page background ── */
  .stApp {{
    background: {T['bg']} !important;
    min-height: 100vh;
  }}

  /* floating sun blob */
  .stApp::before {{
    content: '';
    position: fixed;
    top: -80px; right: -80px;
    width: 260px; height: 260px;
    border-radius: 50%;
    background: radial-gradient(circle, {T['sun']} 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
    animation: sunPulse 7s ease-in-out infinite;
  }}
  .stApp::after {{
    content: '';
    position: fixed;
    bottom: -60px; left: -60px;
    width: 200px; height: 200px;
    border-radius: 50%;
    background: radial-gradient(circle, {T['blob1']} 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }}
  @keyframes sunPulse {{
    0%,100%{{transform:scale(1);opacity:.85}} 50%{{transform:scale(1.08);opacity:1}}
  }}

  /* ── Hide Streamlit chrome ── */
  #MainMenu, footer, header {{ visibility: hidden; }}
  .block-container {{ padding-top: 2rem !important; max-width: 680px !important; }}

  /* ── Typography ── */
  body, .stMarkdown, .stText, p, label {{
    color: {text_main} !important;
    font-family: 'Georgia', serif !important;
  }}

  /* ── Section card ── */
  .ev-card {{
    background: {card_bg_alpha};
    backdrop-filter: blur(8px);
    border-radius: 10px;
    padding: 1.4rem 1.7rem;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.4);
    border-left: 4px solid;
    box-shadow: 0 2px 16px rgba(0,0,0,0.06);
    position: relative;
  }}
  .ev-card-tag {{
    font-size: 0.6rem;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    opacity: 0.7;
    margin-bottom: 0.3rem;
    font-family: monospace !important;
  }}
  .ev-card-title {{
    font-size: 1.3rem;
    font-style: italic;
    margin-bottom: 0.5rem;
  }}
  .ev-card-body {{
    font-size: 0.82rem;
    line-height: 1.75;
    opacity: 0.85;
  }}

  /* ── Link button ── */
  .ev-link {{
    display: inline-flex; align-items: center; gap: 0.4rem;
    margin-top: 0.8rem; padding: 0.45rem 0.9rem;
    border-radius: 5px; text-decoration: none;
    font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase;
    font-family: monospace !important;
    border: 1px solid; transition: opacity .2s;
    color: inherit;
  }}
  .ev-link:hover {{ opacity: 0.7; }}

  /* ── Header ── */
  .ev-header {{ text-align: center; margin-bottom: 2rem; color: {text_main}; }}
  .ev-header-label {{
    font-size: 0.6rem; letter-spacing: 0.35em; text-transform: uppercase;
    color: {text_muted}; margin-bottom: 0.5rem; font-family: monospace !important;
  }}
  .ev-header-title {{
    font-size: clamp(3rem, 12vw, 4.5rem);
    font-family: Georgia, serif; font-weight: bold; line-height: 1;
    color: {text_main};
  }}
  .ev-header-title em {{
    display: block; font-size: 0.48em; font-weight: normal;
    color: {text_muted}; letter-spacing: 0.06em;
  }}
  .ev-header-sub {{
    margin-top: 0.7rem; font-size: 0.62rem; letter-spacing: 0.2em;
    text-transform: uppercase; color: {text_muted}; font-family: monospace !important;
  }}
  .ev-divider {{
    height: 1px; margin: 0 auto 1.8rem;
    background: linear-gradient(to right, transparent, {text_muted}, transparent);
    opacity: 0.35;
  }}

  /* ── Form ── */
  .stTextInput input, .stTextArea textarea {{
    background: rgba(255,255,255,0.6) !important;
    border-radius: 5px !important;
    font-family: monospace !important;
    font-size: 0.8rem !important;
  }}
  .stButton > button {{
    font-family: monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }}

  /* ── Admin table ── */
  .ev-admin-table {{ font-size: 0.78rem; }}

  /* ── Footer ── */
  .ev-footer {{
    text-align: center; margin-top: 2rem;
    font-size: 0.58rem; letter-spacing: 0.25em;
    text-transform: uppercase; color: {text_muted};
    font-family: monospace !important;
  }}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def card(num: str, label: str, title: str, body: str, color: str, extra: str = ""):
    st.markdown(f"""
    <div class="ev-card" style="border-left-color:{color}">
      <div class="ev-card-tag" style="color:{color}">{num} — {label}</div>
      <div class="ev-card-title">{title}</div>
      <div class="ev-card-body">{body}</div>
      {extra}
    </div>
    """, unsafe_allow_html=True)


def link_btn(href: str, label: str, icon: str, color: str) -> str:
    return (
        f'<a class="ev-link" href="{href}" target="_blank" rel="noopener" '
        f'style="color:{color};border-color:{color};">'
        f'{icon} {label}</a>'
    )


def log_visit():
    """Append a visit row (IP hash + timestamp). Silently skip on error."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().isoformat(timespec="seconds")
        # anonymise: just a counter entry, no real IP available in Streamlit
        row = pd.DataFrame([{"timestamp": ts, "session": st.session_state.get("_sid", "?")}])
        if LOG_PATH.exists():
            row.to_csv(LOG_PATH, mode="a", header=False, index=False)
        else:
            row.to_csv(LOG_PATH, index=False)
    except Exception:
        pass


def save_request(name: str, request: str):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat(timespec="seconds")
    row = pd.DataFrame([{"timestamp": ts, "name": name, "request": request}])
    if DATA_PATH.exists():
        row.to_csv(DATA_PATH, mode="a", header=False, index=False)
    else:
        row.to_csv(DATA_PATH, index=False)


def load_requests() -> pd.DataFrame:
    if DATA_PATH.exists():
        return pd.read_csv(DATA_PATH)
    return pd.DataFrame(columns=["timestamp", "name", "request"])


def load_visits() -> pd.DataFrame:
    if LOG_PATH.exists():
        return pd.read_csv(LOG_PATH)
    return pd.DataFrame(columns=["timestamp", "session"])


# ── Session init ──────────────────────────────────────────────────────────────
if "_sid" not in st.session_state:
    import random, string
    st.session_state["_sid"] = "".join(random.choices(string.ascii_lowercase, k=8))
    log_visit()

# ── Query params: ?admin=1 ────────────────────────────────────────────────────
params = st.query_params
is_admin_page = params.get("admin", "") == "1"

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN VIEW
# ══════════════════════════════════════════════════════════════════════════════
if is_admin_page:
    admin_pw = cfg["admin"].get("password", "")

    if admin_pw:
        if "admin_ok" not in st.session_state:
            st.session_state["admin_ok"] = False

        if not st.session_state["admin_ok"]:
            st.markdown("### 🔒 Area organizzatore")
            pw = st.text_input("Password", type="password")
            if st.button("Accedi"):
                if pw == admin_pw:
                    st.session_state["admin_ok"] = True
                    st.rerun()
                else:
                    st.error("Password errata.")
            st.stop()

    st.markdown("## 📋 Dashboard organizzatore")

    # Visits
    visits = load_visits()
    st.markdown(f"**Aperture pagina:** {len(visits)}")
    if not visits.empty:
        with st.expander("Dettaglio visite"):
            st.dataframe(visits, use_container_width=True)

    st.divider()

    # Food requests
    reqs = load_requests()
    st.markdown(f"**Richieste alimentari ricevute:** {len(reqs)}")
    if reqs.empty:
        st.info("Nessuna richiesta ancora.")
    else:
        st.dataframe(reqs, use_container_width=True)
        csv = reqs.to_csv(index=False).encode()
        st.download_button("⬇ Scarica CSV", csv, "richieste.csv", "text/csv")

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN PUBLIC VIEW
# ══════════════════════════════════════════════════════════════════════════════

# Header
st.markdown(f"""
<div class="ev-header">
  <div class="ev-header-label">{cfg['event']['subtitle']}</div>
  <div class="ev-header-title">{cfg['event']['title']}<em>26 Aprile</em></div>
  <div class="ev-header-sub">{cfg['event']['tagline']}</div>
</div>
<div class="ev-divider"></div>
""", unsafe_allow_html=True)


# ── I — MODUS ─────────────────────────────────────────────────────────────────
if cfg["modus"]["enabled"]:
    body = cfg["modus"]["content"].strip().replace("\n\n", "<br><br>").replace("**", "<strong>").replace("**", "</strong>")
    # simple bold: swap pairs
    import re
    body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', cfg["modus"]["content"].strip())
    body = body.replace("\n\n", "<br><br>")
    card("I", cfg["modus"]["label"], "Come funziona", body, c_modus)

# ── II — LOCUS ────────────────────────────────────────────────────────────────
if cfg["locus"]["enabled"]:
    btn = link_btn(cfg["locus"]["maps_url"], "Apri su Maps", "📍", c_locus)
    card("II", cfg["locus"]["label"], "Dove siamo",
         cfg["locus"]["content"], c_locus, extra=btn)

# ── III — MUSICA ──────────────────────────────────────────────────────────────
if cfg["musica"]["enabled"]:
    btn = link_btn(cfg["musica"]["spotify_url"], "Apri su Spotify", "🎵", c_musica)
    card("III", cfg["musica"]["label"], "La playlist",
         cfg["musica"]["content"], c_musica, extra=btn)

# ── IV — FOOD REQUESTS ────────────────────────────────────────────────────────
st.markdown(f"""
<div class="ev-card" style="border-left-color:#3a7ca8;background:rgba(220,238,248,0.75)">
  <div class="ev-card-tag" style="color:#3a7ca8">IV — Richieste Alimentari</div>
  <div class="ev-card-title">Cosa vorresti mangiare?</div>
  <div class="ev-card-body">
    Allergie, intolleranze o voglie specifiche? Lascia qui la tua richiesta.
  </div>
</div>
""", unsafe_allow_html=True)

with st.form("food_form", clear_on_submit=True):
    name    = st.text_input("Nome", placeholder="es. Giulia", max_chars=60)
    request = st.text_area("Richiesta", placeholder="es. sono celiaca, evito le noci, vorrei qualcosa di vegetariano…", height=100)
    submitted = st.form_submit_button("Invia richiesta")

if submitted:
    if request.strip():
        save_request(name.strip() or "Anonima", request.strip())
        st.success("✓ Richiesta salvata! L'organizzazione ne terrà conto.")
    else:
        st.warning("Scrivi la tua richiesta prima di inviare.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown('<div class="ev-footer">— ci vediamo il 26 —</div>', unsafe_allow_html=True)
