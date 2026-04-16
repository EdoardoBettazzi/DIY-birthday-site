# Evento — Streamlit Event Info App

Self-contained event info page with food request logging, visit tracking, and offline fallback.

## Structure

```
evento/
├── app.py                  # Main Streamlit app
├── config.toml             # ← Edit this to customise content & theme
├── requirements.txt
├── data/                   # Auto-created; stores requests.csv and visits.csv
├── static/
│   ├── offline.html        # Served when there's no connection (via Service Worker)
│   └── sw.js               # Service Worker — registers on first load
└── .streamlit/
    └── config.toml         # Streamlit UI theme
```

## Customisation

**All content and theme lives in `config.toml`** — you should never need to touch `app.py` for routine changes.

- Edit section text, links, icons under `[modus]`, `[locus]`, `[musica]`
- Change `bg_style` under `[theme]` to one of: `spring`, `summer`, `autumn`, `night`, `custom`
- Set card accent colors with `card_modus_color`, `card_locus_color`, `card_musica_color`
- Set the admin dashboard password under `[admin]`

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud

1. Push this folder to a **public GitHub repo**
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app
3. Point to your repo, branch `main`, file `app.py`
4. Done — you get a free HTTPS URL to share

> **Note on data persistence:** Streamlit Community Cloud restarts apps periodically, which wipes `data/`. For a one-day event this is fine. For permanent storage, either commit the CSVs to git, or swap the CSV writes in `app.py` for a free [Supabase](https://supabase.com) or [PlanetScale](https://planetscale.com) DB (a few lines of change).

## Admin dashboard

Visit `your-app-url/?admin=1` to see:
- Total page opens (visit log)
- All food requests in a table
- CSV download of requests

Password is set in `config.toml` under `[admin] password`.

## Offline behaviour

On first load (requires connection), the browser installs a Service Worker that caches `offline.html`. If a guest later opens the link with no/slow connection, they see the offline shell with:
- All three info sections (Modus, Locus, Musica) fully readable
- Maps and Spotify links still clickable (open if connection recovers)
- A note that food requests require connection
