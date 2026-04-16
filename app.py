"""
evento/app.py — Streamlit event info & food request app
"""

import re
import random
import string
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
import tomllib
import pandas as pd
from supabase import create_client, Client

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent
CONFIG_PATH = ROOT / "config.toml"

# ── Config ────────────────────────────────────────────────────────────────────
@st.cache_data
def load_config():
    with open(CONFIG_PATH, "rb") as f:
        return tomllib.load(f)

cfg = load_config()

# ── Supabase client ───────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

sb = get_supabase()

# ── Theme presets ─────────────────────────────────────────────────────────────
PRESETS = {
    "spring": {
        "bg":    "linear-gradient(135deg, #e8f4e8 0%, #d0eaf7 50%, #f5f9d0 100%)",
        "sun":   "rgba(255,240,80,0.55)",
        "blob1": "rgba(180,230,160,0.35)",
    },
    "summer": {
        "bg":    "linear-gradient(135deg, #fff8d6 0%, #ffe0a0 50%, #ffd0c0 100%)",
        "sun":   "rgba(255,220,50,0.7)",
        "blob1": "rgba(255,190,80,0.3)",
    },
    "autumn": {
        "bg":    "linear-gradient(135deg, #f5e8d0 0%, #e8d0a8 50%, #d4b080 100%)",
        "sun":   "rgba(220,140,40,0.5)",
        "blob1": "rgba(200,120,60,0.25)",
    },
    "night": {
        "bg":    "linear-gradient(135deg, #0d1b2a 0%, #1a2c44 50%, #0a1520 100%)",
        "sun":   "rgba(180,200,255,0.3)",
        "blob1": "rgba(80,120,200,0.2)",
    },
    "custom": {
        "bg":    cfg["theme"].get("bg_color", "#f0f4e8"),
        "sun":   "rgba(255,240,80,0.4)",
        "blob1": "rgba(180,210,160,0.3)",
    },
}

theme_key     = cfg["theme"].get("bg_style", "spring")
T             = PRESETS.get(theme_key, PRESETS["spring"])

c_modus       = cfg["theme"].get("card_modus_color",       "#c9a227")
c_locus       = cfg["theme"].get("card_locus_color",       "#4a8c40")
c_musica      = cfg["theme"].get("card_musica_color",      "#7c6c5a")
c_form        = cfg["theme"].get("card_form_color",        "#3a7ca8")
c_form_bg     = cfg["theme"].get("card_form_background",   "rgba(220,238,248,0.75)")

is_night      = theme_key == "night"
text_main     = "#403F4C"
text_muted    = "#8a8997"
card_bg_alpha = "rgba(20,35,55,0.85)" if is_night else "rgba(255,255,255,0.72)"

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{cfg['event']['title']} — {cfg['event']['subtitle']}",
    page_icon="🌿",
    layout="centered",
)

# ── Global CSS + Service Worker ───────────────────────────────────────────────
st.markdown(f"""
<script>
if ('serviceWorker' in navigator) {{
  navigator.serviceWorker.register('/app/static/sw.js', {{scope: '/'}})
    .catch(e => console.warn('SW:', e));
}}
</script>

<style>
  .stApp {{
    background: {T['bg']} !important;
    min-height: 100vh;
  }}

  * {{ color: #403F4C !important; }}

  #MainMenu, footer, header {{ visibility: hidden; }}
  .block-container {{ padding-top: 2rem !important; max-width: 680px !important; }}

  body, .stMarkdown, .stText, p, label {{
    font-family: 'Georgia', serif !important;
  }}

  .ev-card {{
    background: {card_bg_alpha};
    backdrop-filter: blur(8px);
    border-radius: 10px;
    padding: 1.4rem 1.7rem;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.4);
    border-left: 4px solid;
    box-shadow: 0 2px 16px rgba(0,0,0,0.06);
  }}
  .ev-card-tag {{
    font-size: 0.6rem; letter-spacing: 0.25em; text-transform: uppercase;
    opacity: 0.75; margin-bottom: 0.3rem; font-family: monospace !important;
  }}
  .ev-card-title {{ font-size: 1.3rem; font-style: italic; margin-bottom: 0.5rem; }}
  .ev-card-body  {{ font-size: 0.82rem; line-height: 1.75; opacity: 0.85; }}

  .ev-link {{
    display: inline-flex; align-items: center; gap: 0.4rem;
    margin-top: 0.8rem; padding: 0.45rem 0.9rem;
    border-radius: 5px; text-decoration: none;
    font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase;
    font-family: monospace !important; border: 1px solid; transition: opacity .2s;
  }}
  .ev-link:hover {{ opacity: 0.7; }}

  .ev-header {{ text-align: center; margin-bottom: 2rem; }}
  .ev-header-label {{
    font-size: 0.6rem; letter-spacing: 0.35em; text-transform: uppercase;
    color: {text_muted}; margin-bottom: 0.5rem; font-family: monospace !important;
  }}
  .ev-header-title {{
    font-size: clamp(3rem, 12vw, 4.5rem);
    font-family: Georgia, serif; font-weight: bold; line-height: 1;
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

  .stButton > button {{
    font-family: monospace !important; font-size: 0.7rem !important;
    letter-spacing: 0.1em; text-transform: uppercase;
    background-color: {c_form} !important;
    border-color: {c_form} !important;
    color: white !important;
  }}
  .stButton > button:hover {{ opacity: 0.85; }}

  .stTextInput input, .stTextArea textarea {{
    background: rgba(255,255,255,0.6) !important;
    border-radius: 5px !important;
    font-family: monospace !important; font-size: 0.8rem !important;
  }}

  .ev-footer-quote {{
    font-size: 0.65rem; line-height: 1.8; max-width: 480px;
    margin: 0 auto 1rem; opacity: 0.55; font-style: italic;
    text-align: center; font-family: Georgia, serif !important;
  }}
  .ev-footer-main {{
    font-size: 0.58rem; letter-spacing: 0.25em;
    text-transform: uppercase; font-family: monospace !important;
  }}
  .ev-footer {{
    text-align: center; margin-top: 2rem;
    font-size: 0.58rem; letter-spacing: 0.25em;
    text-transform: uppercase; font-family: monospace !important;
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


def md_to_html(text: str) -> str:
    """Convert **bold** and paragraph breaks to HTML."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text.strip())
    return text.replace("\n\n", "<br><br>")


# ── Supabase I/O ──────────────────────────────────────────────────────────────
def log_visit(session_id: str):
    try:
        sb.table("visits").insert({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session":   session_id,
        }).execute()
    except Exception:
        pass  # never crash the page over a visit log


def save_request(name: str, request: str):
    sb.table("requests").insert({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "name":      name,
        "request":   request,
    }).execute()


def load_requests() -> pd.DataFrame:
    res = sb.table("requests").select("*").order("timestamp").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["timestamp", "name", "request"])


def load_visits() -> pd.DataFrame:
    res = sb.table("visits").select("*").order("timestamp").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=["timestamp", "session"])


# ── Session init ──────────────────────────────────────────────────────────────
if "_sid" not in st.session_state:
    st.session_state["_sid"] = "".join(random.choices(string.ascii_lowercase, k=8))
    log_visit(st.session_state["_sid"])

# ── Query params: ?admin=1 ────────────────────────────────────────────────────
is_admin_page = st.query_params.get("admin", "") == "1"

# ══════════════════════════════════════════════════════════════════════════════
#  ADMIN VIEW
# ══════════════════════════════════════════════════════════════════════════════
if is_admin_page:
    admin_pw = cfg["admin"].get("password", "")

    if admin_pw:
        if not st.session_state.get("admin_ok", False):
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

    visits = load_visits()
    st.markdown(f"**Aperture pagina:** {len(visits)}")
    if not visits.empty:
        with st.expander("Dettaglio visite"):
            st.dataframe(visits, use_container_width=True)

    st.divider()

    reqs = load_requests()
    st.markdown(f"**Richieste alimentari ricevute:** {len(reqs)}")
    if reqs.empty:
        st.info("Nessuna richiesta ancora.")
    else:
        st.dataframe(reqs, use_container_width=True)
        st.download_button("⬇ Scarica CSV", reqs.to_csv(index=False).encode(), "richieste.csv", "text/csv")

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN PUBLIC VIEW
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div class="ev-header">
  <div class="ev-header-label">{cfg['event']['subtitle']}</div>
  <div class="ev-header-title">{cfg['event']['title']}<em>{cfg['event']['date']}</em></div>
  <div class="ev-header-sub">{cfg['event']['tagline']}</div>
</div>
<div class="ev-divider"></div>
""", unsafe_allow_html=True)

# ── I — MODUS ─────────────────────────────────────────────────────────────────
if cfg["modus"]["enabled"]:
    card("I", cfg["modus"]["label"], "Come funziona",
         md_to_html(cfg["modus"]["content"]), c_modus)

# ── II — LOCUS ────────────────────────────────────────────────────────────────
if cfg["locus"]["enabled"]:
    card("II", cfg["locus"]["label"], "Dove siamo",
         cfg["locus"]["content"], c_locus,
         extra=link_btn(cfg["locus"]["maps_url"], "Apri su Maps", "📍", c_locus))

# ── III — MUSICA ──────────────────────────────────────────────────────────────
if cfg["musica"]["enabled"]:
    card("III", cfg["musica"]["label"], "La playlist",
         cfg["musica"]["content"], c_musica,
         extra=link_btn(cfg["musica"]["spotify_url"], "Apri su Spotify", "🎵", c_musica))

# ── IV — FOOD REQUESTS ────────────────────────────────────────────────────────
st.markdown(f"""
<div class="ev-card" style="border-left-color:{c_form}; background:{c_form_bg}">
  <div class="ev-card-tag" style="color:{c_form}">IV — Richieste Alimentari</div>
  <div class="ev-card-title">Allergie, intolleranze o voglie specifiche?</div>
  <div class="ev-card-body">
    Porca m*donna ma faccelo sapere subito, lascia qui la tua richiesta.
  </div>
</div>
""", unsafe_allow_html=True)

with st.form("food_form", clear_on_submit=True):
    name    = st.text_input("Nome", placeholder="es. Giulia", max_chars=60)
    request = st.text_area(
        "Richiesta",
        placeholder="es. sono celiaca, evito le noci e la musica reggaeton, consumo solo microplastiche, no piombo o asbesto…",
        height=100,
    )
    submitted = st.form_submit_button("Invia richiesta")

if submitted:
    if request.strip():
        save_request(name.strip() or "Anonima", request.strip())
        st.success("✓ Richiesta salvata! L'organizzazione ne terrà conto.")
    else:
        st.warning("Scrivi la tua richiesta prima di inviare.")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="ev-footer">
  <div class="ev-footer-quote">
    ..la-la merda della maiala degli stronzoli 
    ne culo de le poppe piene di piscio co-con gli
    stronzoli che escan dalle poppe de
    budelli de-de vitelli co-co-con-con le cosce della
    sposa che gli sorte fra-fra le cosce troppe
    troppi seghe dentro ai cazzo troppi troppi
    troppe cazzi dentro ai culo
    che-che gli spuntano dalle cosce che-che gli
    tornan dalle gambe con la mamma ne' pompino
    della nonna che gli che gli schianta da-da
    dalle da-da i su corpo che gli-gli
    leccano la schiena
    poi poi gli sputano e leccano i
    groppone..
  </div>
  <div class="ev-footer-main">— ci vediamo il 26 —</div>
</div>
""", unsafe_allow_html=True)
