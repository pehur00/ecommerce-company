#!/usr/bin/env python3
"""
Build script for AI Company Dashboard v3.
2D top-down office view with walking characters, desks, coffee corner, meeting room.
"""

import subprocess, json, os, sys
from datetime import datetime

DASHBOARD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(DASHBOARD_DIR, "docs", "index.html")

WORKERS = {
    "worker-ops":         {"name":"Ops",       "emoji":"⚙️", "color":"#34d399","role":"Operations & Infrastructure",    "desk":1,"speed":1.8},
    "worker-researcher":  {"name":"Research",  "emoji":"🔬", "color":"#a78bfa","role":"Research & Content",             "desk":2,"speed":1.5},
    "worker-developer":   {"name":"Dev",       "emoji":"💻", "color":"#60a5fa","role":"Software Development",           "desk":3,"speed":2.0},
    "worker-reviewer":    {"name":"Review",    "emoji":"🔍", "color":"#fbbf24","role":"Quality Assurance",              "desk":4,"speed":1.6},
    "worker-pm":          {"name":"PM",        "emoji":"📋", "color":"#fb923c","role":"Project Management",             "desk":5,"speed":1.9},
    "worker-data":        {"name":"Data",      "emoji":"📊", "color":"#f87171","role":"Data Engineering",               "desk":6,"speed":1.3},
    "worker-designer":    {"name":"Design",    "emoji":"🎨", "color":"#f472b6","role":"UI/UX Design",                  "desk":7,"speed":2.1},
    "security":           {"name":"Security",  "emoji":"🛡️", "color":"#94a3b8","role":"Security & Compliance",          "desk":8,"speed":1.1},
}

FINANCIALS = {
    "expenses": [
        {"item":"Hetzner VPS (CX23)","amount":4.83,"period":"maand","category":"infra","note":"x86, 2 cores, 4 GB RAM, 40 GB disk, shared CPU, fsn1 — echte API-prijs incl. btw"},
        {"item":"Domain .nl (TransIP)","amount":0.49,"period":"jaar","category":"infra","note":"promotieprijs 1e jaar; vervolg €8,99/jaar"},
        {"item":"GitHub Free","amount":0.00,"period":"gratis","category":"tools"},
        {"item":"Amazon.nl Partner","amount":0.00,"period":"gratis","category":"marketing"},
        {"item":"Bol.com Partner","amount":0.00,"period":"gratis","category":"marketing"},
        {"item":"MailerLite Free","amount":0.00,"period":"gratis","category":"marketing"},
    ],
    "revenue": [
        {"item":"Amazon.nl Affiliate","amount":0.00,"period":"maand","category":"affiliate"},
        {"item":"Bol.com Affiliate","amount":0.00,"period":"maand","category":"affiliate"},
    ]
}

# ── Desk positions (x, y) in % of office canvas ──
# Office layout (top-down):
#   ┌──────────────────────────────────────────┐
#   │  WINDOW    WINDOW    WINDOW    WINDOW     │  top wall
#   │                                          │
#   │  [Coffee]        [Meeting Room]          │  top area
#   │                                          │
#   │  [Desk1] [Desk2] [Desk3] [Desk4]        │  middle
#   │                                          │
#   │  [Desk5] [Desk6] [Desk7] [Desk8]        │  middle
#   │                                          │
#   │              [DOOR]                      │  bottom center
#   └──────────────────────────────────────────┘
DESK_POSITIONS = {
    1: {"x": 8,  "y": 38},
    2: {"x": 22, "y": 38},
    3: {"x": 36, "y": 38},
    4: {"x": 50, "y": 38},
    5: {"x": 8,  "y": 58},
    6: {"x": 22, "y": 58},
    7: {"x": 36, "y": 58},
    8: {"x": 50, "y": 58},
}

# Other locations
COFFEE_CORNER = {"x": 8,  "y": 18, "label": "☕ Koffiecorner"}
MEETING_ROOM  = {"x": 72, "y": 18, "label": "🤝 Meeting Room"}
DOOR          = {"x": 45, "y": 90, "label": "🚪 Ingang"}

# Spawn points (outside the door)
SPAWN = {"x": 45, "y": 97}


def get_kanban_data():
    try:
        r = subprocess.run(["hermes","kanban","--board","ecommerce","list","--json"], capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            return json.loads(r.stdout)
    except Exception as e:
        print(f"Warning: {e}")
    return []


def get_worker_status(tasks):
    ws = {}
    for t in tasks:
        a = t.get("assignee",""); s = t.get("status",""); title = t.get("title","")
        if a in WORKERS:
            if s == "running": ws[a] = {"status":"busy","task":title}
            elif s == "ready" and a not in ws: ws[a] = {"status":"ready","task":title}
            elif s == "done" and a not in ws: ws[a] = {"status":"done","task":title}
    for wid in WORKERS:
        if wid not in ws: ws[wid] = {"status":"idle","task":"Wacht op nieuwe opdracht"}
    return ws


def calc_financials():
    me = sum(e["amount"] for e in FINANCIALS["expenses"] if e["period"]=="maand")
    me += sum(e["amount"]/12 for e in FINANCIALS["expenses"] if e["period"]=="jaar")
    mr = sum(r["amount"] for r in FINANCIALS["revenue"] if r["period"]=="maand")
    return me, mr


def generate_html(tasks, worker_status):
    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    monthly_exp, monthly_rev = calc_financials()
    profit = monthly_rev - monthly_exp
    done_c  = sum(1 for t in tasks if t.get("status")=="done")
    run_c   = sum(1 for t in tasks if t.get("status")=="ready")
    ready_c = sum(1 for t in tasks if t.get("status")=="ready")
    tot_c   = len(tasks)

    # Worker data for JS
    wjs = []
    for wid, wi in WORKERS.items():
        ws = worker_status.get(wid, {"status":"idle","task":"Wacht"})
        dp = DESK_POSITIONS[wi["desk"]]
        wjs.append({
            "id": wid, "name": wi["name"], "emoji": wi["emoji"],
            "color": wi["color"], "role": wi["role"],
            "deskX": dp["x"], "deskY": dp["y"],
            "speed": wi["speed"],
            "status": ws["status"], "task": ws["task"],
        })
    workers_json = json.dumps(wjs)

    # Kanban cards
    kc = ""
    for t in tasks:
        s = t.get("status",""); a = t.get("assignee","?")
        wi2 = WORKERS.get(a, {"emoji":"🤖"})
        kc += f'<div class="kc-card {s}"><div class="kc-title">{wi2["emoji"]} {t.get("title","")}</div><div class="kc-meta">{a} · {s}</div></div>'
    if not kc: kc = '<div class="kc-card"><div class="kc-title">Geen taken</div></div>'

    # Activity
    dt = [t for t in tasks if t.get("status")=="done"]
    ah = ""
    for t in dt[:6]:
        a = t.get("assignee","?"); wi2 = WORKERS.get(a,{"emoji":"🤖","name":a})
        title = t.get("title","")
        ca = t.get("completed_at","")
        try: ts = datetime.fromtimestamp(int(ca)).strftime("%d/%m %H:%M") if ca else "recent"
        except: ts = "recent"
        ah += f'<div class="act-item"><span class="act-emoji">{wi2["emoji"]}</span><span class="act-text"><b>{wi2["name"]}</b> — {title}</span><span class="act-time">{ts}</span></div>'
    if not ah: ah = '<div class="act-item"><span class="act-text">Nog geen activiteit</span></div>'

    # Financials
    eh = ""
    for e in FINANCIALS["expenses"]:
        m = e["amount"] if e["period"]=="maand" else e["amount"]/12
        eh += f'<div class="fin-row"><span>{e["item"]}</span><span class="fin-amt">€{m:.2f}/{e["period"]}</span></div>'
    rh = ""
    for r in FINANCIALS["revenue"]:
        rh += f'<div class="fin-row"><span>{r["item"]}</span><span class="fin-amt pos">€{r["amount"]:.2f}/{r["period"]}</span></div>'

    return f'''<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Company — Live Dashboard</title>
<style>
:root{{--bg:#07111f;--bg2:#0b1220;--card:rgba(255,255,255,.08);--text:#f7fbff;--muted:#a9b8cc;--line:rgba(255,255,255,.12);--brand:#7c3aed;--brand2:#06b6d4;--ok:#34d399;--warn:#fbbf24;--danger:#f87171;--floor:#1e293b;--wall:#0f172a;--desk:#334155;--coffee:#78350f;--meeting:#1e3a5f;--door:#451a03}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:Inter,ui-sans-serif,system-ui,sans-serif;background:var(--bg);color:var(--text);overflow-x:hidden}}
a{{color:inherit}}
.wrap{{max-width:1320px;margin:auto;padding:20px 18px 54px}}

/* Header */
.hd{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px}}
.hd h1{{font-size:clamp(24px,4vw,38px);letter-spacing:-.04em;background:linear-gradient(135deg,var(--brand),var(--brand2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hd .sub{{color:var(--muted);font-size:12px;margin-top:2px}}
.live{{display:inline-flex;align-items:center;gap:7px;background:rgba(52,211,53,.1);border:1px solid rgba(52,211,153,.25);border-radius:999px;padding:5px 13px;font-size:11px;font-weight:700;color:var(--ok)}}
.live::before{{content:'';width:6px;height:6px;background:var(--ok);border-radius:50%;animation:blink 2s infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}

/* Mission */
.mission{{background:linear-gradient(135deg,rgba(124,58,237,.12),rgba(6,182,212,.08));border:1px solid rgba(124,58,237,.2);border-radius:18px;padding:18px 22px;margin-bottom:20px}}
.mission h2{{font-size:16px;font-weight:800;margin-bottom:6px}}
.mission p{{color:var(--muted);font-size:13px;line-height:1.6;max-width:780px}}
.goals{{display:flex;gap:12px;margin-top:12px;flex-wrap:wrap}}
.goal{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px 12px;font-size:11px}}
.goal b{{display:block;font-size:13px;color:var(--text);margin-bottom:1px}}

/* Stats */
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:8px;margin-bottom:20px}}
.stat{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;text-align:center}}
.stat b{{display:block;font-size:22px}}
.stat span{{color:var(--muted);font-size:10px}}

/* ═══════════════════════════════════════════
   2D TOP-DOWN OFFICE
   ═══════════════════════════════════════════ */
.office-wrap{{margin-bottom:28px}}
.office-title{{font-size:15px;font-weight:800;margin-bottom:10px;display:flex;align-items:center;gap:8px}}

.office{{
  position:relative;width:100%;aspect-ratio:16/10;
  background:var(--floor);
  border-radius:20px;border:1px solid var(--line);overflow:hidden;
  image-rendering:pixelated;
}}

/* Wall strip at top */
.wall-strip{{
  position:absolute;top:0;left:0;right:0;height:12%;
  background:var(--wall);border-bottom:2px solid rgba(255,255,255,.06);
}}

/* Windows on wall */
.win{{
  position:absolute;top:2%;width:8%;height:8%;
  background:linear-gradient(180deg,rgba(96,165,250,.2),rgba(96,165,250,.08));
  border:1px solid rgba(96,165,250,.25);border-radius:2px;
}}

/* Floor tiles pattern */
.floor-tiles{{
  position:absolute;bottom:0;left:0;right:0;height:88%;
  background-image:
    linear-gradient(rgba(255,255,255,.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.02) 1px, transparent 1px);
  background-size:40px 40px;
}}

/* ── Rooms ── */
.room{{
  position:absolute;border-radius:8px;display:flex;align-items:center;justify-content:center;
  font-size:10px;font-weight:700;text-align:center;line-height:1.3;
}}
.coffee-room{{
  left:5%;top:15%;width:18%;height:16%;
  background:rgba(120,53,15,.25);border:2px solid rgba(120,53,15,.4);
  color:#fbbf24;
}}
.meeting-room{{
  right:5%;top:15%;width:22%;height:16%;
  background:rgba(30,58,95,.4);border:2px solid rgba(30,58,95,.6);
  color:#60a5fa;
}}

/* ── Desks ── */
.desk{{
  position:absolute;
  width:10%;height:8%;
  background:var(--desk);border:1px solid rgba(255,255,255,.15);border-radius:4px;
  display:flex;align-items:center;justify-content:center;
  font-size:9px;font-weight:700;color:var(--muted);
  z-index:2;
}}
.desk::after{{
  content:attr(data-label);
  font-size:8px;font-weight:600;letter-spacing:.02em;
}}

/* ── Door ── */
.door{{
  position:absolute;
  left:42%;bottom:2%;width:16%;height:6%;
  background:linear-gradient(180deg,#78350f,#451a03);
  border:2px solid #92400e;border-radius:4px 4px 0 0;
  display:flex;align-items:center;justify-content:center;
  font-size:9px;font-weight:700;color:#fbbf24;z-index:3;
}}

/* ── Worker characters (top-down) ── */
.worker{{
  position:absolute;
  width:32px;height:32px;
  z-index:5;cursor:pointer;
  transition: transform .1s;
}}
.worker:hover{{z-index:20}}

/* Top-down character SVG */
.char-topdown{{width:32px;height:32px;position:relative}}

/* Shadow */
.char-shadow{{
  position:absolute;bottom:0;left:50%;transform:translateX(-50%);
  width:20px;height:6px;background:rgba(0,0,0,.3);border-radius:50%;
}}

/* Body (top-down: circle) */
.char-body{{
  position:absolute;bottom:4px;left:50%;transform:translateX(-50%);
  width:22px;height:22px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:11px;
  border:2px solid rgba(0,0,0,.2);
  box-shadow:0 2px 4px rgba(0,0,0,.3);
}}

/* Direction indicator (small line showing facing) */
.char-dir{{
  position:absolute;top:2px;left:50%;transform:translateX(-50%);
  width:0;height:0;
  border-left:3px solid transparent;border-right:3px solid transparent;
  border-bottom:5px solid rgba(255,255,255,.5);
}}

/* Walking animation */
.walking .char-body{{animation:walk-bob .35s ease-in-out infinite}}
.walking .char-shadow{{animation:walk-shadow .35s ease-in-out infinite}}
@keyframes walk-bob{{0%,100%{{transform:translateX(-50%) translateY(0)}}50%{{transform:translateX(-50%) translateY(-2px)}}}}
@keyframes walk-shadow{{0%,100%{{transform:translateX(-50%) scale(1);opacity:.3}}50%{{transform:translateX(-50%) scale(.8);opacity:.2}}}}

/* Working (sitting) animation */
.working .char-body{{animation:sit-bob 2s ease-in-out infinite}}
@keyframes sit-bob{{0%,100%{{transform:translateX(-50%) scale(1)}}50%{{transform:translateX(-50%) scale(1.05)}}}}

/* Idle breathing */
.idle .char-body{{animation:breathe 3s ease-in-out infinite}}
@keyframes breathe{{0%,100%{{transform:translateX(-50%) scale(1)}}50%{{transform:translateX(-50%) scale(1.03)}}}}

/* Status dot */
.sdot{{
  position:absolute;top:-2px;right:-2px;
  width:8px;height:8px;border-radius:50%;border:1.5px solid var(--floor);z-index:6;
}}
.sdot.busy{{background:var(--ok);animation:pulse-dot 2s infinite}}
.sdot.ready{{background:var(--warn)}}
.sdot.done{{background:var(--brand2)}}
.sdot.idle{{background:var(--muted)}}
@keyframes pulse-dot{{0%,100%{{box-shadow:0 0 0 0 rgba(52,211,153,.5)}}50%{{box-shadow:0 0 6px 2px rgba(52,211,153,.3)}}}}

/* Speech bubble */
.speech{{
  position:absolute;bottom:38px;left:50%;transform:translateX(-50%);
  background:rgba(15,23,42,.9);border:1px solid var(--line);
  border-radius:8px;padding:5px 8px;font-size:9px;color:var(--muted);
  white-space:nowrap;max-width:160px;overflow:hidden;text-overflow:ellipsis;
  opacity:0;transition:opacity .2s;pointer-events:none;z-index:30;
}}
.speech::after{{content:'';position:absolute;bottom:-5px;left:50%;transform:translateX(-50%);border-left:5px solid transparent;border-right:5px solid transparent;border-top:5px solid var(--line)}}
.worker:hover .speech{{opacity:1}}

/* ── Two-col ── */
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:28px}}
@media(max-width:768px){{.two-col{{grid-template-columns:1fr}}}}
.panel{{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px}}
.pt{{font-size:14px;font-weight:800;margin-bottom:12px;display:flex;align-items:center;gap:7px}}

/* Activity */
.act-item{{display:flex;align-items:center;gap:7px;padding:7px 0;border-bottom:1px solid var(--line);font-size:11px}}
.act-item:last-child{{border-bottom:none}}
.act-emoji{{font-size:16px;flex-shrink:0}}
.act-text{{flex:1;color:var(--muted)}}
.act-text b{{color:var(--text)}}
.act-time{{color:var(--muted);font-size:9px;flex-shrink:0}}

/* Financials */
.fin-row{{display:flex;justify-content:space-between;align-items:center;padding:5px 0;border-bottom:1px solid var(--line);font-size:11px}}
.fin-row:last-child{{border-bottom:none}}
.fin-amt{{font-weight:700}}
.fin-amt.pos{{color:var(--ok)}}
.fin-summary{{margin-top:10px;padding-top:10px;border-top:2px solid var(--line);display:flex;justify-content:space-between;font-weight:800;font-size:13px}}
.fin-summary .pos{{color:var(--ok)}}
.fin-summary .neg{{color:var(--danger)}}

/* Kanban */
.kanban{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px;margin-bottom:28px}}
.kc-card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;font-size:11px}}
.kc-card.done{{border-color:rgba(52,211,153,.2);opacity:.65}}
.kc-card.running{{border-color:rgba(251,191,36,.25)}}
.kc-card.ready{{border-color:rgba(96,165,250,.25)}}
.kc-title{{font-weight:700;margin-bottom:3px;font-size:12px}}
.kc-meta{{color:var(--muted);font-size:10px}}

footer{{text-align:center;color:var(--muted);font-size:10px;margin-top:28px;line-height:1.6}}
</style>
</head>
<body>
<div class="wrap">

<div class="hd">
  <div><h1>🛒 AI Company</h1><div class="sub">Volledig autonoom AI-gestuurde e-commerce · Laatste update: {now}</div></div>
  <div class="live">● LIVE</div>
</div>

<div class="mission">
  <h2>🎯 Missie</h2>
  <p>Wij bouwen en beheren volledig autonome e-commerce bedrijven. Ons AI-team werkt 24/7 aan het opzetten, optimaliseren en schalen van online winkels — van productresearch tot content, van SEO tot conversie. Jij beslist de strategie, wij doen het werk.</p>
  <div class="goals">
    <div class="goal"><b>€0 → €1K</b><span>Maandelijkse omzet</span></div>
    <div class="goal"><b>1 → 5</b><span>Actieve webshops</span></div>
    <div class="goal"><b>0 → 10K</b><span>Maandelijkse bezoekers</span></div>
    <div class="goal"><b>8 → 15</b><span>AI-werknemers</span></div>
  </div>
</div>

<div class="stats">
  <div class="stat"><b>{len(WORKERS)}</b><span>AI-werknemers</span></div>
  <div class="stat"><b>{tot_c}</b><span>Totaal taken</span></div>
  <div class="stat"><b>{done_c}</b><span>Afgerond</span></div>
  <div class="stat"><b>{run_c}</b><span>Bezig</span></div>
  <div class="stat"><b>{ready_c}</b><span>In wachtrij</span></div>
  <div class="stat"><b>€{monthly_exp:.0f}</b><span>Maandkosten</span></div>
  <div class="stat"><b>€{monthly_rev:.0f}</b><span>Maandomzet</span></div>
  <div class="stat"><b style="color:{'var(--ok)' if profit>=0 else 'var(--danger)'}">€{profit:.0f}</b><span>Maandwinst</span></div>
</div>

<!-- ═══ 2D TOP-DOWN OFFICE ═══ -->
<div class="office-wrap">
  <div class="office-title">🏢 Ons Kantoor — Top-Down View</div>
  <div class="office" id="office">

    <!-- Wall -->
    <div class="wall-strip"></div>

    <!-- Windows -->
    <div class="win" style="left:8%"></div>
    <div class="win" style="left:28%"></div>
    <div class="win" style="left:52%"></div>
    <div class="win" style="left:72%"></div>

    <!-- Floor tiles -->
    <div class="floor-tiles"></div>

    <!-- Coffee Corner -->
    <div class="room coffee-room">☕<br>Koffiecorner</div>

    <!-- Meeting Room -->
    <div class="room meeting-room">🤝<br>Meeting<br>Room</div>

    <!-- Desks -->
    <div class="desk" id="desk-1" data-label="Ops"     style="left:8%;top:38%"></div>
    <div class="desk" id="desk-2" data-label="Research" style="left:22%;top:38%"></div>
    <div class="desk" id="desk-3" data-label="Dev"      style="left:36%;top:38%"></div>
    <div class="desk" id="desk-4" data-label="Review"   style="left:50%;top:38%"></div>
    <div class="desk" id="desk-5" data-label="PM"       style="left:8%;top:58%"></div>
    <div class="desk" id="desk-6" data-label="Data"     style="left:22%;top:58%"></div>
    <div class="desk" id="desk-7" data-label="Design"   style="left:36%;top:58%"></div>
    <div class="desk" id="desk-8" data-label="Security" style="left:50%;top:58%"></div>

    <!-- Door -->
    <div class="door">🚪 Ingang</div>

    <!-- Workers injected by JS -->
  </div>
</div>

<div class="two-col">
  <div class="panel">
    <div class="pt">📋 Recente Activiteit</div>
    {ah}
  </div>
  <div class="panel">
    <div class="pt">💰 Financiën</div>
    <div style="margin-bottom:8px;color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.04em;font-weight:700">Uitgaven</div>
    {eh}
    <div style="margin:8px 0 6px;color:var(--ok);font-size:10px;text-transform:uppercase;letter-spacing:.04em;font-weight:700">Inkomsten</div>
    {rh}
    <div class="fin-summary">
      <span>Maandelijks resultaat</span>
      <span class="{'pos' if profit>=0 else 'neg'}" style="color:{'var(--ok)' if profit>=0 else 'var(--danger)'}">{'+' if profit>=0 else ''}€{profit:.2f}</span>
    </div>
  </div>
</div>

<div class="pt" style="margin-bottom:10px">📌 Kanban Board</div>
<div class="kanban">{kc}</div>

<footer>AI Company Dashboard v3 · 2D Top-Down Office · Laatste build: {now} · <a href="https://github.com/pehur00/ecommerce-company" style="color:var(--brand2)">GitHub</a></footer>
</div>

<script>
const workers = {workers_json};
const office = document.getElementById('office');

// Create worker DOM
workers.forEach(w => {{
  const el = document.createElement('div');
  el.className = 'worker';
  el.id = 'w-' + w.id;
  el.innerHTML = `
    <div class="char-topdown">
      <div class="char-shadow"></div>
      <div class="char-body" style="background:${{w.color}};border-color:${{w.color}}">
        ${{w.emoji}}
      </div>
      <div class="char-dir"></div>
    </div>
    <div class="sdot ${{w.status}}"></div>
    <div class="speech">${{w.task.length > 45 ? w.task.substring(0,42) + '...' : w.task}}</div>
  `;
  office.appendChild(el);
}});

// ── Animation state ──
const S = {{}};
workers.forEach(w => {{
  // Start at door, walk to desk
  S[w.id] = {{
    x: 45, y: 95,          // start at door
    tx: w.deskX, ty: w.deskY,  // target = desk
    state: 'walking-to-desk',
    speed: w.speed,
    el: document.getElementById('w-' + w.id),
    body: document.querySelector('#w-' + w.id + ' .char-body'),
    shadow: document.querySelector('#w-' + w.id + ' .char-shadow'),
    dir: document.querySelector('#w-' + w.id + ' .char-dir'),
    pause: 0,
    coffeeTimer: 0,
    meetingTimer: 0,
  }};
}});

// Waypoints for interesting paths
function getWaypoints(fromX, fromY, toX, toY, worker) {{
  const pts = [];
  // 30% chance to detour via coffee
  if (Math.random() < 0.3 && fromY > 25) {{
    pts.push({{ x: COFFEE_CORNER.x, y: COFFEE_CORNER.y, label: 'coffee' }});
  }}
  // 15% chance to detour via meeting room
  if (Math.random() < 0.15 && fromY > 25) {{
    pts.push({{ x: MEETING_ROOM.x, y: MEETING_ROOM.y, label: 'meeting' }});
  }}
  pts.push({{ x: toX, y: toY, label: 'desk' }});
  return pts;
}}

const COFFEE_CORNER = {{ x: 14, y: 23 }};
const MEETING_ROOM = {{ x: 81, y: 23 }};

// Initialize: send everyone to their desk with possible detours
workers.forEach(w => {{
  const s = S[w.id];
  s.waypoints = getWaypoints(s.x, s.y, w.deskX, w.deskY, w);
  s.wpIndex = 0;
  s.state = 'walking';
  s.el.classList.add('walking');
}});

let lastT = 0;
function animate(ts) {{
  const dt = lastT ? (ts - lastT) / 1000 : 0;
  lastT = ts;

  workers.forEach(w => {{
    const s = S[w.id];
    if (!s.el) return;

    // Pause timer
    if (s.pause > 0) {{
      s.pause -= dt;
      s.el.classList.remove('walking');
      s.el.classList.add('working');
      return;
    }}

    // Get current target waypoint
    const wp = s.waypoints[s.wpIndex];
    if (!wp) {{ s.state = 'working'; s.el.classList.remove('walking'); s.el.classList.add('working'); return; }}

    const dx = wp.x - s.x;
    const dy = wp.y - s.y;
    const dist = Math.sqrt(dx*dx + dy*dy);

    if (dist < 1.5) {{
      // Arrived at waypoint
      s.wpIndex++;
      s.el.classList.remove('walking');
      s.el.classList.add('working');

      if (wp.label === 'coffee') {{
        s.pause = 2 + Math.random() * 3;  // 2-5s coffee break
      }} else if (wp.label === 'meeting') {{
        s.pause = 3 + Math.random() * 4;  // 3-7s meeting
      }} else {{
        s.pause = 1 + Math.random() * 2;  // 1-3s at desk
      }}
      return;
    }}

    // Move toward waypoint
    const move = s.speed * dt * 12;
    s.x += (dx / dist) * move;
    s.y += (dy / dist) * move;

    // Flip direction indicator
    if (s.dir) {{
      s.dir.style.transform = dx < 0 ? 'translateX(-50%) scaleX(-1)' : 'translateX(-50%)';
    }}

    s.el.style.left = s.x + '%';
    s.el.style.top = s.y + '%';
    s.el.classList.add('walking');
    s.el.classList.remove('working');
  }});

  requestAnimationFrame(animate);
}}

requestAnimationFrame(animate);

// Click worker → quick info
workers.forEach(w => {{
  document.getElementById('w-' + w.id).addEventListener('click', function() {{
    this.style.transform = 'scale(1.3)';
    setTimeout(() => this.style.transform = '', 200);
  }});
}});
</script>
</body>
</html>'''


def main():
    print("🔨 Building AI Company Dashboard v3 (2D top-down office)...")
    tasks = get_kanban_data()
    ws = get_worker_status(tasks)
    print(f"  📊 {len(tasks)} tasks, {len(ws)} workers")
    html = generate_html(tasks, ws)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ {os.path.getsize(OUTPUT_PATH)/1024:.1f} KB → {OUTPUT_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
