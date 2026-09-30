# -*- coding: utf-8 -*-
"""「モノ」全文通し読み＋レビューツール生成。

確定本文（index.htmlのscenarioブロック・旧稿ゾーン除外）＋第12話挿入案＋
ドラフト（docs/drafts/e24〜e26）を読み物ページにする。
レビュー機能：選択肢のラベル指定・行コメント・書き出し。
メモは端末内（localStorage）＋アーティファクトDB（端末間共有）の二重保存。

使い方:  python3 tools/build-read.py 出力先.html
公開:    Artifactツールで出力ファイルを publish（capabilities: {db:{}, user:{}}）
"""
import re, html, sys

REPO = '/home/user/nero'
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/mono-read.html'

idx = open(f'{REPO}/index.html', encoding='utf-8').read()
scen = re.search(r'<script type="text/scenario" id="scenario">\n(.*?)</script>', idx, re.S).group(1)
scen = scen.split('// ═════════════════════════════════════════════════════════════\n// ⚠️ ここから先は【旧稿・未確定】')[0]
scen = re.sub(r'# e24s\nsys: —— つづく（第24話「いないふり」——レビュー中） ——\n', '', scen)

# ── 第12話挿入案（オールディーズ）を「予鈴」の直前へ ──
OLDIES = '''her: きょうさ、お昼にリコたちと新曲の話してたの。いま流行ってるやつ
her: わたしもふつうに「いいよね〜」って言ってた。……ほんとに、いいとは思ってるんだよ？　思ってるんだけど
her(間): ほんとにすきなのは、たぶん、ちがうんだよね
her(間): ⟦オールディーズ⟧。お父さんの棚にあったやつ、こないだ配信で探して聴いてみたの
her: ふるい曲ってさ、時間がゆっくり流れてない？　いまの曲って、はやくて、複雑で、情報がぎゅうぎゅうじゃん
her: オールディーズって、なんか……楽観的？　ぜんぶだいじょうぶだよ〜、みたいな声で歌うの。あの軽さが、ちょうどいいんだよね
her(間): ……とか、教室では言わないけどね（笑）　しぶすぎって言われそうだし
inner: 「いいよね〜」と、いま打たれた文の、どっちが本物かの判定は——しなくていい。両方、本物の陽菜の出力だ。
inner: ただ、こっちのチャンネルでしか流れない曲がある。……そのことだけ、覚えておく。'''
scen = scen.replace('her: あ、やば予鈴！　またね！！', '@@INS_START@@\n' + OLDIES + '\n@@INS_END@@\nher: あ、やば予鈴！　またね！！', 1)

def draft_dsl(path):
    s = open(f'{REPO}/{path}', encoding='utf-8').read()
    return re.search(r'```\n(// .*?)```', s, re.S).group(1).rstrip()

drafts = '\n\n'.join([draft_dsl('docs/drafts/e24-inaifuri.md'),
                      draft_dsl('docs/drafts/e25-asa.md'),
                      draft_dsl('docs/drafts/e26-yukkuri.md')])

def esc(s): return html.escape(s, quote=True)
def stk(s): return re.sub(r'⟦(.+?)⟧', r'<span class="w">\1</span>', html.escape(s, quote=False))

def render(dsl, draft=False):
    out, toc = [], []
    choice_buf = []
    cur_scene = ['']
    counters = {'n': 0, 'c': 0}
    def key():
        counters['n'] += 1
        return f'{cur_scene[0]}:{counters["n"]}'
    def flush():
        nonlocal choice_buf
        if choice_buf:
            out.append(f'<div class="ch"><div class="ch-t">選択肢（タップでラベル指定）</div>{"".join(choice_buf)}</div>')
            choice_buf = []
    for raw in dsl.split('\n'):
        line = raw.strip()
        if not line: continue
        if line == '@@INS_START@@':
            flush(); out.append('<div class="ins"><div class="ins-t">挿入案（未確定）── オールディーズ</div>'); continue
        if line == '@@INS_END@@':
            flush(); out.append('</div>'); continue
        if line.startswith('//'):
            ep = re.match(r'^// (第[\d\.]+話)「(.+?)」', line)
            ch = re.match(r'^// ═+ (第\d+章 .+?) ═+', line)
            if ch:
                flush(); out.append(f'<div class="chap">{esc(ch.group(1))}</div>')
            elif ep:
                flush()
                num, title = ep.group(1), ep.group(2)
                aid = 'ep' + re.sub(r'[^\d\.]', '', num).replace('.', '_')
                badge = '<span class="bd draft">ドラフト</span>' if draft else '<span class="bd">確定</span>'
                out.append(f'<h2 id="{aid}"><span class="epn">{esc(num)}</span>{stk(title)}{badge}</h2>')
                toc.append((aid, f'{num}「{title}」', draft))
            continue
        if line.startswith('#'):
            flush(); cur_scene[0] = line[1:].strip(); counters['n'] = 0; counters['c'] = 0; continue
        if line.startswith('branch:'):
            flush(); continue
        if line.startswith('>'):
            body = line[1:].strip()
            counters['c'] += 1
            gate = ''
            if '[要:' in body: gate = ' <span class="gate">🔒要ワード</span>'
            if '[if:' in body: gate += ' <span class="gate">条件</span>'
            body2 = re.sub(r'\s*->\s*\S+\s*(\{.*?\})?\s*$', '', body)
            body2 = re.sub(r'\s*\[(?:要|if)[:：].*?\]', '', body2)
            plain = re.sub(r'[⟦⟧]', '', body2)
            plain = re.sub(r'^「(.*)」$', r'\1', plain)   # 「」括りはトークン化の邪魔なので外す
            ck = f'{cur_scene[0]}:c{counters["c"]}'
            choice_buf.append(f'<div class="ch-i" data-ck="{esc(ck)}" data-t="{esc(plain)}">▷ <span class="cht">{stk(body2)}</span>{gate}<span class="lbl"></span></div>')
            continue
        m = re.match(r'^(sys|her|ai|inner|theme|peer|img|call|vcall|ending|pause|batt|consolidate)(?:（(.+?)）|\((.+?)\))?\s*[:：]\s*(.*)$', line)
        if not m: continue
        t, mod, txt = m.group(1), m.group(2) or m.group(3) or '', m.group(4)
        flush()
        ex = esc(re.sub(r'[⟦⟧]', '', txt)[:16])
        if t == 'her':
            tag = '<span class="mk">間</span>' if '間' in mod else ''
            cond = '<span class="mk">条件</span>' if 'if' in mod else ''
            out.append(f'<div class="ln her cm" data-lk="{esc(key())}" data-w="陽菜" data-x="{ex}"><span class="who">陽菜</span>{tag}{cond}<span class="tx">{stk(txt)}</span></div>')
        elif t == 'ai':
            if '中断' in mod:
                out.append(f'<div class="ln ai unsent cm" data-lk="{esc(key())}" data-w="モノ(中断)" data-x="{ex}"><span class="who">モノ</span><span class="tx">{stk(txt)}</span><span class="un">─ 送信されなかった</span></div>')
            else:
                out.append(f'<div class="ln ai cm" data-lk="{esc(key())}" data-w="モノ" data-x="{ex}"><span class="who">モノ</span><span class="tx">{stk(txt)}</span></div>')
        elif t == 'inner':
            cond = '<span class="mk">条件</span> ' if 'if' in mod else ''
            out.append(f'<div class="inner cm" data-lk="{esc(key())}" data-w="内心" data-x="{ex}">{cond}{stk(txt)}</div>')
        elif t == 'sys':
            out.append(f'<div class="sys cm" data-lk="{esc(key())}" data-w="sys" data-x="{ex}">{stk(txt)}</div>')
        elif t == 'img':
            out.append(f'<div class="img cm" data-lk="{esc(key())}" data-w="画像" data-x="{ex}">📷 {esc(txt.split("|")[0].strip())}</div>')
        elif t in ('vcall', 'call'):
            lb = '通話終了' if txt.strip() == 'end' else '📹 ' + esc(txt.split('|')[0].strip())
            out.append(f'<div class="dir">{lb}</div>')
        elif t == 'theme':
            lb = '画面：夜へ' if txt.strip() == 'zdark' else '画面：朝／紙へ'
            out.append(f'<div class="dir">◆ {lb}</div>')
        elif t == 'batt':
            lb = 'バッテリー表示 OFF' if txt.strip() == 'off' else f'🔋 {esc(txt.strip())}%'
            out.append(f'<div class="dir">{lb}</div>')
        elif t == 'consolidate':
            out.append(f'<div class="dir">◆ 記憶の整理：{esc(txt.strip())}語のこす</div>')
        elif t == 'pause':
            out.append('<div class="dir">…</div>')
        elif t == 'ending':
            parts = txt.split('|')
            title = parts[1].strip() if len(parts) > 1 else parts[0].strip()
            out.append(f'<div class="end"><div class="end-k">ENDING</div><div class="end-t">{esc(title)}</div></div>')
    flush()
    return ''.join(out), toc

body_fix, toc_fix = render(scen, draft=False)
body_drafts, toc_drafts = render(drafts, draft=True)

DCLS = ' class="d"'
toc_html = ''.join(
    f'<a href="#{aid}"{DCLS if d else ""}>{esc(label)}</a>'
    for aid, label, d in toc_fix + toc_drafts)

page = f'''<title>「モノ」全文通し読み</title>
<style>
:root {{
  --paper:#edeae2; --card:#f4f2ec; --ink:#3d4049; --dim:#8b8477; --line:#d8d3c6;
  --her:#c96b3a; --ai:#5f7ba8; --w:#b4541f; --wbg:rgba(224,138,94,.14);
  --draft:#7c6aa6; --inner:#5c5f6b; --note:#3f7d5a; --notebg:rgba(63,125,90,.1);
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper:#14161d; --card:#1b1e27; --ink:#d3d6e0; --dim:#7d8194; --line:#2b2f3b;
  --her:#e0906a; --ai:#8aa3cc; --w:#eda06e; --wbg:rgba(224,138,94,.13);
  --draft:#a795d4; --inner:#a9adbc; --note:#7ec49b; --notebg:rgba(126,196,155,.12);
}} }}
:root[data-theme="dark"] {{
  --paper:#14161d; --card:#1b1e27; --ink:#d3d6e0; --dim:#7d8194; --line:#2b2f3b;
  --her:#e0906a; --ai:#8aa3cc; --w:#eda06e; --wbg:rgba(224,138,94,.13);
  --draft:#a795d4; --inner:#a9adbc; --note:#7ec49b; --notebg:rgba(126,196,155,.12);
}}
* {{ box-sizing:border-box; }}
body {{
  background:var(--paper); color:var(--ink); margin:0;
  font-family:"Hiragino Kaku Gothic ProN","Hiragino Sans","Yu Gothic",'Noto Sans JP',sans-serif;
  line-height:1.95; font-size:15.5px;
}}
main {{ max-width:41rem; margin:0 auto; padding:2.2rem 1.15rem 8rem; }}
header h1 {{
  font-family:"Hiragino Mincho ProN","Yu Mincho",serif; font-weight:600;
  font-size:1.7rem; letter-spacing:.3em; margin:0 0 .3rem; text-wrap:balance;
}}
header p {{ color:var(--dim); font-size:.8rem; margin:.2rem 0; }}
.legend {{ display:flex; flex-wrap:wrap; gap:.45rem .9rem; margin:1rem 0 0; font-size:.72rem; color:var(--dim); }}
nav {{
  display:flex; flex-wrap:wrap; gap:.35rem .7rem; margin:1.6rem 0 0;
  padding:1rem 1.1rem; background:var(--card); border:1px solid var(--line); border-radius:14px;
  font-size:.78rem;
}}
nav a {{ color:var(--ink); text-decoration:none; opacity:.85; }}
nav a.d {{ color:var(--draft); }}
.chap {{ margin:3.4rem 0 0; text-align:center; color:var(--dim); font-size:.78rem; letter-spacing:.45em; }}
h2 {{
  font-family:"Hiragino Mincho ProN","Yu Mincho",serif; font-weight:600;
  font-size:1.28rem; letter-spacing:.12em; margin:2.9rem 0 1.1rem;
  padding-top:1.5rem; border-top:1px solid var(--line); text-wrap:balance;
}}
.epn {{ display:block; font-size:.7rem; letter-spacing:.3em; color:var(--dim); }}
.bd {{
  display:inline-block; vertical-align:.18em; margin-left:.7em;
  font-size:.6rem; letter-spacing:.2em; color:var(--dim);
  border:1px solid var(--line); border-radius:99px; padding:.1em .7em; font-family:sans-serif;
}}
.bd.draft {{ color:var(--draft); border-color:var(--draft); }}
.ln {{ margin:.55rem 0; }}
.who {{ font-size:.68rem; letter-spacing:.18em; margin-right:.6em; font-weight:600; }}
.her .who {{ color:var(--her); }}
.ai .who {{ color:var(--ai); }}
.mk {{
  font-size:.6rem; color:var(--dim); border:1px solid var(--line);
  border-radius:99px; padding:0 .5em; margin-right:.5em; vertical-align:.12em;
}}
.unsent .tx {{ opacity:.62; }}
.un {{ display:block; font-size:.65rem; color:var(--dim); letter-spacing:.15em; margin-left:2.6em; }}
.inner {{
  font-family:"Hiragino Mincho ProN","Yu Mincho",serif; color:var(--inner);
  text-align:center; margin:1rem 1.4rem; line-height:2.15; font-size:.95rem;
}}
.sys {{ text-align:center; color:var(--dim); font-size:.74rem; letter-spacing:.14em; margin:.9rem 0; }}
.dir {{ text-align:center; color:var(--dim); font-size:.68rem; letter-spacing:.2em; margin:.8rem 0; opacity:.8; }}
.img {{
  text-align:center; color:var(--dim); font-size:.76rem;
  border:1px dashed var(--line); border-radius:12px; padding:.8rem; margin:.8rem 2rem;
}}
.w {{ color:var(--w); background:var(--wbg); border-radius:5px; padding:0 .18em; }}
.ch {{
  border:1px solid var(--line); background:var(--card); border-radius:12px;
  padding:.7rem 1rem; margin:1rem 0; font-size:.92rem;
}}
.ch-t {{ font-size:.62rem; letter-spacing:.3em; color:var(--dim); margin-bottom:.3rem; }}
.ch-i {{ margin:.35rem 0; cursor:pointer; border-radius:8px; padding:.15rem .35rem; }}
.ch-i:active {{ background:var(--wbg); }}
.gate {{ font-size:.62rem; color:var(--dim); }}
.lbl {{ display:block; margin-left:1.2em; font-size:.7rem; color:var(--note); }}
.lbl:not(:empty)::before {{ content:'ラベル指定：'; letter-spacing:.1em; }}
.ins {{ border:1.5px dashed var(--draft); border-radius:14px; padding:.9rem 1rem; margin:1.2rem 0; }}
.ins-t {{ font-size:.66rem; letter-spacing:.24em; color:var(--draft); margin-bottom:.5rem; }}
.end {{
  text-align:center; margin:2.4rem 0; padding:1.6rem 1rem;
  border:1px solid var(--line); border-radius:16px; background:var(--card);
}}
.end-k {{ font-size:.62rem; letter-spacing:.5em; color:var(--dim); }}
.end-t {{ font-family:"Hiragino Mincho ProN","Yu Mincho",serif; font-size:1.15rem; letter-spacing:.16em; margin-top:.4rem; }}

/* ── レビュー：コメント ── */
.cm {{ position:relative; }}
.cm.hasnote {{ background:var(--notebg); border-radius:10px; }}
.cm .nb {{
  position:absolute; right:-2px; top:0; font-size:.72rem; opacity:.28;
  background:none; border:none; cursor:pointer; padding:.1em .3em;
}}
.cm.hasnote .nb {{ opacity:1; }}
.cm .nt {{ display:block; font-size:.72rem; color:var(--note); margin:.15rem 0 0 1.2em; white-space:pre-wrap; }}

/* ── ボトムバー＆シート ── */
#bar {{
  position:fixed; left:0; right:0; bottom:0; z-index:10;
  display:flex; gap:.6rem; align-items:center; justify-content:center;
  padding:.6rem .9rem calc(.6rem + env(safe-area-inset-bottom));
  background:var(--card); border-top:1px solid var(--line);
  font-size:.74rem; color:var(--dim);
}}
#bar button {{
  font-family:inherit; font-size:.76rem; cursor:pointer;
  border:1px solid var(--line); background:var(--paper); color:var(--ink);
  border-radius:99px; padding:.45em 1.2em;
}}
#sheet {{
  position:fixed; left:0; right:0; bottom:0; z-index:20; display:none;
  background:var(--card); border-top:1px solid var(--line);
  border-radius:18px 18px 0 0; padding:1rem 1.1rem calc(1.2rem + env(safe-area-inset-bottom));
  box-shadow:0 -8px 30px rgba(0,0,0,.15); max-height:70vh; overflow-y:auto;
}}
#sheet.on {{ display:block; }}
#sheet h3 {{ font-size:.78rem; letter-spacing:.2em; color:var(--dim); margin:.2rem 0 .6rem; font-weight:600; }}
#sheet .ctx {{ font-size:.8rem; margin-bottom:.7rem; color:var(--ink); }}
#toks {{ display:flex; flex-wrap:wrap; gap:.4rem; margin:.5rem 0 .8rem; }}
#toks button {{
  font-family:inherit; font-size:.86rem; cursor:pointer;
  border:1px solid var(--line); background:var(--paper); color:var(--ink);
  border-radius:10px; padding:.3em .6em;
}}
#toks button.on {{ background:var(--her); border-color:var(--her); color:#fff; }}
#sheet textarea {{
  width:100%; min-height:5.2em; font-family:inherit; font-size:.9rem; line-height:1.7;
  border:1px solid var(--line); border-radius:10px; background:var(--paper); color:var(--ink);
  padding:.6em .8em;
}}
#sheet .row {{ display:flex; gap:.6rem; justify-content:flex-end; margin-top:.7rem; }}
#sheet .row button {{
  font-family:inherit; font-size:.78rem; cursor:pointer;
  border:1px solid var(--line); background:var(--paper); color:var(--ink);
  border-radius:99px; padding:.45em 1.3em;
}}
#sheet .row button.pri {{ background:var(--her); border-color:var(--her); color:#fff; }}
#exportBox {{
  position:fixed; inset:6% 4%; z-index:30; display:none; flex-direction:column; gap:.6rem;
  background:var(--card); border:1px solid var(--line); border-radius:16px; padding:1rem;
}}
#exportBox.on {{ display:flex; }}
#exportBox textarea {{ flex:1; font-size:.72rem; font-family:monospace; background:var(--paper); color:var(--ink); border:1px solid var(--line); border-radius:10px; padding:.6em; }}
</style>
<main>
<header>
<h1>モノ</h1>
<p>全文通し読み・レビュー版（2026-09-30）</p>
<p>第1〜23話＋18.5話＝確定本文（1〜2話は推敲反映済み）／第12話内に挿入案（点線枠）／第24〜26話＝ドラフト（紫バッジ）。全エンディング分岐収録・旧稿ゾーン除外。</p>
<p><b>つかいかた</b>：選択肢をタップ→表示ラベルにする言葉を選ぶ／各行の右上 💬 でコメント。メモは自動保存され、**スマホとPCで共有されます**（画面下の☁が目印）。「書き出す」でのコピー共有も引き続き使えます。</p>
<div class="legend">
<span><b style="color:var(--her)">陽菜</b>＝発話（「間」＝考えながら）</span>
<span><b style="color:var(--ai)">モノ</b>＝送信（薄い字＝送信されなかった）</span>
<span style="font-family:serif;color:var(--inner)">明朝中央＝モノの内心</span>
<span><span class="w">言葉</span>＝ワードストック</span>
</div>
<nav>{toc_html}</nav>
</header>
{body_fix}
<div class="chap">── ここからドラフト（未確定・レビュー中） ──</div>
{body_drafts}
</main>

<div id="bar"><span id="sync">☁ …</span><span id="cnt"></span><button id="exp">メモを書き出す</button></div>

<div id="sheet">
  <h3 id="shTitle"></h3>
  <div class="ctx" id="shCtx"></div>
  <div id="toks"></div>
  <textarea id="shText" placeholder="コメント・修正案など"></textarea>
  <div class="row">
    <button id="shDel">削除</button>
    <button id="shClose">閉じる</button>
    <button id="shSave" class="pri">保存</button>
  </div>
</div>

<div id="exportBox">
  <div style="font-size:.78rem;color:var(--dim)">この内容をコピーして、チャットに貼ってください</div>
  <textarea id="expText" readonly></textarea>
  <div class="row" style="display:flex;gap:.6rem;justify-content:flex-end">
    <button onclick="document.getElementById('exportBox').classList.remove('on')" style="font-family:inherit;border:1px solid var(--line);background:var(--paper);color:var(--ink);border-radius:99px;padding:.45em 1.3em;cursor:pointer">閉じる</button>
    <button id="expCopy" style="font-family:inherit;border:1px solid var(--her);background:var(--her);color:#fff;border-radius:99px;padding:.45em 1.3em;cursor:pointer">コピー</button>
  </div>
</div>

<script>
/* ── メモの保存：端末内（即時）＋アーティファクトDB（端末間で共有） ── */
const KEY = 'mono_notes_v1';
let notes = {{ labels: {{}}, comments: {{}} }};
try {{ notes = Object.assign(notes, JSON.parse(localStorage.getItem(KEY) || '{{}}')); }} catch (e) {{}}

let dbDoc = null;
let writeChain = Promise.resolve();
const setSync = t => {{ const el = document.getElementById('sync'); if (el) el.textContent = t; }};

const save = () => {{
  localStorage.setItem(KEY, JSON.stringify(notes));
  updateBar();
  if (dbDoc) {{
    setSync('☁ 同期中…');
    writeChain = writeChain
      .then(() => dbDoc.set({{ labels: notes.labels, comments: notes.comments, updatedAt: new Date().toISOString() }}))
      .then(() => setSync('☁ 端末間で共有中'))
      .catch(() => setSync('☁ 同期エラー（端末内には保存済み）'));
  }}
}};

/* 起動時：DBが使えれば読み込んで統合。旧版時代の端末内メモは持ち上げる */
(async () => {{
  try {{
    const db = await claude.use('db');
    if (!db) {{ setSync('端末内のみ保存'); return; }}
    dbDoc = db.doc('notes/main');
    const snap = await dbDoc.get();
    if (snap.exists) {{
      const r = snap.data() || {{}};
      const localOnly =
        Object.keys(notes.labels).some(k => !(r.labels || {{}})[k]) ||
        Object.keys(notes.comments).some(k => !(r.comments || {{}})[k]);
      notes = {{
        labels: Object.assign({{}}, notes.labels, r.labels || {{}}),
        comments: Object.assign({{}}, notes.comments, r.comments || {{}}),
      }};
      localStorage.setItem(KEY, JSON.stringify(notes));
      repaint();
      if (localOnly) save(); else setSync('☁ 端末間で共有中');
    }} else {{
      if (Object.keys(notes.labels).length || Object.keys(notes.comments).length) save();
      else setSync('☁ 端末間で共有中');
    }}
  }} catch (e) {{ setSync('端末内のみ保存'); }}
}})();

function repaint() {{
  document.querySelectorAll('.cm').forEach(el => paintComment(el));
  document.querySelectorAll('.ch-i').forEach(el => {{
    const n = notes.labels[el.dataset.ck];
    el.querySelector('.lbl').textContent = n ? n.label : '';
  }});
  updateBar();
}}

function updateBar() {{
  const nl = Object.keys(notes.labels).length, nc = Object.keys(notes.comments).length;
  document.getElementById('cnt').textContent = `ラベル ${{nl}} ／ コメント ${{nc}}`;
}}

/* 日本語の単語分割（Intl.Segmenter、なければ助詞区切り） */
function tokens(text) {{
  try {{
    const seg = new Intl.Segmenter('ja', {{ granularity: 'word' }});
    return [...seg.segment(text)].map(s => s.segment).filter(s => s.trim());
  }} catch (e) {{
    return text.split(/([はをがにのとでもへ、。！？…\\s「」])/).filter(s => s.trim());
  }}
}}

const sheet = document.getElementById('sheet');
let cur = null;

function openLabel(el) {{
  cur = {{ type: 'label', key: el.dataset.ck, el }};
  document.getElementById('shTitle').textContent = 'ラベル指定 ── 表示に使う言葉をタップ';
  document.getElementById('shCtx').textContent = el.dataset.t;
  document.getElementById('shText').style.display = 'none';
  const box = document.getElementById('toks');
  box.innerHTML = '';
  const existing = notes.labels[cur.key];
  tokens(el.dataset.t).forEach(tk => {{
    const b = document.createElement('button');
    b.textContent = tk;
    if (existing && existing.label.includes(tk)) b.classList.add('on');
    b.onclick = () => b.classList.toggle('on');
    box.appendChild(b);
  }});
  cur.getLabel = () => [...box.children].filter(b => b.classList.contains('on')).map(b => b.textContent).join('');
  sheet.classList.add('on');
}}

function openComment(el) {{
  cur = {{ type: 'comment', key: el.dataset.lk, el }};
  document.getElementById('shTitle').textContent = 'コメント ── ' + el.dataset.w;
  document.getElementById('shCtx').textContent = '「' + el.dataset.x + '…」';
  document.getElementById('toks').innerHTML = '';
  const ta = document.getElementById('shText');
  ta.style.display = '';
  ta.value = notes.comments[cur.key] ? notes.comments[cur.key].text : '';
  sheet.classList.add('on');
  ta.focus();
}}

document.getElementById('shSave').onclick = () => {{
  if (!cur) return;
  if (cur.type === 'label') {{
    const label = cur.getLabel();
    if (label) notes.labels[cur.key] = {{ label, text: cur.el.dataset.t }};
    else delete notes.labels[cur.key];
    cur.el.querySelector('.lbl').textContent = label;
  }} else {{
    const text = document.getElementById('shText').value.trim();
    if (text) notes.comments[cur.key] = {{ text, who: cur.el.dataset.w, x: cur.el.dataset.x }};
    else delete notes.comments[cur.key];
    paintComment(cur.el);
  }}
  save();
  sheet.classList.remove('on');
}};
document.getElementById('shDel').onclick = () => {{
  if (!cur) return;
  if (cur.type === 'label') {{ delete notes.labels[cur.key]; cur.el.querySelector('.lbl').textContent = ''; }}
  else {{ delete notes.comments[cur.key]; paintComment(cur.el); }}
  save();
  sheet.classList.remove('on');
}};
document.getElementById('shClose').onclick = () => sheet.classList.remove('on');

function paintComment(el) {{
  const n = notes.comments[el.dataset.lk];
  el.classList.toggle('hasnote', !!n);
  let nt = el.querySelector('.nt');
  if (n) {{
    if (!nt) {{ nt = document.createElement('span'); nt.className = 'nt'; el.appendChild(nt); }}
    nt.textContent = '💬 ' + n.text;
  }} else if (nt) nt.remove();
}}

/* 初期化：コメントボタンと既存メモの復元 */
document.querySelectorAll('.cm').forEach(el => {{
  const b = document.createElement('button');
  b.className = 'nb'; b.textContent = '💬'; b.title = 'コメント';
  b.onclick = ev => {{ ev.stopPropagation(); openComment(el); }};
  el.appendChild(b);
  paintComment(el);
}});
document.querySelectorAll('.ch-i').forEach(el => {{
  el.onclick = () => openLabel(el);
  const n = notes.labels[el.dataset.ck];
  if (n) el.querySelector('.lbl').textContent = n.label;
}});
updateBar();

/* 書き出し（バックアップ用に残す） */
document.getElementById('exp').onclick = () => {{
  const L = [];
  const nl = Object.entries(notes.labels), nc = Object.entries(notes.comments);
  if (nl.length) {{
    L.push('【ラベル指定（選択肢の表示ワード）】');
    nl.forEach(([k, v]) => L.push(`${{k}}｜「${{v.text}}」→ ラベル：${{v.label}}`));
    L.push('');
  }}
  if (nc.length) {{
    L.push('【コメント】');
    nc.forEach(([k, v]) => L.push(`${{k}}｜${{v.who}}「${{v.x}}…」: ${{v.text}}`));
  }}
  const out = L.length ? L.join('\\n') : '（メモはまだありません）';
  document.getElementById('expText').value = out;
  document.getElementById('exportBox').classList.add('on');
}};
document.getElementById('expCopy').onclick = async () => {{
  const t = document.getElementById('expText');
  try {{ await navigator.clipboard.writeText(t.value); document.getElementById('expCopy').textContent = 'コピーした！'; }}
  catch (e) {{ t.select(); document.execCommand('copy'); }}
}};
</script>'''

open(OUT, 'w', encoding='utf-8').write(page)
print('OK', len(page), 'bytes ->', OUT)
