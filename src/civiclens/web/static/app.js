/* CivicLens frontend: three-stage flow (Analyze -> Verify -> Draft). No framework, no build step.
   Every piece of model- or user-supplied text goes through esc() before it touches innerHTML. */
(() => {
"use strict";
const $ = (s, r = document) => r.querySelector(s);
const main = $("#main"), banners = $("#banners");
const MAX_BYTES = 10 * 1024 * 1024;
const S = {
  lang: "en", status: null, view: "analyze",
  file: null, imgUrl: null, sample: null, demo: null,
  analysis: null, isFallback: false, keep: new Set(), category: null,
  answer: "", location: "", ongoing: "unsure", notes: "", docLang: "en", qError: false, locTipShown: false,
  draft: null, text: "", mode: "preview", pendingLang: null,
  busy: null, busyStep: 0, error: null, lastReq: null,
};
let timer = null;

const t = (k) => (window.I18N[S.lang][k] ?? window.I18N.en[k] ?? k);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const store = { get(k) { try { return sessionStorage.getItem(k); } catch { return null; } }, set(k, v) { try { sessionStorage.setItem(k, v); } catch { /* storage unavailable */ } } };

function toast(msg) {
  const el = $("#toast"); el.textContent = msg; el.classList.add("on");
  clearTimeout(toast.t); toast.t = setTimeout(() => el.classList.remove("on"), 2600);
}

async function api(path, opts) {
  let res;
  try { res = await fetch(path, opts); } catch { throw { kind: "network", message: t("errNetwork") }; }
  let body = null;
  try { body = await res.json(); } catch { /* non-JSON error body */ }
  if (!res.ok) {
    const e = body && body.error ? body.error : { kind: "http", message: `Request failed (${res.status}).` };
    throw e;
  }
  return body;
}

/* ---------- derived ---------- */
const catLabel = (c) => ((S.status.category_labels[S.lang] || {})[c]) || c.replace(/_/g, " ");
const demoOn = () => !!S.demo;
const canAnalyze = () => S.status && (S.status.configured || S.demo);

/* ---------- static i18n + chrome ---------- */
function applyChrome() {
  document.documentElement.lang = S.lang;
  document.querySelectorAll("[data-i18n]").forEach((n) => { n.textContent = t(n.dataset.i18n); });
  document.querySelectorAll("#ui-lang button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === S.lang)));
  const order = ["analyze", "verify", "draft"], cur = order.indexOf(S.view);
  $("#steps").innerHTML = order.map((v, i) => {
    const done = i < cur, now = i === cur;
    const inner = `<span class="n" aria-hidden="true">${done ? "&#10003;" : i + 1}</span><span><b>${esc(t("step" + (i + 1)))}</b><small>${esc(t("step" + (i + 1) + "d"))}</small></span>`;
    const sr = `<span class="sr" style="position:absolute;left:-9999px">${esc(done ? t("stepDone") : now ? t("stepNow") : "")}</span>`;
    if (done && !S.busy) return `<li><button type="button" class="step done" data-go="${v}">${inner}${sr}</button></li>`;
    return `<li><div class="step${done ? " done" : ""}${i > cur ? " future" : ""}"${now ? ' aria-current="step"' : ""}>${inner}${sr}</div></li>`;
  }).join("");
}

function renderBanners() {
  const out = [];
  if (S.status && !S.status.configured && !S.demo) {
    out.push(`<div class="notice err" role="alert"><p style="font-weight:700">${esc(t("notConfigured"))}</p><p>${esc(S.status.config_message || "")}</p><p style="margin-top:6px">${esc(t("demoOffer"))}</p><p style="margin-top:10px"><button class="btn sm navy" data-act="demo-on" type="button">${esc(t("demoBtn"))}</button></p></div>`);
  }
  if (S.demo || S.isFallback) out.push(`<div class="notice fallback" role="note">${esc(t("fallbackBanner"))}</div>`);
  banners.innerHTML = out.join("");
}

/* ---------- views ---------- */
function loadingView() {
  const steps = t(S.busy === "analyze" ? "loadAnalyze" : S.busy === "translate" ? "loadTranslate" : "loadDraft");
  const lis = steps.map((s, i) => `<li class="${i < S.busyStep ? "done" : i === S.busyStep ? "on" : ""}">${esc(s)}</li>`).join("");
  const photo = S.imgUrl && S.busy === "analyze" ? `<img class="photo" style="max-height:220px;margin:0 auto 18px;width:auto" src="${S.imgUrl}" alt="">` : "";
  return `<section class="card loading" role="status" aria-live="polite" aria-label="${esc(t("working"))}">${photo}<div class="spin" aria-hidden="true"></div><h1 data-focus tabindex="-1" style="font-size:1.3rem">${esc(t("working"))}...</h1><ul class="lsteps">${lis}</ul></section>`;
}

function errorView() {
  const e = S.error; if (!e) return "";
  const retry = e.retry ? `<button class="btn sm navy" type="button" data-act="${e.retry}">${esc(t("retry"))}</button>` : "";
  const other = e.kind !== "network" && S.view === "analyze" ? `<button class="btn sm" type="button" data-act="pick">${esc(t("errPhoto"))}</button>` : "";
  return `<div class="notice err" role="alert" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center"><div style="flex:1 1 260px"><p style="font-weight:700">${esc(t("errTitle"))}</p><p>${esc(e.message)}</p></div><div style="display:flex;gap:8px;flex-wrap:wrap">${retry}${other}</div></div>`;
}

function analyzeView() {
  const s = S.status;
  const demoBox = S.demo
    ? `<div class="card" style="margin-bottom:16px"><div class="field" style="margin-top:0"><label for="scen">${esc(t("demoScenario"))}</label><select id="scen" data-demo-select>${s.demo_scenarios.map((x) => `<option value="${esc(x)}"${S.demo === x ? " selected" : ""}>${esc(t("scen")[x] || x)}</option>`).join("")}</select></div></div>` : "";
  const dis = !canAnalyze() ? " disabled" : "";
  const hero = `<section class="hero"><h1 data-focus tabindex="-1">${esc(t("heroTitle"))}</h1><p>${esc(t("heroSub"))}</p></section>`;
  let box;
  if (S.file || S.sample) {
    box = `<div class="card"><div class="preview"><img src="${S.imgUrl}" alt="${esc(t("yourPhoto"))}"><div class="stack"><div><h2>${esc(t("yourPhoto"))}</h2><p class="sub">${esc(S.file ? S.file.name : "")}</p></div><div class="btnrow" style="justify-content:flex-start;margin:0"><button class="btn primary" type="button" data-act="analyze"${dis}>${esc(t("analyzeBtn"))}</button><button class="btn" type="button" data-act="pick">${esc(t("changePhoto"))}</button></div></div></div></div>`;
  } else {
    box = `<div class="drop" id="drop"><div class="ico" aria-hidden="true"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#0e7c7b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 16l4-4 4 4 3-3 5 5"/><rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="9" cy="9" r="1.5"/></svg></div><h2>${esc(t("dropTitle"))}</h2><p class="sub">${esc(t("dropSub"))}</p><div class="btnrow"><button class="btn primary" type="button" data-act="pick">${esc(t("choose"))}</button><button class="btn" type="button" data-act="camera">${esc(t("camera"))}</button></div><p class="hint">${esc(t("dropHint"))}</p></div>`;
  }
  const exs = s.samples.map((x) => {
    const blocked = S.demo && !x.demo_scenario;
    return `<div class="ex"><img src="${esc(x.url)}" alt="${esc(t(x.id === "pothole" ? "exPothole" : "exGarbage"))}" loading="lazy"><div><span>${esc(t(x.id === "pothole" ? "exPothole" : "exGarbage"))}</span>${blocked ? `<small>${esc(t("exNeedsLive"))}</small>` : ""}<button class="btn sm" type="button" data-sample="${esc(x.id)}"${blocked || !canAnalyze() ? " disabled" : ""}>${esc(t("exampleBtn"))}</button></div></div>`;
  }).join("");
  const examples = s.samples.length && !(S.file || S.sample) ? `<section class="sect"><h2 class="sec-title">${esc(t("examplesTitle"))}</h2><div class="examples">${exs}</div></section>` : "";
  const how = `<section class="how" aria-label="How it works">${[1, 2, 3].map((i) => `<div class="h"><b>${i}. ${esc(t("how" + i + "t"))}</b><p>${esc(t("how" + i))}</p></div>`).join("")}</section>`;
  return `${hero}${errorView()}${demoBox}${box}${examples}${how}`;
}

function obsList(list, maybe) {
  return `<ul class="ledger">${list.map((o) => `<li><label class="${maybe ? "maybe" : ""}"><input type="checkbox" data-obs="${esc(o.id)}"${S.keep.has(o.id) ? " checked" : ""}><span class="t">${esc(o.text)}<span class="meta"><span class="tag ${maybe ? "assumed" : "seen"}">${esc(t(maybe ? "tagAssumed" : "tagSeen"))}</span> &nbsp;${esc(t("conf")[o.confidence] || o.confidence)}</span></span></label></li>`).join("")}</ul>`;
}

function confirmedItems() {
  const items = [];
  if (S.answer) items.push([S.lang === "hi" ? "आपका उत्तर" : "Your answer", S.answer]);
  if (S.location.trim()) items.push([t("locLabel").replace("?", ""), S.location.trim()]);
  if (S.ongoing !== "unsure") items.push([t("ongoingLabel").replace("?", ""), t("ongoing")[S.ongoing]]);
  if (S.notes.trim()) items.push([S.lang === "hi" ? "नोट" : "Notes", S.notes.trim()]);
  return items;
}
function confirmedHtml() {
  const it = confirmedItems();
  return it.length ? it.map(([k, v]) => `<li><b>${esc(k)}</b><span>${esc(v)}</span></li>`).join("") : `<li style="background:none;padding:0;color:var(--muted)">${esc(t("confirmedEmpty"))}</li>`;
}

function verifyView() {
  const a = S.analysis;
  const photo = `<div class="card sticky"><h2>${esc(t("yourPhoto"))}</h2><img class="photo" style="margin-top:12px" src="${S.imgUrl}" alt="${esc(t("yourPhoto"))}">${a.privacy_flags.length ? `<div class="notice warn" style="margin:14px 0 0" role="note">${esc(t("privacy"))}</div>` : ""}<div style="margin-top:14px"><button class="btn sm" type="button" data-act="reset">${esc(t("changePhoto"))}</button></div></div>`;
  if (!a.is_civic_issue) {
    return `<div class="grid2"><div>${photo}</div><div class="card"><h1 data-focus tabindex="-1" style="font-size:1.4rem">${esc(t("noIssueTitle"))}</h1><p class="sub" style="margin-top:8px">${esc(t("noIssueBody"))}</p><div style="margin-top:18px"><button class="btn primary" type="button" data-act="reset">${esc(t("tryAnother"))}</button></div></div></div>`;
  }
  const seen = a.observations.filter((o) => o.type === "observed");
  const maybe = a.observations.filter((o) => o.type !== "observed");
  const changed = S.category !== a.category;
  const cats = S.status.categories.filter((c) => c !== "no_civic_issue" && (c !== "unclear" || a.category === "unclear"));
  const found = `<section class="card"><div class="issue-h"><h1 id="issue" data-focus tabindex="-1" style="font-size:1.5rem">${esc(catLabel(S.category))}</h1></div>${changed ? "" : `<p class="sub" style="margin-top:6px">${esc(t("confLine").replace("{c}", t("conf")[a.category_confidence] || ""))}</p>`}
    <div class="field"><label for="cat">${esc(t("wrongType"))}</label><select id="cat" data-cat>${cats.map((c) => `<option value="${esc(c)}"${S.category === c ? " selected" : ""}>${esc(catLabel(c))}</option>`).join("")}</select></div>
    <div style="margin-top:22px"><h3 class="sec-title">${esc(t("seenTitle"))}</h3><p class="sub">${esc(t("seenSub"))}</p>${seen.length ? obsList(seen, false) : ""}</div>
    ${maybe.length ? `<div style="margin-top:22px"><h3 class="sec-title">${esc(t("maybeTitle"))}</h3><p class="sub">${esc(t("maybeSub"))}</p>${obsList(maybe, true)}</div>` : ""}
    <p class="sub" style="margin-top:14px">${esc(t("untick"))}</p>
    <div id="keep-err" class="inline-err" role="alert"></div></section>`;
  const confirmed = `<section class="card"><h3 class="sec-title">${esc(t("confirmedTitle"))}</h3><ul class="confirmed" id="confirmed" aria-live="polite">${confirmedHtml()}</ul></section>`;
  let rest;
  if (a.clarifying_question && !S.answer) {
    rest = `<section class="qcard"><h2>${esc(t("qTitle"))}</h2><p class="sub" style="margin-top:4px">${esc(t("qSub"))}</p><form id="qform" novalidate><div class="field"><label for="q">${esc(a.clarifying_question)}</label><input type="text" id="q" autocomplete="off" aria-describedby="qerr"><div id="qerr" class="inline-err" role="alert">${S.qError ? esc(t("qEmpty")) : ""}</div></div><div style="margin-top:14px"><button class="btn primary" type="submit">${esc(t("qBtn"))}</button></div></form></section>`;
  } else {
    const miss = a.missing_info.length ? `<div class="chips"><span>${esc(t("helpful"))}</span>${a.missing_info.map((m) => `<span class="chip">${esc(m)}</span>`).join("")}</div>` : "";
    rest = `<section class="card"><h2>${esc(t("detailsTitle"))}</h2>${miss}<form id="dform" novalidate>
      <div class="field"><label for="loc">${esc(t("locLabel"))}</label><input type="text" id="loc" value="${esc(S.location)}" autocomplete="street-address" aria-describedby="lochelp"><span class="help" id="lochelp">${esc(t("locHelp"))}</span></div>
      <div class="field"><span class="lbl" id="onl">${esc(t("ongoingLabel"))}</span><div class="seg radio" role="radiogroup" aria-labelledby="onl">${["unsure", "yes", "no"].map((k) => `<button type="button" role="radio" aria-checked="${S.ongoing === k}" aria-pressed="${S.ongoing === k}" data-ongoing="${k}">${esc(t("ongoing")[k])}</button>`).join("")}</div></div>
      <div class="field"><label for="notes">${esc(t("notesLabel"))}</label><textarea id="notes" aria-describedby="nh">${esc(S.notes)}</textarea><span class="help" id="nh">${esc(t("notesHelp"))}</span></div>
      <div class="field"><span class="lbl" id="dll">${esc(t("langLabel"))}</span><div class="seg radio" role="radiogroup" aria-labelledby="dll">${["en", "hi"].map((k) => `<button type="button" role="radio" aria-checked="${S.docLang === k}" aria-pressed="${S.docLang === k}" data-doclang="${k}" lang="${k}">${k === "en" ? "English" : "हिन्दी"}</button>`).join("")}</div></div>
      <p class="sub" id="loctip" style="margin-top:14px"${S.location.trim() ? " hidden" : ""}>${esc(t("locTip"))}</p>
      <div style="margin-top:18px"><button class="btn primary" type="submit">${esc(t("createBtn"))}</button></div></form></section>`;
  }
  return `${errorView()}<div class="grid2"><div>${photo}</div><div class="stack">${found}${confirmed}${rest}</div></div>`;
}

/* Render the plain-text draft as a document. Input is the editable text, so edits show up in the preview. */
function docHtml(text, lang) {
  const known = new Set([...window.I18N.en.labels, ...window.I18N.hi.labels]);
  const lines = text.replace(/\r/g, "").split("\n");
  const title = lines.shift() || "";
  let out = [], list = [];
  const flush = () => { if (list.length) { out.push(`<ul>${list.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`); list = []; } };
  for (const raw of lines) {
    const ln = raw.trimEnd();
    if (!ln.trim()) { flush(); continue; }
    if (ln.startsWith("- ")) { list.push(ln.slice(2)); continue; }
    flush();
    const m = ln.match(/^([^:]{1,40}):\s*(.*)$/);
    if (m && known.has(m[1].trim())) {
      out.push(m[2] ? `<div class="row"><b>${esc(m[1])}</b><span>${esc(m[2])}</span></div>` : `<div class="row block"><b>${esc(m[1])}</b></div>`);
    } else out.push(`<p>${esc(ln)}</p>`);
  }
  flush();
  return `<article class="paper" lang="${esc(lang)}" aria-label="${esc(t("docTab"))}"><span class="mark" aria-hidden="true">${esc(window.I18N[lang].docDraftMark)}</span><h2>${esc(title)}</h2>${out.join("")}</article>`;
}

function draftView() {
  const d = S.draft;
  const edited = S.text !== d.original;
  const modes = [["preview", "preview"], ["edit", "edit"], ["copy", "copyTab"]];
  const tools = `<div class="doc-tools"><div class="seg" role="group" aria-label="${esc(t("docTab"))}">${modes.map(([m, k]) => `<button type="button" data-mode="${m}" aria-pressed="${S.mode === m}">${esc(t(k))}</button>`).join("")}</div>
    <div class="seg" role="group" aria-label="${esc(t("docLang"))}">${["en", "hi"].map((k) => `<button type="button" data-translate="${k}" aria-pressed="${d.language === k}" lang="${k}">${k === "en" ? "English" : "हिन्दी"}</button>`).join("")}</div></div>`;
  const confirm = S.pendingLang ? `<div class="confirm" role="alertdialog" aria-label="${esc(t("translateAsk"))}"><p>${esc(t("translateAsk"))}</p><button class="btn sm navy" type="button" data-act="translate-go">${esc(t("translateGo"))}</button><button class="btn sm" type="button" data-act="translate-keep">${esc(t("translateKeep"))}</button></div>` : "";
  let body;
  if (S.mode === "edit") body = `<p class="sub" style="margin-bottom:8px">${esc(t("editHint"))}</p><label class="sr" for="editor" style="position:absolute;left:-9999px">${esc(t("docTab"))}</label><textarea id="editor" class="editor" lang="${esc(d.language)}" spellcheck="true">${esc(S.text)}</textarea>`;
  else if (S.mode === "copy") body = `<pre class="copybox" lang="${esc(d.language)}" tabindex="0">${esc(S.text)}</pre>`;
  else body = docHtml(S.text, d.language);
  const actions = `<div class="doc-actions" style="margin-top:16px"><button class="btn primary" type="button" data-act="copy">${esc(t("copy"))}</button><button class="btn" type="button" data-act="dl-txt">${esc(t("dlTxt"))}</button><button class="btn" type="button" data-act="dl-md">${esc(t("dlMd"))}</button><button class="btn" type="button" data-act="print">${esc(t("print"))}</button></div>`;
  const busy = S.busy === "translate" ? `<div class="busy">${loadingView()}</div>` : "";
  const src = `<section class="card"><h2>${esc(t("sourcesTitle"))}</h2><p class="sub">${esc(t("sourcesSub"))}</p><ul class="src">${d.sources.map((c) => `<li><span>${esc(c.statement)}</span><span><span class="tag ${c.kind}">${esc(t(c.kind === "seen" ? "tagSeen" : c.kind === "user" ? "tagUser" : "tagAssumed"))}</span></span></li>`).join("")}</ul>${d.missing_info.length ? `<p class="sub" style="margin-top:10px">${esc(t("stillMissing"))} ${esc(d.missing_info.join(", "))}</p>` : ""}</section>`;
  const checks = d.passed ? `<div class="notice info" role="status">${esc(t("checkOk"))}</div>` : `<div class="notice warn" role="alert"><p>${esc(t("checkWarn"))}</p><ul style="margin:8px 0 0 18px;padding:0">${d.warnings.map((w) => `<li>${esc(w)}</li>`).join("")}</ul></div>`;
  const send = `<section class="card"><h2>${esc(t("sendTitle"))}</h2><p class="sub" style="margin-top:6px">${esc(t("sendBody"))}</p></section>`;
  const nav = `<div class="doc-actions"><button class="btn" type="button" data-act="back-details">${esc(t("editDetails"))}</button><button class="btn ghost" type="button" data-act="reset">${esc(t("startOver"))}</button></div>`;
  void edited;
  return `<h1 class="sr">${esc(t("docTab"))}</h1><div class="draftbar" role="status" data-focus tabindex="-1">${esc(t("banner"))}</div>${errorView()}<div class="grid-draft"><div class="paper-wrap">${tools}${confirm}${body}${actions}</div><aside class="stack side">${checks}${src}${send}${nav}</aside></div>`;
}

/* ---------- render ---------- */
function render(opts = {}) {
  applyChrome(); renderBanners();
  if (!S.status) { main.innerHTML = `<div class="card"><div class="skeleton" style="width:60%"></div><div class="skeleton" style="margin-top:12px;width:90%"></div></div>`; return; }
  let html;
  if (S.busy && S.busy !== "translate") html = loadingView();
  else if (S.view === "analyze") html = analyzeView();
  else if (S.view === "verify") html = verifyView();
  else html = draftView();
  const keepScroll = opts.keepScroll ? window.scrollY : null;
  main.innerHTML = html;
  bindDrop();
  if (keepScroll !== null) window.scrollTo(0, keepScroll);
  else if (opts.focus) { const f = $("[data-focus]", main); if (f) f.focus({ preventScroll: false }); }
}

function startBusy(kind) {
  S.busy = kind; S.busyStep = 0; S.error = null; clearInterval(timer);
  const n = t(kind === "analyze" ? "loadAnalyze" : kind === "translate" ? "loadTranslate" : "loadDraft").length;
  timer = setInterval(() => { if (S.busyStep < n - 1) { S.busyStep++; render({ keepScroll: true }); } }, 2200);
}
function endBusy() { S.busy = null; clearInterval(timer); }

/* ---------- actions ---------- */
function setFile(f) {
  if (!f) return;
  if (!/^image\/(jpeg|png|webp)$/.test(f.type)) { S.error = { kind: "type", message: window.I18N[S.lang].dropHint }; render(); return; }
  if (f.size > MAX_BYTES) { S.error = { kind: "size", message: window.I18N[S.lang].dropHint }; render(); return; }
  if (S.imgUrl) URL.revokeObjectURL(S.imgUrl);
  S.file = f; S.sample = null; S.imgUrl = URL.createObjectURL(f); S.error = null; render({ focus: false });
}

async function analyze(sampleId) {
  if (sampleId) { const x = S.status.samples.find((s) => s.id === sampleId); S.sample = sampleId; S.file = null; S.imgUrl = x.url; }
  const fd = new FormData();
  if (S.sample) fd.append("sample", S.sample); else fd.append("file", S.file);
  let demo = S.demo;
  if (demo && S.sample) { const x = S.status.samples.find((q) => q.id === S.sample); if (x && x.demo_scenario) demo = x.demo_scenario; }
  if (demo) fd.append("demo", demo);
  startBusy("analyze"); render({ focus: true });
  try {
    const r = await api("/api/analyze", { method: "POST", body: fd });
    S.analysis = r.analysis; S.isFallback = r.is_fallback;
    S.keep = new Set(r.analysis.observations.map((o) => o.id)); S.category = r.analysis.category;
    S.answer = ""; S.location = ""; S.ongoing = "unsure"; S.notes = ""; S.docLang = S.lang; S.qError = false;
    S.draft = null; S.view = "verify"; endBusy();
  } catch (e) {
    endBusy(); S.error = { ...e, retry: e.kind === "limit" ? null : "analyze" };
  }
  render({ focus: true }); window.scrollTo(0, 0);
}

function draftRequest(language) {
  const a = S.analysis;
  return {
    analysis: a, language, demo: S.demo || null,
    location_text: S.location, ongoing: S.ongoing === "yes" ? true : S.ongoing === "no" ? false : null,
    notes: S.notes, clarification_answer: S.answer || null,
    category: S.category !== a.category ? S.category : null, observation_ids: [...S.keep],
  };
}
async function makeDraft(language, kind) {
  S.lastReq = draftRequest(language);
  if (kind === "draft") { startBusy("draft"); render({ focus: true }); } else { startBusy("translate"); render({ keepScroll: true }); }
  try {
    const r = await api("/api/complaint", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(S.lastReq) });
    S.draft = { ...r, original: r.text, language: r.language }; S.text = r.text; S.pendingLang = null;
    if (r.is_fallback) S.isFallback = true;
    S.view = "draft"; S.docLang = r.language; endBusy();
  } catch (e) {
    endBusy(); S.error = { ...e, retry: kind === "draft" ? "make-draft" : null }; if (kind === "draft") S.view = "verify";
  }
  render({ focus: kind === "draft" }); if (kind === "draft") window.scrollTo(0, 0);
}

function reset() {
  if (S.imgUrl && S.file) URL.revokeObjectURL(S.imgUrl);
  Object.assign(S, { view: "analyze", file: null, imgUrl: null, sample: null, analysis: null, draft: null, text: "", isFallback: false, error: null, pendingLang: null, mode: "preview", answer: "", location: "", notes: "", ongoing: "unsure" });
  render({ focus: true }); window.scrollTo(0, 0);
}

async function copyText() {
  const text = S.text;
  try { await navigator.clipboard.writeText(text); toast(t("copied")); return; } catch { /* fall through */ }
  const ta = document.createElement("textarea"); ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0"; document.body.appendChild(ta); ta.select();
  let ok = false; try { ok = document.execCommand("copy"); } catch { ok = false; }
  ta.remove(); toast(ok ? t("copied") : t("copyFail"));
}
function download(kind) {
  let body = S.text, mime = "text/plain", ext = "txt";
  if (kind === "md") { const i = body.indexOf("\n"); body = `# ${body.slice(0, i)}\n${body.slice(i + 1)}`; mime = "text/markdown"; ext = "md"; }
  const blob = new Blob(["﻿" + body], { type: `${mime};charset=utf-8` }); // BOM so Hindi opens correctly in Windows Notepad
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = `complaint_draft.${ext}`; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

/* ---------- events ---------- */
const fileInput = Object.assign(document.createElement("input"), { type: "file", accept: "image/jpeg,image/png,image/webp" });
const camInput = Object.assign(document.createElement("input"), { type: "file", accept: "image/*" });
camInput.setAttribute("capture", "environment");
[fileInput, camInput].forEach((i) => { i.hidden = true; i.addEventListener("change", () => { setFile(i.files[0]); i.value = ""; }); document.body.appendChild(i); });

function bindDrop() {
  const d = $("#drop"); if (!d) return;
  ["dragenter", "dragover"].forEach((ev) => d.addEventListener(ev, (e) => { e.preventDefault(); d.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) => d.addEventListener(ev, (e) => { e.preventDefault(); d.classList.remove("over"); }));
  d.addEventListener("drop", (e) => setFile(e.dataTransfer.files[0]));
}
window.addEventListener("dragover", (e) => e.preventDefault());
window.addEventListener("drop", (e) => { if (!e.target.closest("#drop")) e.preventDefault(); });

document.addEventListener("click", (e) => {
  const lang = e.target.closest("#ui-lang button");
  if (lang) { S.lang = lang.dataset.lang; store.set("cl_lang", S.lang); render({ keepScroll: true }); return; }
  const go = e.target.closest("[data-go]");
  if (go) { if (go.dataset.go === "analyze") { S.view = "analyze"; S.error = null; } else S.view = go.dataset.go; render({ focus: true }); return; }
  const smp = e.target.closest("[data-sample]"); if (smp) { analyze(smp.dataset.sample); return; }
  const og = e.target.closest("[data-ongoing]"); if (og) { S.ongoing = og.dataset.ongoing; syncForm(); render({ keepScroll: true }); return; }
  const dl = e.target.closest("[data-doclang]"); if (dl) { S.docLang = dl.dataset.doclang; syncForm(); render({ keepScroll: true }); return; }
  const md = e.target.closest("[data-mode]"); if (md) { syncEditor(); S.mode = md.dataset.mode; render({ keepScroll: true }); return; }
  const tr = e.target.closest("[data-translate]");
  if (tr) {
    syncEditor();
    if (tr.dataset.translate === S.draft.language) return;
    if (S.text !== S.draft.original) { S.pendingLang = tr.dataset.translate; render({ keepScroll: true }); } else makeDraft(tr.dataset.translate, "translate");
    return;
  }
  const act = e.target.closest("[data-act]"); if (!act) return;
  switch (act.dataset.act) {
    case "pick": fileInput.click(); break;
    case "camera": camInput.click(); break;
    case "analyze": analyze(); break;
    case "reset": reset(); break;
    case "demo-on": S.demo = "pothole"; render(); break;
    case "copy": syncEditor(); copyText(); break;
    case "dl-txt": syncEditor(); download("txt"); break;
    case "dl-md": syncEditor(); download("md"); break;
    case "print": syncEditor(); if (S.mode !== "preview") { S.mode = "preview"; render({ keepScroll: true }); } window.print(); break;
    case "translate-go": { const l = S.pendingLang; S.pendingLang = null; makeDraft(l, "translate"); break; }
    case "translate-keep": S.pendingLang = null; render({ keepScroll: true }); break;
    case "back-details": syncEditor(); S.view = "verify"; S.error = null; render({ focus: true }); window.scrollTo(0, 0); break;
    case "make-draft": makeDraft(S.docLang, "draft"); break;
    default: break;
  }
});

function syncEditor() { const ed = $("#editor"); if (ed) S.text = ed.value; }
function syncForm() {
  const l = $("#loc"); if (l) S.location = l.value;
  const n = $("#notes"); if (n) S.notes = n.value;
}

document.addEventListener("input", (e) => {
  const el = e.target;
  if (el.id === "loc") { S.location = el.value; const c = $("#confirmed"); if (c) c.innerHTML = confirmedHtml(); const tip = $("#loctip"); if (tip) tip.hidden = !!S.location.trim(); }
  else if (el.id === "notes") { S.notes = el.value; const c = $("#confirmed"); if (c) c.innerHTML = confirmedHtml(); }
  else if (el.id === "editor") S.text = el.value;
});
document.addEventListener("change", (e) => {
  const el = e.target;
  if (el.dataset.obs) {
    if (el.checked) S.keep.add(el.dataset.obs); else S.keep.delete(el.dataset.obs);
    const anySeen = S.analysis.observations.some((o) => o.type === "observed" && S.keep.has(o.id));
    const er = $("#keep-err"); if (er) er.textContent = anySeen ? "" : t("keepOne");
  } else if (el.matches("[data-cat]")) { S.category = el.value; render({ keepScroll: true }); $("#cat")?.focus(); }
  else if (el.matches("[data-demo-select]")) S.demo = el.value;
});
document.addEventListener("submit", (e) => {
  e.preventDefault();
  if (e.target.id === "qform") {
    const v = $("#q").value.trim();
    if (!v) { S.qError = true; $("#qerr").textContent = t("qEmpty"); $("#q").focus(); return; }
    S.answer = v; S.qError = false; render({ keepScroll: true }); return;
  }
  if (e.target.id === "dform") {
    syncForm();
    const anySeen = S.analysis.observations.some((o) => o.type === "observed" && S.keep.has(o.id));
    if (!anySeen) { $("#keep-err").textContent = t("keepOne"); $("#issue").scrollIntoView({ block: "center" }); return; }
    makeDraft(S.docLang, "draft");
  }
});

/* ---------- boot ---------- */
(async function init() {
  const saved = store.get("cl_lang");
  S.lang = saved === "hi" || saved === "en" ? saved : (navigator.language || "").toLowerCase().startsWith("hi") ? "hi" : "en";
  S.docLang = S.lang;
  render();
  try { S.status = await api("/api/status"); } catch (e) {
    main.innerHTML = `<div class="notice err" role="alert">${esc(e.message)}</div>`; return;
  }
  render({ focus: false });
})();
})();
