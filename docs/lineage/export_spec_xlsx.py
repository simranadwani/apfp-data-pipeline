#!/usr/bin/env python3
"""
Writes docs/lineage/APFP_Lineage_Spec.xlsx: everything needed to draw the lineage diagram in draw.io without guessing.
Readable sheets (Pages, Tables, Columns, Edges_Column, Edges_Table, Metrics, Charts) + drawable sheets (Shapes, Shape_Edges, Row_Styles, Grid)
+ Reference_Images + Checks + README_and_Prompt + Reference_Script.
Run lineage_pages.py first (it writes the SVG previews); this script renders PNGs from them with headless Chromium.
Usage: python3 docs/lineage/export_spec_xlsx.py
"""
import glob, json, math, os, re, subprocess, sys
from xml.sax.saxutils import escape
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from PIL import Image as PILImage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lineage_pages as P  # noqa: E402

V, B, LM, CODE = P.V, P.B, P.LM, P.CODE
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'APFP_Lineage_Spec.xlsx')
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
DATA = json.loads(open(os.path.join(ROOT, 'LineageData.js'), encoding='utf-8').read().split('LINEAGE_DATA = ', 1)[1].rsplit(';', 1)[0])
CHARTS = DATA['charts']
FONT = 'Arial'
HEAD_FILL = PatternFill('solid', fgColor='0E4A5C')
THIN = Side(style='thin', color='D0D7DC')

KIND_BY_FILL = {P.H_KEY: 'key column', P.H_NUM: 'number', P.H_BOOL: 'true / false', '#FFFFFF': 'none (text or date)', P.C_DASH: 'dashboard metric'}


def sheet(wb, name, headers, rows, widths=None, wrap_cols=(), fills=None):
    ws = wb.create_sheet(name)
    ws.append(headers)
    for c in ws[1]:
        c.font = Font(name=FONT, bold=True, color='FFFFFF', size=10)
        c.fill = HEAD_FILL
        c.alignment = Alignment(vertical='center', wrap_text=True)
    for r in rows:
        ws.append(list(r))
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font = Font(name=FONT, size=10)
            c.alignment = Alignment(vertical='top', wrap_text=(c.column_letter in wrap_cols or c.column - 1 in wrap_cols))
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = ws.dimensions
    for i, h in enumerate(headers, 1):
        w = (widths or {}).get(h) or min(60, max(10, len(str(h)) + 4, *(len(str(r[i - 1])) + 2 for r in rows[:200] if r[i - 1] is not None) if rows else [10]))
        ws.column_dimensions[get_column_letter(i)].width = w
    if fills:
        for (rowi, coli), hexcol in fills.items():
            ws.cell(row=rowi, column=coli).fill = PatternFill('solid', fgColor=hexcol.lstrip('#'))
    return ws


def main():
    pages = P.all_pages()
    # ---------------------------------------------------------------- previews -> PNG
    pngs = []
    for i, p in enumerate(pages):
        name = re.sub(r'[^A-Za-z0-9]+', '_', p.name).strip('_')
        svg = os.path.join(HERE, 'v2_preview', f'{i + 1:02d}_{name}.svg')
        png = svg[:-4] + '.png'
        subprocess.run([CHROME, '--headless', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--screenshot=/tmp/_r.png', f'--window-size={p.width},{p.height + 200}', 'file://' + svg], capture_output=True)
        PILImage.open('/tmp/_r.png').crop((0, 0, p.width, p.height)).save(png)
        pngs.append(png)

    wb = Workbook()
    wb.remove(wb.active)

    # ---------------------------------------------------------------- Shapes / Shape_Edges (drawable)
    shapes, sedges, z = [], [], 0
    for p in pages:
        for s in p.shapes:
            z += 1
            if s['type'] == 'chip':
                st = P.STYLE['chip'].format(fill=s['fill'], stroke=s['stroke'], color=s['color'])
            elif s['type'] == 'swatch':
                st = P.STYLE['swatch'].format(fill=s['fill'])
            else:
                st = P.STYLE['text'].format(size=s['size'], color=s['color'], extra='fontStyle=1;' if s.get('bold') else '')
            shapes.append([p.name, s['id'], '1', z, s['type'], '', '', '', s['x'], s['y'], s['w'], s['h'], '', None, s.get('text', ''), '', s.get('fill', ''),
                           s.get('color', ''), s.get('size', ''), 'yes' if s.get('bold') else '', '', st])
        for t in p.tables:
            z += 1
            label = '<b>' + escape(t['name']) + '</b>' + ('<br><font style="font-size:10px" color="#E2F2F4">' + escape(t['sub']) + '</font>' if t['sub'] else '')
            shapes.append([p.name, t['id'], '1', z, 'Table', t['layer'], t['name'], '', t['x'], t['y'], t['w'], t['h'], '', None, t['name'], label, t['fill'], '#FFFFFF', 14, 'yes', '',
                           P.STYLE['table'].format(head=t['head'], fill=t['fill'])])
            ry = t['head']
            for r in t['rows']:
                z += 1
                shapes.append([p.name, r['id'], t['id'], z, 'TableRow', t['layer'], t['name'], r.get('key') or '', t['x'], r['y'], r['w'], r['h'], '', ry, '', '', '', '', '', '', '', P.STYLE['row']])
                rx = 0
                for j, c in enumerate(r['cells']):
                    z += 1
                    shapes.append([p.name, f'{r["id"]}_{j}', r['id'], z, 'TableCell', t['layer'], t['name'], r.get('key') or '', t['x'] + rx, r['y'], c['w'], r['h'], rx, 0, c['text'], '',
                                   c['fill'], c['color'], c.get('size') or 12, 'yes' if c['bold'] else '', 'yes' if c.get('italic') else '', P.cell_style(c, j, len(r['cells']) - 1)])
                    rx += c['w']
                ry += r['h']
        for e in p.edges:
            vertical = e.get('vertical')
            st = ('edgeStyle=none;html=1;endArrow=block;endFill=1;strokeWidth=1.5;strokeColor=' + P.C_EDGE + ';exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;' + ('dashed=1;' if e['dashed'] else '')) if vertical \
                else P.STYLE['edge'].format(dash='dashed=1;' if e['dashed'] else '')
            wp = 'yes' if (not vertical and abs(e['sy'] - e['ty']) > 0.5) else 'no'
            sedges.append([p.name, e['id'], e['src'], e['tgt'], 'table to table' if vertical else 'row to row', P.C_EDGE, 1.5, 'yes' if e['dashed'] else 'no', wp, round(e['lane_x']), round(e['sx']), round(e['sy']), round(e['tx']), round(e['ty']), st])
    sheet(wb, 'Shapes', ['page', 'shape_id', 'parent_id', 'z', 'type', 'layer', 'table', 'column', 'x', 'y', 'width', 'height', 'rel_x', 'rel_y', 'text', 'label_html', 'fill', 'font_color', 'font_size', 'bold', 'italic', 'drawio_style'],
          shapes, widths={'text': 50, 'label_html': 40, 'drawio_style': 70, 'page': 34})
    ws_edges = sheet(wb, 'Shape_Edges', ['page', 'edge_id', 'source_id', 'target_id', 'kind', 'color', 'width', 'dashed', 'waypoint', 'lane_x', 'source_x', 'source_y', 'target_x', 'target_y', 'drawio_style'],
                     sedges, widths={'drawio_style': 70, 'page': 34})
    # rename columns to the names the reference converter reads
    hdr = [c.value for c in ws_edges[1]]
    hdr[hdr.index('source_x')] = 'source_x'
    wsE = wb['Shape_Edges']

    # ---------------------------------------------------------------- Pages
    template = lambda n: 'Map' if n.startswith('1.') else 'src to stg (all tables)' if 'src to stg' in n else 'fct index (all final tables)' if 'all final tables' in n else 'fct table page (stg to fct + dashboard fields and charts)' if 'stg to fct' in n else 'glossary'
    prow = [[p.name, f'page{i + 1}', i + 1, template(p.name), p.title, p.subtitle or '', p.ribbon or '', p.width, p.height, len(p.tables), len(p.edges)] for i, p in enumerate(pages)]
    sheet(wb, 'Pages', ['page', 'diagram_id', 'order', 'template', 'title', 'subtitle', 'ribbon_active', 'width', 'height', 'tables', 'edges'], prow, widths={'page': 38, 'title': 40, 'subtitle': 60})

    # ---------------------------------------------------------------- Tables
    trow = []
    page_of = {}
    for p in pages:
        for t in p.tables:
            page_of.setdefault(t['name'], []).append(p.name)
    for t in STG_ORDER if (STG_ORDER := P.STG_ORDER) else []:
        pass
    for t in P.STG_ORDER:
        spec = CODE['staging'][t]
        trow.append(['src', spec['source_tab'], '', len(spec['columns']), '', '', t, '', '; '.join(page_of.get(spec['source_tab'], []))])
        trow.append(['stg', t, '', len(spec['columns']), spec['source_tab'], spec['source_tab'], '; '.join(f for f in P.FCT_ORDER if any(u.startswith(t + '.') for _, _, ups, _ in LM.FINAL[f] for u in ups)), '', '; '.join(page_of.get(t, []))])
    for f in P.FCT_ORDER:
        reads = []
        for col, cat, ups, rule in LM.FINAL[f]:
            for u in ups:
                if u.split('.')[0] not in reads:
                    reads.append(u.split('.')[0])
        trow.append(['fct', f, P.GRAIN[f], len(CODE['final'][f]), '', '; '.join(reads), '', '; '.join(LM.FEEDS[f]), '; '.join(page_of.get(f, []))])
    sheet(wb, 'Tables', ['layer', 'table', 'grain', 'columns', 'source_tab', 'reads_from', 'feeds', 'charts_fed', 'drawn_on_pages'], trow, widths={'charts_fed': 60, 'drawn_on_pages': 50})

    # ---------------------------------------------------------------- Columns
    crow, cfill = [], {}
    n = 1
    for t in P.STG_ORDER:
        spec = CODE['staging'][t]
        for i, c in enumerate(spec['columns'], 1):
            k = V.hl(t, c['name'], c['type'])
            crow.append(['src', spec['source_tab'], i, c['source_header'], P.disp_type(k, c['type']), KIND_BY_FILL[k], '', '', '', '', '', ''])
            n += 1
            cfill[(n, 6)] = k
        for i, c in enumerate(spec['columns'], 1):
            k = V.hl(t, c['name'], c['type'])
            crow.append(['stg', t, i, c['name'], P.disp_type(k, c['type']), KIND_BY_FILL[k], '', 'no', c['source_header'], f"{spec['source_tab']} > {c['source_header']}", '', ''])
            n += 1
            cfill[(n, 6)] = k
    for f in P.FCT_ORDER:
        model = {c[0]: c for c in LM.FINAL[f]}
        sections, _, _ = P.fct_rows(f)
        sec = {col: title for key, title, colr, cols in sections for col, *_ in cols}
        for i, col in enumerate(CODE['final'][f], 1):
            cat, ups, rule = model[col][1], model[col][2], model[col][3]
            k = V.hl(f, col)
            full = V.built_from(col, cat, ups, f) if ups else ''
            charts = ', '.join(DATA['columns'][f'{f}.{col}']['charts'])
            crow.append(['fct', f, i, col, P.col_type(col), KIND_BY_FILL[k], sec[col], 'yes' if cat == 'calc' else 'no',
                         full or ({'const': 'fixed value', 'run': 'date of the run', 'blank': 'kept empty'}.get(cat, '')),
                         '; '.join(ups), rule, charts])
            n += 1
            cfill[(n, 6)] = k
    sheet(wb, 'Columns', ['layer', 'table', 'position', 'column', 'type', 'highlight', 'section', 'calculated', 'built_from', 'upstream_exact', 'plain_rule', 'charts_using'], crow,
          widths={'table': 30, 'built_from': 50, 'upstream_exact': 60, 'plain_rule': 60, 'section': 36, 'charts_using': 24}, fills=cfill)

    # ---------------------------------------------------------------- Edges
    erow = []
    for t in P.STG_ORDER:
        for c in CODE['staging'][t]['columns']:
            erow.append(['src to stg', CODE['staging'][t]['source_tab'], c['source_header'], t, c['name'], 'copy'])
    for f in P.FCT_ORDER:
        for col, cat, ups, rule in LM.FINAL[f]:
            if cat in ('copy', 'join'):
                for u in ups:
                    t, c = u.split('.', 1)
                    erow.append([f'stg to {f}', t, c, f, col, 'copy' if cat == 'copy' else 'lookup'])
    sheet(wb, 'Edges_Column', ['page_group', 'from_table', 'from_column', 'to_table', 'to_column', 'kind'], erow, widths={'from_table': 30, 'to_table': 30, 'page_group': 30})
    ert = []
    for t in P.STG_ORDER:
        ert.append(['src', CODE['staging'][t]['source_tab'], 'stg', t, 'solid'])
    for f in P.FCT_ORDER:
        seen = []
        for col, cat, ups, rule in LM.FINAL[f]:
            for u in ups:
                s = u.split('.')[0]
                if s not in seen:
                    seen.append(s)
        for s in seen:
            ert.append(['stg' if s.startswith('stg') else 'fct', s, 'fct', f, 'dashed' if s.startswith('fct') else 'solid'])
    for c in sorted({(c['table'], c['page']) for c in CHARTS}):
        ert.append(['fct', c[0], 'dashboard', c[1], 'solid'])
    sheet(wb, 'Edges_Table', ['from_layer', 'from', 'to_layer', 'to', 'line'], ert, widths={'from': 34, 'to': 34})

    # ---------------------------------------------------------------- Metrics / Charts
    mrow = []
    for field, label, definition, ups, charts, filt in LM.METRICS:
        mrow.append([field, label, definition, filt, '; '.join(ups), ', '.join(f'{c} {LM.CHART_NAMES.get(c, "")}'.strip() for c in charts), P.C_DASH])
    sheet(wb, 'Metrics', ['dashboard_field', 'label', 'plain_definition', 'chart_filter', 'fct_columns_read', 'charts', 'cell_colour'], mrow, widths={'plain_definition': 50, 'fct_columns_read': 60, 'charts': 60})
    crows = [[c['id'], c['page'], c['name'], c['table'], c['shows'], c['filter'], ', '.join(c['columns']), '; '.join(c['source_tabs'])] for c in CHARTS]
    sheet(wb, 'Charts', ['chart', 'dashboard_page', 'name', 'fct_table', 'what_it_shows', 'filter', 'columns_used', 'source_tabs'], crows, widths={'what_it_shows': 60, 'columns_used': 60})

    # ---------------------------------------------------------------- Style_Guide / Grid / Row_Styles
    sg = [['layer header: src', P.C_SRC, 'table header fill, white text'], ['layer header: stg', P.C_STG, 'table header fill, white text'], ['layer header: fct', P.C_FCT, 'table header fill, white text'],
          ['layer header: dashboard', P.C_DASHH, 'table header fill, white text'],
          ['highlight: key column', P.H_KEY, 'cells of name and type; columns checked by the cardinality tests and every *_id column'], ['highlight: number', P.H_NUM, 'name and type cells'],
          ['highlight: true / false', P.H_BOOL, 'name and type cells'], ['highlight: dashboard metric', P.C_DASH, 'dashboard field cells on the metrics page and dashboard page tables on the Map'],
          ['no highlight', '#FFFFFF', 'text and date columns, built-from and rule cells'], ['section bar: stg', P.C_STG, 'row spanning the table: "from stg_xxx (n)"'],
          ['section bar: several tables', P.C_EDGE, 'white bold text'], ['section bar: fixed / run date / empty', P.C_SRC, 'white bold text'], ['arrow colour', P.C_EDGE, 'width 1.5, block arrowhead, dashed only for fct1 to fct6'],
          ['cell border', P.LINE, '1 px'], ['text colour', P.INK, 'built-from and rule text use #5F6C77'], ['font', 'Helvetica', 'header 14 bold; cells 12; built-from, rule and type 11'],
          ['naming rule', '', 'Use the exact src tab, stg_ and fct_ names. No friendly renaming.']]
    cf = {(i + 2, 2): r[1] for i, r in enumerate(sg) if r[1].startswith('#')}
    sheet(wb, 'Style_Guide', ['item', 'value', 'use'], sg, widths={'item': 38, 'value': 14, 'use': 90}, fills=cf)
    grid = [['page margin', P.M], ['table header height', P.HEAD], ['row height (default)', P.ROW], ['row height when text needs 3 lines', '60'], ['gap between stacked tables', P.GAP],
            ['gutter between stg and fct (arrow lane)', P.GUT], ['stg / src table width', P.STG_W], ['stg column widths (name, type)', ', '.join(map(str, P.STG_COLS))],
            ['fct table width', P.FCT_W], ['fct column widths (name, type, built from, rule)', ', '.join(map(str, P.FCT_COLS))], ['src to stg page: src and stg widths (name, type)', '260, 100 each; 100 between the two tables; two table pairs side by side, 80 apart'],
            ['ribbon chip size / y', '150 x 40 at y=20, step 190'], ['title y / subtitle y', '80 / 120'], ['legend row y (fct pages)', '210'], ['first table y (fct pages)', '260'], ['dashboard band (fct pages)', 'starts 80 below the note under the fct table; three tables (360, 600 = 220+380, 380) with 120 gutters, rows aligned, height min 60'],
            ['snap', 'all coordinates are multiples of 10']]
    sheet(wb, 'Grid', ['constant', 'value'], grid, widths={'constant': 60, 'value': 40})
    rs = [['table', P.STYLE['table']], ['row', P.STYLE['row']], ['cell', P.STYLE['cell']], ['edge (row to row)', P.STYLE['edge']], ['edge (table to table, vertical)', 'edgeStyle=none;html=1;endArrow=block;endFill=1;strokeWidth=1.5;strokeColor=' + P.C_EDGE + ';exitX=0.5;exitY=1;entryX=0.5;entryY=0;dashed=1;'],
          ['text', P.STYLE['text']], ['chip', P.STYLE['chip']], ['swatch', P.STYLE['swatch']]]
    sheet(wb, 'Row_Styles', ['element', 'drawio_style_template ({placeholders} are filled from the Shapes sheet)'], rs, widths={'element': 30, 'drawio_style_template ({placeholders} are filled from the Shapes sheet)': 200}, wrap_cols=(2,))

    # ---------------------------------------------------------------- Checks
    chk = [['pages', len(pages)], ['tables drawn (all pages)', sum(len(p.tables) for p in pages)], ['table rows (all pages)', sum(len(t['rows']) for p in pages for t in p.tables)],
           ['edges (all pages)', sum(len(p.edges) for p in pages)], ['shapes in sheet Shapes', len(shapes)], ['edges in sheet Shape_Edges', len(sedges)],
           ['src tables (columns read)', 8], ['stg tables', 8], ['fct tables', 6], ['stg columns', sum(len(v['columns']) for v in CODE['staging'].values())],
           ['fct columns', sum(len(v) for v in CODE['final'].values())], ['charts', len(CHARTS)], ['dashboard fields (metric rows)', len(LM.METRICS)]]
    for p in pages:
        chk.append([f'page "{p.name}": tables / rows / edges', f'{len(p.tables)} / {sum(len(t["rows"]) for t in p.tables)} / {len(p.edges)}'])
    chk.append(['source', 'generated by docs/lineage/export_spec_xlsx.py from the pipeline code (code_columns.json, lineage_model.py, chart_passport.py)'])
    sheet(wb, 'Checks', ['check', 'value'], chk, widths={'check': 60, 'value': 90})

    # ---------------------------------------------------------------- Reference_Script
    script = open(os.path.join(HERE, 'rebuild_from_xlsx.py'), encoding='utf-8').read().split('\n')
    ws = wb.create_sheet('Reference_Script')
    ws['A1'] = 'rebuild_from_xlsx.py: a working converter (tested). Save as a .py file, run: python rebuild_from_xlsx.py APFP_Lineage_Spec.xlsx out.drawio'
    ws['A1'].font = Font(name=FONT, bold=True)
    for i, ln in enumerate(script, 3):
        ws.cell(row=i, column=1, value=ln).font = Font(name='Courier New', size=9)
    ws.column_dimensions['A'].width = 160

    # ---------------------------------------------------------------- Reference_Images
    ws = wb.create_sheet('Reference_Images')
    ws['A1'] = 'Reference render of every page (what the finished draw.io page should look like). Page order = sheet Pages.'
    ws['A1'].font = Font(name=FONT, bold=True)
    row = 3
    for p, png in zip(pages, pngs):
        ws.cell(row=row, column=1, value=p.name).font = Font(name=FONT, bold=True, size=12)
        im = XLImage(png)
        scale = min(1.0, 1200 / im.width)
        im.width, im.height = int(im.width * scale), int(im.height * scale)
        ws.add_image(im, f'A{row + 1}')
        row += 3 + math.ceil(im.height / 20)

    # ---------------------------------------------------------------- README_and_Prompt (first sheet)
    ws = wb.create_sheet('README_and_Prompt', 0)
    sample = ('<mxCell id="T1" value="&lt;b&gt;stg_grants&lt;/b&gt;" style="shape=table;startSize=50;container=1;collapsible=0;childLayout=tableLayout;fixedRows=1;..." vertex="1" parent="1"><mxGeometry x="40" y="340" width="360" height="120" as="geometry"/></mxCell>\n'
              '<mxCell id="R1" style="shape=tableRow;horizontal=0;startSize=0;...;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;" vertex="1" parent="T1"><mxGeometry y="50" width="360" height="40" as="geometry"/></mxCell>\n'
              '<mxCell id="R1_0" value="grant_id" style="shape=partialRectangle;html=1;connectable=0;fillColor=#E1D5E7;..." vertex="1" parent="R1"><mxGeometry width="260" height="40" as="geometry"><mxRectangle width="260" height="40" as="alternateBounds"/></mxGeometry></mxCell>\n'
              '<mxCell id="R1_1" value="text" style="shape=partialRectangle;..." vertex="1" parent="R1"><mxGeometry x="260" width="100" height="40" as="geometry"><mxRectangle width="100" height="40" as="alternateBounds"/></mxGeometry></mxCell>\n'
              '<mxCell id="E1" style="edgeStyle=elbowEdgeStyle;elbow=horizontal;...;exitX=1;exitY=0.5;entryX=0;entryY=0.5;" edge="1" parent="1" source="R1" target="R9"><mxGeometry relative="1" as="geometry"/></mxCell>')
    lines = [
        ('APFP data lineage: specification workbook', 'h'),
        ('Purpose: give this workbook to a tool (for example ChatGPT) so it can build the lineage diagram as a draw.io file (.drawio) without designing anything. Every table, row, cell, arrow, size, position and colour is a row in this workbook.', ''),
        ('', ''),
        ('SHEETS', 'h'),
        ('README_and_Prompt: this page.  Style_Guide, Grid, Row_Styles: colours, sizes, the exact draw.io style strings.', ''),
        ('Pages: the pages in order, with canvas size.  Tables, Columns, Edges_Column, Edges_Table, Metrics, Charts: what the diagram says (readable facts).', ''),
        ('Shapes, Shape_Edges: DRAWABLE. One row per shape / table / row / cell / arrow with coordinates, text, fill and the draw.io style. Draw from these.', ''),
        ('Reference_Images: how each finished page must look.  Checks: counts to verify after drawing.  Reference_Script: a working Python converter.', ''),
        ('', ''),
        ('PROMPT TO PASTE INTO CHATGPT (attach this workbook)', 'h'),
        ('You are given a workbook that fully specifies a data-lineage diagram. Produce one draw.io file (uncompressed XML, <mxfile> with one <diagram> per row of sheet Pages, in order). Do not design, rename, move or resize anything; convert rows to XML.', ''),
        ('1. Best method: write and run a Python script that reads the workbook with openpyxl and writes the .drawio (the sheet Reference_Script contains a tested one; use it as the starting point). Do not hand-type XML for hundreds of shapes.', ''),
        ('2. For each page, take its rows in sheet Shapes ordered by column z. type Table = a NATIVE draw.io table (style from drawio_style, geometry x, y, width, height, label from label_html). type TableRow = child of the table (parent_id), geometry y=rel_y, width, height, NO x. type TableCell = child of its row, geometry width and height plus an alternateBounds rectangle; add x=rel_x ONLY when rel_x is greater than 0 (draw.io lays cells out from these offsets; without them all cells of a row pile up at the left). No y. Other types (chip, title, subtitle, text, swatch, ...) are plain vertices with parent 1.', ''),
        ('3. Edges: every row of sheet Shape_Edges becomes an edge mxCell with source = source_id and target = target_id (these are TableRow ids, or Table ids for kind "table to table"), style = drawio_style. When waypoint = yes add <Array as="points"><mxPoint x="lane_x" y="source_y"/></Array>.', ''),
        ('4. Use the ids, text and styles exactly as written. Tables must be native tables (shape=table), never swimlanes or rectangles. Arrows are elbow connectors (no curves). Everything is on a 10 px grid.', ''),
        ('5. Verify: counts per page (tables, rows, edges) must equal sheet Checks; open the result and compare each page with the picture in Reference_Images.', ''),
        ('6. Deliver the .drawio file only; do not summarise or restyle it.', ''),
        ('', ''),
        ('MEANING OF THE DIAGRAM (for the reader)', 'h'),
        ('src = source tabs where staff type data. stg = a cleaned copy of each src tab. fct = final tables built only from stg. dashboard = Looker Studio pages. There is no int_ layer.', ''),
        ('Cell colours: lilac = key column (cardinality tests), yellow = number, green = true/false, blue = dashboard metric, white = text or date. Header colour = layer. Arrows: copied or looked-up columns only; calculated columns (marked with the f sign in the type cell) have no arrow, their inputs are written under "built from".', ''),
        ('', ''),
        ('EXAMPLE of the XML for one table, one row, one cell and one arrow (shortened)', 'h'),
        (sample, 'c'),
        ('', ''),
        ('Generated by docs/lineage/export_spec_xlsx.py. Regenerate it after any column change: python3 docs/lineage/lineage_pages.py && python3 docs/lineage/export_spec_xlsx.py', ''),
    ]
    for i, (text, kind) in enumerate(lines, 1):
        c = ws.cell(row=i, column=1, value=text)
        c.alignment = Alignment(wrap_text=True, vertical='top')
        c.font = Font(name='Courier New', size=9) if kind == 'c' else Font(name=FONT, size=14 if (kind == 'h' and i == 1) else 11, bold=(kind == 'h'), color='0E4A5C' if kind == 'h' else '000000')
    ws.column_dimensions['A'].width = 170
    wb.save(OUT)
    print('wrote', OUT, os.path.getsize(OUT) // 1024, 'KB; sheets:', wb.sheetnames)


if __name__ == '__main__':
    main()
