"""
One-page, plain-language picture for clients: where staff type -> dashboard-ready tables -> dashboard pages.
Table level only; column detail lives in the Data_Dictionary and Chart_Passport tabs.
Reads LineageData.js (so it always matches the dictionary) and writes docs/lineage/story/APFP_Data_Story.{svg,drawio}.
    python3 docs/lineage/make_story.py
Render the PNG with headless Chromium (see docs/lineage/README note in DATA_LINEAGE.md).
"""
import json, os, sys
from xml.sax.saxutils import escape as esc, quoteattr

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
s = open(os.path.join(ROOT, 'LineageData.js'), encoding='utf-8').read()
DATA = json.loads(s[s.index('{', s.index('LINEAGE_DATA')):s.rindex(';')])

INK, MUTED, TEAL, DEEP = '#1E2838', '#5F6C77', '#167C88', '#0E4A5C'
SOURCES = [  # tab, plain name, what staff enter
    ('8. Grant Registry', 'Grant register', 'Grants, amounts, dates, status'),
    ('9. Organisation Registry', 'Organisation register', 'Mission, policies, registration'),
    ('4. Decision Tracker', 'Decision tracker', 'Renew / close recommendations'),
    ('2. Outcome Progress', 'Outcome progress', 'Targets and quarterly progress'),
    ('7. Organisation Maturity', 'Organisation maturity', 'Red / Amber / Green ratings'),
    ('3. Support', 'Support requests', 'Help asked for and given'),
    ('6. Committed & Spent Tracker', 'Committed and spent', 'Planned and actual payments'),
    ('5. Dividends', 'Dividends', 'Dividend income per year'),
]
TABLES = [  # key, colour
    ('fct1_grant_portfolio', '#167C88'), ('fct6_grantee_annual_info', '#5F6C77'), ('fct2_outcome_progress', '#EB6834'),
    ('fct5_maturity_rag', '#8A6A2F'), ('fct3_support_activity', '#4A3AA7'), ('fct4_budget_year', '#E87BA4'),
]
TABLE_TEXT = {  # short plain wording for the picture (the long text lives in the Data_Dictionary tab)
    'fct1_grant_portfolio': ('Grant portfolio', 'One row per grant: funding, decision, ratings'),
    'fct6_grantee_annual_info': ('Annual information', 'This year next to last year (built from the portfolio)'),
    'fct2_outcome_progress': ('Outcome progress', 'One row per outcome and quarter'),
    'fct5_maturity_rag': ('Maturity ratings', 'One row per maturity indicator'),
    'fct3_support_activity': ('Support activity', 'One row per support request'),
    'fct4_budget_year': ('Budget by year', 'Dividends, commitments, payments, balance'),
}
PAGES = ['Portfolio', 'Funding', 'Decision Queue', 'Grantee 360']
PAGE_NOTE = {'Portfolio': 'Who we fund and how they are doing', 'Funding': 'Money in, committed, paid out',
             'Decision Queue': 'Renewals and closures to decide', 'Grantee 360': 'One organisation in full'}

# edges
tab_to_table = {}
for t, _ in TABLES:
    if t == 'fct6_grantee_annual_info':
        continue  # built from the grant portfolio, not from the source directly
    tabs = set()
    for ref, e in DATA['columns'].items():
        if ref.startswith(t + '.'):
            tabs |= set(e['source_tabs'])
    tab_to_table[t] = tabs
table_to_page = {}
for c in DATA['charts']:
    table_to_page.setdefault((c['table'], c['page']), []).append(c['id'])

W, H = 1500, 960
SX, SW = 40, 400
TX, TW = 590, 360
PX, PW = 1140, 320
top = 150
sy = {src[0]: top + i * 84 for i, src in enumerate(SOURCES)}
ty = {t: top + 4 + i * 112 for i, (t, _) in enumerate(TABLES)}
py = {p: top + 30 + i * 150 for i, p in enumerate(PAGES)}
NH = 64
col = dict(TABLES)

svg = []
dio = []
vid = {}
n = [1]


def nid(key):
    vid[key] = f'n{n[0]}'
    n[0] += 1
    return vid[key]


def box(key, x, y, w, h, title, sub, fill, stroke, bar=None):
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
    if bar:
        svg.append(f'<rect x="{x}" y="{y}" width="8" height="{h}" rx="3" fill="{bar}"/>')
    svg.append(f'<text x="{x+22}" y="{y+27}" font-size="16" font-weight="700" fill="{INK}">{esc(title)}</text>')
    svg.append(f'<text x="{x+22}" y="{y+49}" font-size="12.5" fill="{MUTED}">{esc(sub)}</text>')
    i = nid(key)
    label = f'<b>{esc(title)}</b><br><font style="font-size:11px" color="{MUTED}">{esc(sub)}</font>'
    dio.append(f'<mxCell id="{i}" value={quoteattr(label)} style="rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};strokeWidth=1.5;align=left;spacingLeft=18;fontSize=14;fontColor={INK};" vertex="1" parent="1">'
               f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')


def band(x, w, title, sub):
    svg.append(f'<rect x="{x}" y="92" width="{w}" height="46" rx="8" fill="{TEAL}"/>')
    svg.append(f'<text x="{x+16}" y="112" font-size="16" font-weight="700" fill="#FFFFFF">{esc(title)}</text>')
    svg.append(f'<text x="{x+16}" y="130" font-size="12" fill="#E2F2F4">{esc(sub)}</text>')
    i = nid('band' + title)
    label = f'<b>{esc(title)}</b><br><font style="font-size:11px">{esc(sub)}</font>'
    dio.append(f'<mxCell id="{i}" value={quoteattr(label)} style="rounded=1;whiteSpace=wrap;html=1;fillColor={TEAL};strokeColor=none;align=left;spacingLeft=14;fontColor=#FFFFFF;fontSize=14;" vertex="1" parent="1">'
               f'<mxGeometry x="{x}" y="92" width="{w}" height="46" as="geometry"/></mxCell>')


svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Raleway, \'Helvetica Neue\', Arial, sans-serif">')
svg.append(f'<rect width="{W}" height="{H}" fill="#F4F6F7"/><rect width="{W}" height="76" fill="{DEEP}"/>')
svg.append('<text x="40" y="36" font-size="26" font-weight="700" fill="#FFFFFF">How the dashboard numbers are made</text>')
svg.append('<text x="40" y="60" font-size="14" fill="#CFE3E6">Programme staff type the data once. The scripts clean it and build six dashboard-ready tables. The dashboard only reads those tables.</text>')
dio.append(f'<mxCell id="title" value={quoteattr("<b>How the dashboard numbers are made</b><br>Programme staff type the data once. The scripts clean it and build six dashboard-ready tables. The dashboard only reads those tables.")} '
           f'style="text;html=1;align=left;fontSize=16;fontColor={DEEP};" vertex="1" parent="1"><mxGeometry x="40" y="14" width="1000" height="60" as="geometry"/></mxCell>')
band(SX, SW, '1  Where staff type', 'APFP Central Administration workbook')
band(TX, TW, '2  Dashboard-ready tables', 'cleaned and combined by the scripts')
band(PX, PW, '3  Where you see it', 'Looker Studio dashboard pages')

edges_svg = []
edges_dio = []


def edge(a, b, x1, y1, x2, y2, color, dashed=False):
    mx = (x1 + x2) / 2
    dash = ' stroke-dasharray="7 5"' if dashed else ''
    edges_svg.append(f'<path d="M{x1},{y1} C{mx},{y1} {mx},{y2} {x2},{y2}" fill="none" stroke="{color}" stroke-width="2.2" opacity="0.8"{dash}/>'
                     f'<circle cx="{x2}" cy="{y2}" r="4" fill="{color}"/>')
    edges_dio.append((a, b, color, dashed))


for t, tabs in tab_to_table.items():
    k = 0
    for src in SOURCES:
        if src[0] in tabs:
            k += 1
    j = 0
    for src in SOURCES:
        if src[0] in tabs:
            off = (j - (k - 1) / 2) * 7
            edge(src[0], t, SX + SW, sy[src[0]] + NH / 2, TX, ty[t] + NH / 2 + off, col[t])
            j += 1
# fct6 built from fct1
svg_note_y = ty['fct6_grantee_annual_info']
edge('fct1_grant_portfolio', 'fct6_grantee_annual_info', TX + TW - 60, ty['fct1_grant_portfolio'] + NH, TX + TW - 60, ty['fct6_grantee_annual_info'], '#5F6C77', True)
for (t, p), ids in table_to_page.items():
    pass
per_page = {}
for (t, p), ids in table_to_page.items():
    per_page.setdefault(p, []).append((t, ids))
for p, lst in per_page.items():
    k = len(lst)
    for j, (t, ids) in enumerate(sorted(lst, key=lambda x: [tt for tt, _ in TABLES].index(x[0]))):
        off = (j - (k - 1) / 2) * 9
        edge(t, 'page:' + p, TX + TW, ty[t] + NH / 2, PX, py[p] + 38 + off, col[t])

for src in SOURCES:
    box(src[0], SX, sy[src[0]], SW, NH, src[1], f'{src[0]}  ·  {src[2]}', '#FFFFFF', '#B9C5CB')
for t, c in TABLES:
    box(t, TX, ty[t], TW, NH, TABLE_TEXT[t][0], TABLE_TEXT[t][1], '#FFFFFF', c, bar=c)
for p in PAGES:
    ids = sum((v for (t, pp), v in table_to_page.items() if pp == p), [])
    box('page:' + p, PX, py[p], PW, 76, p, f'{PAGE_NOTE[p]}  ·  {len(ids)} charts', '#E2F2F4', '#9CC9D0')

svg.extend(edges_svg)
# re-draw nodes above edges: simplest is to emit edges first, so reorder
body = [x for x in svg if not x.startswith('<svg')]
head = svg[0]
node_lines = [x for x in body if x not in edges_svg]
final = [head] + [x for x in node_lines[:2]] + edges_svg + node_lines[2:] + []
foot_y = top + 8 * 84 + 20
final += [f'<rect x="40" y="{foot_y}" width="{W-80}" height="92" rx="10" fill="#FFFFFF" stroke="#CBD5DA"/>',
          f'<text x="60" y="{foot_y+28}" font-size="15" font-weight="700" fill="{DEEP}">Want the detail?</text>',
          f'<text x="60" y="{foot_y+52}" font-size="13" fill="{MUTED}">Data_Dictionary tab: every column, what it holds, which source tab and column it comes from, which charts use it.</text>',
          f'<text x="60" y="{foot_y+72}" font-size="13" fill="{MUTED}">Chart_Passport tab: every chart, what it shows, its filter, the table and the source tabs behind it. Both are rebuilt on every pipeline run.</text>',
          '</svg>']
os.makedirs(os.path.join(HERE, 'story'), exist_ok=True)
open(os.path.join(HERE, 'story', 'APFP_Data_Story.svg'), 'w', encoding='utf-8').write('\n'.join(final))

# drawio: connect to shapes so arrows follow when moved
eid = 0
for a, b, color, dashed in edges_dio:
    eid += 1
    st = f'edgeStyle=orthogonalEdgeStyle;curved=1;rounded=1;html=1;strokeColor={color};strokeWidth=2;endArrow=oval;endFill=1;{"dashed=1;" if dashed else ""}'
    dio.append(f'<mxCell id="e{eid}" style="{st}" edge="1" parent="1" source="{vid[a]}" target="{vid[b]}"><mxGeometry relative="1" as="geometry"/></mxCell>')
foot = ('<b>Want the detail?</b><br>Data_Dictionary tab: every column, what it holds, where it comes from, which charts use it.<br>'
        'Chart_Passport tab: every chart, what it shows, its filter, the table and the source tabs. Both are rebuilt on every pipeline run.')
dio.append(f'<mxCell id="foot" value={quoteattr(foot)} style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#CBD5DA;align=left;spacingLeft=16;fontSize=13;fontColor={MUTED};" vertex="1" parent="1">'
           f'<mxGeometry x="40" y="{foot_y}" width="{W-80}" height="92" as="geometry"/></mxCell>')
xml = (f'<mxfile host="app.diagrams.net"><diagram name="How the dashboard numbers are made" id="story"><mxGraphModel dx="1500" dy="960" grid="1" gridSize="10" page="1" pageWidth="{W}" pageHeight="{H}">'
       f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>' + ''.join(dio) + '</root></mxGraphModel></diagram></mxfile>')
open(os.path.join(HERE, 'story', 'APFP_Data_Story.drawio'), 'w', encoding='utf-8').write(xml)
print('ok', len(edges_dio), 'arrows')
