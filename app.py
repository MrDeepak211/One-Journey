import streamlit as st
import sqlite3, os, math, json, sys
import urllib.request, urllib.parse
from datetime import datetime
import anthropic

sys.path.insert(0, os.path.dirname(__file__))
from data.cities import (CITIES, MUMBAI_LOCAL_LINES, MUMBAI_METRO_LINES,
                          PUNE_METRO_LINES, BUS_ROUTES, INTERCITY_ROUTES,
                          SAFETY_ZONES, CARBON_PER_KM)

st.set_page_config(page_title="OneJourney AI", page_icon="🚇", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body,[class*="css"],.stApp{font-family:'Inter',sans-serif!important;background:#0B0F1A!important;color:#E2E8F0!important;}
.main .block-container{padding:0!important;max-width:100%!important;}
section[data-testid="stSidebar"]{display:none!important;}
::-webkit-scrollbar{width:5px;}::-webkit-scrollbar-track{background:#0B0F1A;}::-webkit-scrollbar-thumb{background:#1E2D4A;border-radius:3px;}
.navbar{display:flex;align-items:center;justify-content:space-between;background:#111827;border-bottom:1px solid #1E2D4A;padding:0 20px;height:60px;position:sticky;top:0;z-index:100;}
.nav-logo{width:38px;height:38px;border-radius:9px;background:linear-gradient(135deg,#3B82F6,#06B6D4);display:flex;align-items:center;justify-content:center;font-size:18px;}
.nav-title{font-size:1rem;font-weight:800;color:#fff;}.nav-title span{color:#3B82F6;}
.nav-sub{font-size:.65rem;color:#64748B;}
.nav-right{display:flex;align-items:center;gap:16px;}
.nav-weather-temp{font-size:1rem;font-weight:600;color:#fff;}
.nav-weather-city{font-size:.65rem;color:#64748B;}
.nav-bell{width:34px;height:34px;border-radius:8px;background:#1E2D4A;display:flex;align-items:center;justify-content:center;font-size:16px;position:relative;}
.nav-badge{position:absolute;top:-4px;right:-4px;width:15px;height:15px;border-radius:50%;background:#EF4444;font-size:.55rem;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;}
.nav-avatar{width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#3B82F6,#8B5CF6);display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;}
.nav-uname{font-size:.82rem;font-weight:600;color:#fff;}.nav-urole{font-size:.65rem;color:#64748B;}
.filter-tabs{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;}
.ftab{padding:7px 14px;border-radius:10px;font-size:.75rem;font-weight:700;cursor:pointer;border:1px solid #1E2D4A;background:#111827;color:#64748B;}
.ftab.best{border-color:#F59E0B;color:#F59E0B;background:rgba(245,158,11,.08);}
.ftab.cheap{border-color:#10B981;color:#10B981;background:rgba(16,185,129,.08);}
.ftab.fast{border-color:#EF4444;color:#EF4444;background:rgba(239,68,68,.08);}
.ftab.eco{border-color:#22C55E;color:#22C55E;background:rgba(34,197,94,.08);}
.ftab.safe{border-color:#3B82F6;color:#3B82F6;background:rgba(59,130,246,.08);}
.sec-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;}
.sec-title{font-size:.9rem;font-weight:700;color:#fff;}
.sec-count{font-size:.72rem;color:#64748B;background:#1E2D4A;padding:3px 9px;border-radius:20px;}
.rcard{background:#111827;border:1px solid #1E2D4A;border-radius:13px;padding:14px;margin-bottom:10px;transition:border-color .2s;}
.rcard:hover{border-color:#3B82F6;}
.rcard.best{border-color:#F59E0B;background:linear-gradient(135deg,rgba(245,158,11,.05),#111827);}
.rcinner{display:flex;align-items:flex-start;gap:12px;}
.micon{width:36px;height:36px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0;}
.ib{background:rgba(59,130,246,.18);}.io{background:rgba(249,115,22,.18);}.ip{background:rgba(139,92,246,.18);}.ig{background:rgba(16,185,129,.18);}.ir{background:rgba(239,68,68,.18);}.it{background:rgba(6,182,212,.18);}
.rname{font-size:.9rem;font-weight:700;color:#fff;margin-bottom:2px;}
.rpath{font-size:.72rem;color:#64748B;margin-bottom:5px;}
.rmeta{display:flex;align-items:center;gap:10px;font-size:.72rem;color:#94A3B8;}
.rscores{display:flex;gap:10px;margin-top:6px;}
.rscore{font-size:.68rem;color:#64748B;}
.rright{text-align:right;min-width:90px;flex-shrink:0;}
.rfare{font-size:1.2rem;font-weight:800;color:#fff;}
.bpill{display:inline-block;padding:2px 9px;border-radius:20px;font-size:.65rem;font-weight:700;margin-top:3px;}
.pgold{background:rgba(245,158,11,.15);color:#F59E0B;border:1px solid rgba(245,158,11,.3);}
.pgreen{background:rgba(16,185,129,.15);color:#10B981;border:1px solid rgba(16,185,129,.3);}
.pred{background:rgba(239,68,68,.15);color:#EF4444;border:1px solid rgba(239,68,68,.3);}
.pblue{background:rgba(59,130,246,.15);color:#3B82F6;border:1px solid rgba(59,130,246,.3);}
.agrid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;}
.acard{background:#111827;border:1px solid #1E2D4A;border-radius:11px;padding:11px;}
.atype{font-size:.75rem;font-weight:700;}
.amsg{font-size:.7rem;color:#94A3B8;line-height:1.4;margin:4px 0;}
.asev{font-size:.63rem;font-weight:700;padding:2px 7px;border-radius:20px;}
.sh{background:rgba(239,68,68,.15);color:#EF4444;}.sm{background:rgba(245,158,11,.15);color:#F59E0B;}.sl{background:rgba(16,185,129,.15);color:#10B981;}
.atime{font-size:.63rem;color:#475569;}
.sbitem{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:9px;cursor:pointer;margin-bottom:3px;font-size:.82rem;font-weight:500;color:#94A3B8;}
.sbitem:hover{background:#1E2D4A;color:#fff;}
.sbitem.active{background:#1D4ED8;color:#fff;font-weight:600;}
.impact-box{background:#0F172A;border:1px solid #1E2D4A;border-radius:11px;padding:12px;margin-top:10px;}
.irow{display:flex;align-items:center;gap:8px;margin-bottom:7px;}
.iicon{width:26px;height:26px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:.9rem;}
.ival{font-size:.85rem;font-weight:700;}.ilbl{font-size:.65rem;color:#64748B;}
.qs-box{background:#0B0F1A;border:1px solid #1E2D4A;border-radius:11px;padding:12px;margin-top:12px;}
.qs-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px;}
.qs-lbl{font-size:.65rem;color:#64748B;}
.qs-val{font-size:.92rem;font-weight:700;color:#fff;}
.mstats{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;padding:8px 12px 12px;}
.ms-val{font-size:.82rem;font-weight:700;color:#fff;text-align:center;}
.ms-lbl{font-size:.6rem;color:#64748B;text-align:center;}
.chat-wrap{padding:10px 12px;max-height:200px;overflow-y:auto;display:flex;flex-direction:column;gap:7px;}
.bu{background:#1D4ED8;border-radius:11px 11px 3px 11px;padding:8px 11px;font-size:.78rem;color:#fff;align-self:flex-end;max-width:88%;}
.ba{background:#1E2D4A;border-radius:3px 11px 11px 11px;padding:8px 11px;font-size:.78rem;color:#E2E8F0;align-self:flex-start;max-width:92%;display:flex;gap:7px;}
.stTextInput>div>div>input{background:#0B0F1A!important;color:#E2E8F0!important;border:1px solid #1E2D4A!important;border-radius:9px!important;font-family:'Inter',sans-serif!important;font-size:.85rem!important;padding:9px 13px!important;}
.stTextInput label{color:#64748B!important;font-size:.7rem!important;font-weight:700!important;text-transform:uppercase!important;letter-spacing:.05em!important;}
.stSelectbox>div>div{background:#0B0F1A!important;border:1px solid #1E2D4A!important;color:#E2E8F0!important;border-radius:9px!important;}
.stSelectbox label{color:#64748B!important;font-size:.7rem!important;font-weight:700!important;text-transform:uppercase!important;}
.stButton>button{background:linear-gradient(135deg,#1D4ED8,#3B82F6)!important;color:#fff!important;border:none!important;border-radius:9px!important;font-weight:700!important;font-size:.88rem!important;padding:11px!important;width:100%!important;}
div[data-testid="stSidebar"]{display:none!important;}
[data-testid="stMetric"]{background:#111827!important;border:1px solid #1E2D4A!important;border-radius:11px!important;padding:10px!important;}
[data-testid="stMetricLabel"]{color:#64748B!important;font-size:.7rem!important;}
[data-testid="stMetricValue"]{color:#fff!important;font-size:1.2rem!important;font-weight:700!important;}
.element-container{margin:2px 0!important;}
.stTabs [data-baseweb="tab-list"]{background:#111827!important;border-radius:9px!important;gap:3px!important;padding:3px!important;}
.stTabs [data-baseweb="tab"]{background:transparent!important;border-radius:7px!important;color:#64748B!important;font-weight:600!important;font-size:.78rem!important;}
.stTabs [aria-selected="true"]{background:#1D4ED8!important;color:#fff!important;}
</style>
""", unsafe_allow_html=True)

# ── DB ──
def init_db():
    conn = sqlite3.connect("onejourney.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS trips(id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,destination TEXT,mode TEXT,cost INTEGER,time_min INTEGER,
        distance_km REAL,safety_score INTEGER,carbon_score INTEGER,co2_saved_g REAL,timestamp TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,message TEXT,severity TEXT,city TEXT,timestamp TEXT)""")
    if conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]==0:
        conn.executemany("INSERT INTO alerts VALUES(NULL,?,?,?,?,?)",[
            ("Traffic","Heavy traffic on NH65 near Daund. Expect 20 min delay.","high","Maharashtra","10 min ago"),
            ("Weather","Light rain expected in Pune after 2 PM. Carry umbrella.","medium","Pune","20 min ago"),
            ("Transport","Metro Line 1 operating normally in Pune.","low","Pune","30 min ago"),
            ("Bus","MSRTC bus services running on time today.","low","Maharashtra","45 min ago"),
            ("Traffic","Western Express Hwy congested near Andheri — 20 min delay.","high","Mumbai","5 min ago"),
            ("Metro","Mumbai Metro Line 2A delayed 12 min at Borivali East.","medium","Mumbai","15 min ago"),
        ])
    conn.commit(); conn.close()
init_db()

# ── Utils ──
def haversine(lat1,lon1,lat2,lon2):
    R=6371;d=math.radians
    dlat,dlon=d(lat2-lat1),d(lon2-lon1)
    a=math.sin(dlat/2)**2+math.cos(d(lat1))*math.cos(d(lat2))*math.sin(dlon/2)**2
    return R*2*math.asin(math.sqrt(a))

def geocode(name):
    clean=name.strip().title()
    for key,coords in CITIES.items():
        if clean.lower() in key.lower() or key.lower() in clean.lower():
            return coords,key
    try:
        q=urllib.parse.quote(name+", India")
        url=f"https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1&countrycodes=in"
        req=urllib.request.Request(url,headers={"User-Agent":"OneJourneyAI/2.0"})
        with urllib.request.urlopen(req,timeout=6) as r:
            data=json.loads(r.read())
            if data: return (float(data[0]["lat"]),float(data[0]["lon"])),data[0].get("display_name","").split(",")[0]
    except: pass
    return None,None

def get_city_type(name):
    n=name.lower()
    if any(k in n for k in ["mumbai","thane","navi mumbai","borivali","andheri","bandra","dadar","churchgate","cst","kurla","ghatkopar","mulund","kalyan","panvel","vasai","virar","mira road","vashi","belapur"]): return "Mumbai"
    if any(k in n for k in ["pune","pimpri","chinchwad","shivajinagar","kothrud","hadapsar","viman nagar","hinjewadi","wakad","baner","aundh","kharadi","magarpatta","camp","swargate"]): return "Pune"
    return "Other"

def fmt_time(m): return f"{m//60}h {m%60:02d}m" if m>=60 else f"{m} min"

def build_routes(d,src_name,dst_name,time_pref="morning"):
    is_night="night" in time_pref.lower(); is_eve="evening" in time_pref.lower()
    surge=1.5 if is_night else (1.2 if is_eve else 1.0)
    city=get_city_type(src_name); np=-10 if is_night else 0
    # intercity check
    ic=None
    for (a,b),rts in INTERCITY_ROUTES.items():
        sa,sb=src_name.lower(),dst_name.lower()
        if (a.lower() in sa or sa in a.lower()) and (b.lower() in sb or sb in b.lower()): ic=rts;break
        if (b.lower() in sa or sa in b.lower()) and (a.lower() in sb or sb in a.lower()): ic=rts;break
    if ic or d>60:
        if ic:
            routes=[]
            for r in ic:
                cost=round(r["fare"]*surge) if "Cab" in r["mode"] else r["fare"]
                cs=next((100-v for k,v in CARBON_PER_KM.items() if k.lower() in r["mode"].lower()),40)
                routes.append({**r,"cost":cost,"time":r["time_min"],"carbon_score":max(10,cs),
                    "safety_score":88,"desc":f"~{round(d)}km intercity","best":False,"co2":0,
                    "carbon":r.get("carbon","Good"),"safety":r.get("safety","High")})
        else:
            routes=[
                {"mode":"🚌 State Bus (MSRTC)","cost":round(d*1.2/10)*10,"time":round(d*6.5),
                 "safety":"High","safety_score":85,"carbon":"Good","carbon_score":72,
                 "desc":f"~{d:.0f}km • {round(d*6.5/60,1)}hrs","best":False,"co2":0},
                {"mode":"🚆 Indian Railways","cost":round(d*0.75/10)*10,"time":round(d*5.2),
                 "safety":"High","safety_score":88,"carbon":"Excellent","carbon_score":90,
                 "desc":f"~{d:.0f}km • {round(d*5.2/60,1)}hrs","best":False,"co2":0},
                {"mode":"🚗 Cab (Outstation)","cost":round(d*18*surge/100)*100,"time":round(d*3.2),
                 "safety":"High","safety_score":91,"carbon":"Poor","carbon_score":22,
                 "desc":f"AC cab • {round(d*3.2/60,1)}hrs • surge {surge}x","best":False,"co2":0},
            ]
        bi=min(range(len(routes)),key=lambda i:routes[i]["cost"]*.4+routes[i]["time"]*.3+(100-routes[i].get("safety_score",80))*.15+(100-routes[i].get("carbon_score",40))*.15)
        routes[bi]["best"]=True; return routes,"intercity"
    routes=[]
    if city=="Mumbai" and d>=3:
        lt=max(5,min(55,round(d*1.8/5)*5))
        routes.append({"mode":"🚉 Mumbai Local Train","cost":lt,"time":round(d*2.5+10),
            "safety":"High" if not is_night else "Medium","safety_score":max(55,88+np),
            "carbon":"Excellent","carbon_score":92,"desc":"Western/Central/Harbour • very frequent","best":False,
            "co2":round((CARBON_PER_KM["Cab"]-CARBON_PER_KM["Local Train"])*d)})
    if d>=2:
        mf=max(10,min(60,round(d*2.3/5)*5))
        ml="🚇 Mumbai Metro" if city=="Mumbai" else ("🚇 Pune Metro" if city=="Pune" else "🚇 Metro")
        routes.append({"mode":ml+" + Walk","cost":mf,"time":round(d*2.6+8),
            "safety":"High","safety_score":min(95,92+np),"carbon":"Excellent","carbon_score":93,
            "desc":f"Metro ({round(d*.85,1)}km)+{round(d*.15*13)}min walk","best":False,
            "co2":round((CARBON_PER_KM["Cab"]-CARBON_PER_KM["Metro"])*d)})
    bl="🚌 BEST Bus" if city=="Mumbai" else ("🚌 PMC Bus" if city=="Pune" else "🚌 City Bus")
    routes.append({"mode":bl,"cost":max(8,round(d*1.9/5)*5),"time":round(d*4.8+12),
        "safety":"Medium" if is_night else "High","safety_score":max(55,75+np),
        "carbon":"Good","carbon_score":78,"desc":"Govt bus • cheapest option","best":False,
        "co2":round((CARBON_PER_KM["Cab"]-CARBON_PER_KM["Bus"])*d)})
    routes.append({"mode":"🛵 Bike Taxi (Rapido)","cost":max(25,round(d*7.5/5)*5),"time":round(d*2+3),
        "safety":"High","safety_score":min(88,85+np),"carbon":"Average","carbon_score":52,
        "desc":"Fastest 2-wheeler • no traffic jams","best":False,
        "co2":round((CARBON_PER_KM["Cab"]-CARBON_PER_KM["Bike Taxi"])*d)})
    ab=25 if city=="Pune" else 23; ap=13 if city=="Pune" else 14.5
    routes.append({"mode":"🛺 Auto Rickshaw","cost":max(30,round((ab+d*ap)/5)*5),
        "time":round(d*3+5),"safety":"High","safety_score":min(90,88+np),
        "carbon":"Poor","carbon_score":32,"desc":f"₹{ab} base+₹{ap}/km metered","best":False,"co2":0})
    cf=round((50+d*(13 if city=="Pune" else 15))*surge/10)*10
    routes.append({"mode":"🚗 Cab (Ola/Uber)","cost":max(80,cf),"time":round(d*2.7+6),
        "safety":"High","safety_score":92,"carbon":"Poor","carbon_score":22,
        "desc":f"AC cab•{'🌙'+str(surge)+'x surge' if surge>1 else 'no surge'}","best":False,"co2":0})
    if d<=2.5:
        routes.append({"mode":"🚶 Walk","cost":0,"time":round(d*14),
            "safety":"Medium" if is_night else "High","safety_score":max(55,65+np),
            "carbon":"Excellent","carbon_score":100,"desc":f"~{round(d*1000)}m•free•healthy 💪","best":False,
            "co2":round(CARBON_PER_KM["Cab"]*d)})
    def ws(r): return r["cost"]*.35+r["time"]*.30+(100-r["safety_score"])*.20+(100-r["carbon_score"])*.15
    routes[min(range(len(routes)),key=lambda i:ws(routes[i]))]["best"]=True
    return routes,"city"

def ask_ai(messages,src="",dst="",dist=0,routes=[],time_pref=""):
    api_key=os.environ.get("ANTHROPIC_API_KEY","")
    rt="\n".join([f"- {r['mode']}: ₹{r['cost']}, {r['time']}min, Safety:{r.get('safety_score','?')}/100, Carbon:{r.get('carbon_score','?')}/100{'  ⭐BEST' if r.get('best') else ''}" for r in routes]) if routes else "No routes yet."
    system=f"""You are OneJourney AI — smart urban mobility assistant for India.
Journey: {src} → {dst} | Distance: {round(dist,1)}km | Time: {time_pref}
Routes:\n{rt}
Reply same language as user (Hindi/English/Marathi). Under 80 words. Warm & specific."""
    if api_key:
        try:
            client=anthropic.Anthropic(api_key=api_key)
            resp=client.messages.create(model="claude-sonnet-4-6",max_tokens=250,system=system,
                messages=[{"role":m["role"],"content":m["content"]} for m in messages])
            return resp.content[0].text
        except Exception as e: return f"⚠️ {str(e)[:50]}"
    q=messages[-1]["content"].lower()
    best=next((r for r in routes if r.get("best")),routes[0] if routes else None)
    cheap=min(routes,key=lambda r:r["cost"]) if routes else None
    fast=min(routes,key=lambda r:r["time"]) if routes else None
    if any(w in q for w in ["cheap","budget","sasta","₹","less"]) and cheap:
        return f"💰 Cheapest: **{cheap['mode']}** — ₹{cheap['cost']} ({cheap['time']} min)!\n💡 Book monthly pass for 40% savings!"
    if any(w in q for w in ["fast","quick","jaldi","urgent"]) and fast:
        return f"⚡ Fastest: **{fast['mode']}** — {fast['time']} min! Costs ₹{fast['cost']}.\n💡 Leave 5 min early!"
    if any(w in q for w in ["safe","night","raat","women"]):
        sf=max(routes,key=lambda r:r["safety_score"]) if routes else None
        if sf: return f"🛡️ Safest: **{sf['mode']}** — Safety {sf['safety_score']}/100.\n💡 Always share live location at night!"
    if any(w in q for w in ["time","best","when","early","morning"]) and dist>50:
        return "🕐 Early morning (5–7 AM) is ideal for road travel. For buses/trains, mid-morning offers better punctuality and availability."
    if best: return f"🤖 Best overall: **{best['mode']}** — ₹{best['cost']}, {best['time']} min.\n💡 Set ANTHROPIC_API_KEY for full AI!"
    return "🤖 Use Route Planner first, then I'll give personalized advice!"

def micon(mode):
    if "Local Train" in mode or "Railway" in mode: return "🚉","ib"
    if "Metro" in mode: return "🚇","ip"
    if "Bus" in mode: return "🚌","io"
    if "Bike" in mode: return "🛵","it"
    if "Auto" in mode: return "🛺","ig"
    if "Cab" in mode: return "🚗","ir"
    if "Walk" in mode: return "🚶","ig"
    return "🚌","ib"

# ── Session ──
if "page"       not in st.session_state: st.session_state.page="Route Planner"
if "messages"   not in st.session_state: st.session_state.messages=[
    {"role":"user","content":"What is the best time to travel from Parbhani to Pune?"},
    {"role":"assistant","content":"Based on current traffic and transport data, early morning (5 AM – 7 AM) is ideal for road travel. For buses and trains, mid-morning offers better punctuality and availability."}]
if "routes"     not in st.session_state: st.session_state.routes=[]
if "last_src"   not in st.session_state: st.session_state.last_src=""
if "last_dst"   not in st.session_state: st.session_state.last_dst=""
if "last_dist"  not in st.session_state: st.session_state.last_dist=0
if "src_coords" not in st.session_state: st.session_state.src_coords=None
if "dst_coords" not in st.session_state: st.session_state.dst_coords=None
if "searched"   not in st.session_state: st.session_state.searched=False

# ── NAVBAR ──
st.markdown("""<div class="navbar">
<div style="display:flex;align-items:center;gap:10px;">
  <div class="nav-logo">🚇</div>
  <div><div class="nav-title">OneJourney <span>AI</span></div><div class="nav-sub">Your Smart Mobility Companion</div></div>
</div>
<div class="nav-right">
  <div style="display:flex;align-items:center;gap:8px;">
    <span style="font-size:1.3rem;">☀️</span>
    <div><div class="nav-weather-temp">28°C</div><div class="nav-weather-city">Mumbai</div></div>
  </div>
  <div class="nav-bell">🔔<div class="nav-badge">3</div></div>
  <div style="display:flex;align-items:center;gap:8px;cursor:pointer;">
    <div class="nav-avatar">D</div>
    <div><div class="nav-uname">Deepak</div><div class="nav-urole">Student</div></div>
    <span style="color:#64748B;font-size:.75rem;">▾</span>
  </div>
</div>
</div>""", unsafe_allow_html=True)

# ── LAYOUT: 4 columns ──
sb, lp, cp, rp = st.columns([1.1, 1.55, 3.6, 1.9])
# ══════════════════════════════════
# SIDEBAR
# ══════════════════════════════════

# ── LAYOUT: 4 columns ──
sb, lp, cp, rp = st.columns([1.1, 1.55, 3.6, 1.9])
# ══════════════════════════════════
# SIDEBAR
# ══════════════════════════════════
with sb:
    nav_items=[
        ("🗺️","Route Planner"),
        ("🤖","AI Assistant"),
        ("🔔","Live Alerts"),
        ("📊","Dashboard"),
        ("📅","Trip History"),
        ("⚙️","Preferences"),
        ("ℹ️","About Us")
    ]

    nav_html="".join([
        f'<div class="sbitem {"active" if st.session_state.page==l else ""}">{ic} {l}</div>'
        for ic,l in nav_items
    ])

    conn = sqlite3.connect("onejourney.db")
    stats = conn.execute("SELECT COUNT(*) FROM trips").fetchone()
    conn.close()

    trips_n = stats[0] if stats else 0
    co2 = round(trips_n * 0.6, 1)

    st.markdown(f"""
    <div style="height:calc(100vh - 68px);display:flex;flex-direction:column;padding:10px 6px;background:#111827;border-right:1px solid #1E2D4A;overflow-y:auto;">
        <div style="flex:1;">{nav_html}</div>

        <div class="impact-box">
            <div style="font-size:.72rem;font-weight:700;color:#10B981;margin-bottom:8px;">
                🌿 Our Impact
            </div>

            <div class="irow">
                <div class="iicon" style="background:rgba(16,185,129,.15);">♻️</div>
                <div>
                    <div class="ival" style="color:#10B981;">{co2} kg</div>
                    <div class="ilbl">Carbon Saved CO₂</div>
                </div>
            </div>

            <div class="irow">
                <div class="iicon" style="background:rgba(59,130,246,.15);">⏱️</div>
                <div>
                    <div class="ival" style="color:#3B82F6;">12.4 hrs</div>
                    <div class="ilbl">Time Saved</div>
                </div>
            </div>

            <div class="irow">
                <div class="iicon" style="background:rgba(245,158,11,.15);">💰</div>
                <div>
                    <div class="ival" style="color:#F59E0B;">₹1,250</div>
                    <div class="ilbl">Money Saved</div>
                </div>
            </div>
        </div>

        <div style="display:flex;align-items:center;gap:8px;padding:10px 8px;border-radius:9px;background:linear-gradient(135deg,#1E2D4A,#0F172A);margin-top:8px;border:1px solid #1E2D4A;">
            <div style="font-size:1.8rem;">🐺</div>
            <div>
                <div style="font-size:.8rem;font-weight:700;color:#fff;">Night Wolf</div>
                <div style="font-size:.65rem;color:#3B82F6;">
                    Building the future of smart mobility 💙
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════
# LEFT PANEL — Form
# ══════════════════════════════════
with lp:
    st.markdown('<div style="height:calc(100vh - 68px);overflow-y:auto;padding:14px 12px;background:#111827;border-right:1px solid #1E2D4A;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:.95rem;font-weight:700;color:#fff;margin-bottom:3px;">Plan Your Journey</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:.72rem;color:#64748B;margin-bottom:14px;">Find the best way to travel with AI-powered recommendations</div>', unsafe_allow_html=True)

    src_val = st.text_input("FROM", value=st.session_state.last_src or "Parbhani, Maharashtra, India", key="src_inp")
    dst_val = st.text_input("TO",   value=st.session_state.last_dst or "Pune, Maharashtra, India",    key="dst_inp")
    date_v  = st.selectbox("TRAVEL DATE",["13 June 2025","14 June 2025","Today"], key="date_inp")
    time_v  = st.selectbox("DEPARTURE TIME",["09:00 AM","Morning (6–10 AM)","Afternoon","Evening (5–9 PM)","Night (After 9 PM)"], key="time_inp")
    pref_v  = st.selectbox("PREFERENCES",["Balanced (Time + Cost)","Fastest","Cheapest","Safest","Eco-Friendly"], key="pref_inp")

    if st.button("🔍 Find Best Routes", key="find_btn"):
        with st.spinner("Calculating..."):
            sc,sl=geocode(src_val); dc,dl=geocode(dst_val)
        if sc and dc:
            dist=haversine(*sc,*dc)
            routes,rtype=build_routes(dist,src_val,dst_val,time_v)
            st.session_state.update({"routes":routes,"last_src":src_val,"last_dst":dst_val,
                "last_dist":dist,"src_coords":sc,"dst_coords":dc,"rtype":rtype,"searched":True})
            best=next((r for r in routes if r.get("best")),routes[0])
            conn=sqlite3.connect("onejourney.db")
            conn.execute("INSERT INTO trips VALUES(NULL,?,?,?,?,?,?,?,?,?,?)",(
                src_val,dst_val,best["mode"],best["cost"],best["time"],
                round(dist,2),best.get("safety_score",85),best.get("carbon_score",50),
                best.get("co2",0),str(datetime.now())))
            conn.commit(); conn.close()
            st.rerun()
        else:
            st.error("❌ Location not found. Add state name e.g. 'Pune, Maharashtra'")

    if st.session_state.searched and st.session_state.routes:
        routes=st.session_state.routes
        mc=min(r["cost"] for r in routes); mt=min(r["time"] for r in routes)
        dk=st.session_state.last_dist
        st.markdown(f"""<div class="qs-box">
<div style="font-size:.72rem;font-weight:700;color:#94A3B8;">Quick Stats</div>
<div class="qs-grid">
  <div><div class="qs-lbl">📏 Distance</div><div class="qs-val">{round(dk)} km</div></div>
  <div><div class="qs-lbl">⏱ Est. Time</div><div class="qs-val" style="color:#3B82F6;">{fmt_time(mt)}</div></div>
  <div><div class="qs-lbl">💰 Min. Cost</div><div class="qs-val" style="color:#10B981;">₹{mc}</div></div>
  <div><div class="qs-lbl">🚌 Options</div><div class="qs-val">{len(routes)} Modes</div></div>
</div>
</div>""", unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════
# CENTER PANEL — Routes + Alerts
# ══════════════════════════════════
with cp:
    st.markdown('<div style="height:calc(100vh - 68px);overflow-y:auto;padding:14px 16px;background:#0B0F1A;">', unsafe_allow_html=True)
    routes=st.session_state.routes

    if routes:
        best_r  = next((r for r in routes if r.get("best")), routes[0])
        cheap_r = min(routes,key=lambda r:r["cost"])
        fast_r  = min(routes,key=lambda r:r["time"])
        eco_r   = max(routes,key=lambda r:r.get("carbon_score",0))
        safe_r  = max(routes,key=lambda r:r.get("safety_score",0))

        def short(m): parts=m.split(); return " ".join(parts[1:3]) if len(parts)>2 else m.split()[0]

        st.markdown(f"""<div class="filter-tabs">
<div class="ftab best">⭐ Best Overall<br><small>{short(best_r['mode'])} • ₹{best_r['cost']} • {fmt_time(best_r['time'])}</small></div>
<div class="ftab cheap">💚 Cheapest<br><small>{short(cheap_r['mode'])} • ₹{cheap_r['cost']} • {fmt_time(cheap_r['time'])}</small></div>
<div class="ftab fast">🔴 Fastest<br><small>{short(fast_r['mode'])} • ₹{fast_r['cost']} • {fmt_time(fast_r['time'])}</small></div>
<div class="ftab eco">🌿 Eco-Friendly<br><small>{short(eco_r['mode'])} • ₹{eco_r['cost']} • {fmt_time(eco_r['time'])}</small></div>
<div class="ftab safe">🛡️ Safest<br><small>{short(safe_r['mode'])}<br>Safety Score: {safe_r.get('safety_score',90)}</small></div>
</div>""", unsafe_allow_html=True)

        src_s=st.session_state.last_src.split(",")[0]
        dst_s=st.session_state.last_dst.split(",")[0]

        st.markdown(f"""<div class="sec-row">
<div class="sec-title">Recommended Routes</div>
<div class="sec-count">{len(routes)} Options Found</div>
</div>""", unsafe_allow_html=True)

        shown=0
        for i,r in enumerate(routes):
            if shown==3:
                with st.expander(f"▼ Show {len(routes)-3} More Options"):
                    for r2 in routes[3:]:
                        ic2,icls2=micon(r2["mode"])
                        s2="#10B981" if r2.get("safety_score",80)>=85 else "#F59E0B"
                        c2="#10B981" if r2.get("carbon_score",50)>=80 else "#F59E0B"
                        st.markdown(f"""<div class="rcard" style="margin-bottom:8px;">
<div class="rcinner">
  <div class="micon {icls2}">{ic2}</div>
  <div class="rinfo" style="flex:1;">
    <div class="rname">{r2['mode']}</div>
    <div class="rmeta"><span>{fmt_time(r2['time'])}</span><span>•</span><span>{r2.get('desc','')}</span></div>
    <div class="rscores"><span class="rscore">🛡️<span style="color:{s2};"> {r2.get('safety_score',80)}</span></span><span class="rscore">🌿<span style="color:{c2};"> {r2.get('carbon_score',50)}</span></span></div>
  </div>
  <div class="rright"><div class="rfare">₹{r2['cost']}</div></div>
</div></div>""", unsafe_allow_html=True)
                break

            ic,icls=micon(r["mode"])
            is_best=r.get("best",False)
            cls="rcard best" if is_best else "rcard"
            badge=""
            if is_best:   badge='<span class="bpill pgold">⭐ BEST OVERALL</span>'
            elif r==cheap_r: badge='<span class="bpill pgreen">💚 CHEAPEST</span>'
            elif r==fast_r:  badge='<span class="bpill pred">🔴 FASTEST</span>'
            elif r==eco_r:   badge='<span class="bpill pgreen">🌿 ECO-FRIENDLY</span>'
            elif r==safe_r:  badge='<span class="bpill pblue">🛡️ SAFEST</span>'
            mid=""
            if "Local Train" in r["mode"]: mid="→ CST/Dadar "
            elif "Metro" in r["mode"]: mid="→ Metro Stn "
            sc_color="#10B981" if r.get("safety_score",80)>=85 else ("#F59E0B" if r.get("safety_score",80)>=65 else "#EF4444")
            cc_color="#10B981" if r.get("carbon_score",50)>=80 else ("#F59E0B" if r.get("carbon_score",50)>=50 else "#EF4444")
            co2_str=f'<span class="rscore">🌿 Saves {r.get("co2",0)}g CO₂</span>' if r.get("co2",0)>0 else ""
            st.markdown(f"""<div class="{cls}">
<div class="rcinner">
  <div class="micon {icls}">{ic}</div>
  <div style="flex:1;">
    <div class="rname">{r['mode']}</div>
    <div class="rpath">{src_s} {mid}→ {dst_s}</div>
    <div class="rmeta"><span>{fmt_time(r['time'])}</span><span>•</span><span style="font-size:.7rem;">{r.get('desc','')}</span></div>
    <div class="rscores">
      <span class="rscore">🛡️ <span style="color:{sc_color};">Safety {r.get('safety_score',80)}</span></span>
      <span class="rscore">🌿 <span style="color:{cc_color};">Carbon {r.get('carbon_score',50)}</span></span>
      {co2_str}
    </div>
  </div>
  <div class="rright"><div class="rfare">₹{r['cost']}</div>{badge}</div>
</div></div>""", unsafe_allow_html=True)
            shown+=1

    else:
        st.markdown("""<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:45vh;text-align:center;">
<div style="font-size:3.5rem;margin-bottom:12px;">🗺️</div>
<div style="font-size:1rem;font-weight:700;color:#fff;margin-bottom:6px;">Plan Your Journey</div>
<div style="font-size:.8rem;color:#64748B;max-width:280px;">Enter source & destination on the left, then click Find Best Routes for AI-powered recommendations.</div>
</div>""", unsafe_allow_html=True)

    # Alerts
    conn=sqlite3.connect("onejourney.db")
    alerts=conn.execute("SELECT type,message,severity,timestamp FROM alerts ORDER BY CASE severity WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END LIMIT 4").fetchall()
    conn.close()
    si={"high":"⚠️","medium":"🌧️","low":"🚌"}
    sc_={"high":"#EF4444","medium":"#F59E0B","low":"#10B981"}
    alcards="".join([f"""<div class="acard">
<div style="display:flex;align-items:center;gap:7px;margin-bottom:5px;">
  <span>{si.get(sv,'ℹ️')}</span>
  <span class="atype" style="color:{sc_.get(sv,'#3B82F6')};">{at} Alert</span>
</div>
<div class="amsg">{msg}</div>
<div style="display:flex;align-items:center;justify-content:space-between;">
  <span class="asev s{sv[0]}">{sv.capitalize()}</span>
  <span class="atime">{ts}</span>
</div>
</div>""" for at,msg,sv,ts in alerts])
    st.markdown(f"""<div style="margin-top:16px;">
<div class="sec-row"><div class="sec-title">Live Alerts</div><div style="font-size:.72rem;color:#3B82F6;cursor:pointer;">View All Alerts →</div></div>
<div class="agrid">{alcards}</div>
</div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════
# RIGHT PANEL — Map + AI
# ══════════════════════════════════
with rp:
    st.markdown('<div style="height:calc(100vh - 68px);display:flex;flex-direction:column;background:#111827;border-left:1px solid #1E2D4A;overflow:hidden;">', unsafe_allow_html=True)

    # Map header
    st.markdown("""<div style="padding:12px 14px;border-bottom:1px solid #1E2D4A;">
<div style="display:flex;align-items:center;justify-content:space-between;">
  <div style="font-size:.88rem;font-weight:700;color:#fff;">Route Map</div>
  <div style="font-size:.7rem;font-weight:600;color:#3B82F6;background:rgba(59,130,246,.1);border:1px solid rgba(59,130,246,.3);padding:3px 9px;border-radius:6px;cursor:pointer;">View Full Map</div>
</div>
</div>""", unsafe_allow_html=True)

    import folium
    from streamlit_folium import st_folium
    sc=st.session_state.src_coords; dc=st.session_state.dst_coords
    if sc and dc:
        mid=((sc[0]+dc[0])/2,(sc[1]+dc[1])/2)
        dk=st.session_state.last_dist
        zoom=13 if dk<5 else(11 if dk<25 else(9 if dk<80 else 7))
        m=folium.Map(location=list(mid),zoom_start=zoom,tiles="CartoDB dark_matter")
        folium.Marker(list(sc),popup=f"📍 {st.session_state.last_src.split(',')[0]}",
            icon=folium.Icon(color="green",icon="home",prefix="fa")).add_to(m)
        folium.Marker(list(dc),popup=f"🎯 {st.session_state.last_dst.split(',')[0]}",
            icon=folium.Icon(color="red",icon="flag",prefix="fa")).add_to(m)
        folium.PolyLine([list(sc),list(dc)],color="#3B82F6",weight=4,opacity=0.9,
            tooltip=f"{round(dk,1)}km").add_to(m)
        folium.Circle(list(sc),radius=400,color="#10B981",fill=True,fill_opacity=0.15).add_to(m)
        folium.Circle(list(dc),radius=400,color="#EF4444",fill=True,fill_opacity=0.15).add_to(m)
        if dk>60:
            mp=((sc[0]+dc[0])/2,(sc[1]+dc[1])/2)
            folium.CircleMarker(list(mp),radius=5,color="#F59E0B",fill=True,fill_opacity=0.8,popup="Midpoint").add_to(m)
    else:
        m=folium.Map(location=[19.2,73.5],zoom_start=7,tiles="CartoDB dark_matter")
        for city,(lat,lon) in list(CITIES.items())[:25]:
            ct=get_city_type(city)
            color="blue" if ct=="Mumbai" else("red" if ct=="Pune" else "gray")
            folium.CircleMarker([lat,lon],radius=4 if ct!="Other" else 2,color=color,fill=True,fill_opacity=0.7,popup=city).add_to(m)
    st_folium(m,width=None,height=195,returned_objects=[])

    # Map stats
    if sc and dc:
        dk=st.session_state.last_dist
        routes=st.session_state.routes
        mt=min(r["time"] for r in routes) if routes else 0
        st.markdown(f"""<div class="mstats">
<div><div class="ms-val">{round(dk)} km</div><div class="ms-lbl">Distance</div></div>
<div><div class="ms-val" style="color:#3B82F6;">{fmt_time(mt)}</div><div class="ms-lbl">Est. Time</div></div>
<div><div class="ms-val">Via NH65</div><div class="ms-lbl">Best Route</div></div>
</div>""", unsafe_allow_html=True)

    st.markdown('<div style="border-top:1px solid #1E2D4A;"></div>', unsafe_allow_html=True)

    # AI Chat
    st.markdown("""<div style="padding:10px 12px 4px;">
<div style="display:flex;align-items:center;justify-content:space-between;">
  <div style="display:flex;align-items:center;gap:7px;font-size:.82rem;font-weight:700;color:#fff;">🤖 AI Assistant</div>
  <div style="font-size:.68rem;color:#3B82F6;cursor:pointer;">🗑️ Clear Chat</div>
</div>
</div>""", unsafe_allow_html=True)

    chat_html="".join([
        f'<div class="bu">{m["content"]}</div>' if m["role"]=="user"
        else f'<div class="ba"><span>🤖</span><div>{m["content"]}</div></div>'
        for m in st.session_state.messages[-4:]])
    st.markdown(f'<div class="chat-wrap">{chat_html}</div>', unsafe_allow_html=True)

    chat_in=st.text_input("",placeholder="Ask me anything about your journey...",key="chat_inp",label_visibility="collapsed")
    c1,c2=st.columns([3,1])
    with c1:
        if st.button("Send 🚀",key="send_btn",use_container_width=True) and chat_in:
            st.session_state.messages.append({"role":"user","content":chat_in})
            reply=ask_ai(st.session_state.messages,src=st.session_state.last_src,
                dst=st.session_state.last_dst,dist=st.session_state.last_dist,
                routes=st.session_state.routes,time_pref=st.session_state.get("time_inp",""))
            st.session_state.messages.append({"role":"assistant","content":reply})
            st.rerun()
    with c2:
        if st.button("🗑️",key="clr_btn"):
            st.session_state.messages=[]; st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
