# 🚇 OneJourney AI — Unified Mobility Super App
**Phase 1: Mumbai + Pune + Maharashtra**

**Team:** Night Wolf 🐺 | **Participant:** Deepak Tandale
**Institute:** SSIEMS Parbhani • Dr. BATU Lonere
**Hackathon:** OneJourney Mobility Hackathon 2026

---

## 🚀 Run in 3 Steps

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here   # optional
streamlit run app.py
```
Open → **http://localhost:8501** 🎉

---

## 🖥️ UI Features (Matching Reference Design)
- **Navbar** — Logo, weather, notifications, user profile
- **Sidebar** — Navigation + Impact stats + Night Wolf branding
- **Left Panel** — Journey form with quick stats
- **Center Panel** — Filter tabs + Route cards + Live alerts
- **Right Panel** — Folium map + AI chat assistant

## 🗺️ Coverage
- **Mumbai** — Local Train (3 lines), Metro (Line 1, 2A), BEST Bus, Auto, Cab
- **Pune** — Pune Metro (Purple + Aqua), PMC Bus, Auto, Cab
- **Maharashtra** — 35+ cities including Parbhani, Nanded, Nashik, Aurangabad, Nagpur
- **Intercity** — Real MSRTC + Indian Railways fares
- **All India** — OpenStreetMap geocoding fallback

## 📂 Structure
```
onejourney_app/
├── app.py              ← Main app (full UI)
├── requirements.txt
├── README.md
├── onejourney.db       ← Auto-created on first run
└── data/
    ├── __init__.py
    └── cities.py       ← 70+ cities, real transport data
```

*"One Search. Every Journey."* 🚇🐺
