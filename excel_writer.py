from __future__ import annotations

from typing import Dict, Any, List, Tuple
from datetime import date
from io import BytesIO

import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font, Alignment
from openpyxl.worksheet.worksheet import Worksheet


# If you want 5 tabs instead of 3, set to True.
SPLIT_TABLES_TO_TABS = False


def _write_heading(ws: Worksheet, meta: Dict[str, Any], start_row: int = 1) -> int:
    """
    Writes a 2-line heading block and returns the next empty row.
    """
    ws.cell(row=start_row, column=1, value=f"Generated: {meta.get('generated_date','')}")
    ws.cell(row=start_row + 1, column=1, value=f"Created by: {meta.get('created_by','')}")
    ws.cell(row=start_row, column=1).font = Font(bold=True)
    ws.cell(row=start_row + 1, column=1).font = Font(bold=True)
    return start_row + 3


def _autosize(ws: Worksheet, max_width: int = 70):
    # crude autosize
    for col in ws.columns:
        max_len = 0
        col_letter = col[0].column_letter
        for cell in col:
            v = cell.value
            if v is None:
                continue
            s = str(v)
            if len(s) > max_len:
                max_len = len(s)
        ws.column_dimensions[col_letter].width = min(max(12, max_len + 2), max_width)


def _sanitize_for_excel(val: Any) -> Any:
    """
    Convert values that Excel/openpyxl can't handle into strings.
    """
    if isinstance(val, list):
        # Convert lists to comma-separated strings
        return ", ".join(str(v) for v in val)
    elif isinstance(val, dict):
        # Convert dicts to string representation
        return str(val)
    elif val is None:
        return ""
    else:
        return val


def _write_table(ws: Worksheet, title: str, columns: List[str], rows: List[Dict[str, Any]], start_row: int) -> int:
    ws.cell(row=start_row, column=1, value=title).font = Font(bold=True, size=12)
    start_row += 1

    # Sanitize all values in rows before creating DataFrame
    sanitized_rows = []
    for row in rows:
        sanitized_row = {k: _sanitize_for_excel(v) for k, v in row.items()}
        sanitized_rows.append(sanitized_row)

    df = pd.DataFrame(sanitized_rows)
    
    # ensure column order
    df = df.reindex(columns=columns)

    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), start=start_row):
        for c_idx, val in enumerate(row, start=1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            if r_idx == start_row:  # header
                cell.font = Font(bold=True)
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            else:
                cell.alignment = Alignment(wrap_text=True, vertical="top")

    end_row = start_row + len(df.index) + 2  # + header + blank row
    return end_row


def build_workbook(prompt1: Dict[str, Any], prompt2: Dict[str, Any], prompt3: Dict[str, Any]) -> bytes:
    wb = Workbook()
    # remove default sheet
    wb.remove(wb.active)

    if SPLIT_TABLES_TO_TABS:
        _build_5_tabs(wb, prompt1, prompt2, prompt3)
    else:
        _build_3_tabs(wb, prompt1, prompt2, prompt3)

    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()


def _build_3_tabs(wb: Workbook, p1: Dict[str, Any], p2: Dict[str, Any], p3: Dict[str, Any]):
    ws1 = wb.create_sheet("01_Geotech_Table1")
    r = _write_heading(ws1, p1.get("meta", {}), start_row=1)
    t1 = p1.get("table1", {})
    r = _write_table(ws1, t1.get("title","Table 1"), t1.get("columns", []), t1.get("rows", []), r)
    ws1.freeze_panes = "A4"
    _autosize(ws1)

    ws2 = wb.create_sheet("02_Concrete_Table2")
    r = _write_heading(ws2, p2.get("meta", {}), start_row=1)
    t2 = p2.get("table2", {})
    r = _write_table(ws2, t2.get("title","Table 2"), t2.get("columns", []), t2.get("rows", []), r)
    ws2.freeze_panes = "A4"
    _autosize(ws2)

    ws3 = wb.create_sheet("03_Rebar_SI_SIP")
    r = _write_heading(ws3, p3.get("meta", {}), start_row=1)

    for key in ("table3", "table4", "table5"):
        t = p3.get(key, {})
        r = _write_table(ws3, t.get("title", key), t.get("columns", []), t.get("rows", []), r)
    ws3.freeze_panes = "A4"
    _autosize(ws3)


def _build_5_tabs(wb: Workbook, p1: Dict[str, Any], p2: Dict[str, Any], p3: Dict[str, Any]):
    # Table 1
    ws = wb.create_sheet("Table1_Geotech")
    r = _write_heading(ws, p1.get("meta", {}), start_row=1)
    t = p1.get("table1", {})
    _write_table(ws, t.get("title","Table 1"), t.get("columns", []), t.get("rows", []), r)
    ws.freeze_panes = "A4"
    _autosize(ws)

    # Table 2
    ws = wb.create_sheet("Table2_Concrete")
    r = _write_heading(ws, p2.get("meta", {}), start_row=1)
    t = p2.get("table2", {})
    _write_table(ws, t.get("title","Table 2"), t.get("columns", []), t.get("rows", []), r)
    ws.freeze_panes = "A4"
    _autosize(ws)

    # Table 3
    ws = wb.create_sheet("Table3_Rebar")
    r = _write_heading(ws, p3.get("meta", {}), start_row=1)
    t = p3.get("table3", {})
    _write_table(ws, t.get("title","Table 3"), t.get("columns", []), t.get("rows", []), r)
    ws.freeze_panes = "A4"
    _autosize(ws)

    # Table 4
    ws = wb.create_sheet("Table4_Struct_Fire")
    r = _write_heading(ws, p3.get("meta", {}), start_row=1)
    t = p3.get("table4", {})
    _write_table(ws, t.get("title","Table 4"), t.get("columns", []), t.get("rows", []), r)
    ws.freeze_panes = "A4"
    _autosize(ws)

    # Table 5
    ws = wb.create_sheet("Table5_SIP")
    r = _write_heading(ws, p3.get("meta", {}), start_row=1)
    t = p3.get("table5", {})
    _write_table(ws, t.get("title","Table 5"), t.get("columns", []), t.get("rows", []), r)
    ws.freeze_panes = "A4"
    _autosize(ws)