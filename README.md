# 🚇 OneJourney AI — Unified Mobility Super App

**Team:** Night Wolf 🐺 | **Participant:** Deepak Tandale  
**Institute:** SSIEMS Parbhani • Dr. BATU Lonere  
**Hackathon:** OneJourney Mobility Hackathon 2026

---

## 🚀 Run in 3 Steps

```bash
# 1. Install
pip install -r requirements.txt

# 2. Add API Key (optional — app works without it too!)
set ANTHROPIC_API_KEY=your_key_here   # Windows
export ANTHROPIC_API_KEY=your_key_here  # Mac/Linux

# 3. Run
streamlit run app.py
```
Open → **http://localhost:8501** 🎉

---

## ✨ Features

| Feature | Description | Intelligence |
|---|---|---|
| 🗺️ Route Planner | Real geocoding via OpenStreetMap | Dynamic distance-based fares & times |
| 🤖 AI Assistant | Hindi/English/Marathi queries | Claude AI + smart fallback |
| 🛡️ Safety Score | Per-route safety ranking | Time-of-day aware |
| 🌿 Carbon Score | Eco footprint per mode | CO₂ per km calculation |
| 🔔 Live Alerts | Traffic/Metro/Weather alerts | SQLite driven |
| 📊 Dashboard | Trip history & savings | Persistent DB |

## 🛠️ Tech Stack
- **Frontend:** Streamlit (Python)
- **AI:** Claude AI API (Anthropic) + Smart Fallback
- **Maps:** Folium + OpenStreetMap (Nominatim geocoding — FREE)
- **Distance:** Haversine formula (real-world calculation)
- **Database:** SQLite (persistent trip history)
- **Alerts:** SQLite seed data

## 📂 Structure
```
onejourney_app/
├── app.py            ← Main app (all features)
├── requirements.txt  ← Dependencies
├── onejourney.db     ← Auto-created on first run
└── README.md         ← This file
```

*"One Search. Every Journey."* 🚇
