#!/usr/bin/env python3
"""
Layout v2 of the lineage diagram: exact src / stg / fct names, columns visible, banded pages, colour = source table.
Reuses Scene and the draw.io / SVG emitters of build_drawio.py.
Usage: python3 docs/lineage/build_v2.py [--out FILE] [--svg-dir DIR]
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_drawio as B
import lineage_model as LM
from xml.sax.saxutils import quoteattr

INK, MUTED, TEAL, DEEP = B.INK, B.MUTED, B.TEAL, B.DEEP
# Colour = layer only. src grey, stg teal, fct deep teal, dashboard pale teal. Arrows one grey. One highlight: calculated rows (pale amber).
C_SRC, C_STG, C_FCT, C_DASH, C_EDGE, C_CALC = '#6B7B86', '#167C88', '#0E4A5C', '#E2F2F4', '#5F6C77', '#FFF3DC'
STG_COLOUR = {t: C_STG for t in ['stg_grants', 'stg_organisations', 'stg_decisions', 'stg_outcome_progress', 'stg_maturity', 'stg_support',
                                 'stg_disbursements', 'stg_dividends']}
STG_COLOUR['fct1_grant_portfolio'] = C_FCT
FCT_COLOUR = {f: C_FCT for f in ['fct1_grant_portfolio', 'fct2_outcome_progress', 'fct3_support_activity', 'fct4_budget_year', 'fct5_maturity_rag',
                                 'fct6_grantee_annual_info']}
STG_ORDER = ['stg_grants', 'stg_organisations', 'stg_decisions', 'stg_outcome_progress', 'stg_maturity', 'stg_support', 'stg_disbursements', 'stg_dividends']
SRC_OF = {t: v['source_tab'] for t, v in B.CODE['staging'].items()}
FCT_ORDER = list(FCT_COLOUR)
GRAIN = {'fct1_grant_portfolio': 'one row per grant', 'fct6_grantee_annual_info': 'one row per grant and measure', 'fct2_outcome_progress': 'one row per outcome and quarter',
         'fct3_support_activity': 'one row per support request', 'fct5_maturity_rag': 'one row per maturity indicator', 'fct4_budget_year': 'one row per financial year'}
MAP_FCT_ORDER = ['fct1_grant_portfolio', 'fct6_grantee_annual_info', 'fct2_outcome_progress', 'fct5_maturity_rag', 'fct3_support_activity', 'fct4_budget_year']
NAME_W, TYPE_W, FROM_W, RULE_W = 250, 78, 290, 330


def ribbon(sc, active, x=40, y=20):
    labels = [('src', 'source tabs'), ('stg', 'staging'), ('fct', 'final'), ('dashboard', 'Looker Studio')]
    cx = x
    for i, (k, sub) in enumerate(labels):
        on = (k == active)
        sc.box(cx, y, 150, 34, title=k, fill=TEAL if on else '#FFFFFF', stroke=TEAL if on else '#B9C5CB',
               tcolor='#FFFFFF' if on else INK, tsize=15)
        sc.items[-1]['fill'] = {'src': C_SRC, 'stg': C_STG, 'fct': C_FCT, 'dashboard': C_STG}.get(k, C_STG) if on else '#FFFFFF'
        if i < 3:
            sc.text(cx + 156, y + 4, 22, 24, ['›'], size=22, color=MUTED, bold=True)
        cx += 190
    return cx


def stg_row(table, col):
    c = next(c for c in B.CODE['staging'][table]['columns'] if c['name'] == col)
    k = B.kind_of(col, c['type'])
    r = B.row_dict(col, None, k, key=col, type_text=B.type_label(k))
    r['fill'] = '#FFFFFF'
    return r


def fct_row_simple(table, col):
    k = B.kind_of(col)
    r = B.row_dict(col, None, k, key=col)
    r['fill'] = '#FFFFFF'
    return r


def group_text(ups):
    by = {}
    for u in ups:
        t, c = u.split('.', 1)
        by.setdefault(t, []).append(c)
    return ' · '.join(f'{t}: ' + ', '.join(cs) for t, cs in by.items()), list(by)


# ------------------------------------------------------------------ page 1: map
def page_map():
    sc = B.Scene('1. Map: src, stg, fct')
    ribbon(sc, None)
    sc.text(40, 72, 1700, 24, ['Every table, by its real name. Read left to right. Colour = layer: grey src, teal stg, dark fct.'], size=14, color=MUTED)
    top, dy, bw, bh = 190, 92, 330, 70
    xs = {'src': 40, 'stg': 520, 'fct': 1000, 'dash': 1480}
    heads = [('src', 'src  ·  source tabs', 'APFP Central Administration workbook'), ('stg', 'stg  ·  staging', 'one cleaned table per source tab'),
             ('fct', 'fct  ·  final', 'built from stg only (no int_ layer)'), ('dash', 'dashboard  ·  Looker Studio', 'one data source per fct table')]
    for k, t, sub in heads:
        lc = {'src': C_SRC, 'stg': C_STG, 'fct': C_FCT, 'dash': C_STG}[k]
        sc.box(xs[k], top - 70, bw, 60, title=t, body=[sub], fill=lc, stroke=lc, tcolor='#FFFFFF', tsize=15, bsize=10)
        sc.items[-1]['bcolor'] = '#CFE3E6'
    src_id, stg_id, fct_id = {}, {}, {}
    for i, t in enumerate(STG_ORDER):
        n = len(B.CODE['staging'][t]['columns'])
        y = top + i * dy
        src_id[t] = sc.box(xs['src'], y, bw, bh, title=SRC_OF[t], body=[f'{n} columns read'], stroke=C_SRC, tsize=15)
        stg_id[t] = sc.box(xs['stg'], y, bw, bh, title=t, body=[f'{n} columns'], fill='#FFFFFF', stroke=STG_COLOUR[t], tsize=15)
        sc.items[-1]['stroke'] = STG_COLOUR[t]
        sc.edge(src_id[t], stg_id[t], 'copy', color=C_EDGE, width=2)
    fy = {f: top + 10 + i * 112 for i, f in enumerate(MAP_FCT_ORDER)}
    for f in FCT_ORDER:
        n = len(B.CODE['final'][f])
        fct_id[f] = sc.box(xs['fct'], fy[f], bw, bh, title=f, body=[f'{n} columns  ·  {GRAIN[f]}'], stroke=FCT_COLOUR[f], tsize=15)
    reads = {}
    for f in FCT_ORDER:
        reads[f] = []
        for col, cat, ups, rule in LM.FINAL[f]:
            for u in ups:
                t = u.split('.')[0]
                if t not in reads[f]:
                    reads[f].append(t)
    for f in FCT_ORDER:
        for t in reads[f]:
            sc.edge(stg_id[t] if t.startswith('stg') else fct_id[t], fct_id[f], 'copy', color=C_EDGE,
                    dashed=t.startswith('fct'), width=2)
    pages = {'1': 'Portfolio', '2': 'Funding', '3': 'Decision Queue', '4': 'Grantee 360'}
    ids_by_page = {}
    for f in FCT_ORDER:
        for ch in LM.FEEDS[f]:
            ids_by_page.setdefault((f, ch[0]), []).append(ch)
    page_id = {}
    for i, (d, name) in enumerate(pages.items()):
        page_id[d] = sc.box(xs['dash'], top + 20 + i * 150, bw, 80, title=f'{name}', body=[f'charts {d}.xx'], fill=C_DASH, stroke='#9CC9D0', tsize=15)
    for (f, d), chs in ids_by_page.items():
        sc.edge(fct_id[f], page_id[d], 'copy', color=C_EDGE, width=2)
    sc.text(40, top + 8 * dy + 10, 1700, 20, ['Dashed grey arrow: fct6_grantee_annual_info is built from fct1_grant_portfolio, not from stg directly.'], size=12, color=MUTED)
    return sc


# ------------------------------------------------------------------ page: one fct table as bands
def page_fct_bands(f, num):
    sc = B.Scene(f'{num}. stg to fct: {f}')
    ribbon(sc, 'fct')
    info = LM.TABLE_INFO[f]
    sc.text(40, 70, 1700, 30, [f'{f}   ({len(B.CODE["final"][f])} columns)'], size=24, color=DEEP, bold=True)
    sc.text(40, 106, 1700, 40, [info[1] + '.  Charts: ' + ', '.join(LM.FEEDS[f])], size=12, color=TEAL)
    # colour legend
    used = []
    for col, cat, ups, rule in LM.FINAL[f]:
        for u in ups:
            t = u.split('.')[0]
            if t not in used:
                used.append(t)
    lx = 40
    sc.text(lx, 172, 160, 18, ['Dot colour = stg table:'], size=11, color=MUTED)
    lx = 200
    for t in sorted(used, key=lambda t: STG_ORDER.index(t) if t in STG_ORDER else 99):
        sc.box(lx, 171, 14, 14, fill=STG_COLOUR[t], stroke=STG_COLOUR[t])
        sc.text(lx + 20, 171, 220, 18, [t], size=11, color=INK)
        lx += 40 + len(t) * 7
    model = {c[0]: c for c in LM.FINAL[f]}
    blocks = LM.BLOCKS.get(f) or [('All columns', [c for c in B.CODE['final'][f]])]
    covered = [c for _, cols in blocks for c in cols]
    assert sorted(covered) == sorted(B.CODE['final'][f]), f'BLOCKS for {f} must list every column exactly once'
    y = 215
    left_x, gap = 40, 150
    right_x = left_x + NAME_W + TYPE_W + gap
    for bi, (btitle, cols) in enumerate(blocks, 1):
        sc.text(40, y, 1700, 24, [f'Block {bi} of {len(blocks)}: {btitle}'], size=16, color=DEEP, bold=True)
        y += 32
        # upstream columns used by this block, per stg table, in first-use order
        per = {}
        for col in cols:
            for u in model[col][2]:
                t, c = u.split('.', 1)
                per.setdefault(t, [])
                if c not in per[t]:
                    per[t].append(c)
        ly = y
        placed = {}
        for t in sorted(per, key=lambda t: STG_ORDER.index(t) if t in STG_ORDER else 99):
            rows = [stg_row(t, c) if t.startswith('stg') else fct_row_simple(t, c) for c in per[t]]
            tb = sc.table(left_x, ly, t, t, rows, STG_COLOUR[t], widths=(NAME_W, TYPE_W), row_h=34, subtitle=SRC_OF.get(t, 'final table'))
            placed[t] = tb
            ly += B.HEAD_H + len(rows) * 34 + 24
        rows = []
        for col in cols:
            cat, ups, rule = model[col][1], model[col][2], model[col][3]
            r = fct_row_simple(f, col)
            r['calc'] = cat == 'calc'
            r['type'] = B.type_label(r['kind'], r['calc'])
            txt, tabs = group_text(ups)
            r['dots'] = [STG_COLOUR[t] for t in tabs]
            r['cols'] = [txt or {'const': 'fixed value', 'run': 'date of the run', 'blank': 'kept empty'}.get(cat, ''), rule]
            rows.append(r)
        ft = sc.table(right_x, y, f, f, rows, FCT_COLOUR[f], widths=(NAME_W, TYPE_W, FROM_W, RULE_W), row_h=40,
                      subtitle=f'block {bi}: {btitle}', dot_w=14 * 3)
        for col in cols:
            tgt = ft['by_key'][col]['cells'][0]
            for u in model[col][2]:
                t, c = u.split('.', 1)
                sc.edge(placed[t]['by_key'][c]['cells'][-1], tgt, model[col][1], color=STG_COLOUR[t], width=1.6)
        y = max(ly, y + B.HEAD_H + len(rows) * 40 + 24) + 30
    sc.text(40, y, 1700, 20, ['Solid arrow: copied or looked up.  Dashed arrow: calculated (ƒ).  Column "built from" lists the exact upstream columns; the last column is the rule in plain words.'], size=11, color=MUTED)
    return sc


# ------------------------------------------------------------------ page: one fct table, arranged by source
ROW_H2, HEAD2 = 38, 46


def classify(f):
    """Group the columns of fct f by where they come from. Returns [(section key, title, colour, [(col, cat, ups, rule)])]."""
    order = STG_ORDER + ['fct1_grant_portfolio']
    secs = {}
    for col, cat, ups, rule in LM.FINAL[f]:
        tabs = []
        for u in ups:
            t = u.split('.')[0]
            if t not in tabs:
                tabs.append(t)
        if not tabs:
            key = 'fixed'
        elif len(tabs) == 1:
            key = tabs[0]
        else:
            key = 'several'
        secs.setdefault(key, []).append((col, cat, ups, rule))
    for key in secs:  # copied / looked-up columns first (they get the flat arrows), calculated ones after
        secs[key] = [r for r in secs[key] if r[1] in ('copy', 'join')] + [r for r in secs[key] if r[1] not in ('copy', 'join')]
    out = []
    for key in order:
        if key in secs:
            copied = sum(1 for r in secs[key] if r[1] == 'copy')
            out.append((key, f'from {key}', STG_COLOUR[key], secs[key]))
    if 'several' in secs:
        out.append(('several', 'calculated from several tables', C_EDGE, secs['several']))
    if 'fixed' in secs:
        out.append(('fixed', 'fixed value, run date or kept empty', C_SRC, secs['fixed']))
    return out


def built_from(col, cat, ups, f):
    if not ups:
        return {'const': 'fixed value', 'run': 'date of the run', 'blank': 'kept empty'}.get(cat, '')
    by = {}
    for u in ups:
        t, c = u.split('.', 1)
        by.setdefault(t, []).append(c)
    if len(by) == 1:
        cols = list(by.values())[0]
        if cat in ('copy', 'join') and len(cols) == 1 and cols[0] == col:
            return ''
        return ', '.join(cols)
    return ' + '.join(f'{t}: ' + ', '.join(cs) for t, cs in by.items())


def page_fct(f, num):
    sc = B.Scene(f'{num}. stg to fct: {f}')
    ribbon(sc, 'fct')
    info = LM.TABLE_INFO[f]
    sc.text(40, 70, 1700, 30, [f'{f}   ({len(B.CODE["final"][f])} columns)'], size=24, color=DEEP, bold=True)
    sc.text(40, 104, 1700, 20, [info[1] + '.'], size=13, color=MUTED)
    sc.text(40, 126, 1700, 40, ['Charts: ' + ', '.join(LM.FEEDS[f])], size=12, color=TEAL)
    sections = classify(f)
    left_w, gap = NAME_W + TYPE_W, 120
    right_x = 40 + left_w + gap
    widths = (250, 78, 390, 330)
    y0 = 200
    # fct rows (section bars included)
    rows, sec_start, row_of = [], {}, {}
    for key, title, colr, cols in sections:
        sec_start[key] = len(rows)
        bar = B.row_dict(f'{title}   ({len(cols)})', None, 'text', key='sec:' + key)
        bar['section'] = True
        bar['fill'] = colr
        rows.append(bar)
        for col, cat, ups, rule in cols:
            r = fct_row_simple(f, col)
            r['calc'] = cat == 'calc'
            r['type'] = B.type_label(r['kind'], r['calc'])
            r['cols'] = [built_from(col, cat, ups, f), '' if cat == 'copy' else rule]
            if r['calc']:
                r['fill'] = r['rowfill'] = C_CALC
            rows.append(r)
    ft = sc.table(right_x, y0, f, f, rows, FCT_COLOUR[f], widths=widths, row_h=ROW_H2, subtitle=info[1][:70], fs=11)
    # left cards, each once, level with its own section
    used = {}
    for key, title, colr, cols in sections:
        for col, cat, ups, rule in sorted(cols, key=lambda r: r[1] not in ('copy', 'join')):
            for u in ups:
                t, c = u.split('.', 1)
                used.setdefault(t, [])
                if c not in used[t]:
                    used[t].append(c)
    placed, ly = {}, y0
    for t in sorted(used, key=lambda t: STG_ORDER.index(t) if t in STG_ORDER else 99):
        top = y0 + HEAD2 + sec_start[t] * ROW_H2 - (HEAD2 - ROW_H2) if t in sec_start else ly
        top = max(top, ly)
        crow = [stg_row(t, c) if t.startswith('stg') else fct_row_simple(t, c) for c in used[t]]
        tb = sc.table(40, top, t, t, crow, STG_COLOUR[t], widths=(NAME_W, TYPE_W), row_h=ROW_H2,
                      subtitle=(SRC_OF[t] + '  ·  ' if t in SRC_OF else '') + f'{len(used[t])} columns used', fs=11)
        placed[t] = tb
        ly = top + HEAD2 + len(crow) * ROW_H2 + 24
    # arrows: every column from its first input; the full input list is in "built from"
    for key, title, colr, cols in sections:
        for col, cat, ups, rule in cols:
            if not ups:
                continue
            tgt = ft['by_key'][col]['cells'][0]
            if cat not in ('copy', 'join'):
                continue  # calculated columns: no arrow, their inputs are listed under "built from"
            for u in ups:
                t, c = u.split('.', 1)
                sc.edge(placed[t]['by_key'][c]['cells'][-1], tgt, cat, color=C_EDGE, width=1.6)
    bottom = max(ly, y0 + HEAD2 + len(rows) * ROW_H2) + 20
    sc.text(40, bottom, 1700, 20, ['White row: copied or looked up (arrow).  Pale amber row, ƒ: calculated (no arrow; inputs under "built from").  Blank "built from": same name as in stg.'], size=12, color=MUTED)
    return sc


# ------------------------------------------------------------------ page: from fct columns to dashboard numbers
def page_metrics_v2(num):
    sc = B.Scene(f'{num}. fct to dashboard: metrics')
    ribbon(sc, 'dashboard')
    sc.text(40, 70, 1700, 30, ['From fct columns to dashboard numbers'], size=24, color=DEEP, bold=True)
    sc.text(40, 104, 1700, 40, ['Each dashboard number is one Looker Studio field. The same field is reused by every chart that needs it; the chart adds its own filter. Fields are named by type: distinct_, sum_, pct_, inr_, txt_.'], size=13, color=MUTED)
    x1, x2, x3, w1, w2, w3 = 40, 560, 1180, 430, 520, 560
    y = 180
    sc.box(x1, y - 44, w1, 38, title='fct columns it reads', fill=C_FCT, stroke=C_FCT, tcolor='#FFFFFF', tsize=14)
    sc.box(x2, y - 44, w2, 38, title='dashboard field (metric)', fill=C_FCT, stroke=C_FCT, tcolor='#FFFFFF', tsize=14)
    sc.box(x3, y - 44, w3, 38, title='charts that show it', fill=C_FCT, stroke=C_FCT, tcolor='#FFFFFF', tsize=14)
    for m in LM.METRICS:
        field, label, definition, ups, charts, filt = m
        by = {}
        for u in ups:
            t, c = u.split('.', 1)
            by.setdefault(t, []).append(c)
        lines = [f'{t}: ' + ', '.join(cs) for t, cs in by.items()]
        tcol = C_EDGE
        names = [f'{c} {LM.CHART_NAMES.get(c, "")}'.strip() for c in charts]
        cl = [', '.join(names[i:i + 2]) for i in range(0, len(names), 2)] if len(names) > 3 else names
        body = [definition] + ([f'Chart filter: {filt}'] if filt else [])
        h = max(78, 24 + 18 * max(len(lines), len(cl), len(body) + 1))
        a = sc.box(x1, y, w1, h, title='', body=lines, fill='#FFFFFF', stroke=C_FCT, bsize=12)
        sc.items[-1]['bcolor'] = INK
        b = sc.box(x2, y, w2, h, title=field, body=body, fill=C_DASH, stroke='#9CC9D0', tsize=15, bsize=12)
        c = sc.box(x3, y, w3, h, title='', body=cl, fill='#FFFFFF', stroke='#B9C5CB', bsize=12)
        sc.items[-1]['bcolor'] = INK
        sc.edge(a, b, 'copy', color=tcol, width=2)
        sc.edge(b, c, 'copy', color=tcol, width=2)
        y += h + 22
    return sc


def main():
    out = os.path.join(HERE, 'pilot', 'APFP_Lineage_pilot.drawio')
    svg_dir = os.path.join(HERE, 'pilot')
    args = sys.argv[1:]
    while args:
        a = args.pop(0)
        if a == '--out': out = args.pop(0)
        elif a == '--svg-dir': svg_dir = args.pop(0)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pages = [page_map(), page_fct('fct1_grant_portfolio', 2), page_metrics_v2(3)]
    xml = '<mxfile host="app.diagrams.net" version="24.0.0">' + ''.join(B.drawio_page(p, i + 1) for i, p in enumerate(pages)) + '</mxfile>'
    open(out, 'w', encoding='utf-8').write(xml)
    os.makedirs(svg_dir, exist_ok=True)
    for i, p in enumerate(pages):
        open(os.path.join(svg_dir, f'{i + 1:02d}_' + re.sub(r'[^A-Za-z0-9]+', '_', p.name).strip('_') + '.svg'), 'w', encoding='utf-8').write(B.svg_page(p))
    print('wrote', out)


if __name__ == '__main__':
    main()
