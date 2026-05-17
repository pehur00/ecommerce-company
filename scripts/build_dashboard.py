#!/usr/bin/env python3
"""
Build script for AI Company Dashboard v2.
Animated office with walking SVG characters, speech bubbles, and clear mission.
"""

import subprocess
import json
import os
import sys
from datetime import datetime

DASHBOARD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(DASHBOARD_DIR, "docs", "index.html")

WORKERS = {
    "worker-ops": {
        "name": "Ops",
        "emoji": "⚙️",
        "color": "#34d399",
        "bg": "rgba(52,211,153,.15)",
        "role": "Operations & Infrastructure",
        "desk": 1,
        "walk_speed": 12,
    },
    "worker-researcher": {
        "name": "Research",
        "emoji": "🔬",
        "color": "#a78bfa",
        "bg": "rgba(167,139,250,.15)",
        "role": "Research & Content",
        "desk": 2,
        "walk_speed": 10,
    },
    "worker-developer": {
        "name": "Dev",
        "emoji": "💻",
        "color": "#60a5fa",
        "bg": "rgba(96,165,250,.15)",
        "role": "Software Development",
        "desk": 3,
        "walk_speed": 14,
    },
    "worker-reviewer": {
        "name": "Review",
        "emoji": "🔍",
        "color": "#fbbf24",
        "bg": "rgba(251,191,36,.15)",
        "role": "Quality Assurance",
        "desk": 4,
        "walk_speed": 11,
    },
    "worker-pm": {
        "name": "PM",
        "emoji": "📋",
        "color": "#fb923c",
        "bg": "rgba(251,146,60,.15)",
        "role": "Project Management",
        "desk": 5,
        "walk_speed": 13,
    },
    "worker-data": {
        "name": "Data",
        "emoji": "📊",
        "color": "#f87171",
        "bg": "rgba(248,113,113,.15)",
        "role": "Data Engineering",
        "desk": 6,
        "walk_speed": 9,
    },
    "worker-designer": {
        "name": "Design",
        "emoji": "🎨",
        "color": "#f472b6",
        "bg": "rgba(244,114,182,.15)",
        "role": "UI/UX Design",
        "desk": 7,
        "walk_speed": 15,
    },
    "security": {
        "name": "Security",
        "emoji": "🛡️",
        "color": "#94a3b8",
        "bg": "rgba(148,163,184,.15)",
        "role": "Security & Compliance",
        "desk": 8,
        "walk_speed": 8,
    },
}

FINANCIALS = {
    "expenses": [
        {"item": "GitHub Pro", "amount": 4.00, "period": "maand", "category": "tools"},
        {"item": "VPS Hosting", "amount": 15.00, "period": "maand", "category": "infra"},
        {"item": "Domain (.nl)", "amount": 10.00, "period": "jaar", "category": "infra"},
        {"item": "Amazon.nl Partner", "amount": 0.00, "period": "gratis", "category": "marketing"},
        {"item": "Bol.com Partner", "amount": 0.00, "period": "gratis", "category": "marketing"},
        {"item": "MailerLite", "amount": 0.00, "period": "gratis", "category": "marketing"},
    ],
    "revenue": [
        {"item": "Amazon.nl Affiliate", "amount": 0.00, "period": "maand", "category": "affiliate"},
        {"item": "Bol.com Affiliate", "amount": 0.00, "period": "maand", "category": "affiliate"},
    ]
}


def get_kanban_data():
    try:
        result = subprocess.run(
            ["hermes", "kanban", "--board", "ecommerce", "list", "--json"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        print(f"Warning: Could not fetch kanban data: {e}")
    return []


def get_worker_status(tasks):
    worker_status = {}
    for task in tasks:
        assignee = task.get("assignee", "")
        status = task.get("status", "")
        title = task.get("title", "")
        if assignee in WORKERS:
            if status == "running":
                worker_status[assignee] = {"status": "busy", "task": title}
            elif status == "ready" and assignee not in worker_status:
                worker_status[assignee] = {"status": "ready", "task": title}
            elif status == "done" and assignee not in worker_status:
                worker_status[assignee] = {"status": "done", "task": title}
    for wid in WORKERS:
        if wid not in worker_status:
            worker_status[wid] = {"status": "idle", "task": "Wacht op nieuwe opdracht"}
    return worker_status


def calc_financials():
    monthly_exp = sum(e["amount"] for e in FINANCIALS["expenses"] if e["period"] == "maand")
    monthly_exp += sum(e["amount"] / 12 for e in FINANCIALS["expenses"] if e["period"] == "jaar")
    monthly_rev = sum(r["amount"] for r in FINANCIALS["revenue"] if r["period"] == "maand")
    return monthly_exp, monthly_rev


def generate_html(tasks, worker_status):
    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    monthly_exp, monthly_rev = calc_financials()
    profit = monthly_rev - monthly_exp
    done_count = sum(1 for t in tasks if t.get("status") == "done")
    running_count = sum(1 for t in tasks if t.get("status") == "running")
    ready_count = sum(1 for t in tasks if t.get("status") == "ready")
    total_count = len(tasks)

    # Build worker data for JS
    workers_js = []
    for wid, winfo in WORKERS.items():
        ws = worker_status.get(wid, {"status": "idle", "task": "Wacht op nieuwe opdracht"})
        workers_js.append({
            "id": wid,
            "name": winfo["name"],
            "emoji": winfo["emoji"],
            "color": winfo["color"],
            "role": winfo["role"],
            "desk": winfo["desk"],
            "walkSpeed": winfo["walk_speed"],
            "status": ws["status"],
            "task": ws["task"],
        })
    workers_json = json.dumps(workers_js)

    # Kanban cards
    kanban_cards = ""
    for t in tasks:
        status = t.get("status", "")
        assignee = t.get("assignee", "?")
        winfo = WORKERS.get(assignee, {"emoji": "🤖"})
        title = t.get("title", "")
        kanban_cards += f'<div class="kc-card {status}"><div class="kc-title">{winfo["emoji"]} {title}</div><div class="kc-meta">{assignee} · {status}</div></div>'
    if not kanban_cards:
        kanban_cards = '<div class="kc-card"><div class="kc-title">Geen taken</div></div>'

    # Activity feed
    done_tasks = [t for t in tasks if t.get("status") == "done"]
    recent_html = ""
    for t in done_tasks[:6]:
        assignee = t.get("assignee", "?")
        winfo = WORKERS.get(assignee, {"emoji": "🤖", "name": assignee})
        title = t.get("title", "")
        completed = t.get("completed_at", "")
        if completed:
            try:
                dt = datetime.fromtimestamp(int(completed))
                time_str = dt.strftime("%d/%m %H:%M")
            except:
                time_str = "recent"
        else:
            time_str = "recent"
        recent_html += f'<div class="act-item"><span class="act-emoji">{winfo["emoji"]}</span><span class="act-text"><b>{winfo["name"]}</b> — {title}</span><span class="act-time">{time_str}</span></div>'
    if not recent_html:
        recent_html = '<div class="act-item"><span class="act-text">Nog geen activiteit</span></div>'

    # Expenses
    exp_html = ""
    for e in FINANCIALS["expenses"]:
        monthly = e["amount"] if e["period"] == "maand" else e["amount"] / 12
        exp_html += f'<div class="fin-row"><span>{e["item"]}</span><span class="fin-amt">€{monthly:.2f}/{e["period"]}</span></div>'

    rev_html = ""
    for r in FINANCIALS["revenue"]:
        rev_html += f'<div class="fin-row"><span>{r["item"]}</span><span class="fin-amt pos">€{r["amount"]:.2f}/{r["period"]}</span></div>'

    return f'''<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Company — Live Dashboard</title>
<meta name="description" content="Live dashboard van ons AI-gestuurde e-commerce bedrijf">
<style>
:root {{
    --bg: #07111f;
    --bg2: #0b1220;
    --card: rgba(255,255,255,.08);
    --card2: rgba(255,255,255,.12);
    --text: #f7fbff;
    --muted: #a9b8cc;
    --line: rgba(255,255,255,.12);
    --brand: #7c3aed;
    --brand2: #06b6d4;
    --ok: #34d399;
    --warn: #fbbf24;
    --danger: #f87171;
    --office-floor: #1a2332;
    --office-wall: #0f172a;
    --desk-color: #2d3748;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    overflow-x: hidden;
}}
a {{ color: inherit; }}
.wrap {{ max-width: 1320px; margin: auto; padding: 20px 18px 54px; }}

/* ── Header ── */
.header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 12px;
}}
.header h1 {{
    font-size: clamp(24px, 4vw, 40px);
    letter-spacing: -.04em;
    background: linear-gradient(135deg, var(--brand), var(--brand2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.header .sub {{ color: var(--muted); font-size: 13px; margin-top: 2px; }}
.live-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(52,211,153,.12);
    border: 1px solid rgba(52,211,153,.25);
    border-radius: 999px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 700;
    color: var(--ok);
}}
.live-badge::before {{
    content: '';
    width: 7px; height: 7px;
    background: var(--ok);
    border-radius: 50%;
    animation: blink 2s infinite;
}}
@keyframes blink {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:.3; }} }}

/* ── Mission Banner ── */
.mission {{
    background: linear-gradient(135deg, rgba(124,58,237,.15), rgba(6,182,212,.1));
    border: 1px solid rgba(124,58,237,.25);
    border-radius: 20px;
    padding: 20px 24px;
    margin-bottom: 24px;
}}
.mission h2 {{
    font-size: 18px;
    font-weight: 800;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.mission p {{
    color: var(--muted);
    font-size: 14px;
    line-height: 1.6;
    max-width: 800px;
}}
.mission .goals {{
    display: flex;
    gap: 16px;
    margin-top: 14px;
    flex-wrap: wrap;
}}
.goal {{
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 10px 14px;
    font-size: 12px;
}}
.goal b {{ display: block; font-size: 14px; color: var(--text); margin-bottom: 2px; }}

/* ── Stats ── */
.stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 10px;
    margin-bottom: 24px;
}}
.stat {{
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 14px;
    text-align: center;
}}
.stat b {{ display: block; font-size: 24px; }}
.stat span {{ color: var(--muted); font-size: 11px; }}

/* ── Office ── */
.office-container {{
    position: relative;
    margin-bottom: 32px;
}}
.office {{
    position: relative;
    width: 100%;
    height: 420px;
    background: linear-gradient(180deg, var(--office-wall) 0%, var(--office-wall) 60%, var(--office-floor) 60%, var(--office-floor) 100%);
    border-radius: 24px;
    border: 1px solid var(--line);
    overflow: hidden;
}}

/* Wall decorations */
.office::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--brand), var(--brand2), var(--brand));
}}
.window {{
    position: absolute;
    top: 20px;
    width: 60px;
    height: 80px;
    background: linear-gradient(180deg, rgba(96,165,250,.15), rgba(96,165,250,.05));
    border: 2px solid rgba(96,165,250,.2);
    border-radius: 4px 4px 0 0;
}}
.window::after {{
    content: '';
    position: absolute;
    top: 50%; left: 0; right: 0;
    height: 2px;
    background: rgba(96,165,250,.2);
}}
.window::before {{
    content: '';
    position: absolute;
    left: 50%; top: 0; bottom: 0;
    width: 2px;
    background: rgba(96,165,250,.2);
}}

/* Desks row */
.desks {{
    position: absolute;
    bottom: 100px;
    left: 0;
    right: 0;
    display: flex;
    justify-content: space-around;
    padding: 0 20px;
}}
.desk {{
    width: 100px;
    height: 50px;
    background: var(--desk-color);
    border-radius: 8px 8px 0 0;
    border: 1px solid rgba(255,255,255,.1);
    border-bottom: none;
    position: relative;
    display: flex;
    align-items: flex-start;
    justify-content: center;
    padding-top: 4px;
}}
.desk::after {{
    content: attr(data-label);
    font-size: 9px;
    color: var(--muted);
    font-weight: 700;
    text-align: center;
}}
.desk-monitor {{
    position: absolute;
    top: -30px;
    width: 50px;
    height: 30px;
    background: #1e293b;
    border: 2px solid #334155;
    border-radius: 3px;
    left: 50%;
    transform: translateX(-50%);
}}
.desk-monitor::after {{
    content: '';
    position: absolute;
    bottom: -8px;
    left: 50%;
    transform: translateX(-50%);
    width: 16px;
    height: 6px;
    background: #334155;
}}

/* Floor line */
.floor {{
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 100px;
    background: linear-gradient(180deg, var(--office-floor), #151d2a);
}}
.floor::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: rgba(255,255,255,.05);
}}

/* ── Worker characters ── */
.worker {{
    position: absolute;
    bottom: 100px;
    width: 44px;
    height: 44px;
    transition: left linear;
    z-index: 10;
    cursor: pointer;
}}
.worker:hover {{ z-index: 20; }}

/* SVG character */
.char {{
    width: 44px;
    height: 44px;
    position: relative;
}}
.char-body {{
    width: 28px;
    height: 32px;
    border-radius: 8px 8px 4px 4px;
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    animation: bob 1.5s ease-in-out infinite;
}}
.char-head {{
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: #fbbf24;
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    border: 2px solid rgba(0,0,0,.15);
}}
.char-eyes {{
    position: absolute;
    top: 8px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 4px;
}}
.char-eyes span {{
    width: 3px;
    height: 3px;
    background: #1e293b;
    border-radius: 50%;
    animation: blink-eyes 4s infinite;
}}
@keyframes blink-eyes {{ 0%,90%,100% {{ opacity:1; }} 95% {{ opacity:0; }} }}
@keyframes bob {{ 0%,100% {{ transform: translateX(-50%) translateY(0); }} 50% {{ transform: translateX(-50%) translateY(-2px); }} }}

/* Walking animation */
.walking .char-body {{ animation: walk-bob .4s ease-in-out infinite; }}
.walking .char-head {{ animation: walk-head .4s ease-in-out infinite; }}
@keyframes walk-bob {{ 0%,100% {{ transform: translateX(-50%) translateY(0) rotate(-2deg); }} 50% {{ transform: translateX(-50%) translateY(-3px) rotate(2deg); }} }}
@keyframes walk-head {{ 0%,100% {{ transform: translateX(-50%) translateY(0); }} 50% {{ transform: translateX(-50%) translateY(-1px); }} }}

/* Working animation (sitting) */
.working .char-body {{ animation: type .3s ease-in-out infinite; }}
@keyframes type {{ 0%,100% {{ transform: translateX(-50%) translateY(0); }} 50% {{ transform: translateX(-50%) translateY(-1px); }} }}

/* Idle animation */
.idle .char-body {{ animation: breathe 3s ease-in-out infinite; }}
@keyframes breathe {{ 0%,100% {{ transform: translateX(-50%) scale(1); }} 50% {{ transform: translateX(-50%) scale(1.03); }} }}

/* Speech bubble */
.speech {{
    position: absolute;
    top: -52px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--card2);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 6px 10px;
    font-size: 10px;
    color: var(--muted);
    white-space: nowrap;
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    opacity: 0;
    transition: opacity .3s;
    pointer-events: none;
    z-index: 30;
}}
.speech::after {{
    content: '';
    position: absolute;
    bottom: -6px;
    left: 50%;
    transform: translateX(-50%);
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 6px solid var(--line);
}}
.worker:hover .speech {{ opacity: 1; }}

/* Status dot on character */
.status-dot {{
    position: absolute;
    top: -2px;
    right: -2px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    border: 2px solid var(--bg);
    z-index: 5;
}}
.status-dot.busy {{ background: var(--ok); animation: pulse-dot 2s infinite; }}
.status-dot.ready {{ background: var(--warn); }}
.status-dot.done {{ background: var(--brand2); }}
.status-dot.idle {{ background: var(--muted); }}
@keyframes pulse-dot {{ 0%,100% {{ box-shadow: 0 0 0 0 rgba(52,211,153,.4); }} 50% {{ box-shadow: 0 0 8px 2px rgba(52,211,153,.3); }} }}

/* ── Two-col ── */
.two-col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 32px;
}}
@media(max-width: 768px) {{
    .two-col {{ grid-template-columns: 1fr; }}
    .office {{ height: 360px; }}
    .desks {{ padding: 0 10px; }}
    .desk {{ width: 70px; }}
}}

/* Panel */
.panel {{
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 20px;
    padding: 20px;
}}
.panel-title {{
    font-size: 15px;
    font-weight: 800;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}}

/* Activity */
.act-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 0;
    border-bottom: 1px solid var(--line);
    font-size: 12px;
}}
.act-item:last-child {{ border-bottom: none; }}
.act-emoji {{ font-size: 18px; flex-shrink: 0; }}
.act-text {{ flex: 1; color: var(--muted); }}
.act-text b {{ color: var(--text); }}
.act-time {{ color: var(--muted); font-size: 10px; flex-shrink: 0; }}

/* Financials */
.fin-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid var(--line);
    font-size: 12px;
}}
.fin-row:last-child {{ border-bottom: none; }}
.fin-amt {{ font-weight: 700; }}
.fin-amt.pos {{ color: var(--ok); }}
.fin-summary {{
    margin-top: 12px;
    padding-top: 12px;
    border-top: 2px solid var(--line);
    display: flex;
    justify-content: space-between;
    font-weight: 800;
    font-size: 14px;
}}
.fin-summary .pos {{ color: var(--ok); }}
.fin-summary .neg {{ color: var(--danger); }}

/* Kanban */
.kanban {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 10px;
    margin-bottom: 32px;
}}
.kc-card {{
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 14px;
    font-size: 12px;
}}
.kc-card.done {{ border-color: rgba(52,211,153,.25); opacity: .7; }}
.kc-card.running {{ border-color: rgba(251,191,36,.25); }}
.kc-card.ready {{ border-color: rgba(96,165,250,.25); }}
.kc-title {{ font-weight: 700; margin-bottom: 4px; font-size: 13px; }}
.kc-meta {{ color: var(--muted); font-size: 11px; }}

/* Footer */
footer {{
    text-align: center;
    color: var(--muted);
    font-size: 11px;
    margin-top: 32px;
    line-height: 1.6;
}}
</style>
</head>
<body>
<div class="wrap">

<!-- Header -->
<div class="header">
    <div>
        <h1>🛒 AI Company</h1>
        <div class="sub">Volledig autonoom AI-gestuurde e-commerce · Laatste update: {now}</div>
    </div>
    <div class="live-badge">● LIVE</div>
</div>

<!-- Mission -->
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

<!-- Stats -->
<div class="stats">
    <div class="stat"><b>{len(WORKERS)}</b><span>AI-werknemers</span></div>
    <div class="stat"><b>{total_count}</b><span>Totaal taken</span></div>
    <div class="stat"><b>{done_count}</b><span>Afgerond</span></div>
    <div class="stat"><b>{running_count}</b><span>Bezig</span></div>
    <div class="stat"><b>{ready_count}</b><span>In wachtrij</span></div>
    <div class="stat"><b>€{monthly_exp:.0f}</b><span>Maandkosten</span></div>
    <div class="stat"><b>€{monthly_rev:.0f}</b><span>Maandomzet</span></div>
    <div class="stat"><b class="{'pos' if profit >= 0 else 'neg'}" style="color:{'var(--ok)' if profit >= 0 else 'var(--danger)'}">€{profit:.0f}</b><span>Maandwinst</span></div>
</div>

<!-- Office -->
<div class="office-container">
    <div class="panel-title">🏢 Ons Kantoor</div>
    <div class="office" id="office">
        <!-- Windows -->
        <div class="window" style="left:8%;"></div>
        <div class="window" style="left:30%;"></div>
        <div class="window" style="left:52%;"></div>
        <div class="window" style="left:74%;"></div>
        <div class="window" style="left:90%;"></div>

        <!-- Desks -->
        <div class="desks" id="desks">
            <div class="desk" data-label="Ops"><div class="desk-monitor"></div></div>
            <div class="desk" data-label="Research"><div class="desk-monitor"></div></div>
            <div class="desk" data-label="Dev"><div class="desk-monitor"></div></div>
            <div class="desk" data-label="Review"><div class="desk-monitor"></div></div>
            <div class="desk" data-label="PM"><div class="desk-monitor"></div></div>
            <div class="desk" data-label="Data"><div class="desk-monitor"></div></div>
            <div class="desk" data-label="Design"><div class="desk-monitor"></div></div>
            <div class="desk" data-label="Security"><div class="desk-monitor"></div></div>
        </div>

        <!-- Floor -->
        <div class="floor"></div>

        <!-- Workers will be injected here by JS -->
    </div>
</div>

<!-- Two-col -->
<div class="two-col">
    <div class="panel">
        <div class="panel-title">📋 Recente Activiteit</div>
        {recent_html}
    </div>
    <div class="panel">
        <div class="panel-title">💰 Financiën</div>
        <div style="margin-bottom:10px;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.04em;font-weight:700;">Uitgaven</div>
        {exp_html}
        <div style="margin:10px 0 8px;color:var(--ok);font-size:11px;text-transform:uppercase;letter-spacing:.04em;font-weight:700;">Inkomsten</div>
        {rev_html}
        <div class="fin-summary">
            <span>Maandelijks resultaat</span>
            <span class="{'pos' if profit >= 0 else 'neg'}" style="color:{'var(--ok)' if profit >= 0 else 'var(--danger)'}">{'+' if profit >= 0 else ''}€{profit:.2f}</span>
        </div>
    </div>
</div>

<!-- Kanban -->
<div class="panel-title">📌 Kanban Board</div>
<div class="kanban">
    {kanban_cards}
</div>

<footer>
    AI Company Dashboard v2 · Automatisch gegenereerd · Laatste build: {now}<br>
    Data: kanban board "ecommerce" · <a href="https://github.com/pehur00/ecommerce-company" style="color:var(--brand2);">GitHub</a>
</footer>

</div>

<script>
// Worker data from server
const workers = {workers_json};
const office = document.getElementById('office');
const FLOOR_BOTTOM = 100;
const DESK_AREA_BOTTOM = 150;

// Create worker DOM elements
workers.forEach(w => {{
    const el = document.createElement('div');
    el.className = 'worker';
    el.id = 'worker-' + w.id;
    el.innerHTML = `
        <div class="char">
            <div class="char-head">
                <div class="char-eyes"><span></span><span></span></div>
            </div>
            <div class="char-body" style="background:${{w.color}};border:2px solid ${{w.color}};">
                ${{w.emoji}}
            </div>
        </div>
        <div class="status-dot ${{w.status}}"></div>
        <div class="speech">${{w.task.length > 50 ? w.task.substring(0,47) + '...' : w.task}}</div>
    `;
    office.appendChild(el);
}});

// Animation state
const state = {{}};
workers.forEach(w => {{
    state[w.id] = {{
        x: Math.random() * 80 + 10, // % position
        targetX: Math.random() * 80 + 10,
        speed: w.walkSpeed,
        status: w.status,
        paused: false,
        pauseTime: 0,
        element: document.getElementById('worker-' + w.id),
        charElement: document.querySelector('#worker-' + w.id + ' .char'),
    }};
}});

// Move worker to their desk
function goToDesk(wid) {{
    const w = workers.find(wr => wr.id === wid);
    if (!w) return;
    const deskIndex = (w.desk - 1) / workers.length;
    state[wid].targetX = deskIndex * 80 + 10 + Math.random() * 8 - 4;
    state[wid].status = 'working';
    state[wid].element.classList.remove('walking', 'idle');
    state[wid].element.classList.add('working');
}}

// Move worker to random position
function wander(wid) {{
    state[wid].targetX = Math.random() * 85 + 5;
    state[wid].status = 'walking';
    state[wid].element.classList.remove('working', 'idle');
    state[wid].element.classList.add('walking');
}}

// Set idle
function setIdle(wid) {{
    state[wid].status = 'idle';
    state[wid].element.classList.remove('walking', 'working');
    state[wid].element.classList.add('idle');
}}

// Animation loop
let lastTime = 0;
function animate(timestamp) {{
    const dt = lastTime ? (timestamp - lastTime) / 1000 : 0;
    lastTime = timestamp;

    workers.forEach(w => {{
        const s = state[w.id];
        if (!s.element) return;

        // If working at desk, occasionally look around
        if (s.status === 'working' && Math.random() < 0.002) {{
            s.paused = true;
            s.pauseTime = 1 + Math.random() * 2;
        }}

        if (s.paused) {{
            s.pauseTime -= dt;
            if (s.pauseTime <= 0) {{
                s.paused = false;
                // After pause, wander or return
                if (Math.random() < 0.4) {{
                    wander(w.id);
                }}
            }}
            return;
        }}

        // Walking logic
        if (s.status === 'walking') {{
            const dx = s.targetX - s.x;
            const dist = Math.abs(dx);
            if (dist < 1) {{
                // Arrived — pause then decide
                s.paused = true;
                s.pauseTime = 1.5 + Math.random() * 3;
                s.element.classList.remove('walking');
                s.element.classList.add('idle');
                s.status = 'idle';
            }} else {{
                const dir = dx > 0 ? 1 : -1;
                const move = dir * s.speed * dt * 3;
                s.x += move;
                s.element.style.left = s.x + '%';
                // Flip character based on direction
                s.charElement.style.transform = dx < 0 ? 'scaleX(-1)' : '';
            }}
        }}

        // Idle — occasionally wander
        if (s.status === 'idle' && Math.random() < 0.003) {{
            wander(w.id);
        }}
    }});

    requestAnimationFrame(animate);
}}

// Initialize positions
workers.forEach(w => {{
    const s = state[w.id];
    s.x = Math.random() * 80 + 10;
    s.targetX = s.x;
    s.element.style.left = s.x + '%';
    // Start some walking, some at desks
    if (w.status === 'busy') {{
        goToDesk(w.id);
    }} else if (Math.random() < 0.5) {{
        wander(w.id);
    }} else {{
        setIdle(w.id);
    }}
}});

// Start animation
requestAnimationFrame(animate);

// Click on worker to see info
workers.forEach(w => {{
    const el = document.getElementById('worker-' + w.id);
    el.addEventListener('click', () => {{
        // Quick bounce
        el.style.transform = 'scale(1.2)';
        setTimeout(() => el.style.transform = '', 200);
    }});
}});
</script>
</body>
</html>'''


def main():
    print("🔨 Building AI Company Dashboard v2...")

    tasks = get_kanban_data()
    worker_status = get_worker_status(tasks)

    print(f"  📊 {len(tasks)} tasks fetched")
    print(f"  👥 {len(worker_status)} workers tracked")

    html = generate_html(tasks, worker_status)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"  ✅ Dashboard v2 written ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
