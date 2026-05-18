#!/usr/bin/env python3
"""
Kanban Safe Sync — pull, sanitize, publish.
Runs on the Hermes host (where `hermes kanban` CLI is available).
Outputs public/kanban_safe.json and a live-index.html.
Syncs to VPS via rsync.
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ── Config ──
BOARD = os.environ.get("KANBAN_BOARD", "ecommerce")
SSH_KEY = os.environ.get("ECOMMERCE_SSH_KEY", "/home/hermes/.ssh/hetzner_ecommerce")
VPS_HOST = os.environ.get("ECOMMERCE_VPS", "root@188.245.52.48")
VPS_REMOTE_DIR = os.environ.get("ECOMMERCE_REMOTE_DIR", "/var/www/ecommerce/public")
LOCAL_PUBLIC_DIR = Path(__file__).with_name("public")
CONFIG_PATH = Path(__file__).with_name("redactor_config.yaml")

# ── Redactor ──
class Redactor:
    def __init__(self, config_path: Path):
        import yaml
        with open(config_path) as f:
            self.cfg = yaml.safe_load(f) or {}
        self._drop = set(self.cfg.get("always_drop", []))
        self._allow = set(self.cfg.get("allow", []))
        self._truncate = self.cfg.get("truncate", {})
        self._patterns = self.cfg.get("patterns", [])

    def sanitize_task(self, task: dict) -> dict:
        out = {}
        for k, v in task.items():
            if k in self._drop:
                continue
            # Only keep explicitly allowed keys; everything else is dropped
            if k not in self._allow:
                continue
            out[k] = self._apply_field_rules(k, v)
        # Belt-and-suspenders: strip any denylisted keys that might slip through
        for deny in ("body", "workspace_path", "comments", "events", "result",
                     "tenant", "created_by", "workspace_kind", "current_run_id",
                     "runs", "error", "summary", "latest_summary", "children", "parents"):
            out.pop(deny, None)
        return out

    def _apply_field_rules(self, field: str, value):
        if isinstance(value, str):
            value = self._redact_str(value, field)
            cap = self._truncate.get(field)
            if cap and len(value) > cap:
                value = value[: cap - 1] + "…"
        return value

    def _redact_str(self, text: str, field: str = None) -> str:
        if not isinstance(text, str):
            return text
        for pat in self._patterns:
            target_fields = pat.get("fields", [])
            if field and target_fields and field not in target_fields:
                continue
            try:
                text = re.sub(pat["regex"], pat["repl"], text)
            except re.error:
                continue
        return text


# ── Kanban CLI helpers ──
def run_kanban_list() -> list:
    proc = subprocess.run(
        ["hermes", "kanban", "--board", BOARD, "list", "--json"],
        capture_output=True, text=True, timeout=30,
        env={**os.environ, "HOME": os.path.expanduser("~")},
    )
    if proc.returncode != 0:
        raise RuntimeError(f"kanban list failed: {proc.stderr[:500]}")
    try:
        data = json.loads(proc.stdout)
        if not isinstance(data, list):
            raise ValueError("expected list")
        return data
    except Exception as e:
        raise RuntimeError(f"invalid kanban JSON: {e}")


# ── Financials helper (safe static file) ──
def load_financials() -> dict:
    fin_path = Path(__file__).with_name("data") / "financials.json"
    if fin_path.exists():
        with open(fin_path) as f:
            return json.load(f)
    return {"monthly_expenses": 0.0, "monthly_revenue": 0.0, "profit": 0.0, "currency": "EUR", "items": []}


# ── Build public payload ──
def build_payload(tasks: list, redactor: Redactor) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    safe_tasks = [redactor.sanitize_task(t) for t in tasks]
    statuses = {}
    for t in safe_tasks:
        statuses[t.get("status", "unknown")] = statuses.get(t.get("status", "unknown"), 0) + 1

    # Worker stats (from all tasks including dropped ones via original mapping)
    worker_stats = {}
    now_ts = time.time()
    cutoff = now_ts - 7 * 86400  # last 7 days
    for t in tasks:
        a = t.get("assignee")
        if not a:
            continue
        entry = worker_stats.setdefault(a, {"running": 0, "ready": 0, "blocked": 0, "done": 0, "total": 0, "recent_done": 0})
        entry["total"] += 1
        s = t.get("status")
        if s == "running":
            entry["running"] += 1
        elif s == "ready":
            entry["ready"] += 1
        elif s == "blocked":
            entry["blocked"] += 1
        elif s == "done":
            entry["done"] += 1
        # recent done
        if s == "done":
            cat = t.get("completed_at")
            if isinstance(cat, (int, float)) and cat >= cutoff:
                entry["recent_done"] += 1

    # Workload scoring: running*3 + ready*2 + blocked*2 + recent_done_last_7d*0.5
    def _workload_score(e):
        return e["running"] * 3 + e["ready"] * 2 + e["blocked"] * 2 + e["recent_done"] * 0.5

    for wid, s in worker_stats.items():
        score = _workload_score(s)
        s["workload_score"] = round(score, 1)
        if score == 0:
            s["load_label"] = "idle"
            s["load_label_nl"] = "rustig"
        elif score <= 3:
            s["load_label"] = "normal"
            s["load_label_nl"] = "normaal"
        elif score <= 6:
            s["load_label"] = "busy"
            s["load_label_nl"] = "druk"
        else:
            s["load_label"] = "overloaded"
            s["load_label_nl"] = "overbelast"

    # Bottleneck = highest workload_score (tie broken by total tasks)
    bottleneck_worker = None
    if worker_stats:
        bottleneck_worker = max(worker_stats.items(), key=lambda kv: (kv[1]["workload_score"], kv[1]["total"]))[0]

    activity = []
    for t in sorted(safe_tasks, key=lambda x: x.get("completed_at") or 0, reverse=True)[:10]:
        if t.get("completed_at"):
            activity.append({
                "worker": t.get("assignee"),
                "task_title": t.get("title"),
                "status": t.get("status"),
                "timestamp": t.get("completed_at"),
            })

    fin = load_financials()

    return {
        "_meta": {
            "generated_at": now,
            "source": BOARD,
            "version": "1",
            "tasks_total": len(tasks),
            "tasks_by_status": statuses,
            "bottleneck_worker": bottleneck_worker,
        },
        "workers": [
            {
                "id": wid,
                "name": wid.replace("worker-", "").title(),
                "active_tasks": s["running"],
                "completed_tasks": s["done"],
                "total_tasks": s["total"],
                "workload_score": s["workload_score"],
                "load_label": s["load_label"],
                "load_label_nl": s["load_label_nl"],
                "status_counts": {
                    "running": s["running"],
                    "ready": s["ready"],
                    "blocked": s["blocked"],
                    "done": s["done"],
                    "recent_done": s["recent_done"],
                },
            }
            for wid, s in worker_stats.items()
        ],
        "tasks": safe_tasks,
        "activity": activity,
        "financials": fin,
    }


# ── Generate live HTML (fetches JSON client-side) ──
def generate_live_html() -> str:
    return r'''<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Company — Live Dashboard</title>
<style>
:root{--bg:#07111f;--bg2:#0b1220;--card:rgba(255,255,255,.08);--text:#f7fbff;--muted:#a9b8cc;--line:rgba(255,255,255,.12);--brand:#7c3aed;--brand2:#06b6d4;--ok:#34d399;--warn:#fbbf24;--danger:#f87171;--info:#60a5fa}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,ui-sans-serif,system-ui,sans-serif;background:var(--bg);color:var(--text);overflow-x:hidden}
.wrap{max-width:1100px;margin:auto;padding:20px 18px 54px}
.hd{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px}
.hd h1{font-size:clamp(24px,4vw,38px);letter-spacing:-.04em;background:linear-gradient(135deg,var(--brand),var(--brand2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hd .sub{color:var(--muted);font-size:12px;margin-top:2px}
.live{display:inline-flex;align-items:center;gap:7px;background:rgba(52,211,153,.1);border:1px solid rgba(52,211,153,.25);border-radius:999px;padding:5px 13px;font-size:11px;font-weight:700;color:var(--ok)}
.live.pulse::before{content:'';width:6px;height:6px;background:var(--ok);border-radius:50%;animation:blink 2s infinite}
.live.stale{color:var(--warn);background:rgba(251,191,36,.1);border-color:rgba(251,191,36,.25)}
.live.stale::before{background:var(--warn);animation:none}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}

.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:8px;margin-bottom:20px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;text-align:center}
.stat b{display:block;font-size:22px}
.stat span{color:var(--muted);font-size:10px}

.worker-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-bottom:24px}

/* Workload color coding */
.wcard{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;position:relative;overflow:hidden}
.wcard::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:12px 12px 0 0}
.wcard.idle::before{background:#6b7280}
.wcard.normal::before{background:var(--ok)}
.wcard.busy::before{background:var(--warn)}
.wcard.overloaded::before{background:var(--danger)}
.wcard .n{font-weight:700;font-size:14px}
.wcard .role{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.04em;margin-top:1px}
.wcard .tagrow{display:flex;gap:4px;margin-top:8px;flex-wrap:wrap}
.wcard .tag{font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px}
.wcard .tag.idle{background:rgba(107,114,128,.15);color:#9ca3af}
.wcard .tag.normal{background:rgba(52,211,153,.12);color:var(--ok)}
.wcard .tag.busy{background:rgba(251,191,36,.12);color:var(--warn)}
.wcard .tag.overloaded{background:rgba(248,113,113,.12);color:var(--danger)}

/* Paper stack */
.wcard .stack{display:flex;align-items:center;gap:5px;margin-top:6px;font-size:11px;color:var(--muted)}
.wcard .stack .pile{display:flex;flex-direction:column-reverse;gap:0}
.wcard .stack .pile .p{width:16px;height:2px;border-radius:1px;background:var(--line);margin-bottom:1px}
.wcard.overloaded .pile .p{background:rgba(248,113,113,.35)}
.wcard.busy .pile .p{background:rgba(251,191,36,.35)}
.wcard.normal .pile .p{background:rgba(52,211,153,.35)}

/* Glow for overloaded */
.wcard.overloaded{box-shadow:inset 0 0 18px rgba(248,113,113,.06)}
.wcard.busy{box-shadow:inset 0 0 10px rgba(251,191,36,.05)}

/* Bubble */
.wcard .bubble{position:relative;margin-top:8px;background:rgba(255,255,255,.06);border:1px solid var(--line);padding:7px 10px;border-radius:8px;font-size:11px;color:var(--muted)}
.wcard .bubble::after{content:'';position:absolute;top:-5px;left:12px;width:8px;height:8px;background:rgba(255,255,255,.06);border-top:1px solid var(--line);border-left:1px solid var(--line);transform:rotate(45deg)}

.bottle{background:rgba(251,191,36,.06);border:1px solid rgba(251,191,36,.25);border-radius:10px;padding:10px 14px;font-size:12px;color:var(--warn);margin-bottom:18px}
.bottle strong{display:block;margin-bottom:2px}

.fin{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;margin-bottom:24px}
.fin-item{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.fin-item .lab{color:var(--muted);font-size:11px}
.fin-item .val{font-size:22px;font-weight:800;margin-top:2px}

.table-wrap{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;margin-bottom:24px}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;padding:10px 14px;color:var(--muted);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid var(--line)}
td{padding:10px 14px;border-bottom:1px solid rgba(255,255,255,.04)}
tr:last-child td{border-bottom:none}
.status{display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:700;padding:3px 10px;border-radius:999px}
.status.done{background:rgba(52,211,153,.12);color:var(--ok)}
.status.running{background:rgba(96,165,250,.12);color:var(--info)}
.status.ready{background:rgba(251,191,36,.12);color:var(--warn)}
.status.blocked{background:rgba(248,113,113,.12);color:var(--danger)}
.msg{color:var(--muted);padding:20px;text-align:center}
</style>
</head>
<body>
<div class="wrap">
  <div class="hd">
    <div>
      <h1>AI Company Dashboard</h1>
      <div class="sub" id="sub">Autonoom e-commerce team — live status</div>
    </div>
    <div id="live" class="live pulse">LIVE</div>
  </div>

  <div class="stats" id="stats"></div>

  <div class="bottle" id="bottle" style="display:none"><strong id="bottleTitle"></strong><span id="bottleBody"></span></div>

  <div class="worker-grid" id="workers"></div>

  <div class="fin" id="fin"></div>

  <div class="table-wrap">
    <table>
      <thead><tr><th>Taak</th><th>Worker</th><th>Status</th></tr></thead>
      <tbody id="tasks"></tbody>
    </table>
  </div>
</div>
<script>
let lastMeta = null;
async function refresh() {
  try {
    const res = await fetch('./kanban_safe.json?_=' + Date.now(), {cache:'no-store'});
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    render(data);
    lastMeta = data._meta;
  } catch (err) {
    document.getElementById('sub').textContent = 'Kan data niet laden — ' + err.message;
    document.getElementById('live').className = 'live stale';
    document.getElementById('live').textContent = 'OFFLINE';
  }
}
function render(data) {
  const m = data._meta || {};
  const btn = document.getElementById('live');
  if (m.stale) { btn.className = 'live stale'; btn.textContent = 'CACHED'; }
  else { btn.className = 'live pulse'; btn.textContent = 'LIVE'; }
  document.getElementById('sub').textContent = 'Autonoom e-commerce team — sync ' + (m.generated_at ? m.generated_at.replace('T',' ').slice(0,16) : 'onbekend');

  const s = m.tasks_by_status || {};
  const stats = [
    {b: m.tasks_total||0, t:'Taken'},
    {b: s.running||0, t:'Actief'},
    {b: s.done||0, t:'Klaar'},
    {b: s.blocked||0, t:'Geblokkeerd'},
  ];
  document.getElementById('stats').innerHTML = stats.map(x=>`<div class="stat"><b>${x.b}</b><span>${x.t}</span></div>`).join('');

  // Bottleneck banner
  const bottle = document.getElementById('bottle');
  if (m.bottleneck_worker) {
    bottle.style.display='block';
    document.getElementById('bottleTitle').textContent = 'Team bottleneck';
    document.getElementById('bottleBody').textContent = 'Drukste worker: ' + m.bottleneck_worker;
  } else {
    bottle.style.display='none';
  }

  // Workers with workload styling
  document.getElementById('workers').innerHTML = (data.workers || []).map(w=>{
    const label = w.load_label || 'idle';
    const score = w.workload_score ?? 0;
    const labelNl = w.load_label_nl || 'rustig';
    const counts = w.status_counts || {running:0,ready:0,blocked:0,done:0};
    const totalRunning = (data.tasks||[]).filter(t=>t.assignee===w.id && t.status==='running');
    const topTask = totalRunning[0];
    const pileCount = Math.min(8, Math.max(1, Math.round(score)));
    let pileHtml = '<span class="pile">';
    for(let i=0;i<pileCount;i++) { pileHtml += '<span class="p"></span>'; }
    pileHtml += '</span>';
    const bubble = (topTask && topTask.title)
      ? `<div class="bubble">${topTask.title.substring(0,80)+(topTask.title.length>80?'…':'')}</div>`
      : '';
    return `<div class="wcard ${label}">
      <div class="n">${w.name}</div>
      <div class="role">${w.id}</div>
      <div class="tagrow"><span class="tag ${label}">${labelNl}</span></div>
      <div class="stack">${pileHtml} Score: ${score}</div>
      ${bubble}
    </div>`;
  }).join('');

  const fin = data.financials || {};
  const pf = (v) => (v>=0?'+':'') + '\u20ac' + v.toFixed(2);
  document.getElementById('fin').innerHTML = [
    {l:'Uitgaven/maand',v:'\u20ac' + (fin.monthly_expenses||0).toFixed(2)},
    {l:'Omzet/maand',v:'\u20ac' + (fin.monthly_revenue||0).toFixed(2)},
    {l:'Winst',v:pf(fin.profit||0)},
  ].map(x=>`<div class="fin-item"><div class="lab">${x.l}</div><div class="val" style="color:${x.v.startsWith('-')?'var(--danger)':'var(--ok)'}"">${x.v}</div></div>`).join('');

  document.getElementById('tasks').innerHTML = (data.tasks || []).map(t=>{
    const st = t.status || 'unknown';
    return `<tr><td>${t.title}</td><td>${t.assignee}</td><td><span class="status ${st}">${st}</span></td></tr>`;
  }).join('');
}
refresh();
setInterval(refresh, 30000);
</script>
</body>
</html>
'''


# ── Write + rsync ──
def write_outputs(payload: dict, public_dir: Path):
    public_dir.mkdir(parents=True, exist_ok=True)
    out_json = public_dir / "kanban_safe.json"
    with open(out_json, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)
    with open(out_json) as f:
        # verify it loads
        json.load(f)

    # F6: also write kanban.json so /kanban.json endpoint works
    out_json2 = public_dir / "kanban.json"
    with open(out_json2, "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

    out_html = public_dir / "index.html"
    with open(out_html, "w") as f:
        f.write(generate_live_html())

    return out_json, out_json2, out_html


def rsync_to_vps(public_dir: Path):
    env = {**os.environ, "SSH_AUTH_SOCK": ""}
    cmd = [
        "rsync", "-az", "--delete",
        "-e", f"ssh -o StrictHostKeyChecking=no -o BatchMode=yes -i {SSH_KEY}",
        str(public_dir) + "/",
        f"{VPS_HOST}:{VPS_REMOTE_DIR}/",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(f"rsync failed: {proc.stderr[:500]}")
    return True


# ── Main ──
def main():
    if not CONFIG_PATH.exists():
        print(f"Config not found: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)

    redactor = Redactor(CONFIG_PATH)
    tasks = []
    stale = False
    try:
        tasks = run_kanban_list()
    except Exception as e:
        print(f"Kanban CLI unavailable: {e}", file=sys.stderr)
        stale = True
        # Try to load cached JSON as fallback for output
        cache = LOCAL_PUBLIC_DIR / "kanban_safe.json"
        if cache.exists():
            with open(cache) as f:
                old = json.load(f)
                tasks = old.get("tasks", [])
                if tasks and isinstance(tasks[0], dict):
                    tasks = [{"id": t.get("id","legacy"), "title": t.get("title","cached"),
                              "assignee": t.get("assignee"), "status": t.get("status"), "priority": t.get("priority",0)} for t in tasks]

    payload = build_payload(tasks, redactor)
    payload["_meta"]["stale"] = stale
    payload["_meta"]["generated_at"] = datetime.now(timezone.utc).isoformat()

    out_json, out_json2, out_html = write_outputs(payload, LOCAL_PUBLIC_DIR)
    print(f"Wrote {out_json} ({out_json.stat().st_size} bytes)")
    print(f"Wrote {out_json2} ({out_json2.stat().st_size} bytes)")
    print(f"Wrote {out_html} ({out_html.stat().st_size} bytes)")

    try:
        rsync_to_vps(LOCAL_PUBLIC_DIR)
        print("Rsync to VPS OK")
    except Exception as e:
        print(f"Rsync failed (files remain local): {e}", file=sys.stderr)
        sys.exit(2)

    print("Done")


if __name__ == "__main__":
    main()
