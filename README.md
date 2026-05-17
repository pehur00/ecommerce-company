# 🛒 AI Company Dashboard

Live dashboard van ons AI-gestuurde e-commerce bedrijf.

**Live URL:** https://pehur00.github.io/ecommerce-company/

## Wat je ziet

- **AI-werknemers** — Visuele poppetjes met ballonnetjes die tonen waar elke worker mee bezig is
- **Financieel overzicht** — Uitgaven vs inkomsten, maandelijks resultaat
- **Kanban board** — Live overzicht van alle taken uit het e-commerce board
- **Recente activiteit** — Laatste afgerond taken per worker

## Build

```bash
python scripts/build_dashboard.py
```

Haalt live data uit `hermes kanban --board ecommerce list --json` en genereert `dashboard/index.html`.

## Deployment

```bash
python scripts/build_dashboard.py
git add dashboard/index.html
git commit -m "update dashboard"
git push
```

GitHub Pages served vanaf `master` branch, `/dashboard` folder.
