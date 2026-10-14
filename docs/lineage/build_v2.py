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
STG_COLOUR = {
    'stg_grants': '#167C88', 'stg_organisations': '#8A6A2F', 'stg_decisions': '#EB6834', 'stg_outcome_progress': '#4A3AA7',
    'stg_maturity': '#C2185B', 'stg_support': '#2E7D32', 'stg_disbursements': '#E87BA4', 'stg_dividends': '#6D7B86',
    'fct1_grant_portfolio': '#167C88',
}
FCT_COLOUR = {'fct1_grant_portfolio': '#167C88', 'fct2_outcome_progress': '#EB6834', 'fct3_support_activity': '#4A3AA7',
              'fct4_budget_year': '#E87BA4', 'fct5_maturity_rag': '#8A6A2F', 'fct6_grantee_annual_info': '#5F6C77'}
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
        if i < 3:
            sc.text(cx + 156, y + 4, 22, 24, ['›'], size=22, color=MUTED, bold=True)
        cx += 190
    return cx


def stg_row(table, col):
    c = next(c for c in B.CODE['staging'][table]['columns'] if c['name'] == col)
    k = B.kind_of(col, c['type'])
    return B.row_dict(col, None, k, key=col, type_text=B.type_label(k))


def fct_row_simple(table, col):
    k = B.kind_of(col)
    return B.row_dict(col, None, k, key=col)


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
    sc.text(40, 72, 1700, 24, ['Every table, by its real name. Read left to right. Colour = which stg table feeds the fct table.'], size=14, color=MUTED)
    top, dy, bw, bh = 190, 92, 330, 70
    xs = {'src': 40, 'stg': 520, 'fct': 1000, 'dash': 1480}
    heads = [('src', 'src  ·  source tabs', 'APFP Central Administration workbook'), ('stg', 'stg  ·  staging', 'one cleaned table per source tab'),
             ('fct', 'fct  ·  final', 'built from stg only (no int_ layer)'), ('dash', 'dashboard  ·  Looker Studio', 'one data source per fct table')]
    for k, t, sub in heads:
        sc.box(xs[k], top - 70, bw, 60, title=t, body=[sub], fill=B.DEEP, stroke=B.DEEP, tcolor='#FFFFFF', tsize=15, bsize=10)
        sc.items[-1]['bcolor'] = '#CFE3E6'
    src_id, stg_id, fct_id = {}, {}, {}
    for i, t in enumerate(STG_ORDER):
        n = len(B.CODE['staging'][t]['columns'])
        y = top + i * dy
        src_id[t] = sc.box(xs['src'], y, bw, bh, title=SRC_OF[t], body=[f'{n} columns read'], tsize=15)
        stg_id[t] = sc.box(xs['stg'], y, bw, bh, title=t, body=[f'{n} columns'], fill='#FFFFFF', stroke=STG_COLOUR[t], tsize=15)
        sc.items[-1]['stroke'] = STG_COLOUR[t]
        sc.edge(src_id[t], stg_id[t], 'copy', color='#8A97A1', width=2)
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
            sc.edge(stg_id[t] if t.startswith('stg') else fct_id[t], fct_id[f], 'copy', color=STG_COLOUR[t] if t.startswith('stg') else '#5F6C77',
                    dashed=t.startswith('fct'), width=2)
    pages = {'1': 'Portfolio', '2': 'Funding', '3': 'Decision Queue', '4': 'Grantee 360'}
    ids_by_page = {}
    for f in FCT_ORDER:
        for ch in LM.FEEDS[f]:
            ids_by_page.setdefault((f, ch[0]), []).append(ch)
    page_id = {}
    for i, (d, name) in enumerate(pages.items()):
        page_id[d] = sc.box(xs['dash'], top + 20 + i * 150, bw, 80, title=f'{name}', body=[f'charts {d}.xx'], fill='#E2F2F4', stroke='#9CC9D0', tsize=15)
    for (f, d), chs in ids_by_page.items():
        sc.edge(fct_id[f], page_id[d], 'copy', color=FCT_COLOUR[f], width=2)
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


def main():
    out = os.path.join(HERE, 'pilot', 'APFP_Lineage_pilot.drawio')
    svg_dir = os.path.join(HERE, 'pilot')
    args = sys.argv[1:]
    while args:
        a = args.pop(0)
        if a == '--out': out = args.pop(0)
        elif a == '--svg-dir': svg_dir = args.pop(0)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pages = [page_map(), page_fct_bands('fct1_grant_portfolio', 2)]
    xml = '<mxfile host="app.diagrams.net" version="24.0.0">' + ''.join(B.drawio_page(p, i + 1) for i, p in enumerate(pages)) + '</mxfile>'
    open(out, 'w', encoding='utf-8').write(xml)
    os.makedirs(svg_dir, exist_ok=True)
    for i, p in enumerate(pages):
        open(os.path.join(svg_dir, f'{i + 1:02d}_' + re.sub(r'[^A-Za-z0-9]+', '_', p.name).strip('_') + '.svg'), 'w', encoding='utf-8').write(B.svg_page(p))
    print('wrote', out)


if __name__ == '__main__':
    main()
