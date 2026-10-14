#!/usr/bin/env python3
"""
Builds docs/lineage/APFP_Data_Lineage.drawio (and a PNG-ready SVG per page) from
  - code_columns.json   (real column lists, exported from the scripts by export_model.js)
  - lineage_model.py    (which column feeds which, plain-language rules, metrics, worked examples)

Usage:  python3 docs/lineage/build_drawio.py [--out docs/lineage/APFP_Data_Lineage.drawio] [--svg-dir DIR]
Standard library only. The .drawio file is plain (uncompressed) XML and opens in app.diagrams.net,
the draw.io desktop app, or from Google Drive. After the first build the diagram is edited by hand in draw.io;
re-run this script only to start a page again (it overwrites the output file).
"""
import json
import os
import re
import sys
import textwrap
from xml.sax.saxutils import escape, quoteattr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lineage_model as LM  # noqa: E402

CODE = json.load(open(os.path.join(HERE, 'code_columns.json'), encoding='utf-8'))

# ------------------------------------------------------------------ look and feel
INK, MUTED, TEAL, DEEP, SLATE = '#1E2838', '#5F6C77', '#167C88', '#0E4A5C', '#5F6C77'
FILL = {'key': '#E1D5E7', 'text': '#FFFFFF', 'number': '#FFF2CC', 'date': '#DAE8FC', 'flag': '#D5E8D4', 'display': '#F8CECC', 'helper': '#E8ECEF'}
KIND_NAME = {'key': 'Identifier (a key)', 'text': 'Text / grouping field', 'number': 'Number', 'date': 'Date', 'flag': 'True / false flag',
             'display': 'Ready-to-show text', 'helper': 'Sort helper'}
EDGE = {'copy': ('#8A97A1', False, 'Copied as entered'), 'join': (TEAL, False, 'Looked up from another table by a key'),
        'calc': ('#EB6834', True, 'Calculated (the ƒ sign marks a calculated column)')}
HEAD_H, ROW_H = 46, 36
NAME_W, TYPE_W, RULE_W = 240, 86, 330

NUMERIC_FCT = set('''primary_beneficiary_count team_size attrition_rate foreign_contribution_rate core_policies_met_count core_policies_total_count
annual_budget approved_amount committed_amount disbursed_amount proposed_amount total_outcomes_count achieved_outcomes_count cost_per_beneficiary
target_value achieved_value outcome_achievement_pct final_actual_value annual_achievement_pct dividend_income prior_year_carry_forward
available_budget annual_committed_funding next_year_q1_committed_funding annual_disbursed_funding unallocated_balance metric_order'''.split())
DISPLAY_FCT = set('grant_period grant_status_type_amount sub_category_line funding_year current_value previous_value'.split())
DATE_FCT = set('grant_start_date grant_end_date decision_due_date as_of_date planned_date actual_date'.split())


def humanise(name):
    words = name.replace('organization', 'organisation').split('_')
    out = []
    for w in words:
        lw = w.lower()
        out.append({'id': 'ID', 'fy': 'FY', 'fcra': 'FCRA', 'posh': 'POSH', 'pct': '%', 'q1': 'Q1', 'q2': 'Q2', 'q3': 'Q3', 'q4': 'Q4', 'ids': 'IDs'}.get(lw, w))
    s = ' '.join(out)
    return s[0].upper() + s[1:]


def kind_of(name, stype=None):
    if re.search(r'(^|_)id$', name) and name not in ('metric_order',):
        return 'key'
    if name.startswith('is_') or name.startswith('has_'):
        return 'flag'
    if name.endswith('_order') or name == 'aspect_display':
        return 'helper'
    if name in DISPLAY_FCT:
        return 'display'
    if stype == 'date' or name in DATE_FCT or name.endswith('_date'):
        return 'date'
    if stype in ('number', 'rate') or name in NUMERIC_FCT:
        return 'number'
    return 'text'


def type_label(kind, calc=False):
    t = {'key': 'text', 'text': 'text', 'number': 'number', 'date': 'date', 'flag': 'true / false', 'display': 'text', 'helper': 'number'}[kind]
    return t + (' ƒ' if calc else '')


# ------------------------------------------------------------------ scene model
class Scene:
    def __init__(self, name):
        self.name = name
        self.items = []      # drawing order
        self.cells = {}      # id -> (x, y, w, h) absolute
        self.edges = []
        self.n = 0

    def nid(self, prefix='c'):
        self.n += 1
        return f'{prefix}{self.n}'

    def box(self, x, y, w, h, title='', body=None, fill='#FFFFFF', stroke='#B9C5CB', tcolor=INK, tsize=14, bsize=11, bold=True, dashed=False, align='left', tech=None):
        bid = self.nid('b')
        self.cells[bid] = (x, y, w, h)
        self.items.append({'t': 'box', 'id': bid, 'x': x, 'y': y, 'w': w, 'h': h, 'title': title, 'body': body or [], 'fill': fill, 'stroke': stroke,
                           'tcolor': tcolor, 'tsize': tsize, 'bsize': bsize, 'bold': bold, 'dashed': dashed, 'align': align, 'tech': tech})
        return bid

    def text(self, x, y, w, h, lines, size=12, color=INK, bold=False):
        tid = self.nid('t')
        self.cells[tid] = (x, y, w, h)
        self.items.append({'t': 'text', 'id': tid, 'x': x, 'y': y, 'w': w, 'h': h, 'lines': lines, 'size': size, 'color': color, 'bold': bold})
        return tid

    def table(self, x, y, title, tech, rows, head_fill, widths=(NAME_W, TYPE_W), row_h=ROW_H, subtitle=None, table_key=None, dot_w=0, fs=10):
        """rows: list of dict(label, tech, type, kind, rule(optional), key)"""
        tid = self.nid('T')
        w = sum(widths)
        h = HEAD_H + len(rows) * row_h
        self.cells[tid] = (x, y, w, h)
        rowinfo = []
        for i, r in enumerate(rows):
            ry = y + HEAD_H + i * row_h
            cells = []
            cx = x
            for j, cw in enumerate(widths):
                cid = self.nid('r')
                self.cells[cid] = (cx, ry, cw, row_h)
                cells.append(cid)
                cx += cw
            r['cells'] = cells
            r['y'] = ry
            rowinfo.append(r)
        self.items.append({'t': 'table', 'id': tid, 'x': x, 'y': y, 'w': w, 'h': h, 'title': title, 'tech': tech, 'subtitle': subtitle, 'rows': rowinfo,
                           'head_fill': head_fill, 'widths': widths, 'row_h': row_h, 'key': table_key, 'dot_w': dot_w, 'fs': fs})
        return {'id': tid, 'x': x, 'y': y, 'w': w, 'h': h, 'rows': rowinfo, 'by_key': {r['key']: r for r in rowinfo if r.get('key')}}

    def edge(self, src, tgt, cat='copy', label=None, color=None, dashed=None, width=1.6):
        c, dsh, _ = EDGE.get(cat, EDGE['copy'])
        self.edges.append({'src': src, 'tgt': tgt, 'color': color or c, 'dashed': dsh if dashed is None else dashed, 'label': label, 'width': width})

    def bounds(self):
        xs = [c[0] + c[2] for c in self.cells.values()]
        ys = [c[1] + c[3] for c in self.cells.values()]
        return max(xs) + 60, max(ys) + 60


def row_dict(label, tech, kind, calc=False, rule=None, key=None, type_text=None):
    return {'label': label, 'tech': tech, 'kind': kind, 'type': type_text or type_label(kind, calc), 'calc': calc, 'rule': rule, 'key': key}


def stg_rows(table):
    spec = CODE['staging'][table]
    rows = []
    for c in spec['columns']:
        k = kind_of(c['name'], c['type'])
        rows.append(row_dict(humanise(c['name']), c['name'], k, key=c['name'], type_text=type_label(k)))
    return rows


def src_rows(table):
    spec = CODE['staging'][table]
    rows = []
    for c in spec['columns']:
        k = kind_of(c['name'], c['type'])
        rows.append(row_dict(c['source_header'], None, k, key=c['name'], type_text=type_label(k)))
    return rows


def final_rows(table, with_rule=True):
    cols = CODE['final'][table]
    model = {c[0]: c for c in LM.FINAL[table]}
    rows = []
    for name in cols:
        cat, ups, rule = (model[name][1], model[name][2], model[name][3]) if name in model else ('copy', [], '(describe this column)')
        k = kind_of(name)
        calc = cat == 'calc'
        rows.append(row_dict(humanise(name), name, k, calc=calc, rule=rule if with_rule else None, key=name))
    return rows


def legend(sc, x, y):
    """Colour and arrow key, compact."""
    sc.box(x, y, 330, 36 + 7 * 24 + 8 + 3 * 28 + 10, 'Key', [], fill='#FFFFFF', stroke='#CBD5DA', tsize=13)
    yy = y + 34
    for k in ('key', 'text', 'number', 'date', 'flag', 'display', 'helper'):
        sc.box(x + 14, yy, 36, 18, '', [], fill=FILL[k], stroke='#9AA7B0')
        sc.text(x + 60, yy - 1, 260, 20, [KIND_NAME[k]], size=11)
        yy += 24
    yy += 6
    for cat in ('copy', 'join', 'calc'):
        a = sc.box(x + 14, yy, 30, 16, '', [], fill='#FFFFFF', stroke='#9AA7B0')
        b = sc.box(x + 120, yy, 30, 16, '', [], fill='#FFFFFF', stroke='#9AA7B0')
        sc.edge(a, b, cat)
        sc.text(x + 160, yy - 2, 170, 30, [EDGE[cat][2]], size=10)
        yy += 28


# ------------------------------------------------------------------ pages
def page_stack():
    sc = Scene('1. How the pieces fit')
    sc.text(40, 20, 1500, 30, ['How the pieces fit'], size=26, color=DEEP, bold=True)
    sc.text(40, 56, 1500, 24, ['Where the data is typed, what changes it, where it is stored and where people see it. Plain words first; technical names are in brackets.'], size=13, color=MUTED)
    y = 130
    people = sc.box(40, y, 260, 140, 'Programme teams', ['Enter and update grants, outcomes, support requests, decisions and payments.'], fill='#F4F6F9', stroke='#B9C5CB')
    src = sc.box(370, y, 280, 140, 'APFP Central Administration', ['Google Sheets workbook, 8 tabs.', 'The only place data is typed in. The pipeline never changes it.'], fill='#FFF2CC', stroke='#D6B656')
    scr = sc.box(720, y, 300, 140, 'Pipeline scripts', ['Google Apps Script, run on demand.', '1 Check the source columns  2 Clean each tab', '3 Build the dashboard tables  4 Run the tests'], fill='#DAE8FC', stroke='#6C8EBF')
    wb = sc.box(1090, y, 300, 140, 'Data Pipeline workbook', ['Google Sheets workbook.', 'Cleaned tabs (stg_) and dashboard-ready tabs (fct_), plus Index, Pipeline Log and test results.'], fill='#D5E8D4', stroke='#82B366')
    dash = sc.box(1460, y, 280, 140, 'Looker Studio dashboard', ['5 pages: Guide, Portfolio Overview, Funding Allocation, Decision Queue, Grantee 360.'], fill='#E1D5E7', stroke='#9673A6')
    sc.edge(people, src, 'copy', label='type data', color=SLATE, dashed=False)
    sc.edge(src, scr, 'copy', label='read', color=SLATE, dashed=False)
    sc.edge(scr, wb, 'copy', label='write', color=SLATE, dashed=False)
    sc.edge(wb, dash, 'copy', label='read', color=SLATE, dashed=False)
    y2 = 360
    gh = sc.box(720, y2, 300, 110, 'GitHub', ['Keeps the code and every change (who, when, why).', 'clasp copies the code into Apps Script.'], fill='#F4F6F9', stroke='#B9C5CB')
    sc.edge(gh, scr, 'copy', label='clasp push', color=SLATE, dashed=False)
    ctl = sc.box(1090, y2, 300, 110, 'Control tabs in the workbook', ['Index (all tab names), Pipeline Log (every run),', 'Source_Header_Audit, Cardinality Test Results.'], fill='#F4F6F9', stroke='#B9C5CB')
    sc.edge(wb, ctl, 'copy', label='holds', color=SLATE, dashed=False)
    sc.box(40, 360, 600, 150, 'Good to know', ['The pipeline is run by hand today; there is no schedule.', 'If a source column is renamed or removed, the run stops and the owner is emailed, so a broken column never reaches the dashboard.', 'There is no intermediate layer: each dashboard table is built directly from the cleaned tables.'], fill='#FFFFFF', stroke='#167C88', bold=True)
    return sc


def page_journey():
    sc = Scene('2. The journey of the data')
    sc.text(40, 20, 1500, 30, ['The journey of the data'], size=26, color=DEEP, bold=True)
    sc.text(40, 56, 1500, 24, ['Four steps from what people type to what the dashboard shows. Each step is its own set of tabs, so a problem can be traced to one step.'], size=13, color=MUTED)
    cols = [
        ('Source', '8 tabs, Central Administration workbook', SLATE, ['Typed by people.', 'Never changed by the pipeline.'], [LM.TABLE_INFO[t][0] for t in ('8. Grant Registry', '9. Organisation Registry', '4. Decision Tracker', '2. Outcome Progress', '7. Organisation Maturity', '3. Support', '6. Committed & Spent Tracker', '5. Dividends')]),
        ('Staging', '8 tables, prefix stg_', TEAL, ['A cleaned copy of each source tab:', 'keep the columns we use, simple names,', 'right data types, years as FY 26-27.', 'No joins, no calculations.'], [t + '  (' + LM.TABLE_INFO[t][0] + ')' for t in CODE['staging']]),
        ('Final', '6 tables, prefix fct_', DEEP, ['Dashboard-ready tables:', 'join the cleaned tables, calculate,', 'build ready-to-show text and sort numbers.', 'Each is built straight from staging.'], [t + '  (' + LM.TABLE_INFO[t][0] + ')' for t in CODE['final']]),
        ('Dashboard', 'Looker Studio, 5 pages', '#245563', ['One data source per final table.', 'Metrics count and add the final columns;', 'filters choose the year, status or organisation.'], ['Guide', 'Portfolio Overview', 'Funding Allocation', 'Decision Queue', 'Grantee 360']),
    ]
    x = 40
    ids = []
    for title, sub, color, what, items in cols:
        sc.box(x, 110, 380, 70, title, [sub], fill=color, stroke=color, tcolor='#FFFFFF', tsize=18, bsize=12)
        # recolour body text for dark header: handled by tcolor only for the title, body drawn white via flag
        sc.items[-1]['bcolor'] = '#E2F2F4'
        sc.box(x, 196, 380, 120, 'What happens here', what, fill='#FFFFFF', stroke='#CBD5DA', tsize=13)
        ids.append(sc.box(x, 332, 380, 36 + 24 * len(items) + 10, 'Tabs', items, fill='#F4F6F9', stroke='#CBD5DA', tsize=13))
        x += 450
    for a, b in zip(ids, ids[1:]):
        sc.edge(a, b, 'copy', color=TEAL, dashed=False, width=2.4)
    sc.box(40, 700, 1760, 90, 'Why there is no intermediate layer', ['An intermediate layer is useful when the same joined data is needed by several final tables. Here every final table is one readable join of cleaned tables, so the extra step would only add tabs.', 'One final table (annual information, fct6) is reshaped from the grant portfolio (fct1); if a second table needs the same reshaping, that is the time to add one.'], fill='#E2F2F4', stroke=TEAL, bsize=12)
    return sc


def page_source():
    sc = Scene('3. Source: what we read')
    sc.text(40, 20, 1700, 30, ['Source: what we read'], size=26, color=DEEP, bold=True)
    sc.text(40, 56, 1700, 24, ['The columns of the APFP Central Administration workbook that the pipeline uses. Other columns in the workbook are not read.'], size=13, color=MUTED)
    order = ['stg_grants', 'stg_organisations', 'stg_decisions', 'stg_support', 'stg_outcome_progress', 'stg_disbursements', 'stg_maturity', 'stg_dividends']
    pos = [(40, 110), (460, 110), (880, 110), (1300, 110), (40, 1050), (460, 1050), (880, 1050), (1300, 1050)]
    for t, (x, y) in zip(order, pos):
        tab = CODE['staging'][t]['source_tab']
        sc.table(x, y, tab, None, src_rows(t), SLATE, subtitle=LM.TABLE_INFO[tab][1], widths=(260, 80))
    legend(sc, 1300, 700)
    return sc


def stg_pair_page(name, tables, subtitle):
    sc = Scene(name)
    sc.text(40, 20, 1500, 30, [name.split('. ', 1)[1]], size=26, color=DEEP, bold=True)
    sc.text(40, 56, 1500, 24, [subtitle], size=13, color=MUTED)
    y = 110
    for t in tables:
        tab = CODE['staging'][t]['source_tab']
        left = sc.table(40, y, tab, None, src_rows(t), SLATE, subtitle='source tab', widths=(280, 80))
        right = sc.table(620, y, LM.TABLE_INFO[t][0], t, stg_rows(t), TEAL, subtitle=t, widths=(NAME_W, TYPE_W))
        for lr, rr in zip(left['rows'], right['rows']):
            sc.edge(lr['cells'][-1], rr['cells'][0], 'copy')
        y += HEAD_H + len(left['rows']) * ROW_H + 70
    legend(sc, 1010, 110)
    sc.box(1010, 470, 330, 200, 'What staging does', ['Keeps the columns the dashboard needs.', 'Renames them in simple lower-case words.', 'Sets the right type (text, number, date).', 'Writes years as FY 26-27; 8% becomes 0.08.', 'Does not join or calculate.'], fill='#E2F2F4', stroke=TEAL, bsize=12)
    return sc


def box_h(w, title, body, tsize=12, bsize=10):
    n = sum(len(textwrap.wrap(b, max(8, int((w - 24) / (bsize * 0.56)))) or ['']) for b in body)
    return int(16 + tsize + 10 + n * (bsize + 5) + 12)


def page_index():
    sc = Scene('7. Final tables: index')
    sc.text(40, 20, 1700, 30, ['Final tables: index'], size=26, color=DEEP, bold=True)
    sc.text(40, 56, 1700, 24, ['Every column of the six dashboard-ready tables, with the charts each table feeds. Details of where each column comes from are on the next pages.'], size=13, color=MUTED)
    columns = [(40, ['fct1_grant_portfolio']), (470, ['fct2_outcome_progress', 'fct3_support_activity']),
               (900, ['fct5_maturity_rag', 'fct6_grantee_annual_info', 'fct4_budget_year'])]
    for x, tables in columns:
        y = 110
        for t in tables:
            w = NAME_W + TYPE_W
            body = [LM.TABLE_INFO[t][1] + '.', 'Shown in: ' + ', '.join(LM.FEEDS[t])]
            h = box_h(w, 'About this table', body)
            sc.box(x, y, w, h, 'About this table', body, fill='#E2F2F4', stroke=TEAL, tsize=12, bsize=10)
            tb = sc.table(x, y + h + 10, LM.TABLE_INFO[t][0], t, final_rows(t, with_rule=False), DEEP, subtitle=t)
            y = tb['y'] + tb['h'] + 50
    legend(sc, 1330, 110)
    return sc


def stg_cols_used(table):
    used = {}
    for col, cat, ups, rule in LM.FINAL[table]:
        for u in ups:
            t, c = u.split('.', 1)
            used.setdefault(t, {})
            used[t].setdefault(c, len(used[t]) + 1000 * 0)
    return used


def page_final(table, num):
    info = LM.TABLE_INFO[table]
    sc = Scene(f'{num}. Staging to final: {info[0]}')
    sc.text(40, 20, 1800, 30, [f'Staging to final: {info[0]}  ({table})'], size=24, color=DEEP, bold=True)
    sc.text(40, 54, 1800, 22, [info[1] + '.'], size=13, color=MUTED)
    sc.text(40, 76, 1800, 22, ['Feeds: ' + ', '.join(LM.FEEDS[table])], size=12, color=TEAL)
    model = LM.FINAL[table]
    # order of use: first final column index that uses each upstream column
    first = {}
    for i, (col, cat, ups, rule) in enumerate(model):
        for u in ups:
            first.setdefault(u, i)
    tables = {}
    for u, i in first.items():
        t, c = u.split('.', 1)
        tables.setdefault(t, []).append((i, c))
    order = sorted(tables, key=lambda t: sum(i for i, _ in tables[t]) / len(tables[t]))
    x_left, x_right = 40, 560
    y = 120
    placed = {}
    for t in order:
        cols = [c for i, c in sorted(tables[t])]
        if t.startswith('fct'):
            allrows = {r['key']: r for r in final_rows(t, with_rule=False)}
            rows = [allrows[c] for c in cols]
            title, head = LM.TABLE_INFO[t][0], DEEP
        else:
            allrows = {r['key']: r for r in stg_rows(t)}
            rows = [allrows[c] for c in cols]
            title, head = LM.TABLE_INFO[t][0], TEAL
        tb = sc.table(x_left, y, title, t, rows, head, subtitle=t + '  (columns used)', widths=(NAME_W, TYPE_W))
        placed[t] = tb
        y += HEAD_H + len(rows) * ROW_H + 40
    frows = final_rows(table, with_rule=True)
    ft = sc.table(x_right, 120, info[0], table, frows, DEEP, widths=(NAME_W, TYPE_W, RULE_W), row_h=42, subtitle=table + '  (all columns)')
    for (col, cat, ups, rule) in model:
        tgt = ft['by_key'][col]['cells'][0]
        for u in ups:
            t, c = u.split('.', 1)
            sc.edge(placed[t]['by_key'][c]['cells'][-1], tgt, cat)
    legend(sc, x_right + NAME_W + TYPE_W + RULE_W + 60, 120)
    return sc


def page_metrics():
    sc = Scene('14. From columns to dashboard numbers')
    sc.text(40, 20, 1800, 30, ['From columns to dashboard numbers'], size=26, color=DEEP, bold=True)
    sc.text(40, 56, 1800, 24, ['How the numbers on the dashboard are made: the final columns they use, a plain definition, and where they are shown. A chart-level filter (for example "active grants only") then narrows what is counted.'], size=13, color=MUTED)
    used = {}
    for m in LM.METRICS:
        for u in m[3]:
            t, c = u.split('.', 1)
            used.setdefault(t, [])
            if c not in used[t]:
                used[t].append(c)
    x_left, y = 40, 110
    placed = {}
    for t in ['fct1_grant_portfolio', 'fct2_outcome_progress', 'fct3_support_activity', 'fct4_budget_year']:
        if t not in used:
            continue
        allrows = {r['key']: r for r in final_rows(t, with_rule=False)}
        rows = [allrows[c] for c in used[t]]
        placed[t] = sc.table(x_left, y, LM.TABLE_INFO[t][0], t, rows, DEEP, subtitle=t + '  (columns used)')
        y += HEAD_H + len(rows) * ROW_H + 40
    my = 110
    for name, label, definition, ups, charts, filt in LM.METRICS:
        body = [definition]
        if filt:
            body.append('Filter: ' + filt)
        body.append('Field: ' + name)
        h = 40 + 17 * (sum(len(textwrap.wrap(b, 52)) for b in body)) + 14
        mb = sc.box(560, my, 400, h, label, body, fill='#FFF2CC', stroke='#D6B656', tsize=14, bsize=11)
        ch = ', '.join(c + ' ' + LM.CHART_NAMES.get(c, '') for c in charts)
        cb = sc.box(1060, my, 440, max(h, 60), 'Shown in', [ch], fill='#E1D5E7', stroke='#9673A6', tsize=12, bsize=10)
        sc.edge(mb, cb, 'copy', color=SLATE, dashed=False)
        for u in ups:
            t, c = u.split('.', 1)
            sc.edge(placed[t]['by_key'][c]['cells'][-1], mb, 'calc', color='#B9C5CB', dashed=False, width=1.2)
        my += max(h, 60) + 24
    return sc


def page_traces():
    sc = Scene('15. A number, step by step')
    sc.text(40, 20, 1800, 30, ['A number, step by step'], size=26, color=DEEP, bold=True)
    sc.text(40, 56, 1800, 24, ['Three examples followed from the source tab to the dashboard. No sample figures are shown on purpose; the path is what matters.'], size=13, color=MUTED)
    y = 110
    for tr in LM.TRACES:
        sc.text(40, y, 1800, 26, [tr['title']], size=16, color=DEEP, bold=True)
        x = 40
        prev = None
        fills = ['#FFF2CC', '#D5E8D4', '#DAE8FC', '#F8CECC', '#E1D5E7']
        for (stage, name, detail), f in zip(tr['steps'], fills):
            b = sc.box(x, y + 36, 320, 150, stage, [name, detail], fill=f, stroke='#9AA7B0', tsize=12, bsize=11)
            if prev:
                sc.edge(prev, b, 'copy', color=SLATE, dashed=False, width=2)
            prev = b
            x += 370
        y += 250
    return sc


def page_glossary():
    sc = Scene('16. Glossary and key')
    sc.text(40, 20, 1500, 30, ['Glossary and key'], size=26, color=DEEP, bold=True)
    terms = [
        ('Source', 'The Central Administration workbook where people type the data.'),
        ('Staging (stg_)', 'A cleaned copy of one source tab: simple names, right types, no calculations.'),
        ('Final (fct_)', 'A dashboard-ready table built from staging tables: joined, calculated, ready to show.'),
        ('Column and row', 'A column is one field (for example Approved amount); a row is one record (for example one grant).'),
        ('Grain', 'What one row means, for example one row per grant, or per grant and outcome and quarter.'),
        ('Key / identifier', 'A column that identifies a record or links two tables, such as Grant ID or Organisation ID.'),
        ('Flag', 'A true or false column, for example "is an active grant".'),
        ('Calculated column (ƒ)', 'A column worked out from other columns, not copied.'),
        ('Metric', 'A number on the dashboard made by counting or adding final columns, for example Grantees.'),
        ('Chart-level filter', 'A condition on one chart, for example "active grants only", so one metric serves many charts.'),
        ('Pipeline run', 'One go of the scripts: check, clean, build, test. Recorded in the Pipeline Log tab.'),
    ]
    y = 90
    for term, text in terms:
        sc.box(40, y, 260, 56, term, [], fill=DEEP, stroke=DEEP, tcolor='#FFFFFF', tsize=13)
        sc.box(310, y, 760, 56, '', [text], fill='#FFFFFF', stroke='#CBD5DA', bsize=12, bold=False)
        y += 66
    legend(sc, 1140, 90)
    sc.box(1140, 440, 330, 300, 'For the team: keeping this diagram right', ['1  Open this file in draw.io (app.diagrams.net).', '2  When a column is added, renamed or removed in the', '    scripts, add or edit the row on the matching page.', '3  Edit a row\'s details with Edit Data (Ctrl+M).', '4  Run  npm run lineage  to list columns that are in', '    the code but missing from the diagram.', '5  Export to PNG, SVG or PDF from File > Export as.'], fill='#E2F2F4', stroke=TEAL, bsize=11)
    return sc


def all_pages():
    pages = [page_stack(), page_journey(), page_source()]
    pages.append(stg_pair_page('4. Source to staging (1 of 3)', ['stg_grants', 'stg_organisations'], 'Each source column becomes one staging column. Arrows join the same position in both tables.'))
    pages.append(stg_pair_page('5. Source to staging (2 of 3)', ['stg_outcome_progress', 'stg_support', 'stg_decisions'], 'Each source column becomes one staging column. Quarters stay side by side until the final layer.'))
    pages.append(stg_pair_page('6. Source to staging (3 of 3)', ['stg_disbursements', 'stg_maturity', 'stg_dividends'], 'Each source column becomes one staging column.'))
    pages.append(page_index())
    for i, t in enumerate(['fct1_grant_portfolio', 'fct2_outcome_progress', 'fct3_support_activity', 'fct4_budget_year', 'fct5_maturity_rag', 'fct6_grantee_annual_info']):
        pages.append(page_final(t, 8 + i))
    pages += [page_metrics(), page_traces(), page_glossary()]
    return pages


# ------------------------------------------------------------------ draw.io emitter
def html_label(title, sub=None):
    s = '<b>' + escape(title) + '</b>'
    if sub:
        s += '<br><font style="font-size:9px" color="#5F6C77">' + escape(sub) + '</font>'
    return s


def drawio_page(sc, idx):
    cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']

    def vertex(cid, parent, x, y, w, h, style, value, props=None):
        geom = f'<mxGeometry x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" as="geometry"/>'
        cell = f'<mxCell style={quoteattr(style)} vertex="1" parent={quoteattr(parent)}>{geom}</mxCell>'
        attrs = f'label={quoteattr(value)} id={quoteattr(cid)}'
        for k, v in (props or {}).items():
            if v:
                attrs += f' {k}={quoteattr(str(v))}'
        return f'<object {attrs}>{cell}</object>'

    base = 'html=1;whiteSpace=wrap;fontFamily=Helvetica;'
    for it in sc.items:
        if it['t'] == 'box':
            body = '<br>'.join(escape(b) for b in it['body'])
            val = ''
            if it['title']:
                val = '<b style="font-size:%dpx">%s</b>' % (it['tsize'], escape(it['title']))
            if body:
                val += ('<br>' if val else '') + '<font style="font-size:%dpx" color="%s">%s</font>' % (it['bsize'], it.get('bcolor', MUTED), body)
            style = base + f"rounded=1;arcSize=6;fillColor={it['fill']};strokeColor={it['stroke']};fontColor={it['tcolor']};align=left;verticalAlign=top;spacing=8;spacingTop=6;" + ('dashed=1;' if it['dashed'] else '')
            cells.append(vertex(it['id'], '1', it['x'], it['y'], it['w'], it['h'], style, val))
        elif it['t'] == 'text':
            val = '<br>'.join(escape(l) for l in it['lines'])
            style = base + f"text;strokeColor=none;fillColor=none;align=left;verticalAlign=top;fontSize={it['size']};fontColor={it['color']};" + ('fontStyle=1;' if it['bold'] else '')
            cells.append(vertex(it['id'], '1', it['x'], it['y'], it['w'], it['h'], style, val))
        elif it['t'] == 'table':
            head = f"swimlane;fontStyle=1;startSize={HEAD_H};html=1;whiteSpace=wrap;fillColor={it['head_fill']};strokeColor={it['head_fill']};fontColor=#FFFFFF;fontSize=14;align=left;spacingLeft=10;collapsible=0;rounded=0;swimlaneLine=0;"
            title = '<b>' + escape(it['title']) + '</b>' + ('<br><font style="font-size:10px" color="#CFE3E6">' + escape(it['subtitle'] or it['tech'] or '') + '</font>' if (it['subtitle'] or it['tech']) else '')
            cells.append(vertex(it['id'], '1', it['x'], it['y'], it['w'], it['h'], head, title, {'tech': it['tech'], 'description': it['subtitle']}))
            for r in it['rows']:
                cx = 0
                for j, cid in enumerate(r['cells']):
                    w = it['widths'][j]
                    fill = r.get('fill') or FILL[r['kind']]
                    if r.get('section'):
                        val = ('<b>' + escape(r['label']) + '</b>') if j == 0 else ''
                        st = base + f"rounded=0;fillColor={fill};strokeColor={fill};align=left;spacingLeft=8;verticalAlign=middle;fontSize=13;fontColor=#FFFFFF;"
                        cells.append(vertex(cid, it['id'], cx, HEAD_H + it['rows'].index(r) * it['row_h'], w, it['row_h'], st, val, None))
                        cx += w
                        continue
                    if j == 0:
                        val = html_label(r['label'], r['tech'])
                        st = base + f"rounded=0;fillColor={fill};strokeColor=#B9C5CB;align=left;spacingLeft=8;verticalAlign=middle;fontSize={max(12, it.get('fs', 10) + 1)};fontColor={INK};" + ('fontStyle=2;' if r['calc'] else '')
                        props = {'tech': r['tech'] or r['label'], 'kind': KIND_NAME[r['kind']], 'rule': r['rule'], 'description': '', 'owner': '', 'last_checked': ''}
                    elif j == 1:
                        val = escape(r['type'])
                        st = base + f"rounded=0;fillColor={fill};strokeColor=#B9C5CB;align=center;verticalAlign=middle;fontSize=11;fontColor={MUTED};"
                        props = None
                    else:
                        txt = r['cols'][j - 2] if r.get('cols') else (r['rule'] or '')
                        val = escape(txt or '')
                        lead = it.get('dot_w', 0) if j == 2 else 0
                        st = base + f"rounded=0;fillColor=#FFFFFF;strokeColor=#B9C5CB;align=left;spacingLeft={6 + lead};verticalAlign=middle;fontSize={it.get('fs', 10)};fontColor={MUTED};"
                        props = None
                    y_rel = HEAD_H + it['rows'].index(r) * it['row_h']
                    cells.append(vertex(cid, it['id'], cx, y_rel, w, it['row_h'], st, val, props))
                    if j == 2:
                        for k, dc in enumerate(r.get('dots', [])):
                            cells.append(vertex(sc.nid('d'), it['id'], cx + 6 + k * 14, y_rel + (it['row_h'] - 10) / 2, 10, 10,
                                                f'ellipse;html=1;fillColor={dc};strokeColor=none;', ''))
                    cx += w
    for n, e in enumerate(sc.edges):
        style = f"edgeStyle=entityRelationEdgeStyle;html=1;endArrow=block;endFill=1;rounded=0;strokeColor={e['color']};strokeWidth={e['width']};" + ('dashed=1;' if e['dashed'] else '') + 'jettySize=auto;orthogonalLoop=1;'
        val = escape(e['label']) if e['label'] else ''
        cells.append(f'<mxCell id="e{n}" value={quoteattr(val)} style={quoteattr(style + "fontSize=11;fontColor=#5F6C77;labelBackgroundColor=#FFFFFF;")} edge="1" parent="1" source={quoteattr(e["src"])} target={quoteattr(e["tgt"])}><mxGeometry relative="1" as="geometry"/></mxCell>')
    w, h = sc.bounds()
    model = f'<mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="0" pageScale="1" pageWidth="{w:.0f}" pageHeight="{h:.0f}" math="0" shadow="0"><root>{"".join(cells)}</root></mxGraphModel>'
    return f'<diagram id="page{idx}" name={quoteattr(sc.name)}>{model}</diagram>'


# ------------------------------------------------------------------ SVG preview emitter
def wrap(text, width_px, size):
    n = max(8, int(width_px / (size * 0.56)))
    return textwrap.wrap(text, n) or ['']


def svg_page(sc):
    W, H = sc.bounds()
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" font-family="Helvetica, Arial, sans-serif">',
         f'<rect width="{W:.0f}" height="{H:.0f}" fill="#F4F6F7"/>']
    def anchor(cid, other):
        x, y, w, h = sc.cells[cid]
        ox, oy, ow, oh = sc.cells[other]
        if x + w <= ox + 1:
            return (x + w, y + h / 2, 'r')
        if ox + ow <= x + 1:
            return (x, y + h / 2, 'l')
        return ((x + w / 2, y + h, 'b') if y + h <= oy + 1 else (x + w / 2, y, 't'))
    edge_svg = []
    for e in sc.edges:
        sx, sy, sd = anchor(e['src'], e['tgt'])
        tx, ty, td = anchor(e['tgt'], e['src'])
        dash = ' stroke-dasharray="6 4"' if e['dashed'] else ''
        if sd in 'rl' and td in 'rl':
            mx = (sx + tx) / 2
            d = f'M{sx:.0f},{sy:.0f} C{mx:.0f},{sy:.0f} {mx:.0f},{ty:.0f} {tx:.0f},{ty:.0f}'
        else:
            d = f'M{sx:.0f},{sy:.0f} L{tx:.0f},{ty:.0f}'
        op = 0.6 if e['dashed'] else 0.9
        edge_svg.append(f'<path d="{d}" fill="none" stroke="{e["color"]}" stroke-width="{e["width"]}"{dash} opacity="{op}" marker-end="url(#arr)"/>')
        if e['label']:
            edge_svg.append(f'<text x="{(sx + tx) / 2:.0f}" y="{(sy + ty) / 2 - 6:.0f}" font-size="11" fill="#5F6C77" text-anchor="middle">{escape(e["label"])}</text>')
    o.insert(2, '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#5F6C77"/></marker></defs>')
    for it in sc.items:
        if it['t'] == 'box':
            x, y, w, h = it['x'], it['y'], it['w'], it['h']
            dash = ' stroke-dasharray="5 4"' if it['dashed'] else ''
            o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{it["fill"]}" stroke="{it["stroke"]}" stroke-width="1.4"{dash}/>')
            ty = y + 8 + it['tsize']
            if it['title']:
                for ln in wrap(it['title'], w - 24, it['tsize']):
                    o.append(f'<text x="{x + 12}" y="{ty:.0f}" font-size="{it["tsize"]}" font-weight="700" fill="{it["tcolor"]}">{escape(ln)}</text>')
                    ty += it['tsize'] + 4
            ty += 2
            for b in it['body']:
                for ln in wrap(b, w - 24, it['bsize']):
                    o.append(f'<text x="{x + 12}" y="{ty + it["bsize"]:.0f}" font-size="{it["bsize"]}" fill="{it.get("bcolor", MUTED)}">{escape(ln)}</text>')
                    ty += it['bsize'] + 5
        elif it['t'] == 'text':
            ty = it['y'] + it['size']
            for ln in it['lines']:
                for part in wrap(ln, it['w'], it['size']):
                    fw = ' font-weight="700"' if it['bold'] else ''
                    o.append(f'<text x="{it["x"]}" y="{ty:.0f}" font-size="{it["size"]}" fill="{it["color"]}"{fw}>{escape(part)}</text>')
                    ty += it['size'] + 4
        elif it['t'] == 'table':
            x, y, w, h = it['x'], it['y'], it['w'], it['h']
            o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{HEAD_H}" fill="{it["head_fill"]}"/>')
            o.append(f'<text x="{x + 10}" y="{y + 20}" font-size="14" font-weight="700" fill="#FFFFFF">{escape(it["title"])}</text>')
            sub = it['subtitle'] or it['tech'] or ''
            for k, part in enumerate(wrap(sub, w - 20, 10)[:1]):
                o.append(f'<text x="{x + 10}" y="{y + 36}" font-size="10" fill="#CFE3E6">{escape(part)}</text>')
            for r in it['rows']:
                cx = x
                for j, cid in enumerate(r['cells']):
                    cw = it['widths'][j]
                    fill = (r.get('fill') or FILL[r['kind']]) if (j < 2 or r.get('section')) else '#FFFFFF'
                    o.append(f'<rect x="{cx}" y="{r["y"]}" width="{cw}" height="{it["row_h"]}" fill="{fill}" stroke="{fill if r.get("section") else "#B9C5CB"}"/>')
                    if r.get('section'):
                        if j == 0:
                            o.append(f'<text x="{cx + 8}" y="{r["y"] + it["row_h"] / 2 + 5:.0f}" font-size="13" font-weight="700" fill="#FFFFFF">{escape(r["label"])}</text>')
                        cx += cw
                        continue
                    if j == 0:
                        nfs = max(12, it.get('fs', 10) + 1)
                        st = ' font-style="italic"' if r['calc'] else ''
                        if r['tech']:
                            o.append(f'<text x="{cx + 8}" y="{r["y"] + 16}" font-size="{nfs}" font-weight="700" fill="{INK}"{st}>{escape(r["label"][:34])}</text>')
                            o.append(f'<text x="{cx + 8}" y="{r["y"] + 30}" font-size="9" fill="#5F6C77">{escape(r["tech"][:46])}</text>')
                        else:
                            o.append(f'<text x="{cx + 8}" y="{r["y"] + it["row_h"] / 2 + 4:.0f}" font-size="{nfs}" fill="{INK}">{escape(r["label"][:44])}</text>')
                    elif j == 1:
                        o.append(f'<text x="{cx + cw / 2}" y="{r["y"] + it["row_h"] / 2 + 4:.0f}" font-size="11" fill="#5F6C77" text-anchor="middle">{escape(r["type"])}</text>')
                    else:
                        txt = r['cols'][j - 2] if r.get('cols') else (r['rule'] or '')
                        lead = it.get('dot_w', 0) if j == 2 else 0
                        fs = it.get('fs', 10)
                        lines = wrap(txt, cw - 12 - lead, fs)[:4]
                        ry = r['y'] + (it['row_h'] - len(lines) * (fs + 2)) / 2 + fs
                        for part in lines:
                            o.append(f'<text x="{cx + 6 + lead}" y="{ry:.0f}" font-size="{fs}" fill="#5F6C77">{escape(part)}</text>')
                            ry += fs + 2
                        if j == 2:
                            for k, dc in enumerate(r.get('dots', [])):
                                o.append(f'<circle cx="{cx + 11 + k * 14}" cy="{r["y"] + it["row_h"] / 2:.0f}" r="5" fill="{dc}"/>')
                    cx += cw
    o.extend(edge_svg)
    o.append('</svg>')
    return '\n'.join(o)


def validate_model():
    """Stops the build when lineage_model.py and the real code disagree."""
    problems = []
    stg = {t: {c['name'] for c in v['columns']} for t, v in CODE['staging'].items()}
    fin = {t: set(cols) for t, cols in CODE['final'].items()}
    for t, cols in CODE['final'].items():
        model = {c[0] for c in LM.FINAL.get(t, [])}
        for c in cols:
            if c not in model:
                problems.append(f'{t}.{c}: in the code, missing from lineage_model.py')
        for c in model - set(cols):
            problems.append(f'{t}.{c}: in lineage_model.py, no longer in the code')
        for col, cat, ups, rule in LM.FINAL.get(t, []):
            for u in ups:
                tt, cc = u.split('.', 1)
                known = stg.get(tt) or fin.get(tt)
                if known is None or cc not in known:
                    problems.append(f'{t}.{col}: upstream {u} does not exist in the code')
    for m in LM.METRICS:
        for u in m[3]:
            tt, cc = u.split('.', 1)
            if cc not in (fin.get(tt) or set()):
                problems.append(f'metric {m[0]}: upstream {u} does not exist in the code')
    return problems


def main():
    problems = validate_model()
    if problems:
        print('lineage_model.py does not match the code:')
        for p in problems:
            print('  -', p)
        sys.exit(1)
    out = os.path.join(HERE, 'APFP_Data_Lineage.drawio')
    svg_dir = None
    args = sys.argv[1:]
    while args:
        a = args.pop(0)
        if a == '--out':
            out = args.pop(0)
        elif a == '--svg-dir':
            svg_dir = args.pop(0)
    pages = all_pages()
    xml = '<mxfile host="app.diagrams.net" version="24.0.0">' + ''.join(drawio_page(p, i + 1) for i, p in enumerate(pages)) + '</mxfile>'
    open(out, 'w', encoding='utf-8').write(xml)
    print('wrote', out, len(pages), 'pages')
    if svg_dir:
        os.makedirs(svg_dir, exist_ok=True)
        for i, p in enumerate(pages):
            name = re.sub(r'[^A-Za-z0-9]+', '_', p.name).strip('_')
            open(os.path.join(svg_dir, f'{i + 1:02d}_{name}.svg'), 'w', encoding='utf-8').write(svg_page(p))
        print('wrote', len(pages), 'svg previews to', svg_dir)


if __name__ == '__main__':
    main()
