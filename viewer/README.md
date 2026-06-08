# OpenClaw QC — vault viewer

A tiny static site that renders the `OpenClaw QC/` Obsidian vault as a browsable web viewer:
the L10 audits (sortable/filterable table + a page per task), the V6/V7 spec, and the live L10
queue snapshot. No framework, no secrets — `build.mjs` reads the vault markdown at build time and
emits static HTML into `public/`.

## Deploy on Vercel (GitHub import — chosen path)
The repo is already on GitHub, so:

1. Vercel → **Add New → Project → Import** this repository (`killianmannarelli/evals`).
2. Set **Root Directory** = `viewer`.
3. Leave the rest as detected — `vercel.json` already pins **Build Command** `node build.mjs` and
   **Output Directory** `public` (Framework Preset: *Other*).
4. **Deploy.** Vercel rebuilds on every push to the branch, so the viewer stays in sync with the
   vault — including task notes added by future audit runs.

That's the whole setup; no environment variables, no token needed.

## Preview locally
```bash
cd viewer
npm install
npm run build      # writes ./public
npm run dev        # builds, then serves ./public via `npx serve`
```

## What it shows
- **Audits** (`index.html`) — 16 L10 audits: verdict vs. drawer verdict, agree flag, platform %,
  6a/6b bands, denominator, run/carryover. Filter by verdict / divergence / run / carryover; sort
  any column; click a row for the full audit.
- **Spec (V6/V7)** (`spec.html`) — the 20-dimension customer rubric (Redash query 304995).
- **Live queue** (`live.html`) — the 2026-06-08 L10-pending snapshot (6 → 13; the two carryover
  Fails still stuck).

## How it stays current
`build.mjs` globs `../OpenClaw QC/Tasks/*.md` and renders whatever is there. Add or update audit
notes in the vault, push, and Vercel redeploys with the new content. To refresh the live-queue
page, regenerate `OpenClaw QC/Live-checks/<date>.md` and point `build.mjs` at it (or add a new
dated page).
