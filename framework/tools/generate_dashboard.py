#!/usr/bin/env python3
"""
Chrysalis Dashboard Generator
Usage:  python3 framework/tools/generate_dashboard.py
Output: dashboard.html at repo root — opens automatically in browser

Design goal: retain the original Chrysalis functionality while presenting the
same data as a polished job-search command center.
"""

import json
import platform
import re
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent  # framework/tools/X.py → repo root

# ── YAML ─────────────────────────────────────────────────────────────────────

def _strip_yaml_comment(value):
    """Remove inline comments outside quotes for the small YAML subset we use."""
    quote = None
    for i, ch in enumerate(value):
        if ch in ('"', "'"):
            quote = None if quote == ch else ch if quote is None else quote
        elif ch == '#' and quote is None and (i == 0 or value[i - 1].isspace()):
            return value[:i].rstrip()
    return value.strip()

def _yaml_scalar(value):
    """Parse the scalar/list subset used by frontmatter and framework/index.yaml."""
    value = _strip_yaml_comment(value).strip()
    if value.startswith('[') and value.endswith(']'):
        return [x.strip().strip('"').strip("'") for x in value[1:-1].split(',') if x.strip()]
    value = value.strip('"').strip("'")
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.lower() in ('null', '~', ''):
        return None
    return value

def _simple_yaml(text):
    """
    Tiny fallback parser for Chrysalis' YAML shape.

    PyYAML is preferred when installed, but dashboard generation should still work
    in a fresh clone. This parser intentionally supports only the structures used
    here: flat frontmatter, top-level mappings, one-level nested mappings, and
    lists of mappings such as `cards:` in framework/index.yaml.
    """
    out = {}
    current_key = None
    current_item = None

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith('#'):
            continue
        indent = len(raw) - len(raw.lstrip(' '))
        line = raw.strip()

        if indent == 0 and ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            parsed = _yaml_scalar(value)
            if parsed is None and _strip_yaml_comment(value) == '':
                parsed = [] if key == 'cards' else {}
            out[key] = parsed
            current_key = key
            current_item = None
            continue

        if current_key is None:
            continue

        container = out.get(current_key)
        if line.startswith('- '):
            if not isinstance(container, list):
                container = []
                out[current_key] = container
            current_item = {}
            container.append(current_item)
            rest = line[2:].strip()
            if ':' in rest:
                key, _, value = rest.partition(':')
                current_item[key.strip()] = _yaml_scalar(value)
            continue

        if ':' not in line:
            continue
        key, _, value = line.partition(':')
        key = key.strip()
        parsed = _yaml_scalar(value)

        if isinstance(container, list) and current_item is not None:
            current_item[key] = parsed
        elif isinstance(container, dict):
            container[key] = parsed
        elif indent > 0:
            out[key] = parsed

    return out

def parse_yaml(text):
    try:
        import yaml
        return yaml.safe_load(text) or {}
    except Exception:
        return _simple_yaml(text)

def frontmatter(text):
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n', text, re.DOTALL)
    return parse_yaml(m.group(1)) if m else {}

# ── Markdown table parsing ────────────────────────────────────────────────────

def parse_table(block):
    """Parse a markdown table block → list of dicts. Handles | inside cells."""
    lines = [l.strip() for l in block.split('\n') if l.strip().startswith('|')]
    if len(lines) < 3:
        return []

    def split_row(line):
        return [c.strip() for c in line.strip().strip('|').split('|')]

    headers = split_row(lines[0])
    n = len(headers)
    result = []
    for line in lines[2:]:          # skip header + separator
        cells = split_row(line)
        if not cells or all(c == '' for c in cells):
            continue
        if len(cells) > n:          # merge overflow into last column
            cells = cells[:n-1] + ['|'.join(cells[n-1:])]
        while len(cells) < n:
            cells.append('')
        result.append(dict(zip(headers, cells)))
    return result

def get_section(text, heading):
    """Return content of the first section matching heading text (any level)."""
    m = re.search(r'^(#{1,4})\s+' + re.escape(heading) + r'[^\n]*$',
                  text, re.MULTILINE | re.IGNORECASE)
    if not m:
        return ''
    level = len(m.group(1))
    start = m.end()
    nm = re.search(r'\n#{1,' + str(level) + r'}\s+', text[start:])
    end = start + nm.start() if nm else len(text)
    return text[start:end].strip()

def first_table_in(section_text):
    """Extract the first markdown table found in a section."""
    if not section_text:
        return []
    lines = section_text.split('\n')
    block, in_t = [], False
    for line in lines:
        if line.strip().startswith('|'):
            block.append(line)
            in_t = True
        elif in_t:
            break
    return parse_table('\n'.join(block))

def first_para(text):
    """Return the first real paragraph of text (up to first blank line, max 400 chars)."""
    paras = [p.strip() for p in re.split(r'\n\n+', text) if p.strip()]
    paras = [p for p in paras if not p.startswith('_') and not p.startswith('|')]
    return paras[0][:400] if paras else ''

# ── Data extraction ───────────────────────────────────────────────────────────

STAGE_ORDER = {'interviewing': 0, 'screening': 1, 'applied': 2, 'researching': 3}

def prep_detail(text, stage):
    if stage not in ('screening', 'interviewing', 'final_round'):
        return {'score': -1, 'done': [], 'todo': []}
    score, done, todo = 10, [], []

    # Research gate — has User Base & Geography been populated?
    ru = frontmatter(text).get('last_user_research_updated')
    if ru and str(ru) not in ('null', ''):
        score += 15; done.append('Company researched — User Base & Geography populated')
    else:
        todo.append('Company research not done — run "Research [company]" first')

    if re.search(r'\|\s*#\s*\|', text):
        score += 20; done.append('Interview process researched and mapped')
    else:
        todo.append('Interview process not yet researched — run prep-planner Phase 1')

    if 'Prep plan generated' in text or 'Opening (' in text:
        score += 30; done.append('Prep plan written (opening, positioning, stories)')
    else:
        todo.append('Prep plan not written — run prep-planner Phase 2')

    if 'Questions to ask' in text:
        score += 15; done.append('Questions to ask the interviewer prepared')
    else:
        todo.append('Questions to ask not written — add to prep plan')

    if 'Company knowledge' in text:
        score += 10; done.append('Company knowledge section populated')
    else:
        todo.append('Company knowledge not researched — run company-research workflow')

    return {'score': min(score, 100), 'done': done, 'todo': todo}

def extract_rich(text):
    """Parse richer card data for the Companies tab detail view."""
    overview      = first_para(get_section(text, 'Business Overview'))
    open_roles    = first_table_in(get_section(text, 'Open Roles'))
    rounds        = first_table_in(get_section(text, 'Interview Process'))
    contacts      = first_table_in(get_section(text, 'Contacts'))
    history       = first_table_in(get_section(text, 'Stage History'))
    prep_raw      = get_section(text, 'Interview Notes')
    # Research sections — populated by company-research workflow
    analysis_raw  = get_section(text, 'PM Perspective')
    geo_raw       = get_section(text, 'Geographic Breakdown')
    prod_matrix   = first_table_in(get_section(text, 'Product × User Segment Matrix'))
    news_raw      = get_section(text, 'Recent News & Performance')
    funding_raw   = get_section(text, 'Funding & Growth')
    culture_raw   = get_section(text, 'Culture & People Signals')
    return {
        'overview':      get_section(text, 'Business Overview'),
        'open_roles':    open_roles,
        'rounds':        rounds,
        'contacts':      contacts,
        'history':       history,
        'prep_notes':    prep_raw      if prep_raw     else '',
        'analysis':      analysis_raw  if analysis_raw else '',
        'geo_breakdown': geo_raw       if geo_raw      else '',
        'prod_matrix':   prod_matrix,
        'recent_news':   news_raw      if news_raw     else '',
        'funding':       funding_raw   if funding_raw  else '',
        'culture':       culture_raw   if culture_raw  else '',
    }

def next_interview_label(text):
    m = re.search(
        r'🔴\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d+[^|\n<]{0,40})',
        text)
    return m.group(1).strip() if m else None

def days_old(ds):
    try:
        return (date.today() - date.fromisoformat(str(ds))).days
    except Exception:
        return 0

def load_profile_name():
    fp = REPO / 'data' / 'profile' / 'me.md'
    if not fp.exists():
        return ''
    m = re.search(r'^#\s+(.+?)(?:\s+—.*)?$', fp.read_text(encoding='utf-8'), re.MULTILINE)
    return m.group(1).strip() if m else ''

def load_search_start_date():
    """Optional data/profile/index override for search start date; falls back to current personal default."""
    candidates = [
        REPO / 'data' / 'profile' / 'me.md',
        REPO / 'framework' / 'index.yaml',
    ]
    for fp in candidates:
        if not fp.exists():
            continue
        txt = fp.read_text(encoding='utf-8')
        fm = frontmatter(txt)
        for key in ('search_started', 'search_start', 'started_search_on'):
            raw = fm.get(key)
            if raw:
                try:
                    return date.fromisoformat(str(raw))
                except Exception:
                    pass
        m = re.search(r'(?:search_started|search_start|started_search_on)\s*:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})', txt)
        if m:
            try:
                return date.fromisoformat(m.group(1))
            except Exception:
                pass
    return date(2026, 5, 21)

def load_companies():
    # Manifest split out of framework/index.yaml in Phase 3. It now lives
    # under data/ (per-user). framework/index.yaml stays framework-only.
    fp = REPO / 'data' / 'manifest.yaml'
    if not fp.exists():
        return []
    manifest = parse_yaml(fp.read_text(encoding='utf-8'))
    out = []
    for meta in manifest.get('cards', []):
        # Card IDs are logical identifiers like "pipeline/<slug>" — NOT file paths.
        # Files live under data/, so we prefix with data/ when resolving to a path.
        cid = meta.get('id', '')
        if not cid.startswith('pipeline/'):
            continue
        slug    = cid[len('pipeline/'):]
        card_fp = REPO / 'data' / f'{cid}.md'
        text    = card_fp.read_text(encoding='utf-8') if card_fp.exists() else ''
        fm      = frontmatter(text)

        hm   = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        name = hm.group(1).strip() if hm else slug.replace('-', ' ').title()

        stage    = str(fm.get('stage')    or meta.get('stage',    'researching'))
        priority = str(fm.get('priority') or meta.get('priority', 'medium'))
        tags     = fm.get('tags') or meta.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in re.split(r'[,\s]+', tags) if t.strip()]
        updated          = str(fm.get('last_updated') or meta.get('updated', ''))
        research_updated = str(fm.get('last_user_research_updated') or '')
        if research_updated in ('null', 'None'):
            research_updated = ''
        pd               = prep_detail(text, stage)
        rich             = extract_rich(text)

        out.append({
            'id':               slug,
            'name':             name,
            'stage':            stage,
            'priority':         priority,
            'tags':             tags if isinstance(tags, list) else [],
            'next_action':      str(fm.get('next_action') or meta.get('next_action', '')),
            'last_updated':     updated,
            'research_updated': research_updated,
            'next_interview':   next_interview_label(text),
            'prep_score':       pd['score'],
            'prep_done':        pd['done'],
            'prep_todo':        pd['todo'],
            # Tier 1 is derived from the manifest summary text — users write
            # "Tier 1" in the summary of their strongest-fit cards.
            'tier1':            'tier 1' in str(meta.get('summary', '')).lower(),
            'stale':            days_old(updated) > 7,
            **rich,
        })
    out.sort(key=lambda c: (STAGE_ORDER.get(c['stage'], 9), 0 if c['priority'] == 'high' else 1))
    return out

def load_today_content():
    today_dir = REPO / 'data' / 'logs' / 'today'
    brief = ''
    updates = []
    brief_fp = today_dir / 'brief.md'
    if brief_fp.exists():
        brief = brief_fp.read_text(encoding='utf-8')
    updates_fp = today_dir / 'updates.md'
    if updates_fp.exists():
        text = updates_fp.read_text(encoding='utf-8')
        for m in re.finditer(r'^[-*]\s+(.+)$', text, re.MULTILINE):
            updates.append(m.group(1).strip())
    return brief, updates

def load_interviews():
    """
    Load upcoming/past interviews from data/state/interviews.yaml.
    Returns a list of dicts with date, time, company, card_id, round, label,
    interviewer, outcome, debrief_logged, and notes fields.
    Used as the primary source of truth for the calendar view.
    """
    fp = REPO / 'data' / 'state' / 'interviews.yaml'
    if not fp.exists():
        return []
    raw = parse_yaml(fp.read_text(encoding='utf-8'))
    out = []
    for entry in raw.get('interviews', []):
        outcome = str(entry.get('outcome', 'pending'))
        start_raw = str(entry.get('start', '') or '')
        date_str = start_raw[:10] if len(start_raw) >= 10 else None
        # Parse wall-clock time from the ISO-8601 string (stored in local tz)
        time_str = None
        if start_raw and 'T' in start_raw:
            time_part = start_raw.split('T')[1][:5]   # "HH:MM"
            try:
                h, m = int(time_part[:2]), int(time_part[3:5])
                ampm = 'AM' if h < 12 else 'PM'
                h12  = h % 12 or 12
                time_str = f'{h12}:{m:02d}{ampm}' if m else f'{h12}{ampm}'
            except Exception:
                pass
        out.append({
            'company':       entry.get('company', ''),
            'card_id':       str(entry.get('card_id', '')).replace('pipeline/', ''),
            'round':         str(entry.get('round', '') or ''),
            'label':         str(entry.get('label', '') or ''),
            'interviewer':   entry.get('interviewer'),
            'date':          date_str,
            'time':          time_str,
            'debrief_logged': bool(entry.get('debrief_logged', False)),
            'outcome':       outcome,
            'notes':         str(entry.get('notes', '') or ''),
        })
    return out


def load_signals():
    """
    Parse data/market/digest.md and return recent industry pulse entries.

    Entry format written by the brief:
        - **YYYY-MM-DD · Topic Name:** Body text. ([Source Name](url))

    Two URL formats in the wild:
        - New (2026-05-24+):  ([Source Name, date](url))
        - Legacy (2026-05-23): [https://raw-url]

    Returns entries from the last 7 days, newest-first, capped at 12.
    Falls back to the 12 most recent entries if fewer than 3 found in window.
    """
    fp = REPO / 'data' / 'market' / 'digest.md'
    if not fp.exists():
        return []
    text = fp.read_text(encoding='utf-8')
    out  = []
    # Capture: date | separator + topic | body text
    # The (?:[^A-Za-z]*) swallows the ' · ' separator without capturing it.
    pat = re.compile(
        r'\*\*([\d]{4}-[\d]{2}-[\d]{2})(?:[^A-Za-z]*)(.+?):\*\*\s*([^\n]+)'
    )
    for m in pat.finditer(text):
        date_str = m.group(1)
        topic    = m.group(2).strip()
        raw      = m.group(3).strip()

        # ── URL extraction ────────────────────────────────────────────────────
        # Try ([Source Name](url)) first, then bare [url] legacy format
        url = None
        url_m = re.search(r'\]\((https?://[^\)]+)\)', raw)   # markdown link: ](url)
        if url_m:
            url = url_m.group(1)
        else:
            url_m = re.search(r'\[https?://([^\]]+)\]', raw)  # bare: [url]
            if url_m:
                url = 'https://' + url_m.group(1)

        # ── Clean body text — strip all citation patterns ─────────────────────
        clean = re.sub(r'\s*\(\s*\[[^\]]+\]\([^)]+\)\s*\)', '', raw)  # ([Name](url))
        clean = re.sub(r'\s*\[[^\]]+\]\([^)]+\)', '', clean)           # [Name](url)
        clean = re.sub(r'\s*\[https?://[^\]]+\]', '', clean)           # [url]
        clean = re.sub(r'\*\*[^*]+\*\*', '', clean)                    # **bold** remnants
        clean = clean.strip()

        if topic and clean:
            out.append({'date': date_str, 'topic': topic, 'text': clean, 'url': url})

    # Sort newest-first (file is prepend-order so this is defensive)
    out.sort(key=lambda x: x['date'], reverse=True)
    # Rolling 7-day window; fall back to top-12 if window is sparse
    cutoff = (date.today() - timedelta(days=7)).isoformat()
    recent = [s for s in out if s['date'] >= cutoff]
    return recent[:12] if len(recent) >= 3 else out[:12]

# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#f6f7fb;
  --bg-radial:radial-gradient(circle at top left,rgba(99,102,241,.14),transparent 34%),
              radial-gradient(circle at top right,rgba(14,165,233,.10),transparent 28%),
              linear-gradient(180deg,#f8fafc 0%,#eef2f7 100%);
  --surf:rgba(255,255,255,.86);
  --surf-strong:#fff;
  --surf-soft:#f8fafc;
  --bdr:rgba(148,163,184,.26);
  --bdr-strong:rgba(99,102,241,.24);
  --tx:#0f172a;--mu:#64748b;--fa:#94a3b8;
  --ind:#635bff;--ind2:#7c3aed;--amb:#f59e0b;--blu:#2563eb;--grn:#10b981;--red:#ef4444;--pur:#8b5cf6;
  --radius-xl:22px;--radius-lg:16px;--radius-md:12px;
  --shadow-sm:0 1px 2px rgba(15,23,42,.05),0 6px 18px rgba(15,23,42,.04);
  --shadow-md:0 14px 40px rgba(15,23,42,.10);
  --shadow-lg:0 24px 80px rgba(15,23,42,.18);
}
html,body{height:100%;overflow:hidden}
body{
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  background:var(--bg-radial);color:var(--tx);font-size:14px;line-height:1.5;
  display:flex;flex-direction:column;
}

/* ── Header ── */
.hdr{
  position:relative;overflow:hidden;background:#0b1020;color:#fff;padding:18px 30px;flex-shrink:0;
  display:flex;align-items:center;justify-content:space-between;gap:18px;
  box-shadow:0 16px 40px rgba(15,23,42,.18);
}
.hdr::before{
  content:"";position:absolute;inset:0;
  background:radial-gradient(circle at 18% 15%,rgba(99,102,241,.42),transparent 26%),
             radial-gradient(circle at 78% 8%,rgba(14,165,233,.24),transparent 24%);
  pointer-events:none;
}
.hdr>*{position:relative;z-index:1}
.hdr-brand{font-size:21px;font-weight:850;letter-spacing:-.04em;display:flex;align-items:baseline;gap:7px}
.hdr-brand em{
  background:linear-gradient(135deg,#8b5cf6,#60a5fa);-webkit-background-clip:text;background-clip:text;
  color:transparent;font-style:normal;
}
.hdr-info{display:flex;gap:10px;font-size:12px;color:#cbd5e1;align-items:center;justify-content:center;flex-wrap:wrap}
.hdr-pill{
  display:inline-flex;align-items:center;gap:6px;padding:6px 10px;border-radius:999px;
  background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.10);backdrop-filter:blur(10px);
}
.hdr-info strong{color:#fff;font-weight:800}
.hdr-ts{font-size:11px;color:#94a3b8;white-space:nowrap}

/* ── Tab bar ── */
.tabbar{
  display:flex;background:rgba(255,255,255,.82);border-bottom:1px solid var(--bdr);
  padding:0 30px;flex-shrink:0;backdrop-filter:blur(16px);
}
.tab{
  padding:14px 18px;font-size:13px;font-weight:750;color:var(--mu);cursor:pointer;
  border-bottom:3px solid transparent;margin-bottom:-1px;transition:color .15s,border-color .15s,background .15s;
  user-select:none;border-radius:12px 12px 0 0;
}
.tab:hover{color:var(--tx);background:rgba(99,102,241,.05)}
.tab.active{color:var(--ind);border-bottom-color:var(--ind);background:rgba(99,102,241,.06)}

/* ── Overview tab ── */
.main{flex:1;overflow-y:auto;padding:22px 30px;display:flex;flex-direction:column;gap:18px;max-width:1520px;width:100%;margin:0 auto}
.card,.cd-hero,.cd-sec,.cd-analysis{
  background:var(--surf);border:1px solid var(--bdr);border-radius:var(--radius-lg);padding:18px;
  box-shadow:var(--shadow-sm);backdrop-filter:blur(14px);
}
.card{transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease}
.card:hover{border-color:var(--bdr-strong);box-shadow:var(--shadow-md)}
.sec,.cd-sec-ttl{
  font-size:11px;font-weight:850;letter-spacing:.10em;text-transform:uppercase;
  color:var(--mu);margin-bottom:14px;display:flex;align-items:center;gap:8px;
}
.sec::before,.cd-sec-ttl::before{
  content:"";width:7px;height:7px;border-radius:999px;background:linear-gradient(135deg,var(--ind),var(--blu));
}
.top{display:grid;grid-template-columns:minmax(340px,1fr) minmax(420px,1fr);gap:18px}
.metrics{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}
.metric{
  background:linear-gradient(180deg,rgba(255,255,255,.96),rgba(255,255,255,.74));
  border:1px solid var(--bdr);border-radius:var(--radius-lg);padding:15px 16px;box-shadow:var(--shadow-sm);
  min-height:98px;position:relative;overflow:hidden;
}
.metric::after{
  content:"";position:absolute;right:-24px;top:-28px;width:72px;height:72px;border-radius:999px;
  background:rgba(99,102,241,.08);
}
.metric-label{font-size:10px;font-weight:850;letter-spacing:.08em;text-transform:uppercase;color:var(--mu)}
.metric-value{font-size:30px;line-height:1;font-weight:900;margin-top:10px;letter-spacing:-.05em}
.metric-sub{font-size:12px;color:var(--mu);margin-top:7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.metric.alert .metric-value{color:var(--red)}
.metric.good .metric-value{color:var(--grn)}
.metric.warn .metric-value{color:var(--amb)}
.call-row{
  display:grid;grid-template-columns:72px 1fr auto;align-items:center;gap:12px;
  padding:12px 0;border-bottom:1px solid var(--bdr);
}
.call-row:last-child{border-bottom:none}
.call-time{font-size:13px;font-weight:850;color:var(--ind)}
.call-co{font-size:15px;font-weight:800;letter-spacing:-.02em}
.call-type{font-size:11px;color:var(--mu);background:var(--surf-soft);border:1px solid var(--bdr);padding:4px 8px;border-radius:999px}
.empty{font-size:13px;color:var(--mu);font-style:italic;padding:10px 0}
.bdg,.bdg-research{
  display:inline-flex;align-items:center;font-size:10px;font-weight:850;padding:3px 8px;border-radius:100px;white-space:nowrap;margin-left:5px;
}
.bdg-t1{background:#fff7ed;color:#c2410c;border:1px solid rgba(245,158,11,.22)}
.bdg-st{background:#fef2f2;color:#b91c1c;border:1px solid rgba(239,68,68,.18)}
.week{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.wd{
  padding:13px 12px;border-radius:15px;background:rgba(248,250,252,.88);border:1px solid var(--bdr);
  transition:transform .15s,box-shadow .15s,border-color .15s;min-height:94px;
}
.wd.ev{background:linear-gradient(180deg,#eff6ff,#fff);border-color:#bfdbfe;cursor:pointer}
.wd.heavy{background:linear-gradient(180deg,#fffbeb,#fff);border-color:#fcd34d;cursor:pointer}
.wd.ev:hover,.wd.heavy:hover{transform:translateY(-2px);box-shadow:var(--shadow-md)}
.wd.today{box-shadow:inset 0 0 0 2px rgba(99,91,255,.18)}
.wd-lbl{font-size:10px;font-weight:850;text-transform:uppercase;color:var(--mu);letter-spacing:.05em}
.wd-num{font-size:27px;font-weight:900;line-height:1;margin:7px 0 5px;letter-spacing:-.05em}
.wd-ev{font-size:12px;color:var(--mu);font-weight:650}
.kanban{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.kcol-hdr{
  font-size:12px;font-weight:850;padding:10px 12px;border-radius:14px;
  display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;border:1px solid transparent;
}
.kcol[data-s=interviewing] .kcol-hdr{background:#fff7ed;color:#9a3412;border-color:#fed7aa}
.kcol[data-s=screening] .kcol-hdr{background:#eff6ff;color:#1d4ed8;border-color:#bfdbfe}
.kcol[data-s=applied] .kcol-hdr{background:#f5f3ff;color:#6d28d9;border-color:#ddd6fe}
.kcol-n{background:rgba(255,255,255,.62);border:1px solid rgba(255,255,255,.72);border-radius:100px;padding:2px 8px;font-size:11px}
.kc{
  position:relative;overflow:hidden;background:var(--surf-strong);border:1px solid var(--bdr);border-radius:16px;
  padding:15px 15px 14px;margin-bottom:10px;box-shadow:var(--shadow-sm);
  transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease;
}
.kc::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--blu);opacity:.75}
.kcol[data-s=interviewing] .kc::before{background:var(--amb)}
.kcol[data-s=applied] .kc::before{background:var(--pur)}
.kc.t1::before{background:linear-gradient(180deg,var(--amb),var(--ind))}
.kc:hover{transform:translateY(-2px);box-shadow:var(--shadow-md);border-color:var(--bdr-strong)}
.kc-name{font-size:15px;font-weight:850;display:flex;align-items:center;flex-wrap:wrap;gap:2px;margin-bottom:3px;letter-spacing:-.02em}
.kc-nxt{
  display:inline-flex;align-items:center;margin-top:8px;padding:5px 9px;border-radius:999px;
  background:#fff7ed;color:#c2410c;border:1px solid #fed7aa;font-size:12px;font-weight:800;
}
.kc-act{font-size:12.5px;color:var(--mu);line-height:1.45;margin-top:8px}
.kc-tags{display:flex;flex-wrap:wrap;gap:5px;margin-top:10px}
.tag{font-size:10.5px;font-weight:650;padding:3px 8px;border-radius:100px;background:#f1f5f9;color:#526174;border:1px solid rgba(148,163,184,.18)}
.pb-wrap{margin-top:10px}
.pb-lbl{display:flex;justify-content:space-between;font-size:11px;color:var(--mu);margin-bottom:5px;font-weight:700}
.pb-track{height:7px;background:#e2e8f0;border-radius:999px;overflow:hidden}
.pb-fill{height:100%;border-radius:999px;transition:width .25s}
.c-lo{color:var(--red)}.c-mi{color:var(--amb)}.c-hi{color:var(--grn)}
.f-lo{background:linear-gradient(90deg,#f97316,var(--red))}
.f-mi{background:linear-gradient(90deg,#fbbf24,var(--amb))}
.f-hi{background:linear-gradient(90deg,#34d399,var(--grn))}
.bot{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.sig-row,.pt-row{
  padding:12px 0;border-bottom:1px solid var(--bdr);border-radius:10px;transition:background .1s,transform .1s;
}
.sig-row:last-child,.pt-row:last-child{border-bottom:none}
.sig-row.link,.pt-row{cursor:pointer}
.sig-row.link:hover,.pt-row:hover{background:rgba(99,102,241,.045);margin:0 -8px;padding:12px 8px}
.sig-dt{font-size:10.5px;color:var(--fa);margin-bottom:2px;font-weight:800;letter-spacing:.04em}
.sig-topic{font-size:13px;font-weight:850;color:var(--tx);margin-bottom:3px;line-height:1.35}
.sig-tx{font-size:12.5px;color:var(--mu);line-height:1.55}
.sig-arrow{font-size:11px;color:var(--ind);margin-top:4px;font-weight:800}
.pt-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:7px;gap:10px}
.pt-name{font-size:13.5px;font-weight:800;transition:color .1s}
.pt-row:hover .pt-name{color:var(--ind)}
.pt-pct{font-size:12px;font-weight:900}

/* ── Companies tab ── */
.co-wrap{flex:1;display:grid;grid-template-columns:300px 1fr;min-height:0}
.co-nav{
  border-right:1px solid var(--bdr);background:rgba(255,255,255,.72);backdrop-filter:blur(16px);
  display:flex;flex-direction:column;min-height:0;
}
.co-search{padding:14px;border-bottom:1px solid var(--bdr);flex-shrink:0}
.co-search-inp{
  width:100%;padding:10px 12px;border:1px solid var(--bdr);border-radius:12px;
  font-size:13px;outline:none;background:rgba(248,250,252,.90);transition:border-color .15s,box-shadow .15s,background .15s;
}
.co-search-inp:focus{border-color:var(--ind);background:#fff;box-shadow:0 0 0 4px rgba(99,91,255,.10)}
.co-list{overflow-y:auto;flex:1;padding:6px 0}
.co-item{
  margin:2px 10px;padding:10px 11px;cursor:pointer;display:flex;align-items:center;gap:9px;
  border-radius:12px;transition:background .1s,transform .1s;color:var(--tx);
}
.co-item:hover{background:rgba(99,102,241,.06)}
.co-item.active{background:#eef2ff;color:#312e81;box-shadow:inset 0 0 0 1px rgba(99,102,241,.12)}
.co-dot{width:9px;height:9px;border-radius:50%;flex-shrink:0;box-shadow:0 0 0 3px rgba(148,163,184,.14)}
.dot-interviewing{background:var(--amb)}
.dot-screening{background:var(--blu)}
.dot-applied{background:var(--pur)}
.dot-researching{background:var(--fa)}
.co-item-name{font-size:13.5px;font-weight:700;flex:1;line-height:1.3}
.co-star{color:var(--amb);font-size:12px;line-height:1}
.co-panel{overflow-y:auto;background:transparent;padding:22px 30px;min-height:0}
.co-empty{display:flex;align-items:center;justify-content:center;height:200px;font-size:14px;color:var(--mu);font-style:italic}

/* ── Company detail ── */
.cd-hero{padding:22px;margin-bottom:16px}
.cd-top{display:grid;grid-template-columns:auto 1fr auto;align-items:flex-start;gap:16px}
.cd-avatar{
  width:52px;height:52px;border-radius:18px;display:flex;align-items:center;justify-content:center;
  background:linear-gradient(135deg,var(--ind),var(--blu));color:#fff;font-size:16px;font-weight:900;
  box-shadow:0 12px 28px rgba(99,91,255,.25);letter-spacing:.02em;flex-shrink:0;
}
.cd-name{font-size:25px;font-weight:900;line-height:1.1;letter-spacing:-.05em}
.cd-right{display:flex;flex-direction:column;align-items:flex-end;gap:6px;flex-shrink:0}
.cd-updated{font-size:11px;color:var(--fa);font-weight:700}
.cd-badges{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:10px}
.cd-stg{font-size:11px;font-weight:850;padding:4px 9px;border-radius:999px}
.stg-interviewing{background:#fff7ed;color:#9a3412;border:1px solid #fed7aa}
.stg-screening{background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe}
.stg-applied{background:#f5f3ff;color:#6d28d9;border:1px solid #ddd6fe}
.stg-researching{background:#f1f5f9;color:#475569;border:1px solid #e2e8f0}
.cd-tags{display:flex;flex-wrap:wrap;gap:5px;margin-top:12px}
.cd-nxt-interview{
  display:inline-flex;align-items:center;margin-top:13px;padding:7px 10px;border-radius:999px;
  background:#fff7ed;color:#c2410c;border:1px solid #fed7aa;font-size:13px;font-weight:850;
}
.cd-pb{margin-top:14px}
.cd-nxt-action{
  margin-top:14px;background:linear-gradient(180deg,#f8fbff,#fff);border:1px solid var(--bdr-strong);
  border-left:4px solid var(--ind);border-radius:14px;padding:12px 14px;
}
.cd-nxt-lbl{font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.08em;color:var(--mu);margin-bottom:5px}
.cd-nxt-text{font-size:13.5px;line-height:1.55;color:var(--tx)}
.cd-sec,.cd-analysis{padding:20px;margin-bottom:16px}
.cd-analysis{border-color:#c7d2fe;background:linear-gradient(180deg,rgba(238,242,255,.82),rgba(255,255,255,.82))}
.cd-analysis .cd-sec-ttl{color:#4338ca}
.bdg-research{margin-left:0}
.bdg-research.ok{background:#ecfdf5;color:#047857;border:1px solid #a7f3d0}
.bdg-research.gap{background:#fffbeb;color:#92400e;border:1px solid #fde68a}

/* Rounds */
.rd-row{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid var(--bdr);align-items:flex-start}
.rd-row:last-child{border-bottom:none}
.rd-icon{font-size:17px;width:28px;text-align:center;flex-shrink:0;line-height:1.5}
.rd-body{flex:1}
.rd-name{font-size:13.5px;font-weight:850;margin-bottom:3px}
.rd-detail{font-size:12.5px;color:var(--mu);line-height:1.55}
.rd-done .rd-name,.rd-done .rd-detail{color:var(--mu)}

/* Contacts */
.ct-row{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid var(--bdr);align-items:flex-start}
.ct-row:last-child{border-bottom:none}
.ct-av{
  width:36px;height:36px;border-radius:14px;background:linear-gradient(135deg,var(--ind),var(--pur));color:#fff;
  font-size:11px;font-weight:900;display:flex;align-items:center;justify-content:center;flex-shrink:0;letter-spacing:.5px;
}
.ct-name{font-size:13.5px;font-weight:850}
.ct-role{font-size:12px;color:var(--mu);margin-top:1px}
.ct-notes{font-size:12.5px;color:var(--tx);margin-top:5px;line-height:1.45}

/* Open roles */
.rl-row{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid var(--bdr);gap:16px}
.rl-row:last-child{border-bottom:none}
.rl-name{font-size:13.5px;font-weight:700}
.rl-spotted{font-size:11px;color:var(--fa);white-space:nowrap}

/* Stage history */
.sh-row{display:grid;grid-template-columns:95px 92px 1fr;gap:12px;padding:9px 0;border-bottom:1px solid var(--bdr)}
.sh-row:last-child{border-bottom:none}
.sh-date{color:var(--mu);font-size:12px}
.sh-stage{font-weight:750;font-size:12px}
.sh-notes{color:var(--tx);line-height:1.45;font-size:12.5px}

/* Prep notes markdown */
.prep-md{font-size:13.2px;line-height:1.72;color:var(--tx)}
.prep-md h4{font-size:13px;font-weight:850;color:var(--ind);margin:15px 0 5px}
.prep-md h3{font-size:14.5px;font-weight:850;margin:17px 0 7px}
.prep-md ul,.prep-md ol{padding-left:20px;margin:5px 0}
.prep-md li{margin:4px 0}
.prep-md p{margin:6px 0}
.prep-md strong{font-weight:850}
.prep-md blockquote{border-left:3px solid var(--bdr);padding:7px 12px;color:var(--mu);margin:7px 0;font-style:italic;border-radius:0 8px 8px 0;background:#f8fafc}

/* Markdown table */
.md-table{width:100%;border-collapse:separate;border-spacing:0;font-size:11.8px;margin:9px 0 4px;overflow:hidden;border-radius:12px;border:1px solid var(--bdr)}
.md-table th{background:#f1f5f9;padding:7px 10px;text-align:left;font-weight:850;color:var(--mu);font-size:10px;letter-spacing:.05em;text-transform:uppercase;border-bottom:1px solid var(--bdr)}
.md-table td{padding:8px 10px;border-bottom:1px solid var(--bdr);vertical-align:top;line-height:1.45}
.md-table tr:last-child td{border-bottom:none}
.md-table tr:nth-child(even) td{background:#f8fafc}

/* News items */
.news-item{padding:9px 0;border-bottom:1px solid var(--bdr)}
.news-item:last-child{border-bottom:none}
.news-date{font-size:10px;color:var(--fa);font-weight:850;margin-bottom:3px;letter-spacing:.04em}
.news-text{font-size:12.8px;line-height:1.55}

/* Info blocks */
.info-block{font-size:13.2px;line-height:1.68;color:var(--tx);padding:2px 0}
.sub-lbl{font-size:10px;font-weight:850;text-transform:uppercase;letter-spacing:.07em;color:var(--mu);margin-bottom:7px}

/* ── Modal ── */
.modal-bg{
  display:none;position:fixed;inset:0;background:rgba(15,23,42,.56);
  backdrop-filter:blur(10px);z-index:200;align-items:center;justify-content:center;padding:24px;
}
.modal-bg.open{display:flex}
.modal{
  background:rgba(255,255,255,.96);border:1px solid rgba(255,255,255,.65);border-radius:22px;width:62%;max-width:760px;max-height:82vh;
  overflow-y:auto;padding:24px;box-shadow:var(--shadow-lg);animation:msi .16s ease;
}
@keyframes msi{from{transform:translateY(12px) scale(.98);opacity:0}to{transform:translateY(0) scale(1);opacity:1}}
.modal-hdr{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:18px}
.modal-ttl{font-size:18px;font-weight:900;line-height:1.25;letter-spacing:-.03em}
.modal-x{
  width:31px;height:31px;border:none;background:#f1f5f9;border-radius:10px;cursor:pointer;
  font-size:13px;display:flex;align-items:center;justify-content:center;flex-shrink:0;margin-left:12px;color:var(--mu);
}
.modal-x:hover{background:#e2e8f0;color:var(--tx)}
.mo-ev{display:flex;gap:14px;padding:14px 0;border-bottom:1px solid var(--bdr)}
.mo-ev:last-child{border-bottom:none}
.mo-ev-time{font-size:13px;font-weight:850;color:var(--ind);min-width:66px;padding-top:2px}
.mo-ev-name{font-size:15px;font-weight:900;margin-bottom:3px;display:flex;align-items:center;flex-wrap:wrap;gap:4px}
.mo-ev-type{font-size:12px;color:var(--mu);margin-bottom:7px}
.mo-ev-act{font-size:12.5px;color:var(--tx);line-height:1.5;background:#f8fafc;border:1px solid var(--bdr);border-radius:10px;padding:9px 10px}
.mo-score-line{display:flex;align-items:baseline;gap:10px;margin-bottom:16px;padding-bottom:16px;border-bottom:1px solid var(--bdr)}
.mo-score-num{font-size:42px;font-weight:950;letter-spacing:-.06em}
.mo-score-lbl{font-size:14px;color:var(--mu);font-weight:700}
.mo-slbl{font-size:11px;font-weight:850;letter-spacing:.08em;text-transform:uppercase;color:var(--mu);margin:16px 0 8px}
.mo-item{display:flex;gap:10px;align-items:flex-start;padding:5px 0;font-size:13px;line-height:1.45}
.mo-icon{font-size:13px;flex-shrink:0;margin-top:1px}
.mo-act-box{background:#f8fafc;border:1px solid var(--bdr);border-radius:12px;padding:12px;font-size:13px;line-height:1.6}

@media (max-width:1100px){
  .metrics{grid-template-columns:repeat(2,1fr)}
  .top,.bot,.kanban{grid-template-columns:1fr}
  .co-wrap{grid-template-columns:240px 1fr}
}
/* ── Today tab ── */
.today-wrap{flex:1;overflow-y:auto;padding:22px 30px;max-width:860px;width:100%;margin:0 auto;display:flex;flex-direction:column;gap:18px}
.updates-sec{background:rgba(255,255,255,.96);border:1px solid rgba(99,102,241,.22);border-left:4px solid var(--ind);border-radius:var(--radius-lg);padding:20px;box-shadow:var(--shadow-sm)}
.updates-hdr{font-size:11px;font-weight:850;letter-spacing:.10em;text-transform:uppercase;color:var(--ind);margin-bottom:14px;display:flex;align-items:center;gap:8px}
.updates-hdr::before{content:"";width:7px;height:7px;border-radius:999px;background:var(--ind)}
.update-item{display:flex;gap:12px;padding:11px 0;border-bottom:1px solid var(--bdr);align-items:flex-start}
.update-item:last-child{border-bottom:none}
.update-num{font-size:12px;font-weight:900;color:var(--ind);min-width:22px;padding-top:1px;flex-shrink:0}
.update-text{font-size:13.5px;line-height:1.55;color:var(--tx)}
.brief-sec{background:var(--surf);border:1px solid var(--bdr);border-radius:var(--radius-lg);padding:22px;box-shadow:var(--shadow-sm)}
.brief-hdr{font-size:11px;font-weight:850;letter-spacing:.10em;text-transform:uppercase;color:var(--mu);margin-bottom:16px;display:flex;align-items:center;gap:8px}
.brief-hdr::before{content:"";width:7px;height:7px;border-radius:999px;background:linear-gradient(135deg,var(--ind),var(--blu))}
.brief-content h1{font-size:17px;font-weight:900;letter-spacing:-.03em;margin:0 0 16px;color:var(--tx)}
.brief-content h2{font-size:15px;font-weight:850;margin:18px 0 8px;color:var(--tx)}
.brief-content h3{font-size:13.5px;font-weight:850;margin:14px 0 6px;color:var(--ind)}
.brief-content h4{font-size:13px;font-weight:850;color:var(--ind);margin:12px 0 4px}
.brief-content strong{font-weight:850}
.brief-content ul,.brief-content ol{padding-left:20px;margin:6px 0}
.brief-content li{margin:5px 0;line-height:1.55}
.brief-content p{margin:7px 0;font-size:13.5px;line-height:1.72;color:var(--tx)}
.brief-empty{font-size:13px;color:var(--mu);font-style:italic;padding:10px 0}

/* ── Research feedback ── */
.feedback-sec{border:1px solid var(--bdr);border-radius:var(--radius-lg);padding:16px 18px;background:var(--surf-soft);margin-top:4px}
.feedback-hdr{font-size:10px;font-weight:850;letter-spacing:.10em;text-transform:uppercase;color:var(--fa);margin-bottom:10px}
.feedback-hint{font-size:12.5px;color:var(--mu);margin-bottom:10px}
.feedback-steps{font-size:12.5px;color:var(--mu);padding-left:18px;margin-bottom:10px}
.feedback-steps li{margin:3px 0}
.feedback-prompt-wrap{position:relative;background:#f1f5f9;border:1px solid var(--bdr);border-radius:10px;padding:10px 40px 10px 12px;margin-top:4px}
.feedback-prompt{font-size:12px;font-family:ui-monospace,"SF Mono",Menlo,monospace;color:#374151;line-height:1.55;word-break:break-word}
.feedback-copy{
  position:absolute;top:8px;right:8px;padding:4px 9px;font-size:11px;font-weight:750;
  border:1px solid var(--bdr);border-radius:8px;background:#fff;cursor:pointer;color:var(--mu);
  transition:background .12s,color .12s;
}
.feedback-copy:hover{background:var(--ind);color:#fff;border-color:var(--ind)}
.feedback-copy.copied{background:var(--grn);color:#fff;border-color:var(--grn)}
"""

# ── JS ────────────────────────────────────────────────────────────────────────

JS = r"""
const M={Jan:0,Feb:1,Mar:2,Apr:3,May:4,Jun:5,Jul:6,Aug:7,Sep:8,Oct:9,Nov:10,Dec:11};

function esc(v){
  return String(v ?? '').replace(/[&<>"']/g,ch=>({
    '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'
  })[ch]);
}
function copyFeedback(id,btn){
  const text=document.getElementById(id).textContent;
  navigator.clipboard.writeText(text).then(()=>{
    btn.textContent='Copied!';btn.classList.add('copied');
    setTimeout(()=>{btn.textContent='Copy';btn.classList.remove('copied');},2000);
  }).catch(()=>{
    const ta=document.createElement('textarea');
    ta.value=text;document.body.appendChild(ta);ta.select();
    document.execCommand('copy');document.body.removeChild(ta);
    btn.textContent='Copied!';btn.classList.add('copied');
    setTimeout(()=>{btn.textContent='Copy';btn.classList.remove('copied');},2000);
  });
}
function pd(s){
  if(!s)return null;
  const m=String(s).match(/([A-Z][a-z]{2})\w*\s+(\d+)/);
  if(!m||!(m[1]in M))return null;
  const y=new Date(DATA.today+'T00:00:00').getFullYear();
  return new Date(y,M[m[1]],+m[2]);
}
function pc(n){return n<40?'lo':n<70?'mi':'hi'}
function el(tag,cls,html){
  const e=document.createElement(tag);
  if(cls)e.className=cls;
  if(html!==undefined)e.innerHTML=html;
  return e;
}
function bdg(t,c){return`<span class="bdg ${c}">${esc(t)}</span>`}
function fmtStage(s){return String(s||'').replace(/_/g,' ').replace(/\b\w/g,m=>m.toUpperCase())}
function shortText(s,n=130){s=String(s||'');return esc(s.slice(0,n))+(s.length>n?'…':'')}

// ── App state ────────────────────────────────────────────────────────────────
const ST={
  tab:'today',
  coId:(()=>{
    const s=[...DATA.companies].sort((a,b)=>a.name.localeCompare(b.name));
    return s.length?s[0].id:null;
  })(),
};

// ── Modal ────────────────────────────────────────────────────────────────────
const Modal=(function(){
  const bg=el('div','modal-bg');
  const box=el('div','modal');
  const hdr=el('div','modal-hdr');
  const ttl=el('div','modal-ttl');
  const btn=el('button','modal-x','✕');
  const body=el('div','modal-body');
  hdr.appendChild(ttl);hdr.appendChild(btn);
  box.appendChild(hdr);box.appendChild(body);
  bg.appendChild(box);
  document.body.appendChild(bg);
  bg.addEventListener('click',e=>{if(e.target===bg)close();});
  btn.addEventListener('click',close);
  document.addEventListener('keydown',e=>{if(e.key==='Escape')close();});
  function open(title,content){
    ttl.textContent=title;body.innerHTML=content;
    bg.classList.add('open');document.body.style.overflow='hidden';
  }
  function close(){bg.classList.remove('open');document.body.style.overflow='';}
  return{open,close};
})();

// ── Shared prep bar ──────────────────────────────────────────────────────────
function prepBar(score,label){
  if(score<0)return'';
  const cls=pc(score);
  return`<div class="pb-wrap">
    <div class="pb-lbl"><span>${esc(label||'Prep')}</span><span class="c-${cls}">${score}%</span></div>
    <div class="pb-track"><div class="pb-fill f-${cls}" style="width:${score}%"></div></div>
  </div>`;
}

// ── Header ───────────────────────────────────────────────────────────────────
function renderHdr(){
  const{today,week_num,generated_at,companies}=DATA;
  const active=companies.filter(c=>['screening','interviewing'].includes(c.stage)).length;
  const d=new Date(today+'T00:00:00');
  const lbl=d.toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric',year:'numeric'});
  const h=el('div','hdr');
  h.innerHTML=`
    <div class="hdr-brand"><span>Chrysalis</span> <em>${esc(DATA.name||'')}</em></div>
    <div class="hdr-info">
      <div class="hdr-pill"><strong>${esc(lbl)}</strong></div>
      <div class="hdr-pill">Week <strong>${esc(week_num)}</strong> of search</div>
      <div class="hdr-pill"><strong>${active}</strong> active processes</div>
    </div>
    <div class="hdr-ts">Generated ${esc(generated_at)}</div>`;
  return h;
}

// ── Tab bar ──────────────────────────────────────────────────────────────────
function renderTabBar(onSwitch){
  const bar=el('div','tabbar');
  ['Today','Overview','Companies'].forEach(name=>{
    const key=name.toLowerCase();
    const t=el('div',`tab${ST.tab===key?' active':''}`,esc(name));
    t.addEventListener('click',()=>{
      if(ST.tab!==key){
        ST.tab=key;
        bar.querySelectorAll('.tab').forEach(el=>el.classList.toggle('active',el.textContent.toLowerCase()===key));
        onSwitch();
      }
    });
    bar.appendChild(t);
  });
  return bar;
}

// ── Overview: Metrics strip ──────────────────────────────────────────────────
function renderMetrics(){
  const companies=DATA.companies||[];
  const today=new Date(DATA.today+'T00:00:00');
  const cut=new Date(today);cut.setDate(cut.getDate()+3);
  // Use interviews.yaml as source of truth — not card emoji markers
  const upcoming=(DATA.interviews||[]).filter(iv=>{
    if(!iv.date||iv.outcome!=='pending')return false;
    const d=new Date(iv.date+'T00:00:00');
    return d>=today&&d<=cut;
  }).length;
  const active=companies.filter(c=>['screening','interviewing'].includes(c.stage)).length;
  const prep=companies.filter(c=>c.prep_score>=0);
  const avg=prep.length?Math.round(prep.reduce((sum,c)=>sum+c.prep_score,0)/prep.length):0;
  const tier1=companies.filter(c=>c.tier1).length;
  const stale=companies.filter(c=>c.stale).length;
  const wrap=el('div','metrics');
  [
    ['Calls next 3 days',upcoming,upcoming?'Calendar pressure':'No immediate calls',upcoming?'warn':''],
    ['Active processes',active,'Screening + interviewing',''],
    ['Avg prep readiness',prep.length?avg+'%':'—',prep.length?'Across active companies':'No prep tracked',avg>=70?'good':avg&&avg<40?'alert':'warn'],
    ['Tier 1 targets',tier1,'Priority companies',''],
    ['Stale cards',stale,stale?'Need follow-up sweep':'Pipeline is fresh',stale?'alert':'good'],
  ].forEach(([label,value,sub,cls])=>{
    const m=el('div',`metric ${cls||''}`);
    m.innerHTML=`<div class="metric-label">${esc(label)}</div><div class="metric-value">${esc(value)}</div><div class="metric-sub">${esc(sub)}</div>`;
    wrap.appendChild(m);
  });
  return wrap;
}

// ── Overview: Focus calls ────────────────────────────────────────────────────
const ROUND_DISPLAY={
  recruiter_screen:'Recruiter Screen',hm:'HM Interview',
  second_interview:'2nd Interview',panel:'Panel',exec:'Exec Round',take_home:'Take-Home'
};
function roundLabel(r){return ROUND_DISPLAY[r]||String(r||'').replace(/_/g,' ').replace(/\b\w/g,m=>m.toUpperCase());}

function renderFocus(){
  const today=new Date(DATA.today+'T00:00:00');
  const cut=new Date(today);cut.setDate(cut.getDate()+3);
  // Use interviews.yaml — structured source of truth with real dates and times
  const ups=(DATA.interviews||[])
    .filter(iv=>{
      if(!iv.date||iv.outcome!=='pending')return false;
      const d=new Date(iv.date+'T00:00:00');
      return d>=today&&d<=cut;
    })
    .sort((a,b)=>(a.date+(a.time||''))<(b.date+(b.time||''))?-1:1);
  const card=el('div','card');
  card.appendChild(el('div','sec','Upcoming calls — next 3 days'));
  if(!ups.length){card.appendChild(el('div','empty','No interviews in the next 3 days.'));return card}
  ups.forEach(iv=>{
    const co=DATA.companies.find(c=>c.id===iv.card_id)||{name:iv.company,tier1:false};
    const row=el('div','call-row');
    row.innerHTML=`
      <div class="call-time">${esc(iv.time||'TBD')}</div>
      <div class="call-co">${esc(co.name||iv.company)}${co.tier1?bdg('Tier 1','bdg-t1'):''}</div>
      <div class="call-type">${esc(roundLabel(iv.round))}</div>`;
    card.appendChild(row);
  });
  return card;
}

// ── Overview: Week strip ─────────────────────────────────────────────────────
function calDayOverlay(dateKey,dayLabel){
  // Use interviews.yaml — structured source with real times, not card emoji markers
  const events=(DATA.interviews||[])
    .filter(iv=>iv.date===dateKey&&iv.outcome==='pending')
    .sort((a,b)=>(a.time||'')<(b.time||'')?-1:1);
  if(!events.length)return;
  const html=events.map(iv=>{
    const co=DATA.companies.find(c=>c.id===iv.card_id)||{name:iv.company,tier1:false,next_action:''};
    const rLabel=roundLabel(iv.round);
    const who=iv.interviewer?` · ${esc(iv.interviewer)}`:'';
    const act=co.next_action?`<div class="mo-ev-act">${esc(co.next_action)}</div>`:'';
    return`<div class="mo-ev">
      <div class="mo-ev-time">${esc(iv.time||'')}</div>
      <div style="flex:1">
        <div class="mo-ev-name">${esc(co.name||iv.company)}${co.tier1?bdg('Tier 1','bdg-t1'):''}</div>
        <div class="mo-ev-type">${esc(rLabel)}${who}</div>${act}
      </div>
    </div>`;
  }).join('');
  Modal.open(dayLabel,html);
}

function renderWeek(){
  const today=new Date(DATA.today+'T00:00:00');
  const dow=today.getDay();
  const mon=new Date(today);
  if(dow===0)mon.setDate(today.getDate()+1);
  else if(dow===6)mon.setDate(today.getDate()+2);
  else mon.setDate(today.getDate()-(dow-1));
  // Use interviews.yaml as source of truth — pending entries by date
  const counts={};
  (DATA.interviews||[]).forEach(iv=>{
    if(iv.date&&iv.outcome==='pending'){counts[iv.date]=(counts[iv.date]||0)+1;}
  });
  const DAYS=['Mon','Tue','Wed','Thu','Fri'];
  const card=el('div','card');
  card.appendChild(el('div','sec','This week'));
  const grid=el('div','week');
  for(let i=0;i<5;i++){
    const d=new Date(mon);d.setDate(mon.getDate()+i);
    const k=d.toISOString().slice(0,10);
    const n=counts[k]||0;
    let cls='wd';if(n>=3)cls+=' heavy';else if(n>0)cls+=' ev';
    if(k===DATA.today)cls+=' today';
    const w=el('div',cls);
    const lbl=d.toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'});
    w.innerHTML=`
      <div class="wd-lbl">${DAYS[i]}</div>
      <div class="wd-num">${d.getDate()}</div>
      <div class="wd-ev">${n?n+(n===1?' call':' calls'):'·'}</div>`;
    if(n>0)w.addEventListener('click',()=>calDayOverlay(k,lbl));
    grid.appendChild(w);
  }
  card.appendChild(grid);return card;
}

// ── Overview: Kanban ─────────────────────────────────────────────────────────
function renderKCard(c){
  const nxt=c.next_interview?`<div class="kc-nxt">🗓 ${esc(c.next_interview)}</div>`:'';
  const act=c.next_action?`<div class="kc-act">${shortText(c.next_action,130)}</div>`:'';
  const shown=(c.tags||[]).slice(0,3);
  const extra=(c.tags||[]).length-shown.length;
  const tags=shown.map(t=>`<span class="tag">${esc(t)}</span>`).join('')+(extra>0?`<span class="tag">+${extra}</span>`:'');
  return`<div class="kc${c.tier1?' t1':''}">
    <div class="kc-name">${esc(c.name)}${c.tier1?bdg('Tier 1','bdg-t1'):''}${c.stale?bdg('Stale','bdg-st'):''}</div>
    ${nxt}${act}${(c.tags||[]).length?`<div class="kc-tags">${tags}</div>`:''}
    ${prepBar(c.prep_score,'Prep')}
  </div>`;
}

function renderKanban(){
  const stages=[{key:'interviewing',lbl:'Interviewing'},{key:'screening',lbl:'Screening'},{key:'applied',lbl:'Applied'}];
  const wrap=el('div');
  wrap.appendChild(el('div','sec','Pipeline'));
  const kb=el('div','kanban');
  stages.forEach(({key,lbl})=>{
    const cos=DATA.companies.filter(c=>c.stage===key);
    const col=el('div','kcol');col.dataset.s=key;
    col.innerHTML=`<div class="kcol-hdr"><span>${esc(lbl)}</span><span class="kcol-n">${cos.length}</span></div>`;
    cos.forEach(c=>{col.innerHTML+=renderKCard(c)});
    kb.appendChild(col);
  });
  wrap.appendChild(kb);return wrap;
}

// ── Overview: Signals ────────────────────────────────────────────────────────
function renderSignals(){
  const card=el('div','card');
  card.appendChild(el('div','sec','Industry pulse — last 7 days'));
  if(!DATA.signals.length){card.appendChild(el('div','empty','No signals yet — run morning brief to populate.'));return card}
  DATA.signals.forEach(s=>{
    const row=el('div',`sig-row${s.url?' link':''}`);
    // Show topic (bold) + truncated body on separate lines
    const topicHtml=s.topic?`<div class="sig-topic">${esc(s.topic)}</div>`:'';
    const bodyHtml=`<div class="sig-tx">${shortText(s.text,160)}</div>`;
    const linkHtml=s.url?'<div class="sig-arrow">Open source →</div>':'';
    row.innerHTML=`<div class="sig-dt">${esc(s.date)}</div>${topicHtml}${bodyHtml}${linkHtml}`;
    if(s.url)row.addEventListener('click',()=>window.open(s.url,'_blank'));
    card.appendChild(row);
  });
  return card;
}

// ── Overview: Prep tracker ───────────────────────────────────────────────────
function prepOverlay(c){
  const cls=pc(c.prep_score);
  const doneHtml=(c.prep_done||[]).map(d=>`<div class="mo-item"><span class="mo-icon" style="color:var(--grn)">✓</span><span>${esc(d)}</span></div>`).join('');
  const todoHtml=(c.prep_todo||[]).map(t=>`<div class="mo-item"><span class="mo-icon" style="color:var(--red)">✗</span><span>${esc(t)}</span></div>`).join('');
  const actHtml=c.next_action?`<div class="mo-slbl">Next action</div><div class="mo-act-box">${esc(c.next_action)}</div>`:'';
  Modal.open(`Prep: ${c.name}`,
    `<div class="mo-score-line"><div class="mo-score-num c-${cls}">${c.prep_score}%</div><div class="mo-score-lbl">prep readiness</div></div>
    ${doneHtml?`<div class="mo-slbl">Completed</div>${doneHtml}`:''}
    ${todoHtml?`<div class="mo-slbl">Still needed</div>${todoHtml}`:''}
    ${actHtml}`);
}

function renderPrep(){
  const active=DATA.companies.filter(c=>c.prep_score>=0);
  const card=el('div','card');
  card.appendChild(el('div','sec','Prep readiness — click for detail'));
  if(!active.length){card.appendChild(el('div','empty','No active prep tracked yet.'));return card}
  active.forEach(c=>{
    const cls=pc(c.prep_score);
    const flag=c.prep_score<40?' ⚠':'';
    const nxt=c.next_interview?`<span style="font-size:11px;color:var(--mu);font-weight:500"> · ${esc(c.next_interview)}</span>`:'';
    const row=el('div','pt-row');
    row.innerHTML=`
      <div class="pt-top"><div class="pt-name">${esc(c.name)}${flag}${nxt}</div><div class="pt-pct c-${cls}">${c.prep_score}%</div></div>
      <div class="pb-track"><div class="pb-fill f-${cls}" style="width:${c.prep_score}%"></div></div>`;
    row.addEventListener('click',()=>prepOverlay(c));
    card.appendChild(row);
  });
  return card;
}

// ── Overview tab ─────────────────────────────────────────────────────────────
function renderOverview(){
  const main=el('div','main');
  main.appendChild(renderMetrics());
  const top=el('div','top');
  top.appendChild(renderFocus());top.appendChild(renderWeek());
  main.appendChild(top);
  main.appendChild(renderKanban());
  const bot=el('div','bot');
  bot.appendChild(renderSignals());bot.appendChild(renderPrep());
  main.appendChild(bot);
  return main;
}

// ── Companies tab: markdown renderer ─────────────────────────────────────────
function mdFmt(t){
  let s=esc(t||'');
  s=s.replace(/\[([^\]]+)\]\(([^)]+)\)/g,'<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  s=s.replace(/\*\*([^*\n]+)\*\*/g,'<strong>$1</strong>');
  s=s.replace(/\*([^*\n]+)\*/g,'<em>$1</em>');
  return s;
}

function mdToHtml(text){
  if(!text)return'';
  const lines=String(text).split('\n');
  let html='',inUl=false;
  lines.forEach(line=>{
    if(/^####\s/.test(line)){
      if(inUl){html+='</ul>';inUl=false;}
      html+=`<h4>${mdFmt(line.replace(/^#+\s+/,''))}</h4>`;
    } else if(/^###\s/.test(line)){
      if(inUl){html+='</ul>';inUl=false;}
      html+=`<h3>${mdFmt(line.replace(/^#+\s+/,''))}</h3>`;
    } else if(/^##\s/.test(line)){
      if(inUl){html+='</ul>';inUl=false;}
      html+=`<h2>${mdFmt(line.replace(/^#+\s+/,''))}</h2>`;
    } else if(/^#\s/.test(line)){
      if(inUl){html+='</ul>';inUl=false;}
      html+=`<h1>${mdFmt(line.replace(/^#+\s+/,''))}</h1>`;
    } else if(/^[-*]\s/.test(line)){
      if(!inUl){html+='<ul>';inUl=true;}
      html+=`<li>${mdFmt(line.replace(/^[-*]\s+/,''))}</li>`;
    } else if(/^\d+\.\s/.test(line)){
      if(!inUl){html+='<ul>';inUl=true;}
      html+=`<li>${mdFmt(line.replace(/^\d+\.\s+/,''))}</li>`;
    } else if(!line.trim()){
      if(inUl){html+='</ul>';inUl=false;}
    } else if(/^\|/.test(line)||/^[-_*]{3,}$/.test(line.trim())||/^_/.test(line)){
      // skip raw table rows, hr, and italic metadata lines
    } else {
      if(inUl){html+='</ul>';inUl=false;}
      html+=`<p>${mdFmt(line)}</p>`;
    }
  });
  if(inUl)html+='</ul>';
  return html;
}

// ── Markdown table renderer ───────────────────────────────────────────────────
function renderMdTable(rows){
  if(!rows||!rows.length)return'';
  const hdrs=Object.keys(rows[0]);
  const ths=hdrs.map(h=>`<th>${esc(h)}</th>`).join('');
  const trs=rows.map(r=>`<tr>${hdrs.map(h=>`<td>${mdFmt(r[h]||'')}</td>`).join('')}</tr>`).join('');
  return`<table class="md-table"><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table>`;
}

// ── News item parser (from raw markdown bullets) ──────────────────────────────
function parseNewsItems(raw){
  if(!raw)return[];
  return String(raw).split('\n')
    .filter(l=>l.trim().startsWith('-')||l.trim().startsWith('*'))
    .map(l=>{
      const cleaned=l.replace(/^[-*]\s*/,'');
      const m=cleaned.match(/^\*\*([\d\-–]+[^*]*)\*\*[:\s]*(.*)/);
      return m?{date:m[1].trim(),text:m[2].trim()}:{date:'',text:cleaned};
    })
    .filter(i=>i.text);
}

// ── Companies tab: detail panel ──────────────────────────────────────────────
function initials(name){
  name=String(name||'');
  const p=name.replace(/[,].*$/,'').trim().split(/\s+/).filter(Boolean);
  return p.length>=2?(p[0][0]+p[p.length-1][0]).toUpperCase():name.slice(0,2).toUpperCase();
}

function roundIcon(status){
  if(!status)return'⬜';
  if(status.includes('✅'))return'✅';
  if(status.includes('🔴'))return'🔴';
  return'⬜';
}

function renderCompanyDetail(c){
  const wrap=el('div');

  // ── Hero ──
  const hero=el('div','cd-hero');
  const stgCls=`stg-${c.stage}`;
  const t1Html=c.tier1?`<span class="bdg bdg-t1">Tier 1</span>`:'';
  const staleHtml=c.stale?`<span class="bdg bdg-st">Stale</span>`:'';
  const researchHtml=c.research_updated
    ?`<span class="bdg-research ok">✓ Researched ${esc(c.research_updated)}</span>`
    :`<span class="bdg-research gap">⚠ Needs research</span>`;
  const tagsHtml=(c.tags||[]).map(t=>`<span class="tag">${esc(t)}</span>`).join('');
  const nxtHtml=c.next_interview?`<div class="cd-nxt-interview">🗓 ${esc(c.next_interview)}</div>`:'';
  const actHtml=c.next_action?`
    <div class="cd-nxt-action">
      <div class="cd-nxt-lbl">Next action</div>
      <div class="cd-nxt-text">${esc(c.next_action)}</div>
    </div>`:'';

  hero.innerHTML=`
    <div class="cd-top">
      <div class="cd-avatar">${esc(initials(c.name))}</div>
      <div>
        <div class="cd-name">${esc(c.name)}</div>
        <div class="cd-badges">
          <span class="cd-stg ${stgCls}">${esc(fmtStage(c.stage))}</span>
          ${t1Html}${staleHtml}${researchHtml}
        </div>
        ${tagsHtml?`<div class="cd-tags">${tagsHtml}</div>`:''}
        ${nxtHtml}
      </div>
      <div class="cd-right">
        <div class="cd-updated">Updated ${esc(c.last_updated||'—')}</div>
      </div>
    </div>
    ${prepBar(c.prep_score,'Prep readiness')}
    ${actHtml}`;
  wrap.appendChild(hero);

  // ── Business overview ──
  if(c.overview){
    const s=el('div','cd-sec');
    s.innerHTML=`<div class="cd-sec-ttl">Business Overview</div>
                 <div class="prep-md">${mdToHtml(c.overview)}</div>`;
    wrap.appendChild(s);
  }

  // ── Profile-Aware Analysis (PM Lens) ──
  if(c.analysis&&c.analysis.trim()){
    const s=el('div','cd-analysis');
    s.innerHTML=`<div class="cd-sec-ttl">Profile-Aware Analysis — PM Lens</div>
                 <div class="prep-md">${mdToHtml(c.analysis)}</div>`;
    wrap.appendChild(s);
  }

  // ── User Base & Geography ──
  if((c.geo_breakdown&&c.geo_breakdown.trim())||(c.prod_matrix&&c.prod_matrix.length)){
    const s=el('div','cd-sec');
    let html=`<div class="cd-sec-ttl">User Base & Geography</div>`;
    if(c.geo_breakdown&&c.geo_breakdown.trim()){
      html+=`<div class="sub-lbl">Geographic Breakdown</div>
             <div class="prep-md">${mdToHtml(c.geo_breakdown)}</div>`;
    }
    if(c.prod_matrix&&c.prod_matrix.length){
      html+=`<div class="sub-lbl" style="margin-top:12px">Product × User Segment</div>
             ${renderMdTable(c.prod_matrix)}`;
    }
    s.innerHTML=html;
    wrap.appendChild(s);
  }

  // ── Recent News ──
  if(c.recent_news&&c.recent_news.trim()){
    const items=parseNewsItems(c.recent_news);
    if(items.length){
      const s=el('div','cd-sec');
      let html=`<div class="cd-sec-ttl">Recent News</div>`;
      items.forEach(i=>{
        html+=`<div class="news-item">
          ${i.date?`<div class="news-date">${esc(i.date)}</div>`:''}
          <div class="news-text">${mdFmt(i.text)}</div>
        </div>`;
      });
      s.innerHTML=html;
      wrap.appendChild(s);
    }
  }

  // ── Funding & Culture ──
  if(c.funding||c.culture){
    const s=el('div','cd-sec');
    let html='';
    if(c.funding){
      html+=`<div class="cd-sec-ttl">Funding & Growth</div>
             <div class="prep-md">${mdToHtml(c.funding)}</div>`;
    }
    if(c.culture){
      html+=`<div class="cd-sec-ttl" style="${c.funding?'margin-top:16px':''}">Culture & People</div>
             <div class="prep-md">${mdToHtml(c.culture)}</div>`;
    }
    s.innerHTML=html;
    wrap.appendChild(s);
  }

  // ── Open roles ──
  if(c.open_roles&&c.open_roles.length){
    const s=el('div','cd-sec');
    s.innerHTML=`<div class="cd-sec-ttl">Open Roles</div>`;
    c.open_roles.forEach(r=>{
      const roleKey=Object.keys(r).find(k=>/role/i.test(k))||Object.keys(r)[0];
      const spotKey=Object.keys(r).find(k=>/spot/i.test(k));
      s.innerHTML+=`<div class="rl-row">
        <div class="rl-name">${esc(r[roleKey]||'—')}</div>
        <div class="rl-spotted">${spotKey&&r[spotKey]?'Spotted '+esc(r[spotKey]):''}</div>
      </div>`;
    });
    wrap.appendChild(s);
  }

  // ── Interview process ──
  if(c.rounds&&c.rounds.length){
    const s=el('div','cd-sec');
    s.innerHTML=`<div class="cd-sec-ttl">Interview Process</div>`;
    c.rounds.forEach(r=>{
      const status=r['Status']||r['status']||'';
      const icon=roundIcon(status);
      const done=status.includes('✅');
      const name=r['Round Name']||r['round name']||'—';
      const format=r['Format']||r['format']||'';
      const dur=r['Duration']||r['duration']||'';
      const intv=r['Interviewer / Team']||r['Interviewer']||r['interviewer']||'';
      const focus=r['Focus Areas']||r['Focus']||r['focus']||'';
      const detail=[format,dur,intv,focus].filter(Boolean).join(' · ');
      const statusLabel=String(status).replace(/[✅🔴⬜]/g,'').trim();
      s.innerHTML+=`<div class="rd-row${done?' rd-done':''}">
        <div class="rd-icon">${esc(icon)}</div>
        <div class="rd-body">
          <div class="rd-name">${esc(name)}${statusLabel?` <span style="font-size:11px;color:var(--mu);font-weight:500">${esc(statusLabel)}</span>`:''}</div>
          ${detail?`<div class="rd-detail">${esc(detail)}</div>`:''}
        </div>
      </div>`;
    });
    wrap.appendChild(s);
  }

  // ── Prep plan ──
  if(c.prep_notes&&c.prep_notes.trim()){
    const s=el('div','cd-sec');
    s.innerHTML=`<div class="cd-sec-ttl">Prep Plan</div>
                 <div class="prep-md">${mdToHtml(c.prep_notes)}</div>`;
    wrap.appendChild(s);
  }

  // ── Contacts ──
  if(c.contacts&&c.contacts.length){
    const s=el('div','cd-sec');
    s.innerHTML=`<div class="cd-sec-ttl">Contacts</div>`;
    c.contacts.forEach(ct=>{
      const name=ct['Name']||ct['name']||'?';
      const role=ct['Role']||ct['role']||'';
      const notes=ct['Notes']||ct['notes']||'';
      const how=ct['How Connected']||ct['how connected']||'';
      s.innerHTML+=`<div class="ct-row">
        <div class="ct-av">${esc(initials(name))}</div>
        <div>
          <div class="ct-name">${esc(name)}</div>
          <div class="ct-role">${esc(role)}${how?` · via ${esc(how)}`:''}</div>
          ${notes?`<div class="ct-notes">${esc(notes)}</div>`:''}
        </div>
      </div>`;
    });
    wrap.appendChild(s);
  }

  // ── Stage history (timeline) ──
  if(c.history&&c.history.length){
    const s=el('div','cd-sec');
    s.innerHTML=`<div class="cd-sec-ttl">Timeline</div>`;
    [...c.history].reverse().forEach(h=>{
      const d=h['Date']||h['date']||'';
      const st=h['Stage']||h['stage']||'';
      const n=h['Notes']||h['notes']||'';
      s.innerHTML+=`<div class="sh-row">
        <div class="sh-date">${esc(d)}</div>
        <div class="sh-stage">${esc(st)}</div>
        <div class="sh-notes">${esc(n)}</div>
      </div>`;
    });
    wrap.appendChild(s);
  }

  // ── Research feedback ──
  const prompt=`Research ${c.name} — I noticed [describe what is missing or wrong]. Update the card with [specific correction or addition].`;
  const fb=el('div','feedback-sec');
  fb.innerHTML=`
    <div class="feedback-hdr">Improve this research</div>
    <div class="feedback-hint">See something missing or outdated?</div>
    <ol class="feedback-steps">
      <li>Copy the prompt below</li>
      <li>Paste into Claude Code and press Enter</li>
    </ol>
    <div class="feedback-prompt-wrap">
      <div class="feedback-prompt" id="fp-${esc(c.id)}">${esc(prompt)}</div>
      <button class="feedback-copy" onclick="copyFeedback('fp-${esc(c.id)}',this)">Copy</button>
    </div>`;
  wrap.appendChild(fb);

  return wrap;
}

// ── Companies tab ─────────────────────────────────────────────────────────────
function renderCompaniesTab(){
  const wrap=el('div','co-wrap');

  // Left nav
  const nav=el('div','co-nav');
  const searchWrap=el('div','co-search');
  const inp=el('input','co-search-inp');
  inp.type='text';inp.placeholder='Search companies...';inp.setAttribute('autocomplete','off');
  searchWrap.appendChild(inp);
  nav.appendChild(searchWrap);
  const list=el('div','co-list');
  nav.appendChild(list);

  // Right panel
  const panel=el('div','co-panel');

  wrap.appendChild(nav);
  wrap.appendChild(panel);

  function updateList(q){
    const sorted=[...DATA.companies]
      .filter(c=>!q||c.name.toLowerCase().includes(q.toLowerCase()))
      .sort((a,b)=>a.name.localeCompare(b.name));
    list.innerHTML='';
    if(!sorted.length){
      list.innerHTML='<div style="padding:16px 14px;font-size:13px;color:var(--mu);font-style:italic">No match</div>';
      return;
    }
    // Auto-select first if current not in filtered list
    if(sorted.length&&!sorted.find(c=>c.id===ST.coId)){
      ST.coId=sorted[0].id;updatePanel();
    }
    sorted.forEach(c=>{
      const item=el('div',`co-item${c.id===ST.coId?' active':''}`);
      const dotCls=`co-dot dot-${c.stage}`;
      item.innerHTML=`<span class="${dotCls}"></span>
        <span class="co-item-name">${esc(c.name)}</span>
        ${c.tier1?'<span class="co-star">★</span>':''}`;
      item.addEventListener('click',()=>{ST.coId=c.id;updateList(q);updatePanel();});
      list.appendChild(item);
    });
  }

  function updatePanel(){
    panel.innerHTML='';
    const company=DATA.companies.find(c=>c.id===ST.coId);
    if(company)panel.appendChild(renderCompanyDetail(company));
    else panel.innerHTML='<div class="co-empty">Select a company</div>';
  }

  inp.addEventListener('input',e=>updateList(e.target.value));
  updateList('');
  updatePanel();
  return wrap;
}

// ── Today tab ─────────────────────────────────────────────────────────────────
function renderTodayTab(){
  const wrap=el('div','today-wrap');
  if(DATA.updates&&DATA.updates.length){
    const sec=el('div','updates-sec');
    sec.appendChild(el('div','updates-hdr','Updates'));
    DATA.updates.forEach((u,i)=>{
      const item=el('div','update-item');
      item.innerHTML=`<div class="update-num">${i+1}</div><div class="update-text">${mdFmt(u)}</div>`;
      sec.appendChild(item);
    });
    wrap.appendChild(sec);
  }
  const bsec=el('div','brief-sec');
  bsec.appendChild(el('div','brief-hdr','Daily Brief'));
  if(DATA.brief){
    const bc=el('div','brief-content prep-md');
    bc.innerHTML=mdToHtml(DATA.brief);
    bsec.appendChild(bc);
  } else {
    bsec.appendChild(el('div','brief-empty','No brief yet — run morning brief to generate.'));
  }
  wrap.appendChild(bsec);
  return wrap;
}

function renderTabContent(){
  return ST.tab==='overview'?renderOverview():ST.tab==='companies'?renderCompaniesTab():renderTodayTab();
}

// ── Main render ───────────────────────────────────────────────────────────────
function renderApp(){
  const app=document.getElementById('app');
  const existing=app.querySelectorAll('.cw');
  existing.forEach(e=>e.remove());

  const content=el('div','cw');
  content.style.cssText='flex:1;display:flex;flex-direction:column;min-height:0;overflow:hidden';

  const tabbar=renderTabBar(()=>{
    const old=content.querySelector('.main,.co-wrap,.today-wrap');
    if(old)old.remove();
    content.appendChild(renderTabContent());
  });
  content.appendChild(tabbar);
  content.appendChild(renderTabContent());
  app.appendChild(content);
}

(function(){
  const app=document.getElementById('app');
  app.style.cssText='height:100%;display:flex;flex-direction:column';
  app.appendChild(renderHdr());
  renderApp();
})();
"""

# ── HTML ──────────────────────────────────────────────────────────────────────

def build_html(data):
    data_json = json.dumps(data, default=str)
    today = data['today']
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<meta http-equiv="refresh" content="300">\n'
        f'<title>Chrysalis — {today}</title>\n'
        '<style>\n' + CSS + '\n</style>\n'
        '</head>\n<body>\n'
        '<div id="app"></div>\n'
        '<script>const DATA=' + data_json + ';</script>\n'
        '<script>\n' + JS + '\n</script>\n'
        '</body>\n</html>\n'
    )

# ── Entry point ───────────────────────────────────────────────────────────────

def generate():
    companies       = load_companies()
    signals         = load_signals()
    interviews      = load_interviews()
    brief, updates  = load_today_content()
    today           = date.today()
    started         = load_search_start_date()
    week_num        = max(1, (today - started).days // 7 + 1)

    data = {
        'today':        today.isoformat(),
        'generated_at': datetime.now().strftime('%b %d, %Y %H:%M'),
        'week_num':     week_num,
        'name':         load_profile_name(),
        'companies':    companies,
        'signals':      signals,
        'interviews':   interviews,
        'brief':        brief,
        'updates':      updates,
    }

    html  = build_html(data)
    out   = REPO / 'dashboard.html'
    out.write_text(html, encoding='utf-8')
    print(f'✓  Dashboard written → {out}')

    cmd = {'darwin': 'open', 'windows': 'start', 'linux': 'xdg-open'}.get(
        platform.system().lower())
    if cmd:
        try:
            subprocess.Popen([cmd, str(out)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    return out

if __name__ == '__main__':
    generate()
