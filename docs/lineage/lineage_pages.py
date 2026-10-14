#!/usr/bin/env python3
"""
Lineage diagram, version 2: every src / stg / fct table is ONE native draw.io table (rows = columns), on one fixed grid.
This module holds the page model (tables, rows, cells, arrows, coordinates, colours) and three emitters:
  - draw.io XML  (docs/lineage/APFP_Data_Lineage_v2.drawio)
  - SVG preview  (docs/lineage/v2_preview/*.svg, then PNG)
  - the shape lists used by export_spec_xlsx.py (the Excel spec handed to another tool)
Usage: python3 docs/lineage/lineage_pages.py        (rebuilds the .drawio and the SVG previews)
"""
import json, math, os, re, sys
from xml.sax.saxutils import escape, quoteattr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_v2 as V  # noqa: E402  (classify, built_from, hl, palette)

B, LM, CODE = V.B, V.LM, V.B.CODE
CHARTS = json.loads(open(os.path.join(HERE, '..', '..', 'LineageData.js'), encoding='utf-8').read().split('LINEAGE_DATA = ', 1)[1].rsplit(';', 1)[0])['charts']

# ------------------------------------------------------------------ grid (all multiples of 10)
M, HEAD, ROW, GAP = 40, 50, 40, 30
STG_COLS = (260, 100)
FCT_COLS = (260, 100, 380, 360)
STG_W, FCT_W = sum(STG_COLS), sum(FCT_COLS)
GUT = 120
FONT = 'Helvetica'
C_SRC, C_STG, C_FCT, C_DASHH, C_DASH, C_EDGE = V.C_SRC, V.C_STG, V.C_FCT, '#3B6BA5', V.C_DASH, V.C_EDGE
H_KEY, H_NUM, H_BOOL = V.H_KEY, V.H_NUM, V.H_BOOL
INK, MUTED, LINE = '#1E2838', '#5F6C77', '#B9C5CB'
LAYER_FILL = {'src': C_SRC, 'stg': C_STG, 'fct': C_FCT, 'dashboard': C_DASHH}
STG_ORDER, FCT_ORDER = V.STG_ORDER, V.FCT_ORDER
SRC_OF = V.SRC_OF
GRAIN = V.GRAIN

STYLE = {
    'table': 'shape=table;startSize={head};container=1;collapsible=0;childLayout=tableLayout;fixedRows=1;rowLines=0;fontStyle=1;align=left;spacingLeft=10;resizeLast=1;html=1;whiteSpace=wrap;fontSize=14;fontColor=#FFFFFF;fillColor={fill};strokeColor={fill};',
    'row': 'shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;strokeColor=inherit;top=0;left=0;bottom=0;right=0;collapsible=0;dropTarget=0;fillColor=none;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;fontSize=12;',
    'cell': 'shape=partialRectangle;html=1;whiteSpace=wrap;connectable=0;overflow=hidden;fillColor={fill};top=1;left=1;bottom=1;right=1;strokeColor=' + LINE + ';pointerEvents=1;align=left;spacingLeft=8;spacingRight=6;fontSize={size};fontColor={color};{extra}',
    'edge': 'edgeStyle=elbowEdgeStyle;elbow=horizontal;html=1;rounded=0;endArrow=block;endFill=1;strokeWidth=1.5;strokeColor=' + C_EDGE + ';exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;{dash}',
    'text': 'text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;fontSize={size};fontColor={color};{extra}',
    'chip': 'rounded=1;arcSize=20;html=1;whiteSpace=wrap;fontSize=15;fontStyle=1;align=center;verticalAlign=middle;fillColor={fill};strokeColor={stroke};fontColor={color};',
    'swatch': 'rounded=0;html=1;fillColor={fill};strokeColor=' + LINE + ';',
}


def est_lines(text, width, size=11):
    if not text:
        return 1
    per = max(8, int((width - 16) / (size * 0.56)))
    return sum(max(1, math.ceil(len(part) / per)) for part in str(text).split('\n'))


def row_height(cells, min_h=ROW):
    need = max(est_lines(c.get('text', ''), c['w'], (c.get('size') or (12 if c['i'] < 2 else 11))) for c in cells)
    return min_h if need <= 2 else 20 * math.ceil((need * 14 + 12) / 20)


class Page:
    def __init__(self, name, title, subtitle=None, ribbon=None, width=1640):
        self.name, self.title, self.subtitle, self.ribbon = name, title, subtitle, ribbon
        self.width, self.height = width, 0
        self.tables, self.shapes, self.edges = [], [], []
        self.n = 0

    def nid(self, p):
        self.n += 1
        return f'{p}{self.n}'

    def text(self, x, y, w, h, text, size=12, color=MUTED, bold=False, kind='text'):
        sid = self.nid('x')
        self.shapes.append({'id': sid, 'type': kind, 'x': x, 'y': y, 'w': w, 'h': h, 'text': text, 'size': size, 'color': color, 'bold': bold})
        return sid

    def box(self, x, y, w, h, text, fill, stroke, color, kind='chip', bold=True, size=15):
        sid = self.nid('x')
        self.shapes.append({'id': sid, 'type': kind, 'x': x, 'y': y, 'w': w, 'h': h, 'text': text, 'fill': fill, 'stroke': stroke, 'color': color, 'bold': bold, 'size': size})
        return sid

    def table(self, x, y, name, sub, layer, rows, widths, head=HEAD, layer_fill=None):
        """rows: list of dict(cells=[dict(text, fill, color, bold, italic)], key=column name or None, section=bool)."""
        tid = self.nid('T')
        cy = y + head
        for r in rows:
            for i, c in enumerate(r['cells']):
                c['i'] = i
                c['w'] = widths[i] if len(r['cells']) == len(widths) else sum(widths)
            r['id'] = self.nid('R')
            r['h'] = r.get('h') or row_height(r['cells'])
            r['x'], r['y'], r['w'] = x, cy, sum(widths)
            cy += r['h']
        t = {'id': tid, 'name': name, 'sub': sub, 'layer': layer, 'x': x, 'y': y, 'w': sum(widths), 'h': cy - y, 'head': head, 'rows': rows,
             'widths': widths, 'fill': layer_fill or LAYER_FILL[layer]}
        self.tables.append(t)
        self.height = max(self.height, cy + 60)
        return t

    def edge(self, src_row, tgt_row, dashed=False, lane_x=None):
        self.edges.append({'id': self.nid('E'), 'src': src_row['id'], 'tgt': tgt_row['id'], 'sx': src_row['x'] + src_row['w'], 'sy': src_row['y'] + src_row['h'] / 2,
                           'tx': tgt_row['x'], 'ty': tgt_row['y'] + tgt_row['h'] / 2, 'dashed': dashed, 'lane_x': lane_x})

    def edge_tables(self, src_t, tgt_t, dashed=False):
        cx = src_t['x'] + src_t['w'] / 2
        self.edges.append({'id': self.nid('E'), 'src': src_t['id'], 'tgt': tgt_t['id'], 'sx': cx, 'sy': src_t['y'] + src_t['h'], 'tx': cx, 'ty': tgt_t['y'],
                           'dashed': dashed, 'lane_x': cx, 'vertical': True})

    def finish(self):
        for e in self.edges:
            if e['lane_x'] is None:
                e['lane_x'] = (e['sx'] + e['tx']) / 2
        self.height = max(self.height, max([s['y'] + s['h'] for s in self.shapes] + [0]) + 60)
        self.width = max(self.width, max([t['x'] + t['w'] for t in self.tables] + [0]) + M)


def cell(text, fill='#FFFFFF', color=INK, bold=False, italic=False, size=None):
    return {'text': text, 'fill': fill, 'color': color, 'bold': bold, 'italic': italic, 'size': size}


def header(page, active):
    chips = [('src', 'src'), ('stg', 'stg'), ('fct', 'fct'), ('dashboard', 'dashboard')]
    x = M
    for i, (k, label) in enumerate(chips):
        on = (k == active)
        page.box(x, 20, 150, 40, label, LAYER_FILL[k] if on else '#FFFFFF', LAYER_FILL[k] if on else LINE, '#FFFFFF' if on else INK, kind='chip')
        if i < 3:
            page.text(x + 156, 24, 30, 30, '›', size=22, color=MUTED, bold=True, kind='chip_arrow')
        x += 190


def legend(page, y):
    x = M
    for fill, text in [(H_KEY, 'Key column (checked by the cardinality tests)'), (H_NUM, 'Number'), (H_BOOL, 'True / false'), (C_DASH, 'Dashboard metric')]:
        page.box(x, y, 20, 20, '', fill, LINE, INK, kind='swatch')
        page.text(x + 28, y, 400, 20, text, size=12, color=INK, kind='legend_text')
        x += 60 + len(text) * 7


# ------------------------------------------------------------------ pages
def page_map():
    p = Page('1. Map: src, stg, fct', 'Map: src, stg, fct', 'Every table by its real name. Left to right: src (source tabs), stg (staging), fct (final), dashboard pages.', None, 1900)
    header(p, None)
    p.text(M, 80, 1800, 30, 'Map: src → stg → fct → dashboard', size=24, color=C_FCT, bold=True, kind='title')
    p.text(M, 120, 1800, 24, 'Every table by its real name. Arrows are table to table. fct6_grantee_annual_info is built from fct1_grant_portfolio (dashed).', size=13, kind='subtitle')
    top, pitch = 190, 130
    X = {'src': M, 'stg': M + 340 + 120, 'fct': M + 340 + 120 + 340 + 300, 'dash': M + 340 + 120 + 340 + 300 + 340 + 200}
    ystg = {}
    rows_src, rows_stg, rows_fct, rows_dash, tabs_fct = {}, {}, {}, {}, {}
    for i, t in enumerate(STG_ORDER):
        n = len(CODE['staging'][t]['columns'])
        y = top + i * pitch
        ts = p.table(X['src'], y, SRC_OF[t], 'src', 'src', [{'cells': [cell(f'{n} columns read')], 'key': None}], (340,))
        tg = p.table(X['stg'], y, t, 'stg', 'stg', [{'cells': [cell(f'{n} columns')], 'key': None}], (340,))
        rows_src[t], rows_stg[t] = ts['rows'][0], tg['rows'][0]
        p.edge(ts['rows'][0], tg['rows'][0])
    map_order = ['fct1_grant_portfolio', 'fct6_grantee_annual_info', 'fct2_outcome_progress', 'fct5_maturity_rag', 'fct3_support_activity', 'fct4_budget_year']
    for i, f in enumerate(map_order):
        n = len(CODE['final'][f])
        tf = p.table(X['fct'], top + i * 170, f, 'fct', 'fct', [{'cells': [cell(f'{n} columns · {GRAIN[f]}')], 'key': None}], (340,))
        rows_fct[f] = tf['rows'][0]
        tabs_fct[f] = tf
    reads = {}
    for f in map_order:
        reads[f] = []
        for col, cat, ups, rule in LM.FINAL[f]:
            for u in ups:
                t = u.split('.')[0]
                if t not in reads[f]:
                    reads[f].append(t)
    gx0 = X['stg'] + 340
    k = 0
    for f in map_order:
        for t in sorted([t for t in reads[f] if t.startswith('stg')], key=STG_ORDER.index):
            p.edge(rows_stg[t], rows_fct[f], lane_x=gx0 + 20 + 14 * k)
            k += 1
    p.edge_tables(tabs_fct['fct1_grant_portfolio'], tabs_fct['fct6_grantee_annual_info'], dashed=True)
    pages = {'1': 'Portfolio', '2': 'Funding', '3': 'Decision Queue', '4': 'Grantee 360'}
    for i, (d, name) in enumerate(pages.items()):
        ids = [c['id'] for c in V.__dict__.get('_charts', [])] or None
    charts = json.loads(open(os.path.join(V.HERE, '..', '..', 'LineageData.js'), encoding='utf-8').read().split('LINEAGE_DATA = ', 1)[1].rsplit(';', 1)[0])['charts']
    for i, (d, name) in enumerate(pages.items()):
        cnt = len([c for c in charts if c['id'].startswith(d + '.')])
        td = p.table(X['dash'], top + 40 + i * 230, name, 'dashboard', 'dashboard', [{'cells': [cell(f'{cnt} charts ({d}.xx)', fill=C_DASH)], 'key': None}], (300,))
        rows_dash[d] = td['rows'][0]
    gx1 = X['fct'] + 340
    k = 0
    for f in map_order:
        for d in pages:
            if any(c['table'] == f and c['id'].startswith(d + '.') for c in charts):
                p.edge(rows_fct[f], rows_dash[d], lane_x=gx1 + 30 + 14 * k)
                k += 1
    p.finish()
    return p


def col_type(col, calc=False):
    t = B.type_label(B.kind_of(col), calc)
    if col == 'aspect_display':
        t = 'text' + (' ƒ' if calc else '')
    return t.replace('true / false', 'true/false')


def disp_type(kind, ctype):
    if kind == H_BOOL:
        return 'true/false'
    return {'fy': 'text', 'rate': 'number'}.get(ctype, ctype)


def page_src_stg_all(num):
    gw = STG_W + 100 + STG_W
    p = Page(f'{num}. src to stg: all tables', 'src to stg: all tables', None, 'stg', M + gw + 80 + gw + M)
    header(p, 'stg')
    p.text(M, 80, 1700, 30, 'src to stg: all 8 source tabs and their stg tables', size=24, color=C_FCT, bold=True, kind='title')
    p.text(M, 120, 1700, 24, 'Each src column is kept in stg under a clean name, same row and same order, so every arrow is a straight line. Left: the source tab. Right: its stg table.', size=13, kind='subtitle')
    legend(p, 160)
    groups = [['stg_grants', 'stg_organisations', 'stg_maturity', 'stg_dividends'],
              ['stg_outcome_progress', 'stg_support', 'stg_decisions', 'stg_disbursements']]
    for gi, tables in enumerate(groups):
        x0 = M + gi * (gw + 80)
        y = 210
        for t in tables:
            spec = CODE['staging'][t]
            lrows, rrows = [], []
            for c in spec['columns']:
                kind = V.hl(t, c['name'], c['type'])
                ty = disp_type(kind, c['type'])
                lrows.append({'cells': [cell(c['source_header'], fill=kind), cell(ty, fill=kind, color=MUTED, size=11)], 'key': c['name']})
                rrows.append({'cells': [cell(c['name'], fill=kind), cell(ty, fill=kind, color=MUTED, size=11)], 'key': c['name']})
            tl = p.table(x0, y, spec['source_tab'], f'src · {len(lrows)} columns read', 'src', lrows, STG_COLS)
            tr = p.table(x0 + STG_W + 100, y, t, f'stg · {len(rrows)} columns', 'stg', rrows, STG_COLS)
            for a, b in zip(tl['rows'], tr['rows']):
                h = max(a['h'], b['h'])
                a['h'] = b['h'] = h
            # recompute y positions after equalising heights
            cy = y + HEAD
            for a, b in zip(tl['rows'], tr['rows']):
                a['y'] = b['y'] = cy
                cy += a['h']
            tl['h'] = tr['h'] = cy - y
            for a, b in zip(tl['rows'], tr['rows']):
                p.edge(a, b)
            y = cy + GAP * 2
        p.height = max(p.height, y)
    p.finish()
    return p


def page_fct_index(num):
    p = Page(f'{num}. fct: all final tables', 'fct: all final tables', None, 'fct', M + 6 * 360 + 5 * 40 + M)
    header(p, 'fct')
    p.text(M, 80, 2000, 30, 'fct: all 6 final tables and every column', size=24, color=C_FCT, bold=True, kind='title')
    p.text(M, 120, 2000, 24, 'One table per final table, columns in the same order as the sheet in the Data Pipeline workbook. Details of each table are on its own page.', size=13, kind='subtitle')
    legend(p, 160)
    for i, f in enumerate(FCT_ORDER):
        rows = []
        for col in CODE['final'][f]:
            kind = V.hl(f, col)
            rows.append({'cells': [cell(col, fill=kind), cell(col_type(col), fill=kind, color=MUTED, size=11)], 'key': col})
        p.table(M + i * 400, 210, f, f'fct · {len(rows)} columns · {GRAIN[f]}', 'fct', rows, STG_COLS)
    p.finish()
    return p


def fct_rows(f):
    sections = V.classify(f)
    rows, start = [], {}
    for key, title, colr, cols in sections:
        start[key] = len(rows)
        rows.append({'cells': [cell(f'{title}   ({len(cols)})', fill=colr, color='#FFFFFF', bold=True, size=13)], 'key': None, 'section': True, 'h': ROW})
        for col, cat, ups, rule in cols:
            kind = V.hl(f, col)
            calc = cat == 'calc'
            typ = col_type(col, calc)
            bf = V.built_from(col, cat, ups, f)
            if len(bf) > 150 and ups:
                bf = f'{len(ups)} columns of ' + ' + '.join(sorted({u.split('.')[0] for u in ups})) + ': ' + ', '.join(u.split('.')[1] for u in ups[:3]) + ', …'
            rows.append({'cells': [cell(col, fill=kind), cell(typ, fill=kind, color=MUTED, size=11), cell(bf, color=MUTED, size=11), cell('' if cat == 'copy' else rule, color=MUTED, size=11)],
                         'key': col, 'cat': cat, 'ups': ups, 'section_key': key, 'built_from': bf, 'rule': '' if cat == 'copy' else rule})
    return sections, rows, start


def page_fct(f, num):
    info = LM.TABLE_INFO[f]
    p = Page(f'{num}. stg to fct: {f}', f, info[1], 'fct', M + STG_W + GUT + FCT_W + M)
    header(p, 'fct')
    p.text(M, 80, 1500, 30, f'{f}   ({len(CODE["final"][f])} columns)', size=24, color=C_FCT, bold=True, kind='title')
    p.text(M, 120, 1500, 24, info[1] + '.', size=13, kind='subtitle')
    p.text(M, 150, 1560, 40, 'Charts: ' + ', '.join(LM.FEEDS[f]), size=12, color=C_STG, kind='charts')
    legend(p, 210)
    sections, rows, start = fct_rows(f)
    top = 260
    # first pass: place the fct table to learn row positions
    tf = p.table(M + STG_W + GUT, top, f, f'fct · {len(CODE["final"][f])} columns', 'fct', rows, FCT_COLS)
    used = {}
    for key, title, colr, cols in sections:
        for col, cat, ups, rule in sorted(cols, key=lambda r: r[1] not in ('copy', 'join')):
            for u in ups:
                t, c = u.split('.', 1)
                used.setdefault(t, [])
                if c not in used[t]:
                    used[t].append(c)
    rowmap = {r['key']: r for r in tf['rows'] if r.get('key')}
    bars = {}
    for key, title, colr, cols in sections:
        i = start[key]
        bars[key] = tf['rows'][i]
    ly = top
    placed = {}
    for t in sorted(used, key=lambda t: STG_ORDER.index(t) if t in STG_ORDER else 99):
        want = (bars[t]['y'] + bars[t]['h'] - HEAD) if t in bars else ly
        y = max(want, ly)
        rws = []
        for c in used[t]:
            if t.startswith('stg'):
                ty = next(x['type'] for x in CODE['staging'][t]['columns'] if x['name'] == c)
                kind = V.hl(t, c, ty)
                typ = col_type(c) if not t.startswith('stg') else disp_type(kind, ty)
            else:
                kind = V.hl(t, c)
                typ = col_type(c)
            rws.append({'cells': [cell(c, fill=kind), cell(typ, fill=kind, color=MUTED, size=11)], 'key': c})
        tl = p.table(M, y, t, f'{SRC_OF[t]} · {len(rws)} columns used' if t in SRC_OF else f'{len(rws)} columns used', 'stg' if t.startswith('stg') else 'fct', rws, STG_COLS)
        placed[t] = {r['key']: r for r in tl['rows']}
        ly = y + tl['h'] + GAP
    k = 0
    for key, title, colr, cols in sections:
        for col, cat, ups, rule in cols:
            if cat not in ('copy', 'join'):
                continue
            tgt = rowmap[col]
            for u in ups:
                t, c = u.split('.', 1)
                src = placed[t][c]
                straight = abs((src['y'] + src['h'] / 2) - (tgt['y'] + tgt['h'] / 2)) < 1
                lane = None if straight else (M + STG_W + 20 + 10 * (k % 10))
                if not straight:
                    k += 1
                p.edge(src, tgt, lane_x=lane)
    band_y = max(ly, tf['y'] + tf['h']) + 20
    p.text(M, band_y, 1560, 24, 'Arrow: copied or looked up. ƒ = calculated: no arrow; its inputs are listed under "built from". Blank "built from": same name as in stg.', size=12, kind='note')
    metrics_band(p, f, band_y + 80)
    p.finish()
    return p


def metrics_band(p, f, y):
    fct_charts = {c['id']: c for c in CHARTS if c['table'] == f}
    p.text(M, y, 1500, 34, f'Dashboard fields and charts built from {f}', size=20, color=C_FCT, bold=True, kind='band_title')
    p.text(M, y + 38, 1560, 22, 'Each dashboard number is one Looker Studio field, reused by every chart that needs it; the chart adds its own filter. Fields are named by type: distinct_, sum_, pct_, inr_, txt_.', size=12, kind='band_note')
    y += 80
    lrows, mrows, rrows, covered = [], [], [], set()
    for field, label, definition, ups, charts, filt in LM.METRICS:
        mine = [u.split('.', 1)[1] for u in ups if u.startswith(f + '.')]
        ch = [c for c in charts if c in fct_charts]
        if not mine or not ch:
            continue
        covered |= set(ch)
        left = f'{f}: ' + ', '.join(mine)
        right = '\n'.join(', '.join(f'{c} {LM.CHART_NAMES.get(c, "")}'.strip() for c in ch[i:i + 2]) for i in range(0, len(ch), 2))
        mid = definition + (f'\nChart filter: {filt}' if filt else '')
        cs = [[cell(left, size=11)], [cell(field, fill=C_DASH, bold=True), cell(mid, color=MUTED, size=11)], [cell(right, size=11)]]
        h = max(60, max(row_height([dict(c, i=1, w=w) for c, w in zip(cs_, ws)], 40) for cs_, ws in zip(cs, [(360,), (220, 380), (380,)])))
        lrows.append({'cells': cs[0], 'key': None, 'h': h})
        mrows.append({'cells': cs[1], 'key': field, 'h': h})
        rrows.append({'cells': cs[2], 'key': None, 'h': h})
    if lrows:
        tl = p.table(M, y, 'fct columns it reads', 'fct', 'fct', lrows, (360,))
        tm = p.table(M + 360 + GUT, y, 'dashboard field (metric)', 'dashboard', 'dashboard', mrows, (220, 380))
        tr = p.table(M + 360 + GUT + 600 + GUT, y, 'charts that show it', 'dashboard', 'dashboard', rrows, (380,))
        for a, b, c in zip(tl['rows'], tm['rows'], tr['rows']):
            p.edge(a, b)
            p.edge(b, c)
        y = tl['y'] + tl['h'] + 50
    else:
        p.text(M, y, 1500, 24, 'No calculated dashboard field is built from this table: its charts read the columns directly (below).', size=13, kind='band_note')
        y += 50
    direct = [c for cid, c in fct_charts.items() if cid not in covered]
    if direct:
        drows = [{'cells': [cell(f'{c["id"]} {c["name"]}', bold=True), cell(', '.join(c['columns']), color=MUTED, size=11), cell(c['filter'], color=MUTED, size=11)], 'key': None} for c in direct]
        p.table(M, y, 'charts that read columns directly (no calculated field)', 'dashboard', 'dashboard', drows, (360, 700, 380))


def page_glossary(num):
    p = Page(f'{num}. Glossary and key', 'Glossary and key', None, None, 1100)
    header(p, None)
    p.text(M, 80, 1000, 30, 'Glossary and key', size=24, color=C_FCT, bold=True, kind='title')
    terms = [('src', 'A source tab in the APFP Central Administration workbook, where programme staff type the data.'),
             ('stg', 'Staging: a cleaned copy of one src tab (clean names, types, one financial-year format). No business logic.'),
             ('fct', 'Final: a table built only from stg tables (joins and calculated columns), shaped for the dashboard.'),
             ('No int_ layer', 'No intermediate layer: every fct table reads stg directly, so int_ would only copy data.'),
             ('Grain', 'What one row means, for example one row per grant.'),
             ('Key column', 'A column checked by the cardinality tests (unique, not blank, exists in its parent table); every *_id column.'),
             ('Calculated column (ƒ)', 'A column worked out by the scripts from other columns; its inputs are listed under "built from".'),
             ('Dashboard field (metric)', 'One Looker Studio field, for example distinct_grantees, reused by every chart that needs it.'),
             ('Chart filter', 'The condition a chart adds to a field, for example active grants only.')]
    p.table(M, 140, 'Terms', 'plain definitions', 'fct', [{'cells': [cell(a, bold=True), cell(b, size=12)], 'key': None} for a, b in terms], (240, 780))
    keys = [(H_KEY, 'Key column'), (H_NUM, 'Number'), (H_BOOL, 'True / false'), ('#FFFFFF', 'Text or date'), (C_DASH, 'Dashboard metric')]
    p.table(M, 140 + HEAD + ROW * len(terms) + 60 + 30, 'Colour key', 'cells of a table row', 'fct', [{'cells': [cell(t, fill=f)], 'key': None} for f, t in keys], (400,))
    p.table(M + 400 + 40, 140 + HEAD + ROW * len(terms) + 60 + 30, 'Header colour', 'the layer', 'fct',
            [{'cells': [cell('src', fill=C_SRC, color='#FFFFFF', bold=True)], 'key': None}, {'cells': [cell('stg', fill=C_STG, color='#FFFFFF', bold=True)], 'key': None},
             {'cells': [cell('fct', fill=C_FCT, color='#FFFFFF', bold=True)], 'key': None}, {'cells': [cell('dashboard', fill=C_DASHH, color='#FFFFFF', bold=True)], 'key': None}], (300,))
    p.finish()
    return p


def all_pages():
    pages = [page_map(), page_src_stg_all(2), page_fct_index(3)]
    for i, f in enumerate(FCT_ORDER):
        pages.append(page_fct(f, 4 + i))
    pages.append(page_glossary(10))
    return pages


# ------------------------------------------------------------------ draw.io emitter
def cell_style(c, i, last):
    extra = ('fontStyle=%d;' % ((1 if c['bold'] else 0) + (2 if c.get('italic') else 0))) if (c['bold'] or c.get('italic')) else ''
    return STYLE['cell'].format(fill=c['fill'], size=c.get('size') or 12, color=c['color'], extra=extra)


def drawio_page(p, idx):
    out = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
    for s in p.shapes:
        sid = f'{p.name[:2].strip(". ")}_{s["id"]}'
        if s['type'] == 'chip':
            st = STYLE['chip'].format(fill=s['fill'], stroke=s['stroke'], color=s['color'])
            val = escape(s['text'])
        elif s['type'] == 'swatch':
            st = STYLE['swatch'].format(fill=s['fill'])
            val = ''
        else:
            extra = ('fontStyle=1;' if s.get('bold') else '')
            st = STYLE['text'].format(size=s['size'], color=s['color'], extra=extra)
            val = escape(s['text'])
        out.append(f'<mxCell id="{s["id"]}" value={quoteattr(val)} style={quoteattr(st)} vertex="1" parent="1"><mxGeometry x="{s["x"]}" y="{s["y"]}" width="{s["w"]}" height="{s["h"]}" as="geometry"/></mxCell>')
    for t in p.tables:
        title = '<b>' + escape(t['name']) + '</b>' + ('<br><font style="font-size:10px" color="#E2F2F4">' + escape(t['sub']) + '</font>' if t['sub'] else '')
        st = STYLE['table'].format(head=t['head'], fill=t['fill'])
        out.append(f'<object label={quoteattr(title)} id="{t["id"]}" layer="{t["layer"]}" table="{escape(t["name"])}"><mxCell style={quoteattr(st)} vertex="1" parent="1"><mxGeometry x="{t["x"]}" y="{t["y"]}" width="{t["w"]}" height="{t["h"]}" as="geometry"/></mxCell></object>')
        ry = t['head']
        for r in t['rows']:
            props = f' layer="{t["layer"]}" table="{escape(t["name"])}"' + (f' column="{escape(r["key"])}"' if r.get('key') else '')
            out.append(f'<object label="" id="{r["id"]}"{props}><mxCell style={quoteattr(STYLE["row"])} vertex="1" parent="{t["id"]}"><mxGeometry y="{ry}" width="{t["w"]}" height="{r["h"]}" as="geometry"/></mxCell></object>')
            rx = 0
            for j, c in enumerate(r['cells']):
                w = c['w']
                val = escape(c['text']).replace('\n', '<br>')
                xa = f' x="{rx}"' if rx else ''
                out.append(f'<mxCell id="{r["id"]}_{j}" value={quoteattr(val)} style={quoteattr(cell_style(c, j, len(r["cells"]) - 1))} vertex="1" parent="{r["id"]}"><mxGeometry{xa} width="{w}" height="{r["h"]}" as="geometry"><mxRectangle width="{w}" height="{r["h"]}" as="alternateBounds"/></mxGeometry></mxCell>')
                rx += w
            ry += r['h']
    for e in p.edges:
        st = STYLE['edge'].format(dash='dashed=1;' if e['dashed'] else '')
        if e.get('vertical'):
            st = 'edgeStyle=none;html=1;endArrow=block;endFill=1;strokeWidth=1.5;strokeColor=' + C_EDGE + ';exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;' + ('dashed=1;' if e['dashed'] else '')
        pts = ''
        if not e.get('vertical') and abs(e['sy'] - e['ty']) > 0.5:
            pts = f'<Array as="points"><mxPoint x="{e["lane_x"]:.0f}" y="{e["sy"]:.0f}"/></Array>'
        out.append(f'<mxCell id="{e["id"]}" style={quoteattr(st)} edge="1" parent="1" source="{e["src"]}" target="{e["tgt"]}"><mxGeometry relative="1" as="geometry">{pts}</mxGeometry></mxCell>')
    model = f'<mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" pageWidth="{p.width}" pageHeight="{p.height}" math="0" shadow="0"><root>{"".join(out)}</root></mxGraphModel>'
    return f'<diagram id="page{idx}" name={quoteattr(p.name)}>{model}</diagram>'


# ------------------------------------------------------------------ SVG emitter (preview only)
def wrap_lines(text, width, size):
    per = max(8, int((width - 16) / (size * 0.56)))
    out = []
    for part in str(text).split('\n'):
        words, line = part.split(' '), ''
        for w in words:
            if len(line) + len(w) + 1 > per and line:
                out.append(line)
                line = w
            else:
                line = (line + ' ' + w).strip()
        out.append(line)
    return out


def svg_page(p):
    W, H = p.width, p.height
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Helvetica, Arial, sans-serif">',
         f'<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{C_EDGE}"/></marker></defs>',
         f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    for s in p.shapes:
        if s['type'] in ('chip',):
            o.append(f'<rect x="{s["x"]}" y="{s["y"]}" width="{s["w"]}" height="{s["h"]}" rx="8" fill="{s["fill"]}" stroke="{s["stroke"]}"/>')
            o.append(f'<text x="{s["x"] + s["w"] / 2}" y="{s["y"] + s["h"] / 2 + 5}" font-size="15" font-weight="700" text-anchor="middle" fill="{s["color"]}">{escape(s["text"])}</text>')
        elif s['type'] == 'swatch':
            o.append(f'<rect x="{s["x"]}" y="{s["y"]}" width="{s["w"]}" height="{s["h"]}" fill="{s["fill"]}" stroke="{LINE}"/>')
        else:
            y = s['y'] + s['size']
            for ln in wrap_lines(s['text'], s['w'], s['size']):
                fw = ' font-weight="700"' if s.get('bold') else ''
                o.append(f'<text x="{s["x"]}" y="{y}" font-size="{s["size"]}" fill="{s["color"]}"{fw}>{escape(ln)}</text>')
                y += s['size'] + 4
    for t in p.tables:
        o.append(f'<rect x="{t["x"]}" y="{t["y"]}" width="{t["w"]}" height="{t["head"]}" fill="{t["fill"]}"/>')
        o.append(f'<text x="{t["x"] + 10}" y="{t["y"] + 22}" font-size="14" font-weight="700" fill="#FFFFFF">{escape(t["name"])}</text>')
        if t['sub']:
            o.append(f'<text x="{t["x"] + 10}" y="{t["y"] + 40}" font-size="10" fill="#E2F2F4">{escape(t["sub"])}</text>')
        for r in t['rows']:
            cx = t['x']
            for c in r['cells']:
                o.append(f'<rect x="{cx}" y="{r["y"]}" width="{c["w"]}" height="{r["h"]}" fill="{c["fill"]}" stroke="{LINE}"/>')
                size = c.get('size') or 12
                lines = wrap_lines(c['text'], c['w'], size)
                ty = r['y'] + (r['h'] - len(lines) * (size + 3)) / 2 + size
                fw = ' font-weight="700"' if c['bold'] else ''
                for ln in lines:
                    o.append(f'<text x="{cx + 8}" y="{ty:.0f}" font-size="{size}" fill="{c["color"]}"{fw}>{escape(ln)}</text>')
                    ty += size + 3
                cx += c['w']
    for e in p.edges:
        dash = ' stroke-dasharray="7 5"' if e['dashed'] else ''
        if e.get('vertical') or abs(e['sy'] - e['ty']) < 0.5:
            d = f'M{e["sx"]},{e["sy"]} L{e["tx"]},{e["ty"]}'
        else:
            d = f'M{e["sx"]},{e["sy"]} L{e["lane_x"]},{e["sy"]} L{e["lane_x"]},{e["ty"]} L{e["tx"]},{e["ty"]}'
        o.append(f'<path d="{d}" fill="none" stroke="{C_EDGE}" stroke-width="1.5"{dash} marker-end="url(#a)"/>')
    o.append('</svg>')
    return '\n'.join(o)


def main():
    pages = all_pages()
    out = os.path.join(HERE, 'APFP_Data_Lineage_v2.drawio')
    xml = '<mxfile host="app.diagrams.net" version="24.0.0">' + ''.join(drawio_page(p, i + 1) for i, p in enumerate(pages)) + '</mxfile>'
    open(out, 'w', encoding='utf-8').write(xml)
    d = os.path.join(HERE, 'v2_preview')
    os.makedirs(d, exist_ok=True)
    for i, p in enumerate(pages):
        name = re.sub(r'[^A-Za-z0-9]+', '_', p.name).strip('_')
        open(os.path.join(d, f'{i + 1:02d}_{name}.svg'), 'w', encoding='utf-8').write(svg_page(p))
    print('wrote', out, len(pages), 'pages')


if __name__ == '__main__':
    main()
