import sys
from xml.sax.saxutils import escape as esc
out = sys.argv[1]
W, H = 1720, 1150
FONT = "Raleway, 'Helvetica Neue', Helvetica, Arial, sans-serif"
INK, MUTED, TEAL, DEEP = '#1E2838', '#5F6C77', '#167C88', '#0E4A5C'

# (source tab, stg tab, grain)
STG = [
 ('8. Grant Registry',          'stg_grants',            'grant_id'),
 ('9. Organisation Registry',   'stg_organisations',     'organization_id'),
 ('4. Decision Tracker',        'stg_decisions',         'grant_id'),
 ('2. Outcome Progress',        'stg_outcome_progress',  'grant_id x outcome_id'),
 ('7. Organisation Maturity',   'stg_maturity',          'grant_id x aspect x indicator'),
 ('3. Support',                 'stg_support',           'support request'),
 ('6. Committed & Spent Tracker','stg_disbursements',    'disbursement_id'),
 ('5. Dividends',               'stg_dividends',         'financial_year'),
]
FCT = [
 ('fct1_grant_portfolio',  'one row per grant',                      '#167C88', 'Pages 1 to 5 (all views)'),
 ('fct6_grantee_annual_info','one row per grant x metric',            '#5F6C77', '4.02'),
 ('fct2_outcome_progress', 'grant x outcome x quarter',              '#EB6834', '1.12, 4.06'),
 ('fct5_maturity_rag',     'grant x aspect x indicator',             '#8A6A2F', '1.13, 4.04'),
 ('fct3_support_activity', 'one row per support request',            '#4A3AA7', '1.04, 1.14, 1.15, 4.07'),
 ('fct4_budget_year',      'one row per financial year',             '#E87BA4', '2.01-2.04, 2.09-2.12'),
]
READS = {  # fct -> stg tables it reads
 'fct1_grant_portfolio': ['stg_grants','stg_organisations','stg_decisions','stg_outcome_progress','stg_maturity','stg_disbursements'],
 'fct2_outcome_progress': ['stg_grants','stg_outcome_progress'],
 'fct5_maturity_rag': ['stg_grants','stg_maturity'],
 'fct3_support_activity': ['stg_grants','stg_support'],
 'fct4_budget_year': ['stg_disbursements','stg_dividends'],
}
SRC_X, STG_X, FCT_X, LKR_X = 50, 470, 940, 1370
NW, NH = 300, 58
LW = 300
y0, dy = 190, 80
stg_y = {s[1]: y0 + i*dy for i, s in enumerate(STG)}
fy0, fdy = 175, 112
fct_y = {f[0]: fy0 + j*fdy for j, f in enumerate(FCT)}

o = []
a = o.append
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">')
a('<defs>')
for name, c in [(f[0], f[2]) for f in FCT] + [('grey', '#8A97A1')]:
    a(f'<marker id="ar_{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>')
a('</defs>')
a(f'<rect width="{W}" height="{H}" fill="#F4F6F7"/>')
a(f'<rect x="0" y="0" width="{W}" height="86" fill="{DEEP}"/>')
a(f'<text x="40" y="38" font-size="28" font-weight="700" fill="#FFFFFF">APFP data lineage</text>')
a(f'<text x="40" y="66" font-size="15" fill="#CFE3E6">APFP Central Administration workbook  →  stg_ (staging)  →  fct_ (final)  →  Looker Studio. No int_ (intermediate) layer: every fct_ table is built directly from stg_ tables.</text>')

def col_header(x, w, title, sub):
    a(f'<rect x="{x}" y="104" width="{w}" height="52" rx="8" fill="{TEAL}"/>')
    a(f'<text x="{x+16}" y="127" font-size="16" font-weight="700" fill="#FFFFFF">{title}</text>')
    a(f'<text x="{x+16}" y="146" font-size="12" fill="#E2F2F4">{sub}</text>')
col_header(SRC_X, NW, 'SOURCE', 'APFP Central Administration workbook (8 tabs)')
col_header(STG_X, NW, 'STAGING  (stg_)', 'one per source tab: clean, rename, cast')
col_header(FCT_X, NW, 'FINAL  (fct_)', 'joins, derived fields, dashboard shape')
col_header(LKR_X, LW, 'LOOKER STUDIO', 'one data source per fct_ table')

# source group frame
top = y0 - 16; bot = y0 + 7*dy + NH + 16
a(f'<rect x="{SRC_X-14}" y="{top}" width="{NW+28}" height="{bot-top}" rx="10" fill="#FFFFFF" stroke="#CBD5DA" stroke-dasharray="5 4"/>')

def node(x, y, w, title, sub, fill='#FFFFFF', stroke='#CBD5DA', tc=INK, sc=MUTED, bar=None):
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{NH}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')
    if bar: a(f'<rect x="{x}" y="{y}" width="7" height="{NH}" rx="3" fill="{bar}"/>')
    a(f'<text x="{x+18}" y="{y+25}" font-size="15" font-weight="700" fill="{tc}">{esc(title)}</text>')
    a(f'<text x="{x+18}" y="{y+44}" font-size="12" fill="{sc}">{esc(sub)}</text>')

# edges first (under nodes)
for s, t, g in STG:
    y = stg_y[t] + NH/2
    a(f'<path d="M{SRC_X+NW},{y} L{STG_X-4},{y}" stroke="#8A97A1" stroke-width="2" fill="none" marker-end="url(#ar_grey)"/>')
colors = {f[0]: f[2] for f in FCT}
for fct, stgs in READS.items():
    fy = fct_y[fct] + NH/2
    n = len(stgs)
    for k, st in enumerate(stgs):
        sy = stg_y[st] + NH/2
        ty = fy + (k - (n-1)/2) * 6
        x1, x2 = STG_X+NW, FCT_X-4
        mx = (x1+x2)/2
        a(f'<path d="M{x1},{sy} C{mx},{sy} {mx},{ty} {x2},{ty}" stroke="{colors[fct]}" stroke-width="2" fill="none" opacity="0.85" marker-end="url(#ar_{fct})"/>')
# fct1 -> fct6
y1 = fct_y['fct1_grant_portfolio'] + NH
y6 = fct_y['fct6_grantee_annual_info']
a(f'<path d="M{FCT_X+NW-40},{y1} L{FCT_X+NW-40},{y6-4}" stroke="#5F6C77" stroke-width="2.4" stroke-dasharray="6 4" fill="none" marker-end="url(#ar_fct6_grantee_annual_info)"/>')
a(f'<text x="{FCT_X+NW-32}" y="{(y1+y6)/2+4}" font-size="11" fill="#5F6C77">reshaped from fct1</text>')
# fct -> looker
for f in FCT:
    y = fct_y[f[0]] + NH/2
    a(f'<path d="M{FCT_X+NW},{y} L{LKR_X-4},{y}" stroke="{f[2]}" stroke-width="2.4" fill="none" marker-end="url(#ar_{f[0]})"/>')

for s, t, g in STG:
    node(SRC_X, stg_y[t], NW, s, 'source tab', stroke='#B9C5CB')
    node(STG_X, stg_y[t], NW, t, 'grain: ' + g, fill='#E2F2F4', stroke='#9CC9D0')
for f in FCT:
    node(FCT_X, fct_y[f[0]], NW, f[0], f[1], fill='#FFFFFF', stroke=f[2], bar=f[2])
    node(LKR_X, fct_y[f[0]], LW, 'charts: ' + f[3], 'data source ' + f[0].split('_')[0], fill='#FFFFFF', stroke='#CBD5DA')
# all-years note
ay = fct_y['fct4_budget_year'] + NH + 30
a(f'<text x="{LKR_X}" y="{ay}" font-size="12" fill="{MUTED}">fct1 is also added a second time ("all years") so</text>')
a(f'<text x="{LKR_X}" y="{ay+16}" font-size="12" fill="{MUTED}">the year-over-year charts ignore the Financial Year</text>')
a(f'<text x="{LKR_X}" y="{ay+32}" font-size="12" fill="{MUTED}">control: 1.16, 2.08, 4.03, 4.05.</text>')

# bottom lane: controls
by = bot + 72
a(f'<rect x="40" y="{by}" width="{W-80}" height="212" rx="10" fill="#FFFFFF" stroke="#CBD5DA"/>')
a(f'<text x="60" y="{by+28}" font-size="16" font-weight="700" fill="{DEEP}">How it runs and how it is checked  (Apps Script, function runCompletePipeline, run by hand)</text>')
steps = [
 ('1  alignTimeZones', 'pipeline workbook time zone = script time zone'),
 ('2  Source Header Check', 'compares source headers with ref_source_header_baseline; writes Source_Header_Audit; stops the run on a missing or renamed column and emails the owner'),
 ('3  Staging layer', '8 build functions: read a source tab, keep and rename columns, cast types, normalise FY to "FY 26-27"'),
 ('4  Final layer', '6 build functions: fct1, fct2, fct3, fct4, fct5, then fct6 (reads fct1)'),
 ('5  Cardinality tests', 'key uniqueness, no blank keys, grant ids exist in stg_grants; result in Cardinality Test Results'),
]
bx = 60; bw = (W-120-4*16)/5
import textwrap
for i, (t, d) in enumerate(steps):
    x = bx + i*(bw+16)
    a(f'<rect x="{x}" y="{by+44}" width="{bw}" height="124" rx="8" fill="#F4F6F9" stroke="#D9E1E5"/>')
    a(f'<text x="{x+12}" y="{by+66}" font-size="13.5" font-weight="700" fill="{INK}">{esc(t)}</text>')
    for k, line in enumerate(textwrap.wrap(d, 38)):
        a(f'<text x="{x+12}" y="{by+86+k*16}" font-size="11.5" fill="{MUTED}">{esc(line)}</text>')
    if i < 4:
        a(f'<text x="{x+bw+1}" y="{by+104}" font-size="16" fill="{TEAL}">›</text>')
a(f'<text x="60" y="{by+190}" font-size="11.5" fill="{MUTED}">Support tabs: Index (all tab names, nothing hard-coded), Pipeline Log (one row per build function: rows written, duration, SUCCESS / ERROR). Edge colour = the fct_ table that reads the stg_ table; grey edges are 1 to 1 source to staging.</text>')
a('</svg>')
open(out, 'w').write('\n'.join(o))
print('ok', out)
