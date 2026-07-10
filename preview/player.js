// 簡易ノベルエンジン v3 — 『眠り姫と黒豹の物語』
// ホストページ側で定義: window.SCENARIOS / window.BG_RESOLVE / window.CHARA_RESOLVE
// v3: タイトル画面 / オートセーブ(localStorage) / バックログ / 立ち絵 [chara]
// タグ: bg wait p l r cm jump choice set if else endif chara chara_hide / #話者 / *ラベル
(function () {
  const textEl = document.getElementById("text");
  const nameEl = document.getElementById("namebox");
  const stage = document.getElementById("stage");
  const charaEl = document.getElementById("charaimg");
  let front = document.getElementById("bgA");
  let back = document.getElementById("bgB");

  const SAVE_KEY = "nero_autosave_v1";
  const START_FILE = "prologue.ks";

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
  let choiceCancel = null, loopActive = false;
  let vars = {};
  let seeds = [];
  let backlog = [];
  let curBg = "", curChara = "", curSys = false;
  window.__vars = vars; window.__seeds = seeds;

  function loadFile(fname, target) {
    if (!window.SCENARIOS[fname]) return;
    gen++;
    file = fname;
    program = parse(window.SCENARIOS[fname]);
    pc = 0;
    if (target) gotoLabel(target);
  }

  function gotoLabel(target) {
    const idx = program.findIndex(o => o.op === "label" && o.name === target);
    if (idx >= 0) pc = idx;
  }

  function setBg(storage, time) {
    curBg = storage;
    back.style.transition = "opacity " + (time / 1000) + "s ease";
    back.style.backgroundImage = "url('" + window.BG_RESOLVE(storage) + "')";
    requestAnimationFrame(() => {
      back.style.opacity = 1;
      front.style.opacity = 0;
      const t = front; front = back; back = t;
    });
  }

  function setChara(storage, time) {
    curChara = storage || "";
    const dur = (time === undefined ? 350 : time) / 1000;
    charaEl.style.transition = "opacity " + dur + "s ease";
    if (!storage) { charaEl.style.opacity = 0; return; }
    const url = window.CHARA_RESOLVE(storage);
    if (charaEl.getAttribute("src") !== url) {
      charaEl.style.opacity = 0;
      setTimeout(() => { charaEl.src = url; charaEl.style.opacity = 1; }, charaEl.src ? dur * 500 : 0);
    } else {
      charaEl.style.opacity = 1;
    }
  }

  function setSysMode(on) {
    curSys = !!on;
    document.getElementById("msgwin").classList.toggle("sysmode", curSys);
  }

  // ---- セーブ ----
  function autoSave() {
    try {
      localStorage.setItem(SAVE_KEY, JSON.stringify({
        file, pc, vars, seeds, bg: curBg, chara: curChara, sys: curSys,
        name: nameEl.textContent, backlog: backlog.slice(-100),
      }));
    } catch (e) { /* private mode 等は黙って諦める */ }
  }
  function loadSave() {
    try { return JSON.parse(localStorage.getItem(SAVE_KEY) || "null"); }
    catch (e) { return null; }
  }

  // ---- バックログ ----
  function pushLog() {
    const t = textEl.textContent.replace(/▾$/, "").trim();
    if (!t) return;
    const last = backlog[backlog.length - 1];
    if (last && last.text === t) return;
    backlog.push({ name: nameEl.textContent, text: t });
    if (backlog.length > 300) backlog.shift();
  }
  function showLog() {
    if (document.querySelector(".log-overlay")) return;
    const ov = document.createElement("div");
    ov.className = "log-overlay";
    const panel = document.createElement("div");
    panel.className = "log-panel";
    if (!backlog.length) {
      const e = document.createElement("div");
      e.className = "log-entry"; e.textContent = "（まだ履歴はありません）";
      panel.appendChild(e);
    }
    for (const item of backlog) {
      const e = document.createElement("div");
      e.className = "log-entry";
      if (item.name) {
        const n = document.createElement("div");
        n.className = "log-name"; n.textContent = item.name;
        e.appendChild(n);
      }
      const t = document.createElement("div");
      t.textContent = item.text;
      e.appendChild(t);
      panel.appendChild(e);
    }
    ov.appendChild(panel);
    ov.addEventListener("click", ev => { if (ev.target === ov) ov.remove(); });
    stage.appendChild(ov);
    panel.scrollTop = panel.scrollHeight;
  }

  // ---- 条件分岐 ----
  function evalIf(attrs) {
    const v = vars[attrs.var];
    if ("eq" in attrs) return String(v) === attrs.eq;
    if ("neq" in attrs) return String(v) !== attrs.neq;
    return !!v;
  }
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
    const hijack = o.attrs.hijack === "1";
    return new Promise(res => {
      choiceCancel = res;
      const overlay = document.createElement("div");
      overlay.className = "choice-overlay" + (hijack ? " hijack" : "");
      const buttons = [];
      const pickOpt = i => {
        const label = o.attrs["opt" + i];
        if (o.attrs.store) vars[o.attrs.store] = label;
        if (o.attrs.seed) seeds.push(label);
        const target = o.attrs["opt" + i + "t"];
        if (target) gotoLabel(target);
        overlay.remove();
        choosing = false;
        choiceCancel = null;
        autoSave();
        res();
      };
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
          if (hijack) { btn.classList.add("refused"); return; } // 入力は、受け付けない
          pickOpt(i);
        });
        overlay.appendChild(btn);
        buttons.push([i, btn]);
      }
      stage.appendChild(overlay);
      if (hijack) {
        const pick = parseInt(o.attrs.pick || "1", 10);
        // 一拍おいて、選択権がこちらに無いことを見せてから、勝手に選ばれる
        setTimeout(() => {
          for (const [i, btn] of buttons) {
            if (i === pick) btn.classList.add("hijack-focus");
            else btn.classList.add("hijack-dim");
          }
          setTimeout(() => pickOpt(pick), 1100);
        }, 1400);
      }
    });
  }

  function waitClick() {
    waitingClick = true;
    pushLog();
    autoSave();
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
      textEl.scrollTop = textEl.scrollHeight;
      if (!skipTyping) await sleep(28);
    }
  }

  // ---- 実行ループ ----
  async function run() {
    if (loopActive) return;
    loopActive = true;
    try {
    while (pc < program.length) {
      const o = program[pc++];
      if (o.op === "text") { skipTyping = false; await typeText(o.s); }
      else if (o.op === "name") { nameEl.textContent = o.name; }
      else if (o.op === "tag") {
        const t = o.name;
        if (t === "r") { textEl.appendChild(document.createTextNode("\n")); textEl.scrollTop = textEl.scrollHeight; }
        else if (t === "p" || t === "l") await waitClick();
        else if (t === "cm") textEl.textContent = "";
        else if (t === "bg") setBg(o.attrs.storage, parseInt(o.attrs.time || "600", 10));
        else if (t === "chara") setChara(o.attrs.storage, o.attrs.time ? parseInt(o.attrs.time, 10) : undefined);
        else if (t === "chara_hide") setChara(null, o.attrs.time ? parseInt(o.attrs.time, 10) : undefined);
        else if (t === "wait") await sleep(Math.min(parseInt(o.attrs.time || "0", 10), 3000));
        else if (t === "jump") loadFile(o.attrs.storage || file, o.attrs.target);
        else if (t === "set") vars[o.attrs.var] = o.attrs.val === undefined ? 1 : o.attrs.val;
        else if (t === "if") { if (!evalIf(o.attrs)) pc = skipToBranch(pc); }
        else if (t === "else") pc = skipToEndif(pc);
        else if (t === "endif") { /* noop */ }
        else if (t === "choice") { await showChoices(o); }
        else if (t === "sysmode") setSysMode(o.attrs.val === "1");
        else if (t === "title_screen") { showTitle(); return; }
      }
    }
    } finally { loopActive = false; }
  }

  function advance() {
    if (choosing || document.querySelector(".log-overlay") || document.querySelector(".title-overlay")) return;
    if (waitingClick && clickResolve) clickResolve();
    else skipTyping = true;
  }

  // ---- タイトル画面 ----
  function showTitle() {
    setBg("bg_forest_night.jpg", 100);
    const ov = document.createElement("div");
    ov.className = "title-overlay";
    const box = document.createElement("div");
    box.className = "title-box";
    const h = document.createElement("div");
    h.className = "title-logo";
    h.textContent = "眠り姫と黒豹の物語";
    const sub = document.createElement("div");
    sub.className = "title-sub";
    sub.textContent = "— 開発プレビュー版 —";
    box.appendChild(h); box.appendChild(sub);

    const save = loadSave();
    const mkBtn = (label, fn) => {
      const b = document.createElement("button");
      b.className = "title-btn"; b.textContent = label;
      b.addEventListener("click", ev => { ev.stopPropagation(); fn(); });
      box.appendChild(b);
    };
    mkBtn("はじめから", () => {
      vars = {}; seeds = []; backlog = [];
      window.__vars = vars; window.__seeds = seeds;
      nameEl.textContent = ""; textEl.textContent = "";
      setChara(null, 0);
      setSysMode(false);
      ov.remove();
      loadFile(START_FILE, "*start");
      run();
    });
    if (save && window.SCENARIOS[save.file]) {
      mkBtn("つづきから", () => {
        vars = save.vars || {}; seeds = save.seeds || []; backlog = save.backlog || [];
        window.__vars = vars; window.__seeds = seeds;
        loadFile(save.file);
        pc = Math.min(save.pc || 0, program.length);
        nameEl.textContent = save.name || "";
        textEl.textContent = "";
        if (save.bg) setBg(save.bg, 300);
        setChara(save.chara || null, 0);
        setSysMode(save.sys);
        ov.remove();
        run();
      });
    }
    stage.appendChild(ov);
    ov.appendChild(box);
  }

  // ---- 入力 ----
  stage.addEventListener("click", e => {
    if (e.target.closest("#toolbar") || e.target.closest(".choice-overlay") ||
        e.target.closest(".title-overlay") || e.target.closest("#logbtn")) return;
    advance();
  });
  document.addEventListener("keydown", e => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); advance(); }
    if (e.key === "l" || e.key === "L") showLog();
  });
  document.getElementById("logbtn").addEventListener("click", ev => { ev.stopPropagation(); showLog(); });
  document.querySelectorAll("#toolbar button").forEach(b => {
    b.addEventListener("click", () => {
      if (b.dataset.action === "title") { location.reload(); return; }
      document.querySelectorAll(".choice-overlay,.title-overlay,.log-overlay").forEach(el => el.remove());
      textEl.textContent = ""; nameEl.textContent = "";
      setChara(null, 0);
      loadFile(b.dataset.jump, "*start");
      if (choosing) { choosing = false; const c = choiceCancel; choiceCancel = null; if (c) c(); }
      else if (waitingClick && clickResolve) clickResolve();
      else if (!loopActive) run();
    });
  });

  // ---- 起動 ----
  showTitle();
})();
