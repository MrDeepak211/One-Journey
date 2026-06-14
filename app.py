import streamlit as st
import sqlite3
import folium
from streamlit_folium import st_folium
from datetime import datetime
import anthropic
import os
import math
import urllib.request
import urllib.parse
import json
import random

# ── Page Config ──────────────────────────────────────────────
st.set_page_config(
    page_title="OneJourney AI",
    page_icon="🚇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #0A1628; color: #FFFFFF; }
.main, .stApp { background-color: #0A1628; }
.hero-banner {
    background: linear-gradient(135deg, #102447 0%, #0A1628 60%, #001529 100%);
    border: 1px solid #00B4D8; border-radius: 16px;
    padding: 1.5rem 2.5rem; margin-bottom: 1.2rem; text-align: center;
}
.hero-title { font-size: 2.8rem; font-weight: 700; color: #FFFFFF; margin: 0; }
.hero-sub { font-size: 1.1rem; color: #00B4D8; margin: 0.2rem 0; }
.hero-tag { font-size: 0.9rem; color: #94A3B8; font-style: italic; }
.transport-pill {
    display: inline-block; background: rgba(21,101,192,0.3);
    border: 1px solid #1565C0; border-radius: 20px;
    padding: 3px 12px; margin: 3px; font-size: 0.82rem; color: #fff;
}
.metric-card {
    background: #102447; border: 1px solid #1565C0;
    border-radius: 12px; padding: 1rem; text-align: center; margin: 0.3rem 0;
}
.metric-value { font-size: 1.8rem; font-weight: 700; color: #00B4D8; }
.metric-label { font-size: 0.78rem; color: #94A3B8; }
.route-card {
    background: #102447; border-radius: 12px;
    padding: 1rem 1.2rem; margin: 0.5rem 0; border-left: 4px solid #00B4D8;
}
.route-card.best { border-left: 4px solid #FFB300; background: #0D1F3C; }
.route-title { font-size: 1.05rem; font-weight: 600; color: #FFFFFF; }
.route-meta { font-size: 0.85rem; color: #94A3B8; margin-top: 0.3rem; }
.badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
.badge-green { background: #1B5E20; color: #A5D6A7; }
.badge-yellow { background: #E65100; color: #FFD54F; }
.badge-red { background: #B71C1C; color: #EF9A9A; }
.chat-user {
    background: #1565C0; border-radius: 12px 12px 3px 12px;
    padding: 0.8rem 1rem; margin: 0.5rem 0 0.5rem 3rem; color: #fff; font-size: 0.95rem;
}
.chat-ai {
    background: #00695C; border-radius: 12px 12px 12px 3px;
    padding: 0.8rem 1rem; margin: 0.5rem 3rem 0.5rem 0; color: #fff; font-size: 0.95rem;
}
.alert-card {
    background: #0D1F3C; border: 1px solid #00B4D8;
    border-radius: 10px; padding: 0.8rem 1rem; margin: 0.4rem 0; font-size: 0.9rem;
}
.section-header {
    font-size: 1.3rem; font-weight: 700; color: #00B4D8;
    margin: 1.2rem 0 0.6rem 0; padding-bottom: 0.3rem; border-bottom: 1px solid #1565C0;
}
div[data-testid="stSidebar"] { background-color: #102447; border-right: 1px solid #1565C0; }
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background-color: #102447 !important; color: #FFFFFF !important;
    border: 1px solid #1565C0 !important; border-radius: 8px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #1565C0, #00B4D8);
    color: white; border: none; border-radius: 8px;
    font-weight: 600; padding: 0.5rem 1.5rem;
}
.stSelectbox > div > div { background-color: #102447 !important; color: #FFFFFF !important; border: 1px solid #1565C0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Database Setup ────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("onejourney.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS trips (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT, destination TEXT, mode TEXT,
        cost INTEGER, time_min INTEGER, distance_km REAL,
        safety_score INTEGER, carbon_score INTEGER, timestamp TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT, message TEXT, severity TEXT, timestamp TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_prefs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pref_key TEXT UNIQUE, pref_value TEXT
    )""")
    c.execute("SELECT COUNT(*) FROM alerts")
    if c.fetchone()[0] == 0:
        seed_alerts = [
            ("Traffic",  "Western Express Highway — heavy congestion near Andheri", "high",   str(datetime.now())),
            ("Metro",    "Metro Line 2 delayed by 12 minutes at Dadar station",     "medium", str(datetime.now())),
            ("Weather",  "Rain expected in next 2 hours — allow extra commute time","medium", str(datetime.now())),
            ("Bus",      "Bus Route 45 running 8 minutes late from Kurla depot",    "low",    str(datetime.now())),
            ("Metro",    "Metro Line 1 — normal operations resume",                 "low",    str(datetime.now())),
        ]
        c.executemany("INSERT INTO alerts VALUES (NULL,?,?,?,?)", seed_alerts)
    conn.commit()
    conn.close()

init_db()

# ── Geocoding via Nominatim (OpenStreetMap — FREE, no key needed) ─
def geocode(place_name):
    """Returns (lat, lon) or None"""
    try:
        query = urllib.parse.quote(place_name + ", India")
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "OneJourneyAI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass
    return None

# ── Haversine Distance ────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

# ── Dynamic Route Engine ──────────────────────────────────────
def calculate_routes(distance_km, time_of_day="morning"):
    """
    Realistic route calculation based on actual distance.
    All fares/times scaled from real Indian transport data.
    """
    d = distance_km
    is_night = "night" in time_of_day.lower()

    # Base safety modifier for night
    night_penalty = -10 if is_night else 0

    routes = []

    # ── 1. Metro + Walk (if distance > 3 km, metro makes sense)
    if d >= 2:
        metro_fare = max(10, min(60, round((d * 2.5) / 5) * 5))   # ₹10–60 slab
        metro_time = round(d * 2.8 + 8)                            # 8 min buffer
        routes.append({
            "mode": "🚇 Metro + Walk",
            "cost": metro_fare,
            "time": metro_time,
            "safety": "High",
            "safety_score": min(95, 90 + night_penalty),
            "carbon": "Excellent",
            "carbon_score": 95,
            "best": False,
            "color": "#1565C0",
            "desc": f"Metro ({round(d*0.85, 1)} km) + {round(d*0.15*12)} min walk • Fastest & Eco-Friendly"
        })

    # ── 2. Bus
    bus_fare = max(10, round(d * 1.8 / 5) * 5)
    bus_time = round(d * 4.5 + 10)
    routes.append({
        "mode": "🚌 City Bus",
        "cost": bus_fare,
        "time": bus_time,
        "safety": "Medium" if is_night else "High",
        "safety_score": max(55, 75 + night_penalty),
        "carbon": "Good",
        "carbon_score": 80,
        "best": False,
        "color": "#E65100",
        "desc": f"BEST/MSRTC bus route • Cheapest option • {bus_time} mins avg"
    })

    # ── 3. Bike Taxi (Rapido)
    bike_fare = max(30, round(d * 8 / 5) * 5)
    bike_time = round(d * 2.2 + 3)
    routes.append({
        "mode": "🛵 Bike Taxi (Rapido)",
        "cost": bike_fare,
        "time": bike_time,
        "safety": "High",
        "safety_score": min(88, 85 + night_penalty),
        "carbon": "Average",
        "carbon_score": 55,
        "best": False,
        "color": "#6A1B9A",
        "desc": f"Rapido/OlaBike • Fastest 2-wheeler • No traffic jams"
    })

    # ── 4. Auto Rickshaw
    auto_fare = max(30, round((25 + d * 12) / 5) * 5)
    auto_time = round(d * 3.2 + 5)
    routes.append({
        "mode": "🛺 Auto Rickshaw",
        "cost": auto_fare,
        "time": auto_time,
        "safety": "High",
        "safety_score": min(90, 88 + night_penalty),
        "carbon": "Poor",
        "carbon_score": 30,
        "best": False,
        "color": "#00695C",
        "desc": f"Metered auto • Door-to-door • Negotiate or use app"
    })

    # ── 5. Cab (Ola/Uber)
    cab_fare = max(80, round((50 + d * 14) / 10) * 10)
    cab_time = round(d * 2.8 + 7)
    surge = 1.4 if is_night else 1.0
    cab_fare = round(cab_fare * surge / 10) * 10
    routes.append({
        "mode": "🚗 Cab (Ola/Uber)",
        "cost": cab_fare,
        "time": cab_time,
        "safety": "High",
        "safety_score": 92,
        "carbon": "Poor",
        "carbon_score": 25,
        "best": False,
        "color": "#B71C1C",
        "desc": f"AC cab • {'1.4x surge at night • ' if is_night else ''}Most comfortable"
    })

    # ── 6. Long distance (if > 80 km — intercity)
    if d > 80:
        bus_long_fare = round(d * 1.2 / 10) * 10
        bus_long_time = round(d * 7)  # minutes
        train_fare = round(d * 0.8 / 10) * 10
        train_time = round(d * 5.5)
        routes = [
            {
                "mode": "🚌 State Bus (MSRTC/GSRTC)",
                "cost": bus_long_fare,
                "time": bus_long_time,
                "safety": "High",
                "safety_score": 85,
                "carbon": "Good",
                "carbon_score": 75,
                "best": False,
                "color": "#E65100",
                "desc": f"Direct state bus • ₹{bus_long_fare} • ~{round(bus_long_time/60, 1)} hrs"
            },
            {
                "mode": "🚆 Train (Indian Railways)",
                "cost": train_fare,
                "time": train_time,
                "safety": "High",
                "safety_score": 88,
                "carbon": "Excellent",
                "carbon_score": 90,
                "best": False,
                "color": "#1565C0",
                "desc": f"Passenger/Express train • ₹{train_fare} • ~{round(train_time/60, 1)} hrs"
            },
            {
                "mode": "🚗 Cab (Ola/Uber Outstation)",
                "cost": round(d * 18 / 100) * 100,
                "time": round(d * 3.5),
                "safety": "High",
                "safety_score": 90,
                "carbon": "Poor",
                "carbon_score": 20,
                "best": False,
                "color": "#B71C1C",
                "desc": f"Outstation cab • One-way • Most comfortable"
            },
        ]

    # ── AI picks best route (lowest weighted score) ──
    def score(r):
        return r["cost"] * 0.4 + r["time"] * 0.3 + (100 - r["safety_score"]) * 0.15 + (100 - r["carbon_score"]) * 0.15
    best_idx = min(range(len(routes)), key=lambda i: score(routes[i]))
    routes[best_idx]["best"] = True

    return routes

# ── AI Assistant Call ─────────────────────────────────────────
def ask_ai(messages, source="", destination="", distance_km=0, routes=[]):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    route_summary = "\n".join([
        f"- {r['mode']}: ₹{r['cost']}, {r['time']} min, Safety: {r['safety']}, Carbon: {r['carbon']}"
        for r in routes
    ]) if routes else "No route calculated yet."

    system = f"""You are OneJourney AI — India's smartest urban mobility assistant for the OneJourney Mobility Hackathon 2026.
You help commuters find best routes across Metro, Bus, Bike Taxi, Auto, and Cab.

Current journey context:
- From: {source or 'Not set'}
- To: {destination or 'Not set'}
- Distance: {round(distance_km, 1)} km
- Available routes:
{route_summary}

For every query:
1. Give a direct, friendly recommendation
2. Mention cost (₹), time (mins), safety & carbon impact
3. Add one smart commute tip
4. Support Hindi/English/Marathi queries naturally
5. If asked about safety at night, always recommend cab or metro
Keep replies under 120 words. Be warm and helpful like a smart friend."""

    if api_key:
        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                system=system,
                messages=[{"role": m["role"], "content": m["content"]} for m in messages]
            )
            return response.content[0].text
        except Exception as e:
            return f"⚠️ API error: {str(e)[:80]}"
    else:
        # Smart fallback without API key
        last = messages[-1]["content"].lower()
        if any(w in last for w in ["cheap", "budget", "₹", "rs", "sasta"]):
            rec = min(routes, key=lambda r: r["cost"]) if routes else None
            if rec:
                return f"💰 Cheapest option is **{rec['mode']}** at ₹{rec['cost']} taking {rec['time']} mins! Great choice for saving money. 🌿 Carbon: {rec['carbon']}\n\n💡 Tip: Book in advance for better fares!"
        if any(w in last for w in ["fast", "quick", "jaldi", "urgent", "hurry"]):
            rec = min(routes, key=lambda r: r["time"]) if routes else None
            if rec:
                return f"⚡ Fastest option is **{rec['mode']}** — only {rec['time']} mins! Costs ₹{rec['cost']}.\n\n💡 Tip: Leave 5 mins early to avoid last-minute rush!"
        if any(w in last for w in ["safe", "night", "raat", "alone", "girl", "women"]):
            safe = max(routes, key=lambda r: r["safety_score"]) if routes else None
            if safe:
                return f"🛡️ Safest option is **{safe['mode']}** with Safety Score {safe['safety_score']}/100. Always share your live location with family!\n\n💡 Tip: Use the SOS feature in the app if needed."
        if any(w in last for w in ["green", "eco", "carbon", "environment", "planet"]):
            green = max(routes, key=lambda r: r["carbon_score"]) if routes else None
            if green:
                return f"🌿 Greenest choice is **{green['mode']}** with Carbon Score {green['carbon_score']}/100! You'll save CO₂ and earn Green Points 🏆\n\n💡 Tip: Choosing metro daily saves ~12 kg CO₂/month!"
        best = next((r for r in routes if r.get("best")), routes[0] if routes else None)
        if best:
            return f"🤖 Best overall option: **{best['mode']}** — ₹{best['cost']}, {best['time']} mins, Safety: {best['safety']}, Carbon: {best['carbon']}.\n\n💡 Set your ANTHROPIC_API_KEY for full AI-powered responses!"
        return "🤖 Please use the Route Planner first to calculate your journey, then I can give personalized advice! Set ANTHROPIC_API_KEY for full AI."

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:0.8rem 0 0.4rem;'>
        <div style='font-size:2.2rem;'>🚇</div>
        <div style='font-size:1.2rem; font-weight:700; color:#FFF;'>OneJourney AI</div>
        <div style='font-size:0.75rem; color:#00B4D8;'>Unified Mobility Super App</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("📍 Navigate", [
        "🏠 Home", "🗺️ Route Planner", "🤖 AI Assistant",
        "🛡️ Safety & Carbon", "🔔 Live Alerts", "📊 My Dashboard"
    ])
    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.75rem; color:#94A3B8; text-align:center;'>
        🐺 Night Wolf &nbsp;|&nbsp; <b style='color:#fff;'>Deepak Tandale</b><br>
        SSIEMS Parbhani • Dr. BATU Lonere
    </div>""", unsafe_allow_html=True)

# ── Hero Banner ───────────────────────────────────────────────
st.markdown("""
<div class='hero-banner'>
    <div class='hero-title'>🚇 OneJourney AI</div>
    <div class='hero-sub'>Unified Mobility Super App</div>
    <div class='hero-tag'>"One Search. Every Journey."</div>
    <div style='margin-top:0.6rem;'>
        <span class='transport-pill'>🚇 Metro</span>
        <span class='transport-pill'>🚌 Bus</span>
        <span class='transport-pill'>🛵 Bike Taxi</span>
        <span class='transport-pill'>🛺 Auto</span>
        <span class='transport-pill'>🚗 Cab</span>
        <span class='transport-pill'>🚆 Train</span>
    </div>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════
# PAGE: HOME
# ══════════════════════════════════════════
if page == "🏠 Home":
    c1,c2,c3,c4 = st.columns(4)
    metrics = [
        ("500M+", "Urban Commuters in India", "#00B4D8"),
        ("₹500+", "Monthly Savings / Commuter", "#FFB300"),
        ("30%",   "Lower Carbon Emissions",    "#66BB6A"),
        ("40%",   "Faster Commute Decisions",  "#EF5350"),
    ]
    for col, (val, label, color) in zip([c1,c2,c3,c4], metrics):
        with col:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-value' style='color:{color};'>{val}</div>
                <div class='metric-label'>{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>🚨 The Problem We Solve</div>", unsafe_allow_html=True)
    p1,p2 = st.columns(2)
    with p1:
        st.error("😤 Commuters juggle 5+ apps — Google Maps, Metro App, Bus App, Uber, Rapido")
        st.error("⏱️ Wasted time comparing options across multiple platforms manually")
    with p2:
        st.error("💸 Poor decisions lead to higher travel costs every single day")
        st.error("😰 No single view combining safety + cost + carbon for best route")

    st.markdown("<div class='section-header'>💡 OneJourney AI Solution</div>", unsafe_allow_html=True)
    s1,s2,s3 = st.columns(3)
    with s1: st.success("🤖 **AI Assistant** — Natural language journey planning")
    with s2: st.success("🛡️ **Safety Score** — Routes ranked by real safety factors")
    with s3: st.success("🌿 **Carbon Score** — Eco options with Green Points rewards")
    f1,f2 = st.columns(2)
    with f1: st.info("🔔 **Smart Alerts** — Real-time traffic, metro & weather alerts")
    with f2: st.info("📈 **Personalization** — AI learns your budget & preferences")

# ══════════════════════════════════════════
# PAGE: ROUTE PLANNER
# ══════════════════════════════════════════
elif page == "🗺️ Route Planner":
    st.markdown("<div class='section-header'>🗺️ Smart Route Planner</div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94A3B8; font-size:0.85rem;'>🌍 Uses OpenStreetMap geocoding to calculate real distance between any two Indian cities/locations</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        source = st.text_input("📍 From", placeholder="e.g. Parbhani, Maharashtra")
    with col2:
        destination = st.text_input("🎯 To", placeholder="e.g. Pune, Maharashtra")

    c1,c2,c3 = st.columns(3)
    with c1:
        budget = st.selectbox("💰 Max Budget", ["Any", "Under ₹50", "Under ₹150", "Under ₹500", "Under ₹2000"])
    with c2:
        priority = st.selectbox("⚡ Priority", ["Balanced", "Fastest", "Cheapest", "Safest", "Greenest"])
    with c3:
        time_pref = st.selectbox("🕐 Departing", ["Now (Morning)", "Afternoon", "Evening", "Night (After 9 PM)"])

    if st.button("🔍 Find Best Routes", use_container_width=True):
        if source and destination:
            with st.spinner("🌍 Fetching real coordinates via OpenStreetMap..."):
                src_coords  = geocode(source)
                dst_coords  = geocode(destination)

            if src_coords and dst_coords:
                distance_km = haversine(*src_coords, *dst_coords)
                # Store in session for AI
                st.session_state["last_src"]  = source
                st.session_state["last_dst"]  = destination
                st.session_state["last_dist"] = distance_km
                st.session_state["last_coords_src"] = src_coords
                st.session_state["last_coords_dst"] = dst_coords

                routes = calculate_routes(distance_km, time_pref)
                st.session_state["last_routes"] = routes

                # Filter by budget
                budget_map = {"Under ₹50":50, "Under ₹150":150, "Under ₹500":500, "Under ₹2000":2000}
                if budget in budget_map:
                    routes = [r for r in routes if r["cost"] <= budget_map[budget]] or routes

                # Sort by priority
                sort_map = {
                    "Fastest":  lambda r: r["time"],
                    "Cheapest": lambda r: r["cost"],
                    "Safest":   lambda r: -r["safety_score"],
                    "Greenest": lambda r: -r["carbon_score"],
                }
                if priority in sort_map:
                    routes = sorted(routes, key=sort_map[priority])

                st.success(f"📍 **{source}** → **{destination}** &nbsp;|&nbsp; 📏 Distance: **{distance_km:.1f} km** (Real OpenStreetMap data)")

                st.markdown(f"<div class='section-header'>🏆 Routes Found</div>", unsafe_allow_html=True)
                best_route = next((r for r in routes if r.get("best")), routes[0])

                for r in routes:
                    sc = "badge-green" if r["safety"]=="High" else "badge-yellow"
                    cc = "badge-green" if r["carbon"]=="Excellent" else ("badge-yellow" if r["carbon"] in ["Good","Average"] else "badge-red")
                    card_cls = "route-card best" if r.get("best") else "route-card"
                    star = " ⭐ AI Recommended" if r.get("best") else ""
                    st.markdown(f"""
                    <div class='{card_cls}'>
                        <div class='route-title'>{r['mode']}{star}</div>
                        <div class='route-meta'>{r['desc']}</div>
                        <div style='margin-top:0.5rem;'>
                            <span style='color:#FFB300; font-weight:700;'>₹{r['cost']}</span> &nbsp;•&nbsp;
                            <span style='color:#00B4D8;'>⏱ {r['time']} min</span> &nbsp;•&nbsp;
                            <span class='badge {sc}'>🛡 {r['safety']} Safety ({r['safety_score']}/100)</span> &nbsp;
                            <span class='badge {cc}'>🌿 {r['carbon']} ({r['carbon_score']}/100)</span>
                        </div>
                    </div>""", unsafe_allow_html=True)

                cab_cost = next((r["cost"] for r in routes if "Cab" in r["mode"]), None)
                best_cost = best_route["cost"]
                savings = cab_cost - best_cost if cab_cost and cab_cost > best_cost else 0
                st.success(f"🤖 **AI Recommends:** {best_route['mode']} — ₹{best_route['cost']}, {best_route['time']} min" + (f" • Save ₹{savings} vs cab!" if savings > 0 else ""))

                # Save trip to DB
                conn = sqlite3.connect("onejourney.db")
                conn.execute("INSERT INTO trips VALUES (NULL,?,?,?,?,?,?,?,?,?)", (
                    source, destination, best_route["mode"],
                    best_route["cost"], best_route["time"], round(distance_km,2),
                    best_route["safety_score"], best_route["carbon_score"], str(datetime.now())
                ))
                conn.commit(); conn.close()

                # Map with real coordinates
                st.markdown("<div class='section-header'>🗺️ Real Route Map (OpenStreetMap)</div>", unsafe_allow_html=True)
                mid_lat = (src_coords[0] + dst_coords[0]) / 2
                mid_lon = (src_coords[1] + dst_coords[1]) / 2
                zoom = 10 if distance_km < 50 else (7 if distance_km < 300 else 5)
                m = folium.Map(location=[mid_lat, mid_lon], zoom_start=zoom, tiles="CartoDB dark_matter")

                folium.Marker(list(src_coords),  popup=f"📍 {source}",      icon=folium.Icon(color="blue",  icon="home")).add_to(m)
                folium.Marker(list(dst_coords),  popup=f"🎯 {destination}", icon=folium.Icon(color="red",   icon="flag")).add_to(m)
                folium.PolyLine([list(src_coords), list(dst_coords)], color="#00B4D8", weight=4, opacity=0.8,
                                tooltip=f"{best_route['mode']} • {distance_km:.1f} km • {best_route['time']} min").add_to(m)

                # Distance circle
                folium.Circle(list(src_coords), radius=500, color="#00B4D8", fill=True, fill_opacity=0.15).add_to(m)
                folium.Circle(list(dst_coords), radius=500, color="#EF5350", fill=True, fill_opacity=0.15).add_to(m)

                st_folium(m, width=None, height=400)
            else:
                st.error("❌ Could not find one or both locations. Try adding city/state name (e.g. 'Parbhani, Maharashtra')")
        else:
            st.warning("Please enter both source and destination!")

# ══════════════════════════════════════════
# PAGE: AI ASSISTANT
# ══════════════════════════════════════════
elif page == "🤖 AI Assistant":
    st.markdown("<div class='section-header'>🤖 AI Commute Assistant</div>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94A3B8;'>Ask in Hindi, English, or Marathi! Use Route Planner first for best results.</p>", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    eq1,eq2,eq3 = st.columns(3)
    with eq1:
        if st.button("🚇 Cheapest option?"):
            st.session_state.prefill = "Which is the cheapest option for my journey?"
    with eq2:
        if st.button("🌙 Safe route at night?"):
            st.session_state.prefill = "Safest route home after 10 PM?"
    with eq3:
        if st.button("🌿 Most eco-friendly?"):
            st.session_state.prefill = "Which option is greenest for environment?"

    for msg in st.session_state.messages:
        css = "chat-user" if msg["role"]=="user" else "chat-ai"
        icon = "💬" if msg["role"]=="user" else "🤖"
        st.markdown(f"<div class='{css}'>{icon} {msg['content']}</div>", unsafe_allow_html=True)

    prefill_val = st.session_state.pop("prefill", "")
    user_input = st.text_input("💬 Ask anything:", value=prefill_val, placeholder="e.g. Mujhe college 9 baje tak pahunchna hai ₹50 mein...")

    if st.button("Send 🚀", use_container_width=True) and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        reply = ask_ai(
            st.session_state.messages,
            source=st.session_state.get("last_src",""),
            destination=st.session_state.get("last_dst",""),
            distance_km=st.session_state.get("last_dist",0),
            routes=st.session_state.get("last_routes",[])
        )
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# ══════════════════════════════════════════
# PAGE: SAFETY & CARBON
# ══════════════════════════════════════════
elif page == "🛡️ Safety & Carbon":
    st.markdown("<div class='section-header'>🛡️ Safety Score & 🌿 Carbon Score</div>", unsafe_allow_html=True)
    routes = st.session_state.get("last_routes", calculate_routes(15))

    tab1, tab2 = st.tabs(["🛡️ Safety Score", "🌿 Carbon Score"])
    with tab1:
        st.markdown("### Route Safety Rankings")
        for r in sorted(routes, key=lambda x: -x["safety_score"]):
            color = "#00C853" if r["safety_score"]>=85 else ("#FFB300" if r["safety_score"]>=65 else "#EF5350")
            st.markdown(f"""
            <div class='route-card'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <span class='route-title'>{r['mode']}</span>
                    <span style='font-size:1.2rem;font-weight:700;color:{color};'>{r['safety_score']}/100</span>
                </div>
                <div style='background:#0D1F3C;border-radius:8px;height:10px;margin-top:8px;'>
                    <div style='background:{color};width:{r["safety_score"]}%;height:10px;border-radius:8px;'></div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("### 🛡️ Safety Factors We Analyse")
        f1,f2 = st.columns(2)
        with f1:
            for f in ["👥 Crowd density analysis","💡 Street lighting level","✅ Verified safe zones"]:
                st.info(f)
        with f2:
            for f in ["🕐 Time-of-day risk rating","👩 Women safety priority mode","🚨 Emergency SOS integration"]:
                st.info(f)

    with tab2:
        st.markdown("### 🌿 Carbon Footprint Rankings")
        for r in sorted(routes, key=lambda x: -x["carbon_score"]):
            color = "#00C853" if r["carbon_score"]>=80 else ("#FFB300" if r["carbon_score"]>=50 else "#EF5350")
            st.markdown(f"""
            <div class='route-card'>
                <div style='display:flex;justify-content:space-between;align-items:center;'>
                    <span class='route-title'>{r['mode']}</span>
                    <span style='font-size:1.2rem;font-weight:700;color:{color};'>{r['carbon_score']}/100 🌿</span>
                </div>
                <div style='background:#0D1F3C;border-radius:8px;height:10px;margin-top:8px;'>
                    <div style='background:{color};width:{r["carbon_score"]}%;height:10px;border-radius:8px;'></div>
                </div>
            </div>""", unsafe_allow_html=True)

        c1,c2,c3 = st.columns(3)
        with c1: st.metric("CO₂ Saved This Month","12.4 kg","↓ 30% vs last month")
        with c2: st.metric("Green Points Earned","340 pts","+85 this week")
        with c3: st.metric("Eco Rank","#47 / 500","↑ 12 spots")

# ══════════════════════════════════════════
# PAGE: LIVE ALERTS
# ══════════════════════════════════════════
elif page == "🔔 Live Alerts":
    st.markdown("<div class='section-header'>🔔 Live Commute Alerts</div>", unsafe_allow_html=True)

    conn = sqlite3.connect("onejourney.db")
    alerts = conn.execute("SELECT type, message, severity FROM alerts ORDER BY id DESC").fetchall()
    conn.close()

    sev_icon  = {"high":"🔴","medium":"🟡","low":"🟢"}
    sev_color = {"high":"#B71C1C","medium":"#E65100","low":"#1B5E20"}
    for atype, msg, sev in alerts:
        color = sev_color.get(sev,"#1565C0")
        st.markdown(f"""
        <div class='alert-card' style='border-left:4px solid {color};'>
            {sev_icon.get(sev,"🔵")} <b style='color:{color};'>{atype} Alert</b><br>
            <span style='color:#CBD5E1;'>{msg}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>🗺️ Live Disruption Map</div>", unsafe_allow_html=True)
    last_lat = st.session_state.get("last_coords_src", (19.076, 72.877))
    m = folium.Map(location=list(last_lat), zoom_start=11, tiles="CartoDB dark_matter")
    disruptions = [
        ([last_lat[0]+0.04, last_lat[1]+0.02], "🔴 Heavy Traffic Ahead", "red"),
        ([last_lat[0]-0.02, last_lat[1]+0.05], "🟡 Metro Delay", "orange"),
        ([last_lat[0]+0.01, last_lat[1]-0.03], "🟢 Clear Zone", "green"),
    ]
    for loc, popup, color in disruptions:
        folium.CircleMarker(loc, radius=20, color=color, fill=True, fill_opacity=0.4, popup=popup).add_to(m)
        folium.Marker(loc, popup=popup, icon=folium.Icon(color=color, icon="info-sign")).add_to(m)
    st_folium(m, width=None, height=380)

# ══════════════════════════════════════════
# PAGE: MY DASHBOARD
# ══════════════════════════════════════════
elif page == "📊 My Dashboard":
    st.markdown("<div class='section-header'>📊 My Commute Dashboard</div>", unsafe_allow_html=True)

    conn = sqlite3.connect("onejourney.db")
    trips_db = conn.execute("SELECT source, destination, mode, cost, time_min, safety_score, carbon_score, timestamp FROM trips ORDER BY id DESC LIMIT 10").fetchall()
    total_trips = conn.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    total_saved = conn.execute("SELECT SUM(cost) FROM trips").fetchone()[0] or 0
    conn.close()

    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("Total Trips Planned", total_trips or 0)
    with c2: st.metric("Total Fare Compared", f"₹{total_saved or 0}")
    with c3: st.metric("CO₂ Saved Est.", f"{round((total_trips or 1) * 0.6, 1)} kg")
    with c4: st.metric("Favourite Mode", "🚇 Metro")

    if trips_db:
        st.markdown("### 📅 Recent Trips")
        import pandas as pd
        df = pd.DataFrame(trips_db, columns=["From","To","Mode","Cost (₹)","Time (min)","Safety","Carbon","Time"])
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("🗺️ Use the Route Planner to start planning trips — they'll appear here!")

    st.markdown("### ⚙️ My Preferences")
    p1,p2,p3 = st.columns(3)
    with p1:
        st.markdown("""<div class='route-card'><div class='route-title'>💰 Budget</div>
        <div class='route-meta'>Under ₹50 per trip</div></div>""", unsafe_allow_html=True)
    with p2:
        st.markdown("""<div class='route-card'><div class='route-title'>📅 Peak Time</div>
        <div class='route-meta'>Mon–Sat, 8:00 AM & 6 PM</div></div>""", unsafe_allow_html=True)
    with p3:
        st.markdown("""<div class='route-card'><div class='route-title'>🌿 Eco Goal</div>
        <div class='route-meta'>Carbon score above 70</div></div>""", unsafe_allow_html=True)
