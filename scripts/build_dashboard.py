#!/usr/bin/env python3
"""
Build script for AI Company Dashboard.
Fetches live kanban data and generates a static HTML dashboard.
"""

import subprocess
import json
import os
import sys
from datetime import datetime

DASHBOARD_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(DASHBOARD_DIR, "dashboard", "index.html")

# Worker profiles with their visual identity
WORKERS = {
    "worker-ops": {
        "name": "Ops",
        "emoji": "⚙️",
        "color": "#34d399",
        "bg": "rgba(52,211,153,.15)",
        "role": "Operations & Infrastructure",
        "tasks": ["Deployments", "Server setup", "Monitoring", "CI/CD"]
    },
    "worker-researcher": {
        "name": "Research",
        "emoji": "🔬",
        "color": "#a78bfa",
        "bg": "rgba(167,139,250,.15)",
        "role": "Research & Content",
        "tasks": ["SEO articles", "Market research", "Data analysis", "Content writing"]
    },
    "worker-developer": {
        "name": "Dev",
        "emoji": "💻",
        "color": "#60a5fa",
        "bg": "rgba(96,165,250,.15)",
        "role": "Software Development",
        "tasks": ["Feature building", "Bug fixes", "Scrapers", "Automation"]
    },
    "worker-reviewer": {
        "name": "Review",
        "emoji": "🔍",
        "color": "#fbbf24",
        "bg": "rgba(251,191,36,.15)",
        "role": "Quality Assurance",
        "tasks": ["Code review", "Security audit", "Testing", "Approval gates"]
    },
    "worker-pm": {
        "name": "PM",
        "emoji": "📋",
        "color": "#fb923c",
        "bg": "rgba(251,146,60,.15)",
        "role": "Project Management",
        "tasks": ["Planning", "Coordination", "Reporting", "Prioritization"]
    },
    "worker-data": {
        "name": "Data",
        "emoji": "📊",
        "color": "#f87171",
        "bg": "rgba(248,113,113,.15)",
        "role": "Data Engineering",
        "tasks": ["Analytics", "Dashboards", "ETL pipelines", "Reporting"]
    },
    "worker-designer": {
        "name": "Design",
        "emoji": "🎨",
        "color": "#f472b6",
        "bg": "rgba(244,114,182,.15)",
        "role": "UI/UX Design",
        "tasks": ["Visual design", "Prototypes", "Branding", "User experience"]
    },
    "security": {
        "name": "Security",
        "emoji": "🛡️",
        "color": "#94a3b8",
        "bg": "rgba(148,163,184,.15)",
        "role": "Security & Compliance",
        "tasks": ["Vulnerability scans", "Access control", "Audits", "Hardening"]
    }
}

# Financial data (seed — will be updated live)
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
    """Fetch live kanban board data."""
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
    """Determine what each worker is currently doing."""
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

    # Workers not in any task are idle
    for wid in WORKERS:
        if wid not in worker_status:
            worker_status[wid] = {"status": "idle", "task": "Wacht op nieuwe opdracht"}

    return worker_status


def calc_financials():
    """Calculate monthly totals."""
    monthly_exp = sum(
        e["amount"] for e in FINANCIALS["expenses"] if e["period"] == "maand"
    ) + sum(
        e["amount"] / 12 for e in FINANCIALS["expenses"] if e["period"] == "jaar"
    )
    monthly_rev = sum(
        r["amount"] for r in FINANCIALS["revenue"] if r["period"] == "maand"
    )
    return monthly_exp, monthly_rev


def generate_html(tasks, worker_status):
    """Generate the full dashboard HTML."""
    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    monthly_exp, monthly_rev = calc_financials()
    profit = monthly_rev - monthly_exp

    # Count tasks by status
    done_count = sum(1 for t in tasks if t.get("status") == "done")
    running_count = sum(1 for t in tasks if t.get("status") == "running")
    ready_count = sum(1 for t in tasks if t.get("status") == "ready")
    total_count = len(tasks)

    # Build worker cards HTML
    worker_cards = ""
    for wid, winfo in WORKERS.items():
        ws = worker_status.get(wid, {"status": "idle", "task": "Wacht op nieuwe opdracht"})
        status = ws["status"]
        task_text = ws["task"]

        if status == "busy":
            status_label = "Bezig"
            status_class = "busy"
            pulse = "pulse"
        elif status == "ready":
            status_label = "Klaar"
            status_class = "ready"
            pulse = ""
        elif status == "done":
            status_label = "Klaar"
            status_class = "done"
            pulse = ""
        else:
            status_label = "Inactief"
            status_class = "idle"
            pulse = ""

        # Truncate task text for bubble
        bubble_text = task_text if len(task_text) < 60 else task_text[:57] + "..."

        worker_cards += f'''
        <div class="worker-card {status_class}">
            <div class="speech-bubble">{bubble_text}</div>
            <div class="avatar {pulse}" style="--c:{winfo['color']};--bg:{winfo['bg']}">
                <span class="emoji">{winfo['emoji']}</span>
            </div>
            <div class="worker-name">{winfo['name']}</div>
            <div class="worker-role">{winfo['role']}</div>
            <div class="status-badge {status_class}">{status_label}</div>
        </div>'''

    # Build recent activity from done tasks
    done_tasks = [t for t in tasks if t.get("status") == "done"]
    recent_html = ""
    for t in done_tasks[:5]:
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

        recent_html += f'''
        <div class="activity-item">
            <span class="act-emoji">{winfo['emoji']}</span>
            <span class="act-text"><b>{winfo['name']}</b> — {title}</span>
            <span class="act-time">{time_str}</span>
        </div>'''

    if not recent_html:
        recent_html = '<div class="activity-item"><span class="act-text">Nog geen activiteit — wacht op eerste taken</span></div>'

    # Build expenses HTML
    exp_html = ""
    for e in FINANCIALS["expenses"]:
        monthly = e["amount"] if e["period"] == "maand" else e["amount"] / 12
        exp_html += f'''
        <div class="fin-row">
            <span>{e['item']}</span>
            <span class="fin-amount">€{monthly:.2f}/{e['period']}</span>
        </div>'''

    rev_html = ""
    for r in FINANCIALS["revenue"]:
        rev_html += f'''
        <div class="fin-row">
            <span>{r['item']}</span>
            <span class="fin-amount pos">€{r['amount']:.2f}/{r['period']}</span>
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Company Dashboard — E-Commerce Business</title>
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
    --shadow: 0 24px 70px rgba(0,0,0,.35);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, sans-serif;
    background: radial-gradient(circle at 8% 0, #173b7a 0, transparent 34%),
                radial-gradient(circle at 88% 10%, #5b21b6 0, transparent 30%),
                linear-gradient(180deg, #050914, #0b1220);
    color: var(--text);
    min-height: 100vh;
}}
a {{ color: inherit; }}
.wrap {{ max-width: 1280px; margin: auto; padding: 28px 18px 54px; }}

/* Header */
.header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
    flex-wrap: wrap;
    gap: 16px;
}}
.header h1 {{
    font-size: clamp(28px, 5vw, 48px);
    letter-spacing: -.04em;
    background: linear-gradient(135deg, var(--brand), var(--brand2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.header .subtitle {{ color: var(--muted); font-size: 14px; margin-top: 4px; }}
.badge-live {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(52,211,153,.15);
    border: 1px solid rgba(52,211,153,.3);
    border-radius: 999px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 700;
    color: var(--ok);
}}
.badge-live::before {{
    content: '';
    width: 8px; height: 8px;
    background: var(--ok);
    border-radius: 50%;
    animation: blink 2s infinite;
}}
@keyframes blink {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:.3; }} }}

/* Stats bar */
.stats-bar {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
    margin-bottom: 32px;
}}
.stat {{
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 16px;
    text-align: center;
}}
.stat b {{ display: block; font-size: 28px; }}
.stat span {{ color: var(--muted); font-size: 12px; }}

/* Section titles */
.section-title {{
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -.02em;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}}

/* Workers grid */
.workers-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 20px;
    margin-bottom: 40px;
}}
.worker-card {{
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 24px;
    padding: 24px 16px 16px;
    text-align: center;
    position: relative;
    transition: .2s ease;
}}
.worker-card:hover {{
    transform: translateY(-4px);
    box-shadow: var(--shadow);
}}
.worker-card.busy {{ border-color: rgba(52,211,153,.4); }}
.worker-card.ready {{ border-color: rgba(251,191,36,.4); }}
.worker-card.idle {{ opacity: .6; }}

/* Speech bubble */
.speech-bubble {{
    position: relative;
    background: var(--card2);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 10px 12px;
    font-size: 12px;
    color: var(--muted);
    margin-bottom: 16px;
    min-height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
}}
.speech-bubble::after {{
    content: '';
    position: absolute;
    bottom: -8px;
    left: 50%;
    transform: translateX(-50%);
    border-left: 8px solid transparent;
    border-right: 8px solid transparent;
    border-top: 8px solid var(--line);
}}
.speech-bubble::before {{
    content: '';
    position: absolute;
    bottom: -7px;
    left: 50%;
    transform: translateX(-50%);
    border-left: 7px solid transparent;
    border-right: 7px solid transparent;
    border-top: 7px solid var(--card2);
    z-index: 1;
}}

/* Avatar */
.avatar {{
    width: 72px;
    height: 72px;
    border-radius: 50%;
    background: var(--bg);
    border: 3px solid var(--c);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 12px;
    font-size: 32px;
    position: relative;
}}
.avatar.pulse {{
    animation: pulse-glow 2s infinite;
}}
@keyframes pulse-glow {{
    0%, 100% {{ box-shadow: 0 0 0 0 rgba(var(--c), .4); }}
    50% {{ box-shadow: 0 0 20px 4px rgba(var(--c), .2); }}
}}
.worker-name {{ font-weight: 800; font-size: 16px; }}
.worker-role {{ color: var(--muted); font-size: 11px; margin: 4px 0 10px; }}

/* Status badge */
.status-badge {{
    display: inline-block;
    border-radius: 999px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .04em;
}}
.status-badge.busy {{ background: rgba(52,211,153,.2); color: var(--ok); }}
.status-badge.ready {{ background: rgba(251,191,36,.2); color: var(--warn); }}
.status-badge.done {{ background: rgba(96,165,250,.2); color: var(--brand2); }}
.status-badge.idle {{ background: rgba(148,163,184,.15); color: var(--muted); }}

/* Two-col layout */
.two-col {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-bottom: 40px;
}}
@media(max-width: 768px) {{
    .two-col {{ grid-template-columns: 1fr; }}
    .workers-grid {{ grid-template-columns: repeat(2, 1fr); }}
}}

/* Panel */
.panel {{
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 24px;
    padding: 24px;
}}
.panel-title {{
    font-size: 16px;
    font-weight: 800;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}}

/* Activity feed */
.activity-item {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 0;
    border-bottom: 1px solid var(--line);
    font-size: 13px;
}}
.activity-item:last-child {{ border-bottom: none; }}
.act-emoji {{ font-size: 20px; flex-shrink: 0; }}
.act-text {{ flex: 1; color: var(--muted); }}
.act-text b {{ color: var(--text); }}
.act-time {{ color: var(--muted); font-size: 11px; flex-shrink: 0; }}

/* Financials */
.fin-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--line);
    font-size: 13px;
}}
.fin-row:last-child {{ border-bottom: none; }}
.fin-amount {{ font-weight: 700; }}
.fin-amount.pos {{ color: var(--ok); }}
.fin-amount.neg {{ color: var(--danger); }}

.fin-summary {{
    margin-top: 16px;
    padding-top: 16px;
    border-top: 2px solid var(--line);
    display: flex;
    justify-content: space-between;
    font-weight: 800;
    font-size: 16px;
}}
.fin-summary .pos {{ color: var(--ok); }}
.fin-summary .neg {{ color: var(--danger); }}

/* Kanban board */
.kanban-board {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 12px;
    margin-bottom: 40px;
}}
.kanban-card {{
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 16px;
    font-size: 13px;
}}
.kanban-card .kc-title {{ font-weight: 700; margin-bottom: 6px; }}
.kanban-card .kc-meta {{ color: var(--muted); font-size: 11px; }}
.kanban-card.done {{ border-color: rgba(52,211,153,.3); opacity: .7; }}
.kanban-card.running {{ border-color: rgba(251,191,36,.3); }}
.kanban-card.ready {{ border-color: rgba(96,165,250,.3); }}

/* Footer */
footer {{
    text-align: center;
    color: var(--muted);
    font-size: 12px;
    margin-top: 40px;
    line-height: 1.6;
}}
</style>
</head>
<body>
<div class="wrap">

<header class="header">
    <div>
        <h1>🛒 AI Company</h1>
        <div class="subtitle">Volledig autonoom AI-gestuurd e-commerce bedrijf · Laatste update: {now}</div>
    </div>
    <div class="badge-live">● LIVE</div>
</header>

<!-- Stats -->
<div class="stats-bar">
    <div class="stat"><b>{len(WORKERS)}</b><span>AI-werknemers</span></div>
    <div class="stat"><b>{total_count}</b><span>Totaal taken</span></div>
    <div class="stat"><b>{done_count}</b><span>Afgerond</span></div>
    <div class="stat"><b>{running_count}</b><span>Bezig</span></div>
    <div class="stat"><b>{ready_count}</b><span>In wachtrij</span></div>
    <div class="stat"><b>€{monthly_exp:.0f}</b><span>Maandelijkse kosten</span></div>
    <div class="stat"><b>€{monthly_rev:.0f}</b><span>Maandelijkse omzet</span></div>
    <div class="stat"><b class="{'pos' if profit >= 0 else 'neg'}">€{profit:.0f}</b><span>Maandelijkse winst</span></div>
</div>

<!-- Workers -->
<h2 class="section-title">👥 Ons AI-team</h2>
<div class="workers-grid">
    {worker_cards}
</div>

<!-- Two col: Activity + Financials -->
<div class="two-col">
    <div class="panel">
        <div class="panel-title">📋 Recente activiteit</div>
        {recent_html}
    </div>
    <div class="panel">
        <div class="panel-title">💰 Financiën</div>
        <div style="margin-bottom:12px;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em;font-weight:700;">Uitgaven</div>
        {exp_html}
        <div style="margin:12px 0 8px;color:var(--ok);font-size:12px;text-transform:uppercase;letter-spacing:.04em;font-weight:700;">Inkomsten</div>
        {rev_html}
        <div class="fin-summary">
            <span>Maandelijks resultaat</span>
            <span class="{'pos' if profit >= 0 else 'neg'}">{'+' if profit >= 0 else ''}€{profit:.2f}</span>
        </div>
    </div>
</div>

<!-- Kanban board -->
<h2 class="section-title">📌 Kanban board</h2>
<div class="kanban-board">
    {''.join(f'<div class="kanban-card {t.get("status","")}"><div class="kc-title">{WORKERS.get(t.get("assignee",""),{"emoji":"🤖"})["emoji"]} {t.get("title","")}</div><div class="kc-meta">{t.get("assignee","")} · {t.get("status","")}</div></div>' for t in tasks) if tasks else '<div class="kanban-card"><div class="kc-title">Geen taken gevonden</div></div>'}
</div>

<footer>
    AI Company Dashboard · Automatisch gegenereerd door build_dashboard.py<br>
    Data: kanban board "ecommerce" · Laatste build: {now}
</footer>

</div>
</body>
</html>'''


def main():
    print("🔨 Building AI Company Dashboard...")

    # Fetch data
    tasks = get_kanban_data()
    worker_status = get_worker_status(tasks)

    print(f"  📊 {len(tasks)} tasks fetched")
    print(f"  👥 {len(worker_status)} workers tracked")

    # Generate HTML
    html = generate_html(tasks, worker_status)

    # Write output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(OUTPUT_PATH) / 1024
    print(f"  ✅ Dashboard written to {OUTPUT_PATH} ({size_kb:.1f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
