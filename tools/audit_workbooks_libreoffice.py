"""Independent application checks of two immutable published workbooks.

Run with the system Python supplied by python3-uno and LibreOffice Calc.
The source workbooks and frozen research references are never overwritten.
"""
import csv
import hashlib
import io
import json
import math
import os
import posixpath
import subprocess
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.document.MacroExecMode import NEVER_EXECUTE
from com.sun.star.document.UpdateDocMode import NO_UPDATE

ROOT = Path(os.environ.get("RUNNER_TEMP", ".")) / "portfolio_workbook_application"
ROOT.mkdir(parents=True, exist_ok=True)
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
REPORT = {
    "engine": subprocess.check_output(["soffice", "--version"], text=True).strip(),
    "scope": "Independent LibreOffice Calc; native Microsoft Excel and visual review not performed.",
    "checks": 0, "books": [], "failures": [], "worst_differences": {},
}


def require(condition, label):
    if not condition:
        raise RuntimeError(label)


def prop(name, value):
    p = PropertyValue()
    p.Name, p.Value = name, value
    return p


def close(actual, expected, label, group="financial", atol=0.0001, rtol=0):
    REPORT["checks"] += 1
    if not isinstance(actual, (int, float)) or not math.isfinite(actual):
        REPORT["failures"].append({"label": label, "actual": str(actual), "expected": expected})
        return
    difference = abs(actual - expected)
    prior = REPORT["worst_differences"].get(group, {"difference": -1})
    if difference > prior["difference"]:
        REPORT["worst_differences"][group] = {"label": label, "difference": difference}
    if difference > atol + rtol * abs(expected):
        REPORT["failures"].append({
            "label": label, "actual": actual, "expected": expected,
            "difference": difference, "atol": atol, "rtol": rtol,
        })


def fetch(book, file):
    url = "https://raw.githubusercontent.com/Prasanna-K-123/{}/{}/{}".format(
        book["repo"], book["commit"], file["path"])
    with urllib.request.urlopen(url, timeout=60) as response:
        raw = response.read()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    require(blob == file["blob"], "Pinned source blob differs: " + file["path"])
    return raw


def sheet_cells(raw):
    result = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        require(z.testzip() is None, "Corrupt XLSX member.")
        require(not any("vbaProject" in n for n in z.namelist()), "Unexpected macro payload.")
        require(not any(n.startswith("xl/externalLinks/") for n in z.namelist()),
                "Unexpected external workbook links.")
        relationships = {
            e.attrib["Id"]: e.attrib["Target"]
            for e in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        }
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        for sheet in workbook.find("s:sheets", NS):
            target = relationships[sheet.attrib[RID]]
            path = target.lstrip("/") if target.startswith("/") else posixpath.normpath(
                posixpath.join("xl", target))
            cells = []
            for c in ET.fromstring(z.read(path)).findall(".//s:c", NS):
                if c.find("s:f", NS) is None:
                    continue
                value = c.find("s:v", NS)
                cells.append({
                    "address": c.attrib["r"], "type": c.attrib.get("t", "n"),
                    "cached": value.text if value is not None else None,
                })
            result[sheet.attrib["name"]] = cells
    return result


def cell(doc, sheet, address):
    return doc.Sheets.getByName(sheet).getCellRangeByName(address)


def value(doc, sheet, address):
    c = cell(doc, sheet, address)
    require(c.getError() == 0, "Formula error: " + sheet + "!" + address)
    return c.getValue()


def formula_cache_check(doc, original, key, phase):
    compared = 0
    for sheet, cells in original.items():
        for item in cells:
            c = cell(doc, sheet, item["address"])
            label = key + "/" + phase + "/" + sheet + "!" + item["address"]
            require(c.getError() == 0, "Application formula error: " + label)
            cached = item["cached"]
            if cached is None:
                continue
            if item["type"] in ("n", "b"):
                close(c.getValue(), float(cached), label, group=key + "_cached",
                      atol=0.0001 if key == "treasury" else 0.000001, rtol=2e-12)
            elif item["type"] in ("str", "inlineStr"):
                require(c.getString() == cached, "Cached formula text differs: " + label)
            else:
                raise RuntimeError("Unexpected cached formula type: " + label)
            compared += 1
    return compared


def treasury_checks(doc, refs):
    current = json.loads(refs["reports/current_case_20261019/current_case.json"])
    annual = list(csv.DictReader(io.StringIO(
        refs["reports/current_case_20261019/runoff_years.csv"].decode())))
    predictions = json.loads(refs["reports/treasury_20261019/final_predictions.json"])
    scores = json.loads(refs["reports/treasury_20261019/final_results.json"])
    methods = ["five_year", "duration_match", "key_rate", "covariance"]
    defaults = {4: 4, 5: 12000, 6: 1, 7: 120, 8: 0, 9: 0, 10: 0,
                11: 0, 12: 0, 13: 0, 14: 1, 15: 0, 16: 0, 20: 1}

    def change(updates=None):
        active = dict(defaults)
        active.update(updates or {})
        doc.Sheets.getByName("Controls").getCellRangeByName("D4:D16").setDataArray(
            tuple((active[r],) for r in range(4, 17)))
        cell(doc, "Controls", "D20").setValue(active[20])
        doc.calculateAll()

    for expected in current["instantaneous_scenarios"]:
        updates = {
            4: methods.index(expected["method"]) + 1,
            6: expected["mortality_force"], 7: expected["maximum_paying_age"],
            8: expected["parallel_shift_decimal"] * 10000,
            14: ["svensson", "flat_forward", "flat_zero"].index(expected["tail"]) + 1,
        }
        updates.update({9 + j: shift * 10000
                        for j, shift in enumerate(expected["key_shifts_decimal"])})
        change(updates)
        for address, field in [("D129", "liability_usd"), ("D136", "assets_usd"),
                               ("D137", "surplus_usd")]:
            close(value(doc, "Benefits", address), expected[field],
                  "Treasury instant/" + expected["scenario"] + "/" + expected["method"] + "/" + field)

    row_map = {
        14: "opening_cash_usd", 15: "base_cash_interest_usd",
        16: "extra_cash_interest_usd", 18: "maturities_usd",
        21: "benefits_due_usd", 25: "gross_bond_sales_usd", 26: "haircut_cost_usd",
        27: "benefits_paid_usd", 28: "unpaid_benefits_usd", 29: "closing_cash_usd",
        40: "assets_usd", 41: "remaining_liability_usd",
        42: "unpaid_forward_carried_usd", 43: "surplus_after_unpaid_usd",
        51: "discounted_wealth_conservation_error_usd",
    }
    row_map.update({32 + j: "remaining_face_{}y_usd".format(year)
                    for j, year in enumerate([1, 5, 10, 20, 30])})
    for expected in current["runoff_scenarios"]:
        change({4: methods.index(expected["method"]) + 1,
                6: expected["mortality_force"], 15: expected["haircut"],
                16: expected["cash_rate_shift_decimal"] * 10000})
        reference_rows = [r for r in annual if int(r["case_id"]) == expected["case_id"]]
        require(len(reference_rows) == 10, "Incomplete frozen runoff case.")
        grid = doc.Sheets.getByName("Runoff").getCellRangeByName("D8:M58").getDataArray()
        for year, row in enumerate(reference_rows):
            for r, field in row_map.items():
                close(grid[r - 8][year], float(row[field]),
                      "Treasury runoff/{}/{}/{}".format(expected["case_id"], year + 1, field))
        for address, field in [("H7", "gross_bond_sales_usd"), ("H8", "haircut_cost_usd"),
                               ("H9", "unpaid_nominal_usd")]:
            close(value(doc, "ALM review", address), expected[field],
                  "Treasury runoff total/" + str(expected["case_id"]) + "/" + field)

    for month_index, month in enumerate(["2019-01", "2020-03", "2022-09"]):
        for method_index, method in enumerate(methods):
            change({4: method_index + 1, 20: month_index + 1})
            expected = next(r for r in predictions
                            if r["end_month"] == month and r["method"] == method)
            close(value(doc, "Historical", "D22"), expected["initial_liability_pv"],
                  "Treasury historical PV/" + month + "/" + method, atol=1e-9)
            close(value(doc, "Historical", "H23"), expected["surplus_change_fraction"],
                  "Treasury historical surplus/" + month + "/" + method,
                  group="historical_fraction", atol=2e-12)

    change()
    for j, method in enumerate(methods):
        expected = scores["final_scores"][method]
        close(value(doc, "Historical", "M" + str(16 + j)), expected["rmse"] * 10000,
              "Treasury final RMSE/" + method, group="historical_bps", atol=1e-10)
        close(value(doc, "Historical", "N" + str(16 + j)), expected["bias"] * 10000,
              "Treasury final bias/" + method, group="historical_bps", atol=1e-10)
    for row in range(16, 46):
        close(value(doc, "Sources", "I" + str(row)), 0,
              "Treasury quoted curve/" + str(row), group="quoted_curve_bps", atol=0.02)
    risk = current["base_liability_risk"]
    for address, field, tolerance in [
        ("D129", "pv", 0.0001), ("D130", "duration", 1e-10),
        ("D131", "convexity", 1e-9), ("D132", "dv01_usd", 0.0001),
        ("D133", "post30_pv_usd", 0.0001),
    ]:
        close(value(doc, "Benefits", address), risk[field], "Treasury risk/" + field,
              group="risk_" + field, atol=tolerance)
    for j, expected in enumerate(risk["key_dv01_usd"]):
        close(value(doc, "Benefits", "H" + str(130 + j)), expected, "Treasury key DV01")

    change({5: 0})
    require(value(doc, "Benefits", "D129") == 0, "Zero benefit rejected.")
    require(cell(doc, "Benefits", "D130").getString() == "n.a.", "Zero-benefit duration differs.")
    cell(doc, "Controls", "D5").setFormula("")
    doc.calculateAll()
    require(cell(doc, "Benefits", "D129").getError() != 0, "Missing benefit hidden as zero.")
    change({6: 0})
    require(cell(doc, "Benefits", "D129").getError() != 0, "Invalid mortality accepted.")
    change({15: 1})
    require(cell(doc, "Runoff", "M43").getError() != 0, "Invalid haircut accepted.")
    change()
    cell(doc, "Controls", "D20").setFormula("")
    doc.calculateAll()
    close(value(doc, "Benefits", "D129"), risk["pv"], "Independent current valuation")
    require(cell(doc, "Historical", "H23").getError() != 0, "Missing historical selector accepted.")
    change()
    return {"instantaneous_cases": 56, "runoff_cases": 108, "runoff_years": 1080,
            "historical_repricing_cases": 12, "boundary_checks": 6}


def finance_checks(doc, refs):
    cases = json.loads(refs["reports/valuation_scenarios.json"])

    def select(index):
        cell(doc, "Assumptions", "D4").setValue(index)
        doc.calculateAll()

    for i, expected in enumerate(cases):
        select(i + 1)
        fields = [
            expected["policy_value"], expected["upfront_investment"],
            expected["annual_cash_pv"], expected["terminal_present_value"],
            expected["no_growth_reference"],
            expected["incremental_policy_value"] / expected["no_growth_reference"],
            expected["terminal_share_of_net_value"], expected["value_per_base_nopat"],
        ]
        for j, target in enumerate(fields):
            close(value(doc, "Policy review", "D" + str(6 + j)), target,
                  "Finance summary/{}/{}".format(i + 1, j),
                  group="finance_scenarios", atol=1e-6, rtol=2e-12)
        for j, ledger in enumerate(expected["year_ledger"]):
            row = doc.Sheets.getByName("Policy review").getCellRangeByName(
                "C{}:K{}".format(22 + j, 22 + j)).getDataArray()[0]
            keys = ["year", "growth", "nopat", "marginal_roic", "next_year_nopat",
                    "net_investment", "cash_flow", "discount_factor", "present_value"]
            for actual, key in zip(row, keys):
                close(actual, ledger[key], "Finance ledger/{}/{}/{}".format(i + 1, j + 1, key),
                      group="finance_scenarios", atol=1e-6, rtol=2e-12)
        for address in ["D8", "D9"]:
            close(value(doc, "Audit", address), 0, "Finance audit/" + address,
                  group="finance_identity", atol=1e-6)
    for row in range(40, 49):
        for col in ["D", "E", "F"]:
            close(value(doc, "Audit", col + str(row)), 0, "Statement identity",
                  group="statement_identity", atol=1e-6)

    select(2)
    growth = cell(doc, "Assumptions", "E19").getValue()
    cell(doc, "Assumptions", "E19").setValue(0.12)
    doc.calculateAll()
    require(value(doc, "Policy review", "D6") != cases[1]["policy_value"],
            "Growth input failed to recalculate.")
    close(value(doc, "Audit", "D8"), 0, "Edited finance identity", atol=1e-6)
    cell(doc, "Assumptions", "E19").setValue(growth)
    unused = cell(doc, "Assumptions", "D19").getValue()
    cell(doc, "Assumptions", "D19").setFormula("")
    doc.calculateAll()
    close(value(doc, "Policy review", "D6"), cases[1]["policy_value"],
          "Unselected blank independence", atol=1e-6, rtol=2e-12)
    cell(doc, "Assumptions", "D19").setValue(unused)
    cell(doc, "Assumptions", "E19").setFormula("")
    doc.calculateAll()
    require(cell(doc, "Policy review", "D6").getError() != 0, "Active blank hidden as zero.")
    cell(doc, "Assumptions", "E19").setValue(growth)
    ebit = cell(doc, "Statements", "F8").getValue()
    cell(doc, "Statements", "F8").setValue(0)
    doc.calculateAll()
    require(value(doc, "Policy review", "D6") == 0, "Zero EBIT rejected.")
    cell(doc, "Statements", "F8").setValue(ebit)
    wacc = cell(doc, "Assumptions", "E23").getValue()
    terminal = cell(doc, "Assumptions", "E22").getValue()
    cell(doc, "Assumptions", "E23").setValue(terminal)
    doc.calculateAll()
    require(cell(doc, "Policy review", "D6").getError() != 0, "Zero terminal spread accepted.")
    cell(doc, "Assumptions", "E23").setValue(wacc)
    for bad in [0, 1.5, 10, None]:
        if bad is None:
            cell(doc, "Assumptions", "D4").setFormula("")
            doc.calculateAll()
        else:
            select(bad)
        require(cell(doc, "Policy review", "D6").getError() != 0, "Invalid selector accepted.")
    select(2)
    boundary = []
    for j in range(17):
        g = j * 0.005
        cell(doc, "Assumptions", "E22").setValue(g)
        cell(doc, "Assumptions", "E23").setValue(g + 0.0001)
        doc.calculateAll()
        error = cell(doc, "Policy review", "D6").getError()
        boundary.append({"terminal_growth": g, "wacc": g + 0.0001, "error_code": error})
        if error:
            REPORT["failures"].append({
                "label": "Exact one-basis-point spreadsheet boundary",
                "terminal_growth": g, "wacc": g + 0.0001, "error_code": error,
            })
    cell(doc, "Assumptions", "E22").setValue(terminal)
    cell(doc, "Assumptions", "E23").setValue(wacc)
    select(2)
    close(value(doc, "Policy review", "D6"), cases[1]["policy_value"],
          "Restored finance default", atol=1e-6, rtol=2e-12)
    return {"scenario_cases": 9, "ledger_rows": 90, "boundary_checks": 9,
            "exact_one_basis_point_cases": boundary}


def main():
    manifest = json.loads(Path("reports/application_audit_plan_20261020.json").read_text())
    profile = ROOT / "profile"
    process = subprocess.Popen([
        "soffice", "-env:UserInstallation=" + profile.as_uri(), "--headless", "--norestore",
        "--nodefault", "--nologo",
        "--accept=socket,host=127.0.0.1,port=2002;urp;StarOffice.ServiceManager",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    desktop = None
    try:
        context = uno.getComponentContext()
        resolver = context.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", context)
        for _ in range(120):
            try:
                remote = resolver.resolve(
                    "uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext")
                break
            except Exception:
                time.sleep(0.25)
        else:
            raise RuntimeError("LibreOffice UNO startup timed out.")
        desktop = remote.ServiceManager.createInstanceWithContext(
            "com.sun.star.frame.Desktop", remote)
        properties = (prop("Hidden", True), prop("ReadOnly", False),
                      prop("MacroExecutionMode", NEVER_EXECUTE), prop("UpdateDocMode", NO_UPDATE))
        for book in manifest["books"]:
            raw = fetch(book, book["workbook"])
            original_sha = hashlib.sha256(raw).hexdigest()
            require(original_sha == book["sha256"], "Workbook SHA-256 differs.")
            originals = sheet_cells(raw)
            folder = ROOT / book["key"]
            folder.mkdir(exist_ok=True)
            source = folder / "original.xlsx"
            source.write_bytes(raw)
            refs = {f["path"]: fetch(book, f) for f in book["refs"]}
            doc = desktop.loadComponentFromURL(source.as_uri(), "_blank", 0, properties)
            require(doc is not None, "Workbook failed to open.")
            require(list(doc.Sheets.getElementNames()) == list(originals), "Worksheet identities differ.")
            doc.enableAutomaticCalculation(True)
            doc.calculateAll()
            record = {"key": book["key"], "commit": book["commit"],
                      "original_sha256": original_sha, "sheet_names": list(originals)}
            record["formula_cells"] = sum(len(v) for v in originals.values())
            record["cached_formula_comparisons"] = formula_cache_check(
                doc, originals, book["key"], "fresh_import")
            if book["key"] == "treasury":
                record["scenarios"] = treasury_checks(doc, refs)
            else:
                record["scenarios"] = finance_checks(doc, refs)
            record["restored_formula_comparisons"] = formula_cache_check(
                doc, originals, book["key"], "restored_default")
            output = folder / "recalculated.xlsx"
            doc.storeToURL(output.as_uri(), (
                prop("FilterName", "Calc MS Excel 2007 XML"), prop("Overwrite", True)))
            doc.close(True)
            reopened = desktop.loadComponentFromURL(output.as_uri(), "_blank", 0, properties)
            reopened.calculateAll()
            record["saved_reopen_formula_comparisons"] = formula_cache_check(
                reopened, originals, book["key"], "saved_reopen")
            reopened.close(True)
            require(hashlib.sha256(source.read_bytes()).hexdigest() == original_sha,
                    "Original workbook was modified.")
            record["source_preserved"] = True
            REPORT["books"].append(record)
            print("Completed independent application checks: " + book["key"], flush=True)
        REPORT["passed"] = not REPORT["failures"]
        require(REPORT["passed"], "Independent application checks found numerical or boundary differences.")
    finally:
        if desktop is not None:
            desktop.terminate()
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()


try:
    main()
except Exception as exc:
    REPORT["passed"] = False
    REPORT["exception"] = str(exc)
    raise
finally:
    (ROOT / "result.json").write_text(json.dumps(REPORT, indent=2, allow_nan=False) + "\n")
    print("APPLICATION_AUDIT_RESULT=" + json.dumps(REPORT, allow_nan=False), flush=True)
