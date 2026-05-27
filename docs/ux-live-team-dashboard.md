# UX Spec: AI Company — Live Public Team Dashboard

## 1. Huidige situatie & probleemanalyse

### Bestaande versies
| Versie | Locatie | Status |
|--------|---------|--------|
| v1 (dark grid) | `/index.html` | Generieke worker-grid + kanban-lijst. Saai, geen "kantoorgevoel". |
| v3 (2D top-down office) | `/docs/index.html` (GitHub Pages) | Levendig, animaties, speech bubbles, koffiecorner, meeting room, lopende workers. |

### UX-knelpunten in v3
1. **Kanban-overload**: Alle DONE-taken worden getoond. Bij 18+ completed items wordt het een muur van grijze tekst.
2. **Workload onzichtbaar**: Status-dot (busy/idle/done) vertelt niet HOE druk iemand is. 1 taak versus 5 taken ziet er hetzelfde uit.
3. **Missing states**: Geen visuele "overloaded" of "blocked" state voor workers. Een worker met een probleem loopt nog steeds vrolijk rond.
4. **Financiën te statisch**: Simpele tabel zonder trend, progress-to-goal, of duidelijke burn-rate-indicatie.
5. **Missie wordt naar beneden gedrukt**: Goede tekst, maar te snel verdwijnend in het visuele geweld van het kantoor.
6. **Geen wachtruimte**: Workers zonder taak verdwijnen bij hun bureau maar "doen" niets. Geen wachtbank, geen koffiezetapparaat, geen idle-gedrag.
7. **Geen board/directie-sectie**: Het management/board heeft geen eigen fysieke plek in het kantoor.
8. **Mobile broken**: Aspect-ratio 16/10 office werkt niet op mobiel; workers worden miniem.

---

## 2. UX-visie: "Het AI-kantoor als theaterstuk"

### Kernprincipe
> Een bezoeker moet in **3 seconden** begrijpen:
> 1. Dit is een **autonoom AI-bedrijf** dat e-commerce webshops bouwt.
> 2. Dit team werkt **nu live** (niet mockup).
> 3. De **gezondheid** van het bedrijf is duidelijk (workload, cashflow, progress).

### Tone-of-voice
- **Speels maar professioneel** — geen kinderlijke graphics, wel karakter en humor.
- **Transparant** — alle data is echt en live, geen nep-cijfers.
- **Humanized AI** — workers hebben persoonlijkheid maar blijven robots (emoji's, kleuren, niet te realistisch).

---

## 3. Informatiearchitectuur (nieuw)

```
┌─────────────────────────────────────────────┐
│  HEADER: bedrijfsnaam + LIVE-badge + uptime │  ← sticky
├─────────────────────────────────────────────┤
│  MISSIE-BANNER: wat doen we + 4 KPI-doelen  │  ← hero, kleurverloop
├─────────────────────────────────────────────┤
│  STAT-BAR: 6 kerngetallen (1-rij, compact)  │
├─────────────────────────────────────────────┤
│                                             │
│  KANTOOR (2D top-down)                      │  ← main attraction
│  · bureaus met workers                      │
│  · koffiecorner + waiting area              │
│  · meeting room + board room               │
│  · animaties + speech bubbles               │
│                                             │
├─────────────────────────────────────────────┤
│  TWO-COL PANELS: activiteit + financiën     │
├─────────────────────────────────────────────┤
│  BOARD-UPDATE: directie-memo (1 regel)    │
├─────────────────────────────────────────────┤
│  KANBAN: alleen RUNNING + READY + BLOCKED   │  ← DONE is verborgen
├─────────────────────────────────────────────┤
│  FOOTER: versie + build-time + GitHub-link │
└─────────────────────────────────────────────┘
```

---

## 4. Component Design Library

### 4.1 Worker (werknemer)

#### Visuele basis
- **Top-down circle** (22px) met emoji (11px).
- **Kleur per role** (consistent met huidige palette).
- **Schaduw** onder de body voor diepte.
- **Richtings-indicator** (pijltje boven circle) waar ze naar kijken.

#### States (nieuw / uitgebreid)

| State | Visueel kenmerk | Betekenis |
|-------|------------------|-----------|
| `idle` | Traag ademend (scale 1.0→1.03), grijze dot | Geen taken, wacht op opdracht |
| `ready` | Geel/oranje dot, staat op wachtbank of loopt rond | Taak toegewezen, start binnenkort |
| `busy` | Groene **pulse-dot**, snelle werk-animatie | Actief bezig met taak |
| `overloaded` | Rode dot + **trillende body** + ⚠️ boven hoofd | 3+ taken gelijktijdig, dreigt vast te lopen |
| `blocked` | Paarse dot + **slaapstand-animatie** (half-transparant) + 💤 | Wacht op input van ander (human of system) |
| `done` | Cyaan dot + **stretch-animatie** (win!) + confetti-mini | Net taak afgerond, gaat terug naar bureau |

#### Speech Bubbles
- **Altijd zichtbaar** bij hover (bestaat al).
- **Auto-rotate** elke 8s bij `busy` workers: toon huidige taak + progress percentage.
- **Emoji-prefixed** tekst voor scanbaarheid:
  - "⚙️ Amazon.nl API setup... 67%"
  - "🔬 SEO-artikel schrijven..."
  - "💤 Wacht op human approval..."

#### Workload Bar (nieuw)
- Kleine **3-segment progress bar** onder de worker (5px hoog, 3 segments):
  - 0/3 = groen (rustig)
  - 2/3 = oranje (druk)
  - 3/3 + overflow = rood (overloaded)
- Toont aantal gelijktijdige taken per worker.

### 4.2 Kantoor-layout (nieuw)

```
  ┌────────────────────────────────────────────────────┐
  │  WINDOW   WINDOW   WINDOW   [BOARD ROOM]          │  ← top wall
  │                                                    │
  │   [☕ COFFEE]        [MEETING ROOM 🤝]              │
  │                                                    │
  │   ┌─┐  ┌─┐  ┌─┐  ┌─┐                               │
  │   │O│  │R│  │D│  │V│  ← desks row 1               │
  │   └─┘  └─┘  └─┘  └─┘                               │
  │                                                    │
  │   ┌─┐  ┌─┐  ┌─┐  ┌─┐     [⌛ WAITING AREA]        │
  │   │P│  │D│  │S│  │S│  ← desks row 2               │
  │   └─┘  └─┘  └─┘  └─┘                               │
  │                                                    │
  │           [PLANTER BOX]                            │
  │                                                    │
  │              ╔═══════╗                             │
  │              ║ 🚪 IN ║  ← door (spawn point)       │
  │              ╚═══════╝                             │
  └────────────────────────────────────────────────────┘

LEGENDA:
  O = Ops       R = Research    D = Developer   V = Reviewer
  P = PM        D = Data        S = Design      S = Security
```

#### Nieuwe ruimtes
- **Waiting Area (⌛)**: Bank + plant. Workers in `idle` of `ready` gaan hier automatisch zitten/vertoeven na korte tijd (30s simulatie).
- **Board Room (📊)**: Afgesloten ruimte rechtsboven. Toont een klein scherm met laatste board-memo. Alleen PM mag hier naar binnen.
- **Planter Box**: Decoratief, maakt het kantoor "leefbaar".

### 4.3 Desks
- **Labelled** met role-emoji + naam (klein).
- **Status-light** op bureauhoek:
  - Uit = bureau vrij (werker niet aanwezig)
  - Groen = werker aanwezig en productief
  - Geel = werker aanwezig maar afgeleid/wachtend
- **Kantelbaar scherm** (CSS transform) voor diepte effect.

### 4.4 Board / Directie Update (nieuw component)

Een banner direct onder het kantoor (full-width):

```
┌─────────────────────────────────────────────────────────────────┐
│  📊 BOARD MEMO — 17 mei 22:00   │   "Omzet nog €0; focus    │
│     via cron: elke dag 12:00    │    volgende week: organic  │
│                                 │    traffic via SEO."      │
└─────────────────────────────────────────────────────────────────┘
```

- **Font**: monospace voor datum/tijd, sans-serif voor bericht.
- **Kleur**: subtiele border (paars/turquoise gradient) om directie-status te signalen.
- **Content**: Automatisch gegenereerd uit laatste done-taak + financial delta.
- **Animatie**: Typewriter-effect bij page-load (1 regel per 30ms).

### 4.5 Financiën-panel (redesign)

#### Nieuw: Goal-tracker bovenaan
```
🎯 Break-even target: €4.87/maand
[████████░░░░░░░░░░░░]  0%   (€0 / €4.87)
```

#### Nieuw: Trend-mini-chart
Simpele SVG lijngrafiek over laatste 30 dagen (stub data → later echt):
- X-as: dagen
- Y-as: cumulatief resultaat
- Positief = groen, negatief = rood

#### Uitgavenlijst (gehandhaafd maar gecondenseerd)
- Alleen items met werkelijke kosten > €0 tonen.
- Gratis items in een dropdown "Gratis tools (5)".
- Totaal per categorie (infra, marketing, tools).

### 4.6 Kanban-panel (redesign)

#### Regel: DONE is hidden by default
- Show **ONLY** `running`, `ready`, `blocked`.
- Add toggle: "Toon 18 afgeronde taken ↓" (collapsed by default).
- Reduces cognitive load for public visitors.

#### Card redesign
- Geen grijze "done" muur meer.
- **Running** cards: border pulse (subtiel), worker-emoji + live-timer ("2h 14m bezig").
- **Blocked** cards: rode border + 🔒 + blocker-reason tooltip.
- **Ready** cards: subtiele glans/glow animatie (wachten op pickup).

---

## 5. Wireframes (textueel)

### 5.1 Desktop (>1024px)

```
+--------------------------------------------------------+
| 🛒 AI Company    [● LIVE]           Laatste update...   |
+--------------------------------------------------------+
| 🎯 Missie                                              |
| "Autonoom AI e-commerce bedrijf..."                    |
| [€0→€1K] [1→5 shops] [0→10K bezoekers] [8→15 workers] |
+--------------------------------------------------------+
| [8]workers [21]taken [0]bezig [0]ready [€-5]maand      |
+--------------------------------------------------------+
|                                                        |
|      🏢 2D TOP-DOWN OFFICE (16:10 aspect)              |
|      + animaties, bureaus, workers, bubbles            |
|                                                        |
+--------------------------------------------------------+
| 📊 BOARD MEMO: "Next: scale content pipeline..."        |
+--------------------------------------------------------+
| 📋 RECENTE ACTIVITEIT    | 💰 FINANCIËN + goal-tracker |
| · Dev — ...              | [break-even bar]            |
| · Ops — ...              | [trend-chart stub]          |
|                          | uitgaven...                   |
|                          | inkomsten...                  |
+--------------------------------------------------------+
| 📌 KANBAN (running/ready/blocked only)                 |
| [RUNNING] [READY] [BLOCKED]                            |
+--------------------------------------------------------+
| Footer...                                              |
+--------------------------------------------------------+
```

### 5.2 Mobile (<768px)

Office wordt **horizontaal scrollbaar** binnen een 800px-wide container (overflow-x: auto). Geen aspect-ratio clamp.
Workers behouden 32px grootte.
Telkens 1 kolom panels stacked.

---

## 6. Interactie & Animatie Spec

### 6.1 Animaties (bestaand behouden + nieuw)

| Animatie | Trigger | CSS/JS |
|-----------|---------|--------|
| `walk-bob` | walking state | bestaand |
| `sit-bob` | working state | bestaand |
| `breathe` | idle state | bestaand |
| `pulse-dot` | busy state | bestaand |
| **`shake`** | overloaded state | nieuw: translateX(±1px) 0.1s infinite |
| **`fade-sleep`** | blocked state | nieuw: opacity 0.4 + slow breathe |
| **`confetti-mini`** | done state (3s) | nieuw: 4 kleine particles explode vanuit worker, leeglopen |
| **`typewriter`** | board memo load | nieuw: karakter per 30ms |
| **`desk-light`** | worker komt aan bureau | nieuw: box-shadow groen pulse 1x |

### 6.2 Gedragslogica (AI simulatie)

```javascript
// Pseudo-worker behavior
loop every 30s:
  if worker.status == "idle":
    if random() < 0.3:
      walk_to("coffee")
      stay(3-5s)
      speech("☕ Even pauze...")
    if random() < 0.2:
      walk_to("waiting area")
      stay(5-10s)

  if worker.status == "overloaded":
    shake_animation = true
    speech_color = "red"
    walk_speed *= 0.7   // trager lopen = druk

  if worker.status == "blocked":
    speech("💤 Wacht op... " + blocker_reason)
    if at_desk:
      fade_to_half_opacity()
```

---

## 7. Kleur & Typografie (huidig palette gehandhaafd)

### CSS variabelen (aanvulling)
```css
:root {
  /* bestaand */
  --bg:#07111f; --card:rgba(255,255,255,.08);
  --text:#f7fbff; --muted:#a9b8cc;
  --brand:#7c3aed; --brand2:#06b6d4;
  --ok:#34d399; --warn:#fbbf24; --danger:#f87171;

  /* nieuw */
  --blocked:#a78bfa;         /* paars voor blocked */
  --overloaded:#ef4444;      /* felrood voor overloaded */
  --boardroom:rgba(124,58,237,.15);
  --waiting:rgba(251,191,36,.08);
  --memo-bg:linear-gradient(90deg, rgba(124,58,237,.1), rgba(6,182,212,.05));
}
```

---

## 8. Prioriteit: MVP vs Later

### MVP (deze week — impact max, effort min)
- [ ] **DONE-taken verbergen** in kanban (grootste winst)
- [ ] **Workload-bar** onder workers (3 segments, CSS-only)
- [ ] **Overloaded + Blocked states** toevoegen (CSS animaties)
- [ ] **Board Memo** component (1 regel text, typewriter effect)
- [ ] **Financiën condenseren**: alleen betalende items tonen, gratis verbergen
- [ ] **Waiting area** toevoegen aan kantoor-div (static element)

### Week 2 (medium effort)
- [ ] **Worker idle-gedrag**: koffie-corner visits, wachtbank
- [ ] **Speech bubble auto-rotate** (taken + progress %)
- [ ] **Goal-tracker** (break-even bar, SVG)
- [ ] **Mobile fix**: horizontale scroll office + stacked layout
- [ ] **Desk status-light** (groen/geel/uit)

### Later (polish)
- [ ] Financiën trend-grafiek (echte data)
- [ ] Confetti-mini animatie bij done
- [ ] Board room fysiek in kantoor (PM loopt erheen)
- [ ] Geluid (optioneel toggle): subtiele office ambient
- [ ] Dark/light mode toggle
- [ ] PWA installeerbaar

---

## 9. Toegankelijkheid & Performance

- **Alt text**: Alle emoji's hebben `aria-label` met role + status.
- **Reduced motion**: `@media (prefers-reduced-motion: reduce)` — alle animaties uit, workers statisch op bureau.
- **Colorblind**: Status-dots krijgen vorm (✓, ○, △, ✕) naast kleur.
- **Performance**: Kanban cards virtualizen als >50 taken.
- **SEO**: Mission-sectie is plain HTML boven de fold, indexeerbaar.

---

## 10. Meetplan ( succes criteria )

| Metric | Huidig | Doel | Hoe meten |
|--------|--------|------|-----------|
| Time-to-understand | >10s | <3s | Hotjar session replay |
| Scroll depth | 60% | >85% | Plausible Analytics |
| Kanban clutter | 21 cards zichtbaar | <10 cards zichtbaar (default) | Eenvoudig tellen |
| Mobile bounce rate | ~70% | <50% | Plausible Analytics |
| "Is dit echt live?" | vaak onduidelijk | 100% duidelijk (LIVE-badge + animaties) | Qualitative |

---

*Document versie: 1.0*  
*Auteur: worker-designer*  
*Datum: 2026-05-17*
