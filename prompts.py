from __future__ import annotations

from typing import Dict, List


CREATED_BY_LINE = "Herman G. Lehman IV, PE, Atlas Technical Consultants; 210-287-1300"


def _common_rules_json_only() -> str:
    return (
        "OUTPUT RULES (MANDATORY):\n"
        "1) Return STRICT JSON only. No markdown. No backticks. No commentary.\n"
        "2) Use the exact JSON schema requested.\n"
        "3) If a value is not explicitly found in the provided documents, write \"NOT SPECIFIED\".\n"
        "4) Never invent drawing numbers, report numbers, quantities, or requirements.\n"
        "5) For every row, include a 'sources' field listing where you found it, e.g. "
        "\"Geotech.pdf p.17\" or \"Civil.pdf sheet 13\". If not found: \"NOT FOUND\".\n"
        "6) If two provided documents conflict on the SAME requirement, set the field value "
        "to \"CONFLICT\" and include both sources. Do NOT flag as conflict if the requirement "
        "only appears in one document.\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT 1 → TABLE 1: Geotechnical & Civil Field Testing Requirements
# ─────────────────────────────────────────────────────────────────────────────

def prompt_1_table1(project_name: str, doc_list: List[str]) -> Dict:
    """Table 1 — Geotechnical & Civil Field Testing Requirements (Herman's 10-column spec)"""

    user = f"""
You are generating Table 1 for a CMT / Special Inspection proposal.

Project: {project_name}
Documents provided (filenames): {", ".join(doc_list)}

PRIMARY SOURCES (focus here first):
- Geotechnical Engineering Report (primary source)
- Geotechnical Addendum (changes/overrides to geotech report)
- Civil Engineering Design Drawings — focus on:
  General Notes, Site Plan, Foundation Plan, Pavement Layout, Plan View, Civil Details

SECONDARY SOURCES (scan for supporting data):
- All other uploaded documents

═══════════════════════════════════════
HEADER BLOCK:
═══════════════════════════════════════
- created_by: use exactly → {CREATED_BY_LINE}
- generated_date: today's date (YYYY-MM-DD)
- total_lot_size:
    Keywords: Lot, square foot, acres
    Rule: if provided in acres, convert to sqft (1 acre = 43,560 sqft). Show both values.
- total_flatwork:
    Extract separately:
      • Total Pavement Square Footage
      • Total Foundation Floor Square Footage
      • Total Building Square Footage
    Validation: if (pavement sqft + foundation sqft) > total lot size sqft,
    set flatwork_exceeds_lot = true and describe in conflict_note.

═══════════════════════════════════════
TABLE ROWS — 10 COLUMNS:
═══════════════════════════════════════

COLUMN 1 — Construction Element
  Order rows strictly by physical depth, deepest first:
  Drilled Piers → Belled Piers → Slurry Piers → Piles →
  In-Situ/Native Material → Subgrade → Utilities (Electrical, Storm, Water, Sanitary) →
  Sub-base → Base → Lime-Stabilized Subgrade → Cement Stabilized Subgrade →
  Moisture Conditioned Subgrade → General Site Fill → Select Fill → Building Pad
  Keywords: Drilled Piers, Belled Piers, Slurry Piers, Piles, In-Situ/Native Material,
  Subgrade, Sub-base, Base, Lime-Stabilized Subgrade, Cement Stabilized Subgrade,
  Moisture Conditioned Subgrade, Electrical Utility, Storm Sewer Utility, Water Line Utility,
  Sanitary Utility, General Site Fill, Select Fill, Building Pad

COLUMN 2 — Material Type
  If one material maps to multiple construction elements, create a SEPARATE row for each.
  Keywords: Native material, aggregate, base, lime stabilized subgrade,
  cement treated subgrade, sand, clay, silt, flex base, PI, general fill, embankment,
  granular cap, granular fill, moisture conditioned soil, cement treated sand,
  cement treated base, fly-ash, Tru-BLN

COLUMN 3 — Max Loose Thickness
  Report in inches. Typical values: 6 in, 8 in, 12 in, 18 in, 24 in
  Keywords: Backfill Layer Thickness, Max Loose Thickness, Loose Material Depth

COLUMN 4 — Compaction Requirements
  Report as percentage. Include ASTM standard if referenced.
  Keywords: %, percent, percent compaction, ASTM D698, ASTM D1557, Max Dry Density, Compaction

COLUMN 5 — Moisture Content Tolerance
  Report as +/- format (e.g. "-2% to +2%")
  Keywords: +/-, +, -, tolerance, percent, ASTM D698, ASTM D1557, Max Dry Density

COLUMN 6 — Plasticity Requirements
  Report PI max/min, liquid limit, plastic limit, soil classification if stated.
  Keywords: PI, plastic limit, liquid limit, select fill, soil classification

COLUMN 7 — Special Testing Notes
  Bulletize all special requirements found.
  Keywords: proofroll, proof roll, proof-roll, clods, mellowing, mixing,
  sieving analysis, measuring, testing, confirmation, depth checks,
  swell test, resistivity test

COLUMN 8 — Testing Frequency
  Bulletize all testing/inspection frequencies found (multiple may exist per material).
  Keywords: per, set, sample

COLUMN 9 — Conflicts or Addendums
  ONLY flag when the SAME requirement appears in BOTH documents with DIFFERENT values.
  Do NOT flag if a requirement appears in only one document.
  Bulletize each conflict. Include both document sources for each conflict.

COLUMN 10 — References
  For each piece of data found, list: sheet number or page number + document name.
  Tag each reference to its corresponding column number (e.g. "Col 4: Geotech.pdf p.12").

{_common_rules_json_only()}

JSON SCHEMA (must match exactly):
{{
  "meta": {{
    "project": "{project_name}",
    "generated_date": "YYYY-MM-DD",
    "created_by": "{CREATED_BY_LINE}"
  }},
  "header": {{
    "total_lot_size": {{
      "value_sqft": null,
      "value_acres": null,
      "source": ""
    }},
    "total_flatwork": {{
      "total_pavement_sqft": null,
      "total_foundation_floor_sqft": null,
      "total_building_sqft": null,
      "flatwork_exceeds_lot": false,
      "conflict_note": ""
    }}
  }},
  "table1": {{
    "title": "Table 1 – Field Testing Requirements (Geotech + Civil)",
    "columns": [
      "Construction Element", "Material Type", "Max Loose Thickness",
      "Compaction Requirements", "Moisture Content Tolerance",
      "Plasticity Requirements", "Special Testing Notes",
      "Testing Frequency", "Conflicts or Addendums", "References"
    ],
    "rows": [
      {{
        "Construction Element": "",
        "depth_order": null,
        "Material Type": "",
        "Max Loose Thickness": "",
        "Compaction Requirements": "",
        "Moisture Content Tolerance": "",
        "Plasticity Requirements": "",
        "Special Testing Notes": [""],
        "Testing Frequency": [""],
        "Conflicts or Addendums": [""],
        "References": [{{"column_ref": "", "sheet_or_page": "", "document": ""}}],
        "sources": [""]
      }}
    ]
  }},
  "assumptions_or_gaps": [""]
}}

DOCUMENT CONTEXT:
""".strip()

    return {
        "system": (
            "You are a meticulous senior geotechnical and civil construction analyst. "
            "Extract only what is explicitly stated. Follow column rules and depth ordering strictly."
        ),
        "user": user,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT 2 → TABLE 2: Concrete Summary
# ─────────────────────────────────────────────────────────────────────────────

def prompt_2_table2(project_name: str, doc_list: List[str]) -> Dict:
    """Table 2 — Concrete Summary"""

    user = f"""
You are generating Table 2 for a CMT / Special Inspection proposal.

Project: {project_name}
Documents provided (filenames): {", ".join(doc_list)}

Task:
Create "Table 2 – Concrete Summary" covering ALL concrete elements found including:
heavy-duty pavement, standard-duty pavement, tank slab, sidewalks, building slab-on-grade,
dumpster pad, grade beams/footings, piers (if any), curbs (if specified).

For each row (one concrete element/type) populate ALL columns below.
Do NOT guess quantities — use "NOT SPECIFIED" if not explicitly stated.

Keywords to scan:
f'c, psi, compressive strength, concrete mix, slump, air content, water-cement ratio,
cylinders, test set, testing frequency, max temperature, grade beam, footing, slab,
pavement, sidewalk, curb, pier, dumpster pad, tank slab, CY, cubic yards, square feet

{_common_rules_json_only()}

JSON SCHEMA (must match exactly):
{{
  "meta": {{
    "project": "{project_name}",
    "generated_date": "YYYY-MM-DD",
    "created_by": "{CREATED_BY_LINE}"
  }},
  "table2": {{
    "title": "Table 2 – Concrete Summary",
    "columns": [
      "Element / Location", "Thickness", "Total SF (or LF/CY basis)",
      "Concrete Yards (CY)", "Cylinders (count)", "f'c (psi)",
      "Testing Frequency", "Max Temp (°F)", "Air Content", "Slump (in)",
      "Notes / Mix Notes", "sources"
    ],
    "rows": [
      {{
        "Element / Location": "",
        "Thickness": "",
        "Total SF (or LF/CY basis)": "",
        "Concrete Yards (CY)": "",
        "Cylinders (count)": "",
        "f'c (psi)": "",
        "Testing Frequency": "",
        "Max Temp (°F)": "",
        "Air Content": "",
        "Slump (in)": "",
        "Notes / Mix Notes": "",
        "sources": [""]
      }}
    ]
  }},
  "assumptions_or_gaps": [""]
}}

DOCUMENT CONTEXT:
""".strip()

    return {
        "system": "You are a meticulous construction document analyst. Extract only what is explicitly stated.",
        "user": user,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT 3 → TABLES 3, 4, 5: Reinforcement + Structural/Fire + SIP
# ─────────────────────────────────────────────────────────────────────────────

def prompt_3_tables3_4_5(project_name: str, doc_list: List[str]) -> Dict:
    """Tables 3, 4, 5 — Reinforcement + Structural & Fire Protection + SIP Connections"""

    user = f"""
You are generating Tables 3, 4, and 5 for a CMT / Special Inspection proposal.

Project: {project_name}
Documents provided (filenames): {", ".join(doc_list)}

─────────────────────────────────────────
TABLE 3 — Reinforcement Summary
─────────────────────────────────────────
Tabulate rebar for ALL reinforced elements:
pavement, foundations/grade beams, footings, piers, sidewalks,
slab-on-grade, curbs/ramps, retaining walls, any other reinforced concrete.

Keywords: rebar, bar size, #3, #4, #5, #6, spacing, configuration, lap splice,
development length, ties, stirrups, temperature steel, shrinkage steel,
ASTM A615, ASTM A706, epoxy coated

─────────────────────────────────────────
TABLE 4 — Structural & Fire Protection Summary
─────────────────────────────────────────
Confirm and report each item below.
ONLY report explicit values — use "NOT SPECIFIED" if not stated.

Items to check:
- Cold-Formed Metal Framing (CFMF): Yes/No + linear feet of wall framing
- Structural Steel Bolting: Yes/No + number of discrete steel members shown
- Spray-Applied Fire Protection (SFRM): Yes/No + thickness/depth requirements
- CJP Welds: Yes/No
- PJP Welds: Yes/No
- Largest Fillet Weld size

Keywords: CFMF, cold-formed, structural steel, HSS, W-shape, bolts, ASTM A325,
ASTM A490, fire protection, sprayed fireproofing, intumescent, CJP, PJP,
fillet weld, weld size, AWS D1.1

─────────────────────────────────────────
TABLE 5 — SIP Panel Connection Inspection Requirements
─────────────────────────────────────────
Summarize SIP panel connection inspection requirements from any SIP plans/specs provided.
If SIP plans are NOT present, state this clearly and return "NOT SPECIFIED" for all details.

Keywords: SIP, structural insulated panel, panel connection, spline, surface spline,
double 2x, LVL, OSB, fastener, screw pattern, adhesive, bearing plate

{_common_rules_json_only()}

JSON SCHEMA (must match exactly):
{{
  "meta": {{
    "project": "{project_name}",
    "generated_date": "YYYY-MM-DD",
    "created_by": "{CREATED_BY_LINE}"
  }},
  "table3": {{
    "title": "Table 3 – Reinforcement Summary",
    "columns": ["Location / Element", "Bar Size", "Configuration",
                "Spacing / Dimensions", "Notes / Reference", "sources"],
    "rows": [
      {{
        "Location / Element": "", "Bar Size": "", "Configuration": "",
        "Spacing / Dimensions": "", "Notes / Reference": "", "sources": [""]
      }}
    ]
  }},
  "table4": {{
    "title": "Table 4 – Structural & Fire Protection Summary",
    "columns": ["Item", "Answer", "Details", "sources"],
    "rows": [
      {{"Item": "Cold-Formed Metal Framing (CFMF)", "Answer": "", "Details": "", "sources": [""]}},
      {{"Item": "Structural Steel Bolting",         "Answer": "", "Details": "", "sources": [""]}},
      {{"Item": "Spray-Applied Fire Protection (SFRM)", "Answer": "", "Details": "", "sources": [""]}},
      {{"Item": "CJP Welds",          "Answer": "", "Details": "", "sources": [""]}},
      {{"Item": "PJP Welds",          "Answer": "", "Details": "", "sources": [""]}},
      {{"Item": "Largest Fillet Weld","Answer": "", "Details": "", "sources": [""]}}
    ]
  }},
  "table5": {{
    "title": "Table 5 – SIP Panel Connection Inspection Requirements",
    "columns": ["Connection / Topic", "Requirement",
                "Acceptance Criteria / Frequency", "sources"],
    "rows": [
      {{
        "Connection / Topic": "", "Requirement": "",
        "Acceptance Criteria / Frequency": "", "sources": [""]
      }}
    ]
  }},
  "assumptions_or_gaps": [""]
}}

DOCUMENT CONTEXT:
""".strip()

    return {
        "system": "You are a meticulous construction document analyst. Extract only what is explicitly stated.",
        "user": user,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT 4 → TABLES 6, 7: Masonry + Soils / Earthwork Quantities
# ─────────────────────────────────────────────────────────────────────────────

def prompt_4_tables6_7(project_name: str, doc_list: List[str]) -> Dict:
    """Tables 6, 7 — Masonry Summary + Soils & Earthwork Quantities"""

    user = f"""
You are generating Tables 6 and 7 for a CMT / Special Inspection proposal.

Project: {project_name}
Documents provided (filenames): {", ".join(doc_list)}

─────────────────────────────────────────
TABLE 6 — Masonry Summary
─────────────────────────────────────────
Tabulate ALL masonry elements found in the documents.
If no masonry is specified, return a single row with "NOT SPECIFIED".

Keywords: CMU, concrete masonry unit, block, brick, grout, mortar, masonry wall,
reinforced masonry, f'm, ASTM C90, ASTM C476, ASTM C270, type S mortar,
type M mortar, prism test, masonry inspection, fully grouted, partially grouted,
joint reinforcement, ladder wire, truss wire

For each masonry element populate:
- Element / Location
- Wall Type (CMU, brick, etc.)
- Thickness (in)
- f'm (psi)
- Grout Type & Strength
- Mortar Type & Mix
- Reinforcement (vertical/horizontal bar sizes and spacing)
- Inspection Level (continuous / periodic)
- Testing Frequency
- Special Notes
- sources

─────────────────────────────────────────
TABLE 7 — Soils & Earthwork Quantities
─────────────────────────────────────────
Extract all earthwork and soils-related quantities from civil drawings and geotech report.
Use "NOT SPECIFIED" if quantity is not explicitly stated — do NOT calculate or estimate.

Keywords: cut, fill, import, export, cubic yards, CY, grading, excavation,
earthwork balance, borrow, haul, lime treatment, cement treatment, subgrade,
pavement section, ABC, crushed stone, flexible base, rigid base, total area,
site area, acres, square feet, depth of treatment

For each item populate:
- Work Item
- Quantity (with units)
- Material Description
- Specification / Standard
- Testing Requirement
- Frequency
- sources

{_common_rules_json_only()}

JSON SCHEMA (must match exactly):
{{
  "meta": {{
    "project": "{project_name}",
    "generated_date": "YYYY-MM-DD",
    "created_by": "{CREATED_BY_LINE}"
  }},
  "table6": {{
    "title": "Table 6 – Masonry Summary",
    "columns": [
      "Element / Location", "Wall Type", "Thickness (in)", "f'm (psi)",
      "Grout Type & Strength", "Mortar Type & Mix",
      "Reinforcement", "Inspection Level", "Testing Frequency",
      "Special Notes", "sources"
    ],
    "rows": [
      {{
        "Element / Location": "", "Wall Type": "", "Thickness (in)": "",
        "f'm (psi)": "", "Grout Type & Strength": "", "Mortar Type & Mix": "",
        "Reinforcement": "", "Inspection Level": "", "Testing Frequency": "",
        "Special Notes": "", "sources": [""]
      }}
    ]
  }},
  "table7": {{
    "title": "Table 7 – Soils & Earthwork Quantities",
    "columns": [
      "Work Item", "Quantity", "Material Description",
      "Specification / Standard", "Testing Requirement", "Frequency", "sources"
    ],
    "rows": [
      {{
        "Work Item": "", "Quantity": "", "Material Description": "",
        "Specification / Standard": "", "Testing Requirement": "",
        "Frequency": "", "sources": [""]
      }}
    ]
  }},
  "assumptions_or_gaps": [""]
}}

DOCUMENT CONTEXT:
""".strip()

    return {
        "system": "You are a meticulous construction document analyst. Extract only what is explicitly stated.",
        "user": user,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT 5 → TABLES 8, 9, 10: Utilities + Special Inspections + Project Summary
# ─────────────────────────────────────────────────────────────────────────────

def prompt_5_tables8_9_10(project_name: str, doc_list: List[str]) -> Dict:
    """Tables 8, 9, 10 — Utilities/Site Work + Special Inspections Checklist + Project Summary"""

    user = f"""
You are generating Tables 8, 9, and 10 for a CMT / Special Inspection proposal.

Project: {project_name}
Documents provided (filenames): {", ".join(doc_list)}

─────────────────────────────────────────
TABLE 8 — Utilities & Site Work Summary
─────────────────────────────────────────
Tabulate ALL underground utility and site work elements requiring inspection or testing.

Keywords: storm sewer, sanitary sewer, water line, gas line, electrical conduit,
duct bank, fire line, irrigation, utility trench, bedding, pipe zone, backfill,
linear feet, LF, diameter, pipe material, PVC, HDPE, RCP, DIP, compaction,
bedding material, haunching, initial backfill, final backfill, density testing

For each utility/site work item populate:
- Utility / Work Item
- Pipe Material & Diameter
- Total Linear Feet
- Trench Bedding Type
- Backfill Material
- Compaction Requirement
- Testing Frequency
- Inspection Type
- Special Notes
- sources

─────────────────────────────────────────
TABLE 9 — Special Inspections Checklist
─────────────────────────────────────────
List ALL special inspections identified across the entire document set.
Cross-reference IBC Section 1705 requirements where applicable.

Keywords: special inspection, statement of special inspections, IBC 1705,
continuous inspection, periodic inspection, fabricator, approved fabricator,
geotechnical observation, structural observation, deputy inspector,
soils, concrete, masonry, steel, welding, bolting, fireproofing,
cold-formed framing, SIP panels, driven piles, drilled piers

For each special inspection item populate:
- Inspection Category
- Specific Work Item
- Inspection Type (Continuous / Periodic / Statement)
- IBC / Code Reference
- Required Inspector Qualification
- Frequency / Trigger
- Responsible Party
- sources

─────────────────────────────────────────
TABLE 10 — Project Summary & Estimated Testing Quantities
─────────────────────────────────────────
Provide a roll-up summary of ALL testing and inspection quantities
derived from Tables 1–9. This is the bid quantity table.

For each line item populate:
- Service / Test Description
- Unit
- Estimated Quantity
- Basis / Source (which table + element)
- Notes
- sources

Include these line items at minimum (add others found in documents):
- Nuclear Density Tests (earthwork)
- Nuclear Density Tests (utility backfill)
- Concrete Cylinder Sets
- Concrete Slump / Air / Temp Tests
- Masonry Prism Tests
- Mortar Cube Tests
- Grout Prism Tests
- Reinforcement Observation (hours)
- Structural Steel Bolt Inspection (connections)
- Weld Visual Inspection (hours)
- SFRM Thickness Tests
- CFMF Inspection (hours)
- SIP Connection Inspection (hours)
- Geotechnical Observation (hours)
- Proofroll Observation (hours)
- Special Inspection — Other

{_common_rules_json_only()}

JSON SCHEMA (must match exactly):
{{
  "meta": {{
    "project": "{project_name}",
    "generated_date": "YYYY-MM-DD",
    "created_by": "{CREATED_BY_LINE}"
  }},
  "table8": {{
    "title": "Table 8 – Utilities & Site Work Summary",
    "columns": [
      "Utility / Work Item", "Pipe Material & Diameter", "Total Linear Feet",
      "Trench Bedding Type", "Backfill Material", "Compaction Requirement",
      "Testing Frequency", "Inspection Type", "Special Notes", "sources"
    ],
    "rows": [
      {{
        "Utility / Work Item": "", "Pipe Material & Diameter": "",
        "Total Linear Feet": "", "Trench Bedding Type": "",
        "Backfill Material": "", "Compaction Requirement": "",
        "Testing Frequency": "", "Inspection Type": "",
        "Special Notes": "", "sources": [""]
      }}
    ]
  }},
  "table9": {{
    "title": "Table 9 – Special Inspections Checklist",
    "columns": [
      "Inspection Category", "Specific Work Item", "Inspection Type",
      "IBC / Code Reference", "Required Inspector Qualification",
      "Frequency / Trigger", "Responsible Party", "sources"
    ],
    "rows": [
      {{
        "Inspection Category": "", "Specific Work Item": "",
        "Inspection Type": "", "IBC / Code Reference": "",
        "Required Inspector Qualification": "", "Frequency / Trigger": "",
        "Responsible Party": "", "sources": [""]
      }}
    ]
  }},
  "table10": {{
    "title": "Table 10 – Project Summary & Estimated Testing Quantities",
    "columns": [
      "Service / Test Description", "Unit", "Estimated Quantity",
      "Basis / Source", "Notes", "sources"
    ],
    "rows": [
      {{
        "Service / Test Description": "", "Unit": "",
        "Estimated Quantity": "", "Basis / Source": "",
        "Notes": "", "sources": [""]
      }}
    ]
  }},
  "assumptions_or_gaps": [""]
}}

DOCUMENT CONTEXT:
""".strip()

    return {
        "system": "You are a meticulous construction document analyst. Extract only what is explicitly stated.",
        "user": user,
    }