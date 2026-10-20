"""Persist the independently verified repair onto its isolated audit branch."""
import base64
import json
import os
import urllib.request
from pathlib import Path

branch = "audit/workbook-application-20261020"
if os.environ["GITHUB_REF"] != "refs/heads/" + branch:
    raise RuntimeError("Repair publication is restricted to the audit branch.")
repo = os.environ["GITHUB_REPOSITORY"]
root = "https://api.github.com/repos/" + repo
headers = {
    "Authorization": "Bearer " + os.environ["GH_TOKEN"],
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "Content-Type": "application/json",
}

def api(path, payload=None, method=None):
    request = urllib.request.Request(
        root + path, headers=headers,
        data=None if payload is None else json.dumps(payload).encode(), method=method)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)

result = json.loads((Path(os.environ["RUNNER_TEMP"]) /
                     "portfolio_workbook_application/result.json").read_text())
if not result["passed"] or result["failures"]:
    raise RuntimeError("Independent application audit did not pass.")
reference = api("/git/ref/heads/" + branch)
if reference["object"]["sha"] != os.environ["GITHUB_SHA"]:
    raise RuntimeError("Audit branch moved during verification.")
revision_path = Path("reports/workbook_validation_revision_20261020.json")
revision = json.loads(revision_path.read_text())
revision["status"] = "passed_independent_application_rerun"
revision["audit_run_url"] = "https://github.com/" + repo + "/actions/runs/" + os.environ["GITHUB_RUN_ID"]
revision_path.write_text(json.dumps(revision, indent=2) + "\n")
result["audit_run_url"] = revision["audit_run_url"]
Path("reports/workbook_application_verification_20261020.json").write_text(
    json.dumps(result, indent=2, allow_nan=False) + "\n")
paths = [
    "artifacts/Corporate_Finance_Decision_Lab.xlsx",
    "docs/exports/Corporate_Finance_Decision_Lab.xlsx",
    "tools/build_workbook.mjs",
    "reports/workbook_verification.json",
    "reports/workbook_verification_before_boundary_revision_20261020.json",
    "reports/workbook_validation_revision_20261020.json",
    "reports/workbook_application_verification_20261020.json",
    "reports/application_audit_plan_20261020.json",
]
parent = api("/git/commits/" + os.environ["GITHUB_SHA"])
entries = []
for path in paths:
    raw = Path(path).read_bytes()
    blob = api("/git/blobs", {"content": base64.b64encode(raw).decode(), "encoding": "base64"})
    entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob["sha"]})
tree = api("/git/trees", {"base_tree": parent["tree"]["sha"], "tree": entries})
commit = api("/git/commits", {
    "message": "Correct workbook spread validation after independent application checks",
    "tree": tree["sha"], "parents": [os.environ["GITHUB_SHA"]],
})
api("/git/refs/heads/" + branch, {"sha": commit["sha"], "force": False}, method="PATCH")
print("WORKBOOK_REPAIR_COMMIT=" + commit["sha"])
