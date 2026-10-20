"""One-time, byte-preserving fix for the published workbook domain guard."""
import copy
import hashlib
import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

OLD_SHA = "81b8d409e4d4c96d2ffd5ea083ab785fcfdb0e8723630d66df7f55b035a6d019"
PATHS = ["artifacts/Corporate_Finance_Decision_Lab.xlsx",
         "docs/exports/Corporate_Finance_Decision_Lab.xlsx"]
SELECTED = "INDEX($D$23:$L$23,1,$D$4)"
OLD_GUARD = SELECTED + "-$D$11>=0.0001"
NEW_GUARD = (SELECTED + "-$D$11>=0.0001-1.7763568394002505E-15*MAX(ABS(" +
             SELECTED + "),ABS($D$11),0.0001)")
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"

raw = Path(PATHS[0]).read_bytes()
if hashlib.sha256(raw).hexdigest() != OLD_SHA:
    raise RuntimeError("Original workbook identity differs.")
if Path(PATHS[1]).read_bytes() != raw:
    raise RuntimeError("Published workbook copies differ.")

with zipfile.ZipFile(io.BytesIO(raw)) as original:
    rels = {r.attrib["Id"]: r.attrib["Target"]
            for r in ET.fromstring(original.read("xl/_rels/workbook.xml.rels"))}
    wb = ET.fromstring(original.read("xl/workbook.xml"))
    sheet = next(s for s in wb.find("s:sheets", NS)
                 if s.attrib["name"] == "Assumptions")
    target = rels[sheet.attrib[RID]]
    target = target.lstrip("/") if target.startswith("/") else "xl/" + target
    text = original.read(target).decode("utf-8")
    root = ET.fromstring(text)
    formula = root.find(".//s:c[@r='D12']/s:f", NS).text
    if formula.count(OLD_GUARD) != 1:
        raise RuntimeError("Original terminal-spread guard differs.")
    revised_formula = formula.replace(OLD_GUARD, NEW_GUARD)
    pattern = re.compile(
        r'(<(?:[A-Za-z_][\w.-]*:)?c\b[^>]*\br\s*=\s*[\x22\x27]D12[\x22\x27][^>]*>'
        r'.*?<(?:[A-Za-z_][\w.-]*:)?f\b[^>]*>)(.*?)(</(?:[A-Za-z_][\w.-]*:)?f>)',
        re.S)
    match = pattern.search(text)
    if not match:
        raise RuntimeError("Target formula XML was not found.")
    revised = text[:match.start(2)] + escape(revised_formula) + text[match.end(2):]
    check = ET.fromstring(revised)
    if check.find(".//s:c[@r='D12']/s:f", NS).text != revised_formula:
        raise RuntimeError("Revised formula XML differs.")
    # Prove that all other XML content, including every cached value, is unchanged.
    node = check.find(".//s:c[@r='D12']/s:f", NS)
    node.text = formula
    if ET.tostring(check) != ET.tostring(root):
        raise RuntimeError("Unexpected worksheet alteration.")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as output:
        output.comment = original.comment
        for item in original.infolist():
            content = revised.encode("utf-8") if item.filename == target else original.read(item.filename)
            output.writestr(copy.copy(item), content)
    updated = buffer.getvalue()
    with zipfile.ZipFile(io.BytesIO(updated)) as verified:
        if verified.testzip() is not None:
            raise RuntimeError("Revised workbook ZIP is corrupt.")
        for item in original.infolist():
            if item.filename != target and verified.read(item.filename) != original.read(item.filename):
                raise RuntimeError("Unrelated XLSX member changed.")

for filename in PATHS:
    Path(filename).write_bytes(updated)
new_sha = hashlib.sha256(updated).hexdigest()
new_blob = hashlib.sha1(b"blob " + str(len(updated)).encode() + b"\0" + updated).hexdigest()

builder_path = Path("tools/build_workbook.mjs")
builder = builder_path.read_text()
needle = "-$D$11>=0.0001"
replacement = ("-$D$11>=0.0001-1.7763568394002505E-15*MAX(ABS(" +
               "$" + "{selected}" + "),ABS($D$11),0.0001)")
if builder.count(needle) != 1:
    raise RuntimeError("Builder guard anchor differs.")
builder_path.write_text(builder.replace(needle, replacement))

report_path = Path("reports/workbook_verification.json")
old_report = report_path.read_bytes()
Path("reports/workbook_verification_before_boundary_revision_20261020.json").write_bytes(old_report)
report = json.loads(old_report)
report["original_workbook_sha256"] = OLD_SHA
report["workbook_sha256"] = new_sha
report["post_export_validation_revision"] = "reports/workbook_validation_revision_20261020.json"
report["verification_scope_note"] = (
    "The 932 construction checks describe the original Artifact Tool build. "
    "The later terminal-spread guard revision is separately checked in LibreOffice Calc; "
    "see workbook_application_verification_20261020.json. Native Microsoft Excel was not executed."
)
report_path.write_text(json.dumps(report, indent=2) + "\n")

revision = {
    "status": "patched_pending_independent_application_rerun",
    "finding": "Valid exact-one-basis-point terminal spreads could be rejected by floating-point subtraction.",
    "original_workbook_sha256": OLD_SHA, "revised_workbook_sha256": new_sha,
    "revised_workbook_git_blob": new_blob,
    "sheet": "Assumptions", "cell": "D12",
    "original_guard": OLD_GUARD, "revised_guard": NEW_GUARD,
    "roundoff_rule": "Eight times the double-precision spacing at 1, scaled by max(|WACC|, |terminal growth|, 0.0001), matching the Python validation contract.",
    "original_xml_member": target,
    "all_other_xlsx_members_and_cached_values_unchanged": True,
    "published_scenario_results_changed": False,
    "original_release_retained": "v1.0.2",
    "verification": "reports/workbook_application_verification_20261020.json",
}
Path("reports/workbook_validation_revision_20261020.json").write_text(
    json.dumps(revision, indent=2) + "\n")
manifest_path = Path("reports/application_audit_plan_20261020.json")
manifest = json.loads(manifest_path.read_text())
for book in manifest["books"]:
    if book["key"] == "finance":
        book["commit"] = "CHECKOUT"
        book["workbook"]["blob"] = new_blob
        book["sha256"] = new_sha
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
print("WORKBOOK_PATCH=" + json.dumps(revision))
