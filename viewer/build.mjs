// Static site generator for the OpenClaw QC vault.
// Reads ../OpenClaw QC/*.md at build time and emits a static site into ./public.
// Vercel runs this on every push (build command: `node build.mjs`), so the
// viewer stays in sync with the vault — including notes added by audit runs.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { marked } from "marked";
import matter from "gray-matter";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const VAULT = path.resolve(__dirname, "..", "OpenClaw QC");
const OUT = path.resolve(__dirname, "public");

marked.setOptions({ gfm: true, breaks: false });

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const VCLASS = { Fail: "v-fail", "Non-Fail": "v-nonfail", Pass: "v-pass" };
const chip = (v) => v ? `<span class="chip ${VCLASS[v] || ""}">${esc(v)}</span>` : "—";

function readMd(rel) {
  const p = path.join(VAULT, rel);
  if (!fs.existsSync(p)) return null;
  return matter(fs.readFileSync(p, "utf8"));
}

function layout(title, active, body) {
  const nav = [
    ["index.html", "Audits", "audits"],
    ["spec.html", "Spec (V6/V7)", "spec"],
    ["live.html", "Live queue", "live"],
  ].map(([href, label, key]) =>
    `<a href="${href}" class="${active === key ? "active" : ""}">${label}</a>`).join("");
  return `<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(title)}</title><link rel="stylesheet" href="style.css">
</head><body>
<header><div class="wrap"><a class="brand" href="index.html">OpenClaw <b>QC</b></a><nav>${nav}</nav></div></header>
<main class="wrap">${body}</main>
<footer class="wrap">Generated from the <code>OpenClaw QC</code> Obsidian vault · audit snapshot 2026-06-07 + live Redash check 2026-06-08 · project <code>mj_blue_shell</code></footer>
<script src="app.js"></script></body></html>`;
}

// ---- load tasks ----
const taskDir = path.join(VAULT, "Tasks");
const tasks = fs.readdirSync(taskDir).filter((f) => f.endsWith(".md")).map((f) => {
  const g = matter(fs.readFileSync(path.join(taskDir, f), "utf8"));
  return { id: f.replace(/\.md$/, ""), fm: g.data, body: g.content.trim() };
});
const ORDER = { Fail: 0, "Non-Fail": 1, Pass: 2 };
tasks.sort((a, b) => (ORDER[a.fm.verdict] - ORDER[b.fm.verdict]) || a.id.localeCompare(b.id));

const counts = { Pass: 0, "Non-Fail": 0, Fail: 0 };
let diverge = 0;
for (const t of tasks) {
  counts[t.fm.verdict]++;
  if (t.fm.verdict !== t.fm.drawer_verdict) diverge++;
}

// ---- index ----
const rows = tasks.map((t) => {
  const f = t.fm;
  const agree = f.verdict === f.drawer_verdict;
  const num = (x) => (x === null || x === undefined ? "" : x);
  return `<tr data-verdict="${esc(f.verdict)}" data-run="${esc(f.run)}" data-diverge="${agree ? 0 : 1}" data-carry="${f.carryover ? 1 : 0}"
    onclick="location.href='tasks/${esc(t.id)}.html'">
    <td class="mono">${esc(t.id.slice(-4))}</td>
    <td>${esc(f.persona)}</td>
    <td>${esc(f.task_type)}</td>
    <td data-sort="${ORDER[f.verdict]}">${chip(f.verdict)}</td>
    <td data-sort="${ORDER[f.drawer_verdict]}">${chip(f.drawer_verdict)}</td>
    <td class="center" title="${agree ? "verdict == drawer" : "verdict != drawer"}">${agree ? "✅" : "⚠️"}</td>
    <td class="num" data-sort="${num(f.platform_pct)}">${num(f.platform_pct)}${f.platform_pct != null ? "%" : ""}</td>
    <td class="num" data-sort="${num(f.band_6a)}">${num(f.band_6a)}</td>
    <td class="num" data-sort="${num(f.band_6b)}">${num(f.band_6b)}</td>
    <td class="num" data-sort="${num(f.denominator)}">${num(f.denominator)}</td>
    <td class="center">${esc(f.run)}${f.carryover ? ' <span class="tag">carry</span>' : ""}</td>
  </tr>`;
}).join("\n");

const indexBody = `
<h1>L10 rubric-QC audits</h1>
<p class="lede">Quality audit of contributor-authored <b>rubrics</b> (not the model's answer) at layer L10, against the customer V6/V7 spec. Three evals side by side: the platform score (response quality), my verdict (rubric quality), and the viewer drawer's cross-check.</p>
<div class="tiles">
  <div class="tile"><b>${tasks.length}</b><span>tasks</span></div>
  <div class="tile v-pass"><b>${counts.Pass}</b><span>Pass</span></div>
  <div class="tile v-nonfail"><b>${counts["Non-Fail"]}</b><span>Non-Fail</span></div>
  <div class="tile v-fail"><b>${counts.Fail}</b><span>Fail</span></div>
  <div class="tile"><b>${diverge}</b><span>divergences</span></div>
</div>
<div class="filters" id="filters">
  <button data-f="all" class="active">All</button>
  <button data-f="Fail">Fail</button>
  <button data-f="Non-Fail">Non-Fail</button>
  <button data-f="Pass">Pass</button>
  <button data-f="diverge">⚠️ Divergences</button>
  <button data-f="run1">run1</button>
  <button data-f="run2">run2</button>
  <button data-f="carry">Carryover</button>
</div>
<table id="grid" class="grid">
<thead><tr>
  <th data-type="text">ID</th><th data-type="text">Persona</th><th data-type="text">Task type</th>
  <th data-type="num">Verdict</th><th data-type="num">Drawer</th><th data-type="text" class="center">=</th>
  <th data-type="num" class="num">Plat%</th><th data-type="num" class="num">6a</th><th data-type="num" class="num">6b</th>
  <th data-type="num" class="num">n</th><th data-type="text" class="center">Run</th>
</tr></thead>
<tbody>${rows}</tbody></table>
<p class="hint">Click a row to open the audit. Click a column header to sort.</p>`;

fs.mkdirSync(path.join(OUT, "tasks"), { recursive: true });
fs.writeFileSync(path.join(OUT, "index.html"), layout("OpenClaw QC — L10 audits", "audits", indexBody));

// ---- per-task pages ----
for (const t of tasks) {
  const f = t.fm;
  const metaRows = [
    ["Persona", esc(f.persona)], ["Task type", esc(f.task_type)], ["Layer", esc(f.layer)],
    ["My verdict", chip(f.verdict)], ["Drawer verdict", chip(f.drawer_verdict)],
    ["Agree", f.verdict === f.drawer_verdict ? "✅ yes" : "⚠️ no"],
    ["Platform score", f.platform_pct != null ? f.platform_pct + "%" : "—"],
    ["Band 6a / 6b", `${f.band_6a ?? "—"} / ${f.band_6b ?? "—"}`],
    ["Denominator", f.denominator ?? "—"], ["Run", esc(f.run) + (f.carryover ? " (carryover)" : "")],
    ["Divergence", esc(f.divergence)],
  ].map(([k, v]) => `<div class="mk"><dt>${k}</dt><dd>${v}</dd></div>`).join("");
  const body = `
<p><a class="back" href="../index.html">← all audits</a></p>
<h1>${esc(f.task_type)} <span class="sub">${esc(f.persona)}</span></h1>
<p>${chip(f.verdict)} <span class="muted">vs drawer</span> ${chip(f.drawer_verdict)}
   &nbsp;·&nbsp; <a href="${esc(f.viewer)}" target="_blank" rel="noopener">open platform viewer ↗</a></p>
<dl class="meta">${metaRows}</dl>
<div class="md">${marked.parse(t.body)}</div>
<p class="mono muted">${esc(t.id)}</p>`;
  fs.writeFileSync(path.join(OUT, "tasks", t.id + ".html"), layout(`${f.task_type} — ${f.persona}`, "audits", body));
}

// ---- spec + live pages (render the vault markdown) ----
function mdPage(rel, active, fallbackTitle) {
  const g = readMd(rel);
  if (!g) return;
  const out = rel.includes("/") ? rel.split("/").pop().replace(/\.md$/, "") : rel.replace(/\.md$/, "");
  const name = active === "spec" ? "spec.html" : "live.html";
  const body = `<div class="md doc">${marked.parse(g.content.trim())}</div>`;
  fs.writeFileSync(path.join(OUT, name), layout(g.data.title || fallbackTitle, active, body));
}
mdPage("Spec-V6V7.md", "spec", "V6/V7 spec");
mdPage("Live-checks/2026-06-08.md", "live", "Live queue");

// ---- assets ----
fs.writeFileSync(path.join(OUT, "style.css"), CSS());
fs.writeFileSync(path.join(OUT, "app.js"), JS());
console.log(`Built ${tasks.length} task pages + index/spec/live into ${OUT}`);

function CSS() {
  return `:root{--bg:#fbfbfd;--card:#fff;--ink:#1b1f24;--muted:#6b7280;--line:#e5e7eb;--accent:#4f46e5;
--pass:#16a34a;--passbg:#dcfce7;--nf:#d97706;--nfbg:#fef3c7;--fail:#dc2626;--failbg:#fee2e2;}
@media(prefers-color-scheme:dark){:root{--bg:#0d1117;--card:#161b22;--ink:#e6edf3;--muted:#8b949e;--line:#30363d;
--passbg:#0f2e1b;--nfbg:#3a2c08;--failbg:#3a1414;}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
header{border-bottom:1px solid var(--line);background:var(--card);position:sticky;top:0;z-index:5}
header .wrap{display:flex;align-items:center;gap:28px;height:56px}
.brand{font-size:18px;font-weight:600;text-decoration:none;color:var(--ink)}.brand b{color:var(--accent)}
nav{display:flex;gap:20px}nav a{color:var(--muted);text-decoration:none;font-weight:500;padding:4px 0;border-bottom:2px solid transparent}
nav a:hover{color:var(--ink)}nav a.active{color:var(--ink);border-color:var(--accent)}
main{padding:28px 20px 48px}h1{font-size:26px;margin:.2em 0 .4em}h1 .sub{font-size:16px;color:var(--muted);font-weight:400}
.lede{color:var(--muted);max-width:75ch}.muted{color:var(--muted)}.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.tiles{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}
.tile{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 18px;min-width:92px;text-align:center}
.tile b{display:block;font-size:24px}.tile span{color:var(--muted);font-size:13px}
.tile.v-pass{border-color:var(--pass)}.tile.v-nonfail{border-color:var(--nf)}.tile.v-fail{border-color:var(--fail)}
.filters{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}
.filters button{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:5px 13px;cursor:pointer;font-size:13px}
.filters button.active{background:var(--accent);color:#fff;border-color:var(--accent)}
table.grid{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;font-size:14px}
.grid th,.grid td{padding:9px 11px;border-bottom:1px solid var(--line);text-align:left}
.grid th{font-size:12px;text-transform:uppercase;letter-spacing:.03em;color:var(--muted);cursor:pointer;user-select:none;white-space:nowrap}
.grid tbody tr{cursor:pointer}.grid tbody tr:hover{background:rgba(79,70,229,.06)}
.grid .num,.grid .center{text-align:center}.num{font-variant-numeric:tabular-nums}
.chip{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;font-weight:600}
.v-pass{color:var(--pass);background:var(--passbg)}.v-nonfail{color:var(--nf);background:var(--nfbg)}.v-fail{color:var(--fail);background:var(--failbg)}
.tag{font-size:10px;background:var(--line);color:var(--muted);border-radius:4px;padding:1px 4px;vertical-align:middle}
.hint{color:var(--muted);font-size:13px;margin-top:10px}.back{color:var(--accent);text-decoration:none}
dl.meta{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;margin:18px 0;padding:0}
dl.meta .mk{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:9px 12px}
dl.meta dt{font-size:11px;text-transform:uppercase;letter-spacing:.03em;color:var(--muted)}dl.meta dd{margin:3px 0 0;font-weight:500}
.md{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:6px 22px;margin-top:8px}
.md.doc{padding:6px 26px}.md h2{font-size:18px;border-top:1px solid var(--line);padding-top:16px;margin-top:22px}
.md table{border-collapse:collapse;width:100%;font-size:13.5px;margin:12px 0}
.md th,.md td{border:1px solid var(--line);padding:6px 9px;text-align:left}.md th{background:rgba(127,127,127,.08)}
.md code{background:rgba(127,127,127,.12);padding:1px 5px;border-radius:5px;font-size:.92em}
.md blockquote{border-left:3px solid var(--accent);margin:12px 0;padding:2px 14px;color:var(--muted)}
footer{color:var(--muted);font-size:12.5px;border-top:1px solid var(--line);padding:18px 20px;margin-top:30px}`;
}

function JS() {
  return `// filter chips
const f=document.getElementById('filters');
if(f){f.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;
[...f.children].forEach(x=>x.classList.toggle('active',x===b));const k=b.dataset.f;
document.querySelectorAll('#grid tbody tr').forEach(tr=>{let show=true;
if(k==='all')show=true;else if(k==='diverge')show=tr.dataset.diverge==='1';
else if(k==='carry')show=tr.dataset.carry==='1';else if(k==='run1'||k==='run2')show=tr.dataset.run===k;
else show=tr.dataset.verdict===k;tr.style.display=show?'':'none';});});}
// sortable headers
document.querySelectorAll('#grid thead th').forEach((th,i)=>{let asc=true;th.addEventListener('click',()=>{
const tb=th.closest('table').querySelector('tbody');const rows=[...tb.rows];const num=th.dataset.type==='num';
rows.sort((a,b)=>{const x=cell(a,i),y=cell(b,i);return num?(x-y):(''+x).localeCompare(''+y);});
if(!asc)rows.reverse();asc=!asc;rows.forEach(r=>tb.appendChild(r));});});
function cell(tr,i){const td=tr.cells[i];const s=td.getAttribute('data-sort');
if(s!==null&&s!=='')return isNaN(+s)?s:+s;return td.textContent.trim();}`;
}
