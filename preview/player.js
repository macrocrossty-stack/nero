// 簡易ノベルエンジン v2 — 『眠り姫と黒豹の物語』
// ホストページ側で以下を定義してから読み込むこと:
//   window.SCENARIOS = { "first.ks": "...", ... }
//   window.BG_RESOLVE = storage => 画像URL
// 対応タグ: bg / wait / p / l / r / cm / jump / #話者 / *ラベル
//           choice / set / if / else / endif（仕様は docs/07）
(function () {
  const textEl = document.getElementById("text");
  const nameEl = document.getElementById("namebox");
  let front = document.getElementById("bgA");
  let back = document.getElementById("bgB");
  const stage = document.getElementById("stage");

  // ---- パーサ ----
  function parse(src) {
    const ops = [];
    for (const rawLine of src.split(/\r?\n/)) {
      const line = rawLine.trim();
      if (!line || line.startsWith(";")) continue;
      if (line.startsWith("*")) { ops.push({ op: "label", name: line.split(/\s/)[0] }); continue; }
      if (line.startsWith("#")) { ops.push({ op: "name", name: line.slice(1).trim() }); continue; }
      let i = 0;
      while (i < line.length) {
        const open = line.indexOf("[", i);
        if (open === -1) { ops.push({ op: "text", s: line.slice(i) }); break; }
        if (open > i) ops.push({ op: "text", s: line.slice(i, open) });
        const close = line.indexOf("]", open);
        if (close === -1) { ops.push({ op: "text", s: line.slice(open) }); break; }
        ops.push(parseTag(line.slice(open + 1, close)));
        i = close + 1;
      }
    }
    return ops;
  }

  function parseTag(body) {
    const parts = body.trim().split(/\s+/);
    const attrs = {};
    for (const p of parts.slice(1)) {
      const eq = p.indexOf("=");
      if (eq > 0) attrs[p.slice(0, eq)] = p.slice(eq + 1).replace(/^["']|["']$/g, "");
    }
    return { op: "tag", name: parts[0], attrs };
  }

  // ---- 状態 ----
  let program = [], pc = 0, file = "", gen = 0;
  let waitingClick = false, clickResolve = null, skipTyping = false, choosing = false;
  const vars = {};   // ゲーム内変数
  const seeds = [];  // 🌱思い出選択の記録（終章で使用）
  window.__vars = vars; window.__seeds = seeds; // デバッグ用

  function loadFile(fname, target) {
    if (!window.SCENARIOS[fname]) return;
    gen++;
    file = fname;
    program = parse(window.SCENARIOS[fname]);
    pc = 0;
    if (target) {
      const idx = program.findIndex(o => o.op === "label" && o.name === target);
      if (idx >= 0) pc = idx;
    }
  }

  function gotoLabel(target) {
    const idx = program.findIndex(o => o.op === "label" && o.name === target);
    if (idx >= 0) pc = idx;
  }

  function setBg(storage, time) {
    back.style.transition = "opacity " + (time / 1000) + "s ease";
    back.style.backgroundImage = "url('" + window.BG_RESOLVE(storage) + "')";
    requestAnimationFrame(() => {
      back.style.opacity = 1;
      front.style.opacity = 0;
      const t = front; front = back; back = t;
    });
  }

  function waitClick() {
    waitingClick = true;
    const m = document.createElement("span");
    m.id = "marker"; m.textContent = "▾";
    textEl.appendChild(m);
    return new Promise(res => { clickResolve = () => { waitingClick = false; m.remove(); res(); }; });
  }

  const sleep = ms => new Promise(r => setTimeout(r, ms));

  async function typeText(s) {
    const myGen = gen;
    for (const ch of s) {
      if (myGen !== gen) return;
      textEl.appendChild(document.createTextNode(ch));
      if (!skipTyping) await sleep(28);
    }
  }

  // ---- 条件分岐 ----
  function evalIf(attrs) {
    const v = vars[attrs.var];
    if ("eq" in attrs) return String(v) === attrs.eq;
    if ("neq" in attrs) return String(v) !== attrs.neq;
    return !!v;
  }
  // if が偽のとき: 対応する else/endif の直後へ
  function skipToBranch(from) {
    let depth = 0;
    for (let i = from; i < program.length; i++) {
      const o = program[i];
      if (o.op !== "tag") continue;
      if (o.name === "if") depth++;
      else if (o.name === "endif") { if (depth === 0) return i + 1; depth--; }
      else if (o.name === "else" && depth === 0) return i + 1;
    }
    return program.length;
  }
  // 真ブランチ実行中に else に到達: endif の直後へ
  function skipToEndif(from) {
    let depth = 0;
    for (let i = from; i < program.length; i++) {
      const o = program[i];
      if (o.op !== "tag") continue;
      if (o.name === "if") depth++;
      else if (o.name === "endif") { if (depth === 0) return i + 1; depth--; }
    }
    return program.length;
  }

  // ---- 選択肢 ----
  function showChoices(o) {
    choosing = true;
    return new Promise(res => {
      const overlay = document.createElement("div");
      overlay.className = "choice-overlay";
      for (let i = 1; i <= 8; i++) {
        const label = o.attrs["opt" + i];
        if (!label) continue;
        const cond = o.attrs["opt" + i + "if"];
        if (cond && !vars[cond]) continue;
        const hide = o.attrs["opt" + i + "hide"];
        if (hide && vars[hide]) continue;
        const btn = document.createElement("button");
        btn.className = "choice-btn";
        btn.textContent = label.replace(/＿/g, " ");
        btn.addEventListener("click", ev => {
          ev.stopPropagation();
          if (o.attrs.store) vars[o.attrs.store] = label;
          if (o.attrs.seed) seeds.push(label);
          overlay.remove();
          choosing = false;
          res(o.attrs["opt" + i + "t"] || null);
        });
        overlay.appendChild(btn);
      }
      stage.appendChild(overlay);
    });
  }

  // ---- 実行ループ ----
  async function run() {
    while (pc < program.length) {
      const o = program[pc++];
      if (o.op === "text") { skipTyping = false; await typeText(o.s); }
      else if (o.op === "name") { nameEl.textContent = o.name; }
      else if (o.op === "tag") {
        const t = o.name;
        if (t === "r") textEl.appendChild(document.createTextNode("\n"));
        else if (t === "p" || t === "l") await waitClick();
        else if (t === "cm") textEl.textContent = "";
        else if (t === "bg") setBg(o.attrs.storage, parseInt(o.attrs.time || "600", 10));
        else if (t === "wait") await sleep(Math.min(parseInt(o.attrs.time || "0", 10), 3000));
        else if (t === "jump") loadFile(o.attrs.storage || file, o.attrs.target);
        else if (t === "set") vars[o.attrs.var] = o.attrs.val === undefined ? 1 : o.attrs.val;
        else if (t === "if") { if (!evalIf(o.attrs)) pc = skipToBranch(pc); }
        else if (t === "else") pc = skipToEndif(pc);
        else if (t === "endif") { /* noop */ }
        else if (t === "choice") {
          const target = await showChoices(o);
          if (target) gotoLabel(target);
        }
        // playbgm / stopbgm / title 等は無視（本実装フェーズで対応）
      }
    }
  }

  function advance() {
    if (choosing) return;
    if (waitingClick && clickResolve) clickResolve();
    else skipTyping = true;
  }

  stage.addEventListener("click", e => {
    if (e.target.closest("#toolbar") || e.target.closest(".choice-overlay")) return;
    advance();
  });
  document.addEventListener("keydown", e => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); advance(); }
  });
  document.querySelectorAll("#toolbar button").forEach(b => {
    b.addEventListener("click", () => {
      textEl.textContent = ""; nameEl.textContent = "";
      document.querySelectorAll(".choice-overlay").forEach(el => el.remove());
      choosing = false;
      loadFile(b.dataset.jump, "*start");
      if (waitingClick && clickResolve) clickResolve();
    });
  });

  loadFile("first.ks", "*start");
  run();
})();
