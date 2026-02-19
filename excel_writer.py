from __future__ import annotations

from typing import Dict, Any, List
from io import BytesIO

import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet


# ── Config ────────────────────────────────────────────────────────────────────
SPLIT_TABLES_TO_TABS = False

# Paige Engineering brand colours
NAVY = "1E3347"
ORANGE = "D4721A"
WHITE = "FFFFFF"
ROW_LIGHT = "F4F6F9"
BORDER_C = "DDE3EC"


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL HELPERS (unchanged — kept so build_workbook still works)
# ─────────────────────────────────────────────────────────────────────────────


def _write_heading(ws: Worksheet, meta: Dict[str, Any], start_row: int = 1) -> int:
    ws.cell(
        row=start_row, column=1, value=f"Generated: {meta.get('generated_date','')}"
    ).font = Font(bold=True)
    ws.cell(
        row=start_row + 1, column=1, value=f"Created by: {meta.get('created_by','')}"
    ).font = Font(bold=True)
    return start_row + 3


def _autosize(ws: Worksheet, max_width: int = 70):
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            v = cell.value
            if v is None:
                continue
            if len(str(v)) > max_len:
                max_len = len(str(v))
        ws.column_dimensions[col_letter].width = min(max(12, max_len + 2), max_width)


def _sanitize_for_excel(val: Any) -> Any:
    if isinstance(val, list):
        return "\n".join(str(v) for v in val)
    if isinstance(val, dict):
        return str(val)
    if val is None:
        return ""
    return val


def _write_table(
    ws: Worksheet,
    title: str,
    columns: List[str],
    rows: List[Dict[str, Any]],
    start_row: int,
) -> int:
    ws.cell(row=start_row, column=1, value=title).font = Font(bold=True, size=12)
    start_row += 1

    sanitized = [{k: _sanitize_for_excel(v) for k, v in row.items()} for row in rows]
    df = pd.DataFrame(sanitized).reindex(columns=columns)

    for r_idx, row in enumerate(
        dataframe_to_rows(df, index=False, header=True), start=start_row
    ):
        for c_idx, val in enumerate(row, start=1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            if r_idx == start_row:
                cell.font = Font(bold=True)

    return start_row + len(df.index) + 2


# ─────────────────────────────────────────────────────────────────────────────
# ORIGINAL build_workbook — UNCHANGED (backwards compat with /generate-bid-excel)
# ─────────────────────────────────────────────────────────────────────────────


def build_workbook(
    prompt1: Dict[str, Any], prompt2: Dict[str, Any], prompt3: Dict[str, Any]
) -> bytes:
    wb = Workbook()
    wb.remove(wb.active)

    if SPLIT_TABLES_TO_TABS:
        _build_5_tabs(wb, prompt1, prompt2, prompt3)
    else:
        _build_3_tabs(wb, prompt1, prompt2, prompt3)

    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()


def _build_3_tabs(wb, p1, p2, p3):
    ws1 = wb.create_sheet("01_Geotech_Table1")
    r = _write_heading(ws1, p1.get("meta", {}))
    t1 = p1.get("table1", {})
    _write_table(
        ws1, t1.get("title", "Table 1"), t1.get("columns", []), t1.get("rows", []), r
    )
    ws1.freeze_panes = "A4"
    _autosize(ws1)

    ws2 = wb.create_sheet("02_Concrete_Table2")
    r = _write_heading(ws2, p2.get("meta", {}))
    t2 = p2.get("table2", {})
    _write_table(
        ws2, t2.get("title", "Table 2"), t2.get("columns", []), t2.get("rows", []), r
    )
    ws2.freeze_panes = "A4"
    _autosize(ws2)

    ws3 = wb.create_sheet("03_Rebar_SI_SIP")
    r = _write_heading(ws3, p3.get("meta", {}))
    for key in ("table3", "table4", "table5"):
        t = p3.get(key, {})
        r = _write_table(
            ws3, t.get("title", key), t.get("columns", []), t.get("rows", []), r
        )
    ws3.freeze_panes = "A4"
    _autosize(ws3)


def _build_5_tabs(wb, p1, p2, p3):
    for sheet_name, src, key in [
        ("Table1_Geotech", p1, "table1"),
        ("Table2_Concrete", p2, "table2"),
        ("Table3_Rebar", p3, "table3"),
        ("Table4_Struct", p3, "table4"),
        ("Table5_SIP", p3, "table5"),
    ]:
        ws = wb.create_sheet(sheet_name)
        r = _write_heading(ws, src.get("meta", {}))
        t = src.get(key, {})
        _write_table(
            ws, t.get("title", key), t.get("columns", []), t.get("rows", []), r
        )
        ws.freeze_panes = "A4"
        _autosize(ws)


# ─────────────────────────────────────────────────────────────────────────────
# NEW HELPERS for build_workbook_v2 (branded, 10-tab)
# ─────────────────────────────────────────────────────────────────────────────


def _thin_border() -> Border:
    s = Side(style="thin", color=BORDER_C)
    return Border(left=s, right=s, top=s, bottom=s)


def _hfill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color)


def _fmt(val: Any) -> str:
    """Flatten any value to a clean Excel string."""
    if val is None:
        return ""
    if isinstance(val, list):
        return "\n".join(f"• {_fmt(v)}" for v in val if v)
    if isinstance(val, dict):
        return "\n".join(f"{k}: {_fmt(v)}" for k, v in val.items() if v)
    return str(val).strip()


def _v2_title_block(ws: Worksheet, title: str, meta: Dict) -> int:
    """Write branded title + meta. Returns next available row."""
    # Navy title bar
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=12)
    c = ws.cell(row=1, column=1, value=title)
    c.font = Font(bold=True, size=13, color=WHITE, name="Calibri")
    c.fill = _hfill(NAVY)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 28

    # Orange accent strip
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=12)
    ws.cell(row=2, column=1).fill = _hfill(ORANGE)
    ws.row_dimensions[2].height = 4

    row = 3
    for label, value in [
        ("Project:", meta.get("project", "")),
        ("Created By:", meta.get("created_by", "")),
        ("Generated:", meta.get("generated_date", "")),
    ]:
        if value:
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
            ws.merge_cells(start_row=row, start_column=5, end_row=row, end_column=12)
            lc = ws.cell(row=row, column=1, value=label)
            vc = ws.cell(row=row, column=5, value=value)
            lc.font = Font(bold=True, size=10, color=NAVY, name="Calibri")
            vc.font = Font(size=10, name="Calibri")
            lc.fill = vc.fill = _hfill("EEF1F5")
            lc.alignment = vc.alignment = Alignment(wrap_text=True, vertical="top")
            row += 1

    return row + 1  # blank spacer


def _v2_header_row(ws: Worksheet, columns: List[str], row: int):
    for c, label in enumerate(columns, 1):
        cell = ws.cell(row=row, column=c, value=label)
        cell.font = Font(bold=True, size=10, color=WHITE, name="Calibri")
        cell.fill = _hfill(NAVY)
        cell.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        cell.border = _thin_border()
    ws.row_dimensions[row].height = 20


def _v2_data_rows(ws: Worksheet, columns: List[str], rows: List[Dict], start_row: int):
    for i, row_data in enumerate(rows):
        r = start_row + i
        fill = _hfill(ROW_LIGHT) if i % 2 == 0 else _hfill(WHITE)
        for c, col in enumerate(columns, 1):
            val = row_data.get(col, "")
            cell = ws.cell(row=r, column=c, value=_fmt(val))
            cell.font = Font(size=10, name="Calibri")
            cell.fill = fill
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.border = _thin_border()
        ws.row_dimensions[r].height = 55


def _v2_write_sheet(ws: Worksheet, tbl: Dict, meta: Dict, col_widths: List[int] = None):
    title = tbl.get("title", ws.title)
    columns = tbl.get("columns", [])
    rows = tbl.get("rows", [])

    hdr_row = _v2_title_block(ws, title, meta)
    _v2_header_row(ws, columns, hdr_row)
    _v2_data_rows(ws, columns, rows, hdr_row + 1)
    ws.freeze_panes = ws.cell(row=hdr_row + 1, column=1).coordinate

    if col_widths:
        for i, w in enumerate(col_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w
    else:
        _autosize(ws)


def _v2_write_table1(ws: Worksheet, tbl: Dict, header: Dict, meta: Dict):
    """Table 1 gets an extra lot-size / flatwork info block."""
    title = tbl.get("title", "Table 1 – Field Testing Requirements")
    columns = tbl.get("columns", [])
    rows = tbl.get("rows", [])

    row = _v2_title_block(ws, title, meta)

    # Site info block
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=12)
    c = ws.cell(row=row, column=1, value="PROJECT SITE INFORMATION")
    c.font = Font(bold=True, size=10, color=WHITE, name="Calibri")
    c.fill = _hfill(ORANGE)
    c.alignment = Alignment(horizontal="center", vertical="center")
    row += 1

    lot = header.get("total_lot_size", {})
    flat = header.get("total_flatwork", {})

    info_rows = [
        (
            "Total Lot Size",
            f"{lot.get('value_sqft') or 'NOT SPECIFIED'}"
            + (f"  ({lot.get('value_acres')} acres)" if lot.get("value_acres") else ""),
        ),
        ("Total Pavement Sqft", flat.get("total_pavement_sqft") or "NOT SPECIFIED"),
        (
            "Total Foundation Floor Sqft",
            flat.get("total_foundation_floor_sqft") or "NOT SPECIFIED",
        ),
        ("Total Building Sqft", flat.get("total_building_sqft") or "NOT SPECIFIED"),
        (
            "Flatwork Exceeds Lot?",
            (
                "⚠ YES — " + str(flat.get("conflict_note", ""))
                if flat.get("flatwork_exceeds_lot")
                else "No"
            ),
        ),
    ]

    for label, value in info_rows:
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
        ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=12)
        lc = ws.cell(row=row, column=1, value=label)
        vc = ws.cell(row=row, column=4, value=str(value))
        lc.font = Font(bold=True, size=10, color=NAVY, name="Calibri")
        vc.font = Font(size=10, name="Calibri")
        lc.fill = vc.fill = _hfill("EEF1F5")
        lc.alignment = vc.alignment = Alignment(wrap_text=True, vertical="top")
        row += 1

    row += 1  # spacer

    _v2_header_row(ws, columns, row)
    _v2_data_rows(ws, columns, rows, row + 1)
    ws.freeze_panes = ws.cell(row=row + 1, column=1).coordinate

    widths = [22, 18, 14, 16, 16, 18, 28, 28, 28, 20]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ─────────────────────────────────────────────────────────────────────────────
# NEW build_workbook_v2 — 10-tab branded workbook
# ─────────────────────────────────────────────────────────────────────────────


def build_workbook_v2(all_tables: Dict[str, Any]) -> bytes:
    """
    Builds a branded 10-sheet workbook from the merged extraction dict.
    Expected keys: meta, header, table1 … table10, assumptions_or_gaps
    """
    wb = Workbook()
    wb.remove(wb.active)

    meta = all_tables.get("meta", {})
    header = all_tables.get("header", {})

    SHEETS = [
        # (tab_name,              dict_key,   col_widths or None)
        ("T1 – Geotech", "table1", None),  # special writer
        ("T2 – Concrete", "table2", [22, 12, 16, 14, 12, 12, 20, 12, 12, 12, 24, 16]),
        ("T3 – Rebar", "table3", [22, 10, 18, 20, 28, 16]),
        ("T4 – Structural", "table4", [28, 12, 40, 16]),
        ("T5 – SIP", "table5", [24, 32, 28, 16]),
        ("T6 – Masonry", "table6", [22, 14, 12, 12, 18, 18, 22, 16, 18, 24, 16]),
        ("T7 – Earthwork", "table7", [24, 18, 24, 22, 22, 18, 16]),
        ("T8 – Utilities", "table8", [22, 18, 14, 18, 18, 18, 16, 18, 24, 16]),
        ("T9 – Inspections", "table9", [20, 24, 16, 16, 22, 18, 16, 16]),
        ("T10 – Summary", "table10", [34, 12, 16, 24, 24, 16]),
    ]

    for tab_name, key, widths in SHEETS:
        ws = wb.create_sheet(tab_name)
        tbl = all_tables.get(key) or {
            "title": tab_name,
            "columns": ["Note"],
            "rows": [{"Note": "No data extracted for this table."}],
        }

        if key == "table1":
            _v2_write_table1(ws, tbl, header, meta)
        else:
            _v2_write_sheet(ws, tbl, meta, col_widths=widths)

    # Gaps & Assumptions tab
    gaps = all_tables.get("assumptions_or_gaps") or []
    if gaps:
        ws_g = wb.create_sheet("Gaps & Assumptions")
        ws_g.merge_cells("A1:C1")
        c = ws_g["A1"]
        c.value = "Assumptions & Gaps Identified by AI"
        c.font = Font(bold=True, size=12, color=WHITE, name="Calibri")
        c.fill = _hfill(NAVY)
        c.alignment = Alignment(horizontal="center", vertical="center")
        ws_g.row_dimensions[1].height = 26
        for i, note in enumerate(gaps, 2):
            cell = ws_g.cell(row=i, column=1, value=f"• {note}")
            cell.font = Font(size=10, name="Calibri")
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            cell.fill = _hfill(ROW_LIGHT if i % 2 == 0 else WHITE)
            ws_g.row_dimensions[i].height = 40
        ws_g.column_dimensions["A"].width = 100

    wb.active = wb.worksheets[0]
    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()
