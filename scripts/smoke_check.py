#!/usr/bin/env python3
"""Generic smoke test for a single-file HTML workspace.

Checks:
  1. required structure markers
  2. no external script / stylesheet / font / image references
  3. generic risk patterns (absolute home paths, private IPs, secret-like literals)
  4. optional deny-list supplied with --deny-file (one term per line, never hard-coded here)
  5. render functions do not call each other (DAG guard)
  6. JavaScript syntax via `node --check`
  7. render stubs: markers, summary rows, full-data aggregation, append-only import, empty state

Usage:
  python scripts/smoke_check.py
  python scripts/smoke_check.py --html path/to/workspace.html --node /path/to/node
  python scripts/smoke_check.py --deny-file my-terms.txt
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_HTML = os.path.join(ROOT, "assets", "workspace-template.html")

REQUIRED = [
    "const CONFIG=",
    "function seedData(){",
    "function load(){",
    "function save(){",
    "function refreshAll(){",
    "function renderToday(){",
    "function renderBoard(){",
    "function renderRoster(){",
    "function renderGrowth(){",
    "function handleAct(act,el){",
    "function handleInput(el,type){",
    "function hostDb(){",
    "function exportJSON(){",
    "DOMContentLoaded",
]

RISK_PATTERNS = [
    (r"<(?:script|link)[^>]+(?:src|href)\s*=\s*[\"'](?:https?:)?//", "external script/link"),
    (r"<img[^>]+(?:src|srcset)\s*=\s*[\"'](?:https?:)?//", "external image"),
    (r"@import\s+url\(\s*[\"']?https?://", "external CSS import"),
    (r"[A-Za-z]:\\Users\\", "absolute home path"),
    (r"/home/[A-Za-z0-9_.-]+/", "absolute home path"),
    (r"\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b", "private IP literal"),
    (r"\b(?:sk-[A-Za-z0-9_-]{12,}|AKIA[A-Z0-9]{12,})\b", "secret-like literal"),
]

MOCK = r"""
var _store = {};
var localStorage = {
  getItem: function(k){ return Object.prototype.hasOwnProperty.call(_store,k) ? _store[k] : null; },
  setItem: function(k,v){ _store[k] = String(v); },
  removeItem: function(k){ delete _store[k]; },
  key: function(i){ return Object.keys(_store)[i] || null; },
  get length(){ return Object.keys(_store).length; }
};
function _el(){
  return { innerHTML:'', value:'', textContent:'', className:'', style:{}, dataset:{}, files:[],
    classList:{toggle:function(){},add:function(){},remove:function(){},contains:function(){return false;}},
    addEventListener:function(){}, appendChild:function(){}, remove:function(){}, click:function(){},
    setAttribute:function(){}, querySelector:function(){return null;}, querySelectorAll:function(){return [];},
    closest:function(){return null;} };
}
var _els = {};
var document = {
  readyState:'loading', title:'',
  getElementById:function(id){ return _els[id] || (_els[id]=_el()); },
  querySelector:function(){ return null; }, querySelectorAll:function(){ return []; },
  createElement:function(){ return _el(); }, addEventListener:function(){},
  body:{appendChild:function(){}}
};
var window = { HostDB:null, innerWidth:1400, addEventListener:function(){},
  location:{href:''} };
var navigator = {};
var setTimeout = function(){ return 0; }; var clearTimeout = function(){};
var setInterval = function(){ return 0; }; var clearInterval = function(){};
var alert = function(){}; var confirm = function(){ return true; };
var fetch = function(){ return Promise.reject(new Error('offline')); };
var FileReader = function(){}; var Blob = function(){};
var URL = { createObjectURL:function(){return '';}, revokeObjectURL:function(){} };
"""

STUB = r"""
var __n=0,__f=0;
function __ok(c,l){ __n++; if(c) console.log('PASS '+l); else { __f++; console.log('FAIL '+l); } }
function __count(s,k){ return s.split(k).length-1; }
try{
  STATE=load(); CUR_DATE=todayStr();
  __ok(STATE && Array.isArray(STATE.members), 'load() returns a usable state');
  __ok(STATE.members.length>=3 && STATE.tasks.some(function(t){ return !t.done && t.due<CUR_DATE; }),
       'seed data has 3+ members and one overdue task');
  __ok(typeof refreshAll==='function','unified refresh entry exists');

  var b=overall();
  __ok(b.total===STATE.members.length,'overall() counts all members');
  var before=b.total;
  BOARD_MODE='owner';
  var b2=overall();
  __ok(b2.total===before,'aggregation is unchanged when the board dimension switches');
  BOARD_MODE='group';

  var today=renderToday();
  __ok(today.indexOf('今天要处理')>-1,'top section renders');
  __ok(today.indexOf('已逾期')>-1,'overdue items are surfaced');

  var board=renderBoard();
  __ok(__count(board,'tr class="sumrow"')===1,'board has exactly one summary row');
  __ok(board.indexOf('<svg')>-1,'board contains an inline SVG chart');
  __ok(board.indexOf('全量口径')>-1,'summary row states its scope');

  var roster=renderRoster();
  __ok(__count(roster,'tr class="sumrow"')===1,'roster has exactly one summary row');
  __ok(roster.indexOf('全部合计')>-1,'roster summary label present');

  var growth=renderGrowth();
  __ok(__count(growth,'class="sumbar"')===2,'growth has two summary cards');
  __ok(growth.indexOf('viewBox="0 0 180 130"')>-1,'relation graph has a fixed viewBox');
  __ok(growth.indexOf('目标与扩充')>-1,'growth section renders');

  /* append-only import: existing rows must not be overwritten */
  var snapshot=JSON.stringify(STATE.members);
  var originalCount=STATE.members.length;
  applyRosterImport([
    {id:'x1',group:'g1',owner:'o1',code:'A-01',name:'duplicate',note:''},
    {id:'x2',group:'g2',owner:'',code:'Z-99',name:'new entry',note:'fresh'}
  ]);
  __ok(STATE.members.length===originalCount+1,'import appends exactly one new row');
  __ok(JSON.stringify(STATE.members.slice(0,originalCount))===snapshot,
       'existing rows are byte-for-byte untouched');

  /* empty state must not throw */
  STATE.members=[]; STATE.tasks=[]; STATE.pipeline=[]; STATE.progress={};
  try{
    var e1=renderToday(), e2=renderBoard(), e3=renderRoster(), e4=renderGrowth();
    __ok(e1&&e2&&e3&&e4,'all four renderers survive an empty state');
    __ok(e2.indexOf('全部合计')>-1,'summary row survives an empty state');
  }catch(err){ __ok(false,'empty state throws: '+err.message); }

  console.log('STUB TOTAL '+__n+' FAIL '+__f);
  process.exit(__f?1:0);
}catch(err){ console.log('EXCEPTION '+err.stack); process.exit(1); }
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", default=DEFAULT_HTML)
    ap.add_argument("--node", default=shutil.which("node") or "node")
    ap.add_argument("--deny-file", default=None,
                    help="optional file with one forbidden term per line; never hard-coded in this repo")
    ap.add_argument("--skip-render", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.html):
        print("FAIL html not found:", args.html)
        return 1
    html = open(args.html, encoding="utf-8").read()
    failures = 0

    print("=== 1. structure markers ===")
    for key in REQUIRED:
        ok = key in html
        print(("PASS " if ok else "FAIL ") + key)
        failures += 0 if ok else 1
    placeholders = re.findall(r"/\* MODULE_[A-Z_]+ \*/", html)
    ok = not placeholders
    print(("PASS " if ok else "FAIL ") + "module placeholders cleared " + str(placeholders))
    failures += 0 if ok else 1

    print("=== 2. no external references / generic risk patterns ===")
    for pattern, label in RISK_PATTERNS:
        hits = re.findall(pattern, html, re.I)
        ok = not hits
        print(("PASS " if ok else "FAIL ") + label + ("" if ok else " -> " + str(hits[:3])))
        failures += 0 if ok else 1

    print("=== 3. optional deny list ===")
    if args.deny_file:
        terms = [t.strip() for t in open(args.deny_file, encoding="utf-8").read().splitlines()
                 if t.strip() and not t.startswith("#")]
        bad = [t for t in terms if t.lower() in html.lower()]
        print(("PASS " if not bad else "FAIL ") + "deny list clean " + str(bad[:10]))
        failures += 0 if not bad else 1
    else:
        print("SKIP no deny file supplied")

    print("=== 4. render function DAG guard ===")
    blocks = re.split(r"(?=^function )", html, flags=re.M)
    render_names = set()
    for blk in blocks:
        m = re.match(r"function (render\w+)\s*\(", blk)
        if m:
            render_names.add(m.group(1))
    cycles = []
    for blk in blocks:
        m = re.match(r"function (render\w+)\s*\(", blk)
        if not m:
            continue
        caller = m.group(1)
        for callee in re.findall(r"\b(render\w+)\s*\(", blk):
            if callee != caller and callee in render_names:
                cycles.append(caller + " -> " + callee)
    ok = not cycles
    print(("PASS " if ok else "FAIL ") + "render functions do not call each other " + str(cycles))
    failures += 0 if ok else 1

    print("=== 5. JavaScript syntax ===")
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.S)
    src = max(scripts, key=len) if scripts else ""
    tmpdir = tempfile.mkdtemp(prefix="ws_smoke_")
    syntax_js = os.path.join(tmpdir, "syntax.js")
    open(syntax_js, "w", encoding="utf-8").write(src)
    try:
        r = subprocess.run([args.node, "--check", syntax_js],
                           capture_output=True, text=True, encoding="utf-8", timeout=60)
        ok = r.returncode == 0
        print(("PASS " if ok else "FAIL ") + "node --check" +
              ("" if ok else "\n" + (r.stderr or "")[:800]))
        failures += 0 if ok else 1
    except (OSError, subprocess.TimeoutExpired) as e:
        print("FAIL node --check unavailable:", e)
        failures += 1
        ok = False

    if args.skip_render or not ok:
        print("SKIP render stubs")
    else:
        print("=== 6. render stubs ===")
        bundle_js = os.path.join(tmpdir, "bundle.js")
        open(bundle_js, "w", encoding="utf-8").write(MOCK + "\n" + src + "\n" + STUB)
        try:
            r = subprocess.run([args.node, bundle_js],
                               capture_output=True, text=True, encoding="utf-8", timeout=90)
            print(r.stdout.strip())
            if r.stderr:
                print("STDERR:", r.stderr[:800])
            failures += 0 if r.returncode == 0 else 1
        except (OSError, subprocess.TimeoutExpired) as e:
            print("FAIL render stubs:", e)
            failures += 1

    try:
        for name in os.listdir(tmpdir):
            os.remove(os.path.join(tmpdir, name))
        os.rmdir(tmpdir)
    except OSError:
        pass

    print("\nRESULT:", "OK" if failures == 0 else "FAIL (" + str(failures) + ")")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
