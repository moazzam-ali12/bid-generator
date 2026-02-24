from __future__ import annotations
from typing import Dict, List


def _common_rules_json_only() -> str:
    return (
        "OUTPUT RULES (MANDATORY):\n"
        "1) Return STRICT JSON only. No markdown. No backticks. No commentary.\n"
        "2) Use the exact JSON schema requested.\n"
        "3) If a value is not explicitly found in the provided documents, write \"NOT SPECIFIED\".\n"
        "4) NEVER format numbers with commas (e.g. write 181000 not 181,000). JSON numbers must have no commas.\n"
        "4) Never invent drawing numbers, report numbers, quantities, or requirements.\n"
        "5) For every row include a 'sources' field listing where you found it e.g. "
        "\"Geotech.pdf p.17\" or \"Civil.pdf sheet C-001\". If not found: \"NOT FOUND\".\n"
        "6) If two provided documents conflict on the SAME requirement, set the field value "
        "to \"CONFLICT\" and include both sources. Do NOT flag as conflict if the requirement "
        "only appears in one document.\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT 0 — COVER PAGE
# ─────────────────────────────────────────────────────────────────────────────

def prompt_0_cover_page(user_info: dict, project_name: str, doc_list: List[str]) -> Dict:
    """Cover Page — user info, project address, county/city, referenced docs, tables generated."""

    name    = user_info.get("name", "")
    company = user_info.get("company", "")
    phone   = user_info.get("phone", "")
    email   = user_info.get("email", "")
    created_by_line = ", ".join(filter(None, [name, company, phone]))

    user = f"""
You are generating the Cover Page metadata for a CMT / Special Inspection proposal.

Project: {project_name}
Documents provided (filenames): {", ".join(doc_list)}

USER INFO (use only what is provided — omit blank fields):
- Created By : {name}
- Company    : {company}
- Phone      : {phone}
- Email      : {email}
- Header line format: "{created_by_line}"

TASKS:
1. Extract the project property address from the design drawings.
2. Use your knowledge to identify the county and city for that address.
3. List all documents referenced as part of this effort (use filenames provided).
4. Record today's date (the date this prompt was run).
5. List the tables that were generated:
   Geotechnical Requirements, Flatwork/Foundation Requirements,
   Structural Requirements, Quantity Estimation.

{_common_rules_json_only()}

JSON SCHEMA (must match exactly):
{{
  "meta": {{
    "project": "{project_name}",
    "generated_date": "YYYY-MM-DD",
    "created_by": "{created_by_line}"
  }},
  "cover_page": {{
    "created_by"          : "{name}",
    "company"             : "{company}",
    "phone"               : "{phone}",
    "email"               : "{email}",
    "project_address"     : "",
    "county"              : "",
    "city"                : "",
    "date_run"            : "YYYY-MM-DD",
    "referenced_documents": [],
    "tables_generated"    : [
      "Geotechnical Requirements",
      "Flatwork/Foundation Requirements",
      "Structural Requirements",
      "Quantity Estimation"
    ]
  }}
}}

DOCUMENT CONTEXT:
""".strip()

    return {
        "system": (
            "You are a meticulous senior construction analyst at Paige Engineering, LLC. "
            "Extract only what is explicitly stated in the documents. Follow all output rules."
        ),
        "user": user,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT 1 — TABLE 1: GEOTECHNICAL TECHNICAL REQUIREMENTS
# ─────────────────────────────────────────────────────────────────────────────

def prompt_1_table1(user_info: dict, project_name: str, doc_list: List[str]) -> Dict:
    """Table 1 — Geotechnical Technical Requirements (11 columns per Herman's spec)."""

    name    = user_info.get("name", "")
    company = user_info.get("company", "")
    phone   = user_info.get("phone", "")
    email   = user_info.get("email", "")
    created_by_line = ", ".join(filter(None, [name, company, phone]))

    user = f"""
You are generating Table 1 (Geotechnical Technical Requirements) for a CMT / Special Inspection proposal.

Project: {project_name}
Documents provided (filenames): {", ".join(doc_list)}

HEADER BLOCK (extract from documents):
- created_by       : "{created_by_line}"
- company          : "{company}"
- phone            : "{phone}"
- email            : "{email}"
- project_address  : Extract from design drawings
- county           : Look up from address
- city             : Look up from address
- referenced_docs  : List all documents provided

PRIMARY SOURCES (focus here first):
- Geotechnical Engineering Report
- Geotechnical Addendum (overrides geotech report where conflicts exist)
- Civil Engineering Design Drawings: General Notes, Site Plan, Foundation Plan,
  Pavement Layout, Plan View, Civil Details
  NOTE: If plans include plumbing drawings, separate plumbing utilities from Civil utilities.

GUIDANCE:
- If specifications exist, plans typically reference spec numbers rather than providing
  technical requirements directly. When plans do provide technical requirements, carefully
  check for conflicts with specifications.
- If a requirement appears in one document only, do NOT flag as conflict.
- Only flag conflicts when the SAME requirement appears in BOTH documents with DIFFERENT values.

═══════════════════════════════════════
TABLE 1 — 11 COLUMNS:
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
  Output: If data conflicts between documents, add conflicting rows at bottom flagged for resolution.

COLUMN 2 — Material Type
  If one material maps to multiple construction elements, create a SEPARATE row for each.
  Keywords: Native material, aggregate, base, lime stabilized subgrade,
  cement treated subgrade, sand, clay, silt, flex base, PI, general fill, embankment,
  granular cap, granular fill, moisture conditioned soil, cement treated sand,
  cement treated base, fly-ash, Tru-BLN

COLUMN 3 — Specification Reference
  List the specification number and title (ALL CAPS) that correlates to the construction element.
  Identify the section and subsection where requirements are found.
  If no specification package provided, leave blank.
  If multiple specifications per row, bulletize them.
  Keywords: embankment, select fill, concrete placement, backfill of structures,
  utility backfill, cement stabilized sand, hydraulic concrete
  Output format: "03300 CONCRETE PLACEMENT, Section 2.1.3" (number + title in ALL CAPS + section)

COLUMN 4 — Backfill Layer Thickness
  Report in inches. Typical: 6", 8", 12", 18", 24"
  Keywords: Backfill Layer Thickness, Max Loose Thickness, Loose Material Depth

COLUMN 5 — Compaction Requirements
  Report as percentage. Include ASTM standard if referenced.
  Keywords: %, percent, percent compaction, ASTM D698, ASTM D1557, Max Dry Density, Compaction

COLUMN 6 — Moisture Content Tolerance
  Report as +/- format (e.g. "-2% to +2%")
  Keywords: +/-, +, -, tolerance, percent, ASTM D698, ASTM D1557, Max Dry Density

COLUMN 7 — Plasticity Requirements
  Report PI max/min, liquid limit, plastic limit, soil classification if stated.
  Keywords: PI, plastic limit, liquid limit, select fill, soil classification

COLUMN 8 — Special Testing Notes
  Bulletize all special requirements found that do not fit columns 1-6.
  Keywords: proofroll, proof roll, proof-roll, clods, mellowing, mixing,
  sieving analysis, measuring, testing, confirmation, depth checks,
  swell test, resistivity test

COLUMN 9 — Testing Frequency
  Bulletize all testing/inspection frequencies (multiple may exist per material).
  Keywords: per, set, sample

COLUMN 10 — Conflicts or Addendums
  ONLY flag when the SAME requirement appears in BOTH documents with DIFFERENT values.
  Bulletize each conflict. Include both document sources.
  Do NOT flag if requirement only appears in one document.

COLUMN 11 — References
  For each piece of data, list: sheet number or page number + document name.
  Tag each reference to its corresponding column number.
  Example: "Col 5: Geotech.pdf p.12", "Col 4: Civil.pdf sheet C-002"

{_common_rules_json_only()}

JSON SCHEMA (must match exactly):
{{
  "meta": {{
    "project": "{project_name}",
    "generated_date": "YYYY-MM-DD",
    "created_by": "{created_by_line}"
  }},
  "header": {{
    "created_by"         : "{created_by_line}",
    "company"            : "{company}",
    "phone"              : "{phone}",
    "email"              : "{email}",
    "project_address"    : "",
    "county"             : "",
    "city"               : "",
    "referenced_documents": []
  }},
  "table1": {{
    "title": "Table 1 – Geotechnical Technical Requirements",
    "columns": [
      "Construction Element", "Material Type", "Specification Reference",
      "Backfill Layer Thickness", "Compaction Requirements",
      "Moisture Content Tolerance", "Plasticity Requirements",
      "Special Testing Notes", "Testing Frequency",
      "Conflicts or Addendums", "References"
    ],
    "rows": [
      {{
        "Construction Element"   : "",
        "Material Type"          : "",
        "Specification Reference": "",
        "Backfill Layer Thickness": "",
        "Compaction Requirements": "",
        "Moisture Content Tolerance": "",
        "Plasticity Requirements": "",
        "Special Testing Notes"  : [""],
        "Testing Frequency"      : [""],
        "Conflicts or Addendums" : [""],
        "References"             : [""],
        "sources"                : [""]
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
# PROMPT 2 — TABLE 2: FLATWORK/FOUNDATION TECHNICAL REQUIREMENTS
# ─────────────────────────────────────────────────────────────────────────────

def prompt_2_table2(user_info: dict, project_name: str, doc_list: List[str]) -> Dict:
    """Table 2 — Flatwork/Foundation Technical Requirements (Herman's spec)."""

    name    = user_info.get("name", "")
    company = user_info.get("company", "")
    phone   = user_info.get("phone", "")
    created_by_line = ", ".join(filter(None, [name, company, phone]))

    user = f"""
You are generating Table 2 (Flatwork/Foundation Technical Requirements) for a CMT / Special Inspection proposal.
Bring forward the same header information from Table 1 and display similarly at the top.

Project: {project_name}
Documents provided (filenames): {", ".join(doc_list)}

PRIMARY SOURCES:
- Geotechnical Engineering Report
- Civil Engineering Design Drawings: General Notes, Site Plan, Foundation Plan,
  Pavement Layout, Plan View, Civil Details
- Structural Engineering Drawings: General Notes, Foundation Plans, Details

GUIDANCE:
- This table summarizes physical width, depth, length, diameter, sizes, thicknesses of
  flatwork/foundation and rebar. It does NOT focus on quantities (that is Prompt 4).
- Do NOT bring geotechnical subgrade or compaction testing data into this table.
  This is strictly for reinforcement and structural details of flatwork and foundation.
- Even if flatwork does not need testing, add it to the table — let reviewer confirm.
- If multiple depth/thickness instances exist for the same element, separate into distinct rows.
- Only flag conflicts when the SAME requirement appears in BOTH documents with DIFFERENT values.

═══════════════════════════════════════
TABLE 2 — COLUMNS:
═══════════════════════════════════════

COLUMN 1 — Flatwork/Foundation Element
  Keywords: Drilled Piers, Belled Piers, Slurry Piers, Piles, retaining walls,
  cast-in-place, footings, pavement, asphalt concrete pavement, concrete pavement,
  heavy duty, light duty, standard duty, driveway, sidewalk, ramps, stairs,
  curb, slotted curb, curb and gutter, bollards, light pole foundation,
  traffic pole foundation, pier cap, bent cap, column, pile cap, mass pour, roll over curb

COLUMN 2 — Material or Mix
  Keywords: Type D, Type B, 64-22, 78-26 TOM, Class A, Class B, Class C, Class F,
  Class HEC, Class, Permeable, concrete, asphalt
  Include asphalt binder numbers if present. Do not include strength here.

COLUMN 3 — Thickness/Depth
  Keywords: Thick, Long, Wide, Deep, diameter, inch, feet
  If multiple thickness/depth instances for same element, separate into distinct rows.

COLUMN 4 — Air Content
  Report target with acceptable +/- range as percentage.
  Keywords: % air content, ASTM C231, ASTM C173
  Note: could apply to grout, mortar, or special mix.

COLUMN 5 — Slump/Spread
  Report target with acceptable +/- range in inches.
  Keywords: inches, spread, ASTM (slump test)

COLUMN 6 — Temperature
  Report min/max with time dependency if applicable.
  Keywords: degrees, F, Fahrenheit
  Include time dependency in output if it corresponds to max/min value.

COLUMN 7 — Compaction Requirements (asphalt)
  For asphalt elements only — report compaction % (RICE, air voids if referenced).
  Keywords: %, percent, percent compaction, RICE, Max Dry Density, air voids

COLUMN 8 — Time Dependency
  Any time-based requirements for the material.
  Keywords: Minute, Hour, Days

COLUMN 9 — Reinforcement
  List all rebar/reinforcement requirements for each element.
  Keywords: Rebar, reinforcement, dowel bar, lap splice, spacing, size,
  edge clear space, depth, tie bar, embedment, longitudinal, transverse,
  vertical, hook, stirrups, O.C., OCEW, U-bars, hoop bars, placement
  Note: Civil drawings will be more basic. Structural drawings may have multiple details
  per element — list each condition separately.

COLUMN 10 — Detail Reference
  Sheet number and detail number for each reinforcement condition.
  Label with numbers matching reinforcement conditions (Condition 1 → Detail Ref 1).
  Note: Sheet numbers look like C-001, S101 — NOT page numbers like "125 of 200".

COLUMN 11 — Inspection Frequency
  Testing and inspection frequencies for each element.
  Do NOT include geotechnical testing.

COLUMN 12 — Conflicts or Addendums
  Only flag when the SAME requirement appears in BOTH documents with DIFFERENT values.
  (e.g., differing depths, concrete strengths, rebar sizes, rebar spacing)

COLUMN 13 — References
  Sheet number / page number / detail number for each data point.
  Tag each reference to its corresponding column number.

{_common_rules_json_only()}

JSON SCHEMA (must match exactly):
{{
  "meta": {{
    "project": "{project_name}",
    "generated_date": "YYYY-MM-DD",
    "created_by": "{created_by_line}"
  }},
  "table2": {{
    "title": "Table 2 – Flatwork/Foundation Technical Requirements",
    "columns": [
      "Flatwork/Foundation Element", "Material or Mix", "Thickness/Depth",
      "Air Content", "Slump/Spread", "Temperature",
      "Compaction Requirements", "Time Dependency",
      "Reinforcement", "Detail Reference",
      "Inspection Frequency", "Conflicts or Addendums", "References"
    ],
    "rows": [
      {{
        "Flatwork/Foundation Element": "",
        "Material or Mix"            : "",
        "Thickness/Depth"            : "",
        "Air Content"                : "",
        "Slump/Spread"               : "",
        "Temperature"                : "",
        "Compaction Requirements"    : "",
        "Time Dependency"            : "",
        "Reinforcement"              : [""],
        "Detail Reference"           : [""],
        "Inspection Frequency"       : [""],
        "Conflicts or Addendums"     : [""],
        "References"                 : [""],
        "sources"                    : [""]
      }}
    ]
  }},
  "assumptions_or_gaps": [""]
}}

DOCUMENT CONTEXT:
""".strip()

    return {
        "system": (
            "You are a meticulous senior structural and civil construction analyst. "
            "Extract only what is explicitly stated. Do not include geotechnical compaction data."
        ),
        "user": user,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PROMPT 3 — TABLE 3: STRUCTURAL TECHNICAL REQUIREMENTS (ABOVE-GRADE ONLY)
# ─────────────────────────────────────────────────────────────────────────────

def prompt_3_table3(user_info: dict, project_name: str, doc_list: List[str]) -> Dict:
    """Table 3 — Structural Technical Requirements (above-grade elements only)."""

    name    = user_info.get("name", "")
    company = user_info.get("company", "")
    phone   = user_info.get("phone", "")
    created_by_line = ", ".join(filter(None, [name, company, phone]))

    user = f"""
You are generating Table 3 (Structural Technical Requirements) for a CMT / Special Inspection proposal.
Bring forward the same header information from Table 1 and display similarly at the top.

Project: {project_name}
Documents provided (filenames): {", ".join(doc_list)}

PRIMARY SOURCES:
- Structural Engineering Drawings (most important — start here)
- Architectural Drawings (second priority)
- Civil Design Drawings (third priority)

GUIDANCE:
- The ICC Building Code year specified in the structural drawings sets the requirements.
- In the general notes of structural drawings, find the Special Inspections summary table.
  This table shows: inspection frequency, type of inspection, structural element being inspected.
- Do NOT bring in soil, subgrade, or pavement into this table (already in Tables 1 and 2).
- Do NOT bring in at-grade reinforcement like paving and foundations.
- ONLY include rebar/reinforcement for elements that are ABOVE GRADE.
- Reinforcement is not a structural element — the column or retaining wall is the element,
  and rebar details go in other columns.
- Only flag conflicts when the SAME requirement appears in BOTH documents with DIFFERENT values.

═══════════════════════════════════════
TABLE 3 — COLUMNS:
═══════════════════════════════════════

COLUMN 1 — Structural Element (above-grade only)
  Keywords: CMU Walls, CMU Bond Beam, Lintels, Columns, Steel, Plinth, piles,
  retaining walls, bolting, welding, field weld, CJP, PJP, fillet welds,
  welding inspection, cold form metal framing, fire, deck, metal,
  structural insulated panels, plate, sill, air leakage, seams,
  windows, doors, anchor, bolts, railing, joints, construction joint, expansion joint
  Output: List each structural element found. Separate conflicting data at bottom for user resolution.

COLUMN 2 — Material Type
  Keywords: steel, concrete, CMU, mortar, masonry, structural insulated panels,
  wood, pre-cast concrete, cast-in-place concrete, post-tensioned concrete
  Focus on structural drawings.

COLUMN 3 — Member Size
  Keywords: W, Thick, Long, Wide, Deep, diameter, inch, feet
  Examples: 18WX54, 24" diameter column, 8' tall x 12" thick retaining wall
  Do NOT include reinforcement sizes or fastener sizes here.
  If wood/truss/framing schedules exist, list various sizes as bullets under the element.

COLUMN 4 — Fasteners and Welding
  List all fastener and weld types/sizes for each structural element.
  Multiple types may apply — list all.
  Keywords: Anchor bolt, nails, screws, lag bolt, CJP, PJP, fillet
  Do NOT include reinforcement as fasteners.

COLUMN 5 — Inspection Frequency
  Testing and inspection frequencies for each structural element.
  Do NOT include geotechnical testing.

COLUMN 6 — Conflicts or Addendums
  Only flag when the SAME requirement appears in BOTH documents with DIFFERENT values.
  (e.g., differing welds, anchor sizes, fastener sizes, member sizes, concrete strengths)

COLUMN 7 — References
  Sheet number / page number / detail number for each data point.
  Tag each reference to its corresponding column number.

{_common_rules_json_only()}

JSON SCHEMA (must match exactly):
{{
  "meta": {{
    "project": "{project_name}",
    "generated_date": "YYYY-MM-DD",
    "created_by": "{created_by_line}"
  }},
  "table3": {{
    "title": "Table 3 – Structural Technical Requirements",
    "columns": [
      "Structural Element", "Material Type", "Member Size",
      "Fasteners and Welding", "Inspection Frequency",
      "Conflicts or Addendums", "References"
    ],
    "rows": [
      {{
        "Structural Element"     : "",
        "Material Type"          : "",
        "Member Size"            : "",
        "Fasteners and Welding"  : [""],
        "Inspection Frequency"   : [""],
        "Conflicts or Addendums" : [""],
        "References"             : [""],
        "sources"                : [""]
      }}
    ]
  }},
  "assumptions_or_gaps": [""]
}}

DOCUMENT CONTEXT:
""".strip()

    return {
        "system": (
            "You are a meticulous senior structural construction analyst. "
            "Extract only above-grade structural elements. "
            "Do not include soil, subgrade, pavement, or at-grade foundations."
        ),
        "user": user,
    }


# ─────────────────────────────────────────────────────────────────────────────
# FINAL PROMPT — QUANTITY ESTIMATION
# ─────────────────────────────────────────────────────────────────────────────

def prompt_final_quantities(user_info: dict, project_name: str, doc_list: List[str]) -> Dict:
    """Final Prompt — Quantity Estimation (Sections A–E per Herman's spec)."""

    name    = user_info.get("name", "")
    company = user_info.get("company", "")
    phone   = user_info.get("phone", "")
    created_by_line = ", ".join(filter(None, [name, company, phone]))

    user = f"""
You are generating the Quantity Estimation table for a CMT / Special Inspection proposal.
Reference all documents and the tables already produced (Tables 1, 2, 3) to perform this task.

Project: {project_name}
Documents provided (filenames): {", ".join(doc_list)}

GUIDANCE:
- This prompt calculates quantities of materials requiring testing.
- We are NOT looking for sizes or inspection specifics — strictly quantities for estimating.
- Use total linear feet, square footage, cubic feet, or counts for each construction element.
- Do NOT calculate or estimate if not explicitly stated — use "NOT SPECIFIED".
- Each construction element gets one line in the table with the appropriate unit.

═══════════════════════════════════════
SECTION A — LOT SIZE
═══════════════════════════════════════
Keywords: Lot, square foot, acres
Output: Total lot square feet. If provided in acres, convert to sqft (1 acre = 43,560 sqft). Show both.

═══════════════════════════════════════
SECTION B — FOUNDATION CONSTRUCTION ELEMENTS
═══════════════════════════════════════
1. Total number of Drilled Shafts and their depths.
2. Total number of spread footings — list quantity by size (up to 10 sizes from footing schedule).
   Include associated width, length, and thickness per size.
3. Total number and length of linear footings — include width and depth (cross-section).

Validation: Total pavement area + foundation area CANNOT exceed total lot size.
If it does, flag in the conflicts field.

═══════════════════════════════════════
SECTION C — TOTAL FLATWORK CONSTRUCTION ELEMENTS
═══════════════════════════════════════
1. Total Pavement Square Footage
2. Total Foundation Floor Square Footage
3. Total Building Square Footage

Keywords: Lot, square foot, acres
Validation: Pavement area + foundation area cannot exceed total lot size. Flag if conflict.

═══════════════════════════════════════
SECTION D — TOTAL UTILITIES WORK
═══════════════════════════════════════
1. Total Water Line Length (linear feet)
2. Total Storm Sewer Length (linear feet)
3. Total Sanitary Sewer Length (linear feet)

Keywords: water, storm, sanitary, Ductile Iron, PVC, black pipe, cast-iron, HDPE
Output: Linear feet for each utility type. Include bottom depth of utilities.

═══════════════════════════════════════
SECTION E — TOTAL STRUCTURAL ELEMENTS (from Table 3)
═══════════════════════════════════════
For each structural element in Table 3:
- If material is concrete → calculate volume (cubic feet/yards) for each member, sum totals.
- For steel columns, beams, rafters → count total number of pieces.
- For Cold-Form metal framing and wood → convert to linear feet of wall.
- For CMU or cast-in-place concrete walls → convert to square footage
  (linear foot × wall height from details).

Keywords: water, storm, sanitary, Ductile Iron, PVC, black pipe, cast-iron, HDPE
Output units: counts, square feet, cubic feet, or linear feet as appropriate per element.

{_common_rules_json_only()}

JSON SCHEMA (must match exactly):
{{
  "meta": {{
    "project": "{project_name}",
    "generated_date": "YYYY-MM-DD",
    "created_by": "{created_by_line}"
  }},
  "quantity_estimation": {{
    "title": "Quantity Estimation",
    "section_a_lot_size": {{
      "total_sqft"  : null,
      "total_acres" : null,
      "source"      : ""
    }},
    "section_b_foundations": {{
      "drilled_shafts": [
        {{"count": null, "depth": "", "source": ""}}
      ],
      "spread_footings": [
        {{"size_label": "", "count": null, "width": "", "length": "", "thickness": "", "source": ""}}
      ],
      "linear_footings": [
        {{"count": null, "length": "", "width": "", "depth": "", "source": ""}}
      ],
      "conflicts": ""
    }},
    "section_c_flatwork": {{
      "total_pavement_sqft"        : null,
      "total_foundation_floor_sqft": null,
      "total_building_sqft"        : null,
      "conflicts"                  : "",
      "source"                     : ""
    }},
    "section_d_utilities": {{
      "water_line_lf"    : null,
      "storm_sewer_lf"   : null,
      "sanitary_sewer_lf": null,
      "utility_depth"    : "",
      "source"           : ""
    }},
    "section_e_structural": [
      {{
        "structural_element": "",
        "material_type"     : "",
        "quantity"          : null,
        "unit"              : "",
        "calculation_basis" : "",
        "source"            : ""
      }}
    ],
    "conflicts": [""]
  }},
  "assumptions_or_gaps": [""]
}}

DOCUMENT CONTEXT:
""".strip()

    return {
        "system": (
            "You are a meticulous senior quantity surveyor and construction analyst. "
            "Extract only explicitly stated quantities. Do not estimate or calculate unless "
            "dimensions are explicitly provided in the documents."
        ),
        "user": user,
    }