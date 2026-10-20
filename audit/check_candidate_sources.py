"""Check the candidate build sources and unchanged numerical explorer behavior."""
import json,pathlib,shutil,subprocess,sys,urllib.request
root=pathlib.Path.cwd()
c=root/"audit/candidates"
finance=c/"financial-decision-lab"
for name in ("docs/index.html","tools/explorer.js","tools/explorer_template.html"):
    shutil.copyfile(finance/name,root/name)
expected=(finance/"docs/index.html").read_bytes()
subprocess.run([sys.executable,"tools/build_demo.py"],check=True)
assert (root/"docs/index.html").read_bytes()==expected,"Finance builder drifted from reviewed HTML"
subprocess.run(["node","tests/check_explorer.cjs"],check=True)
inflation=c/"inflation-vintages"
check=root/"audit/runtime/inflation-check"
commit="dc27fac8b63aa4f84c85cbe807e109e7d6aa757a"
for name in ("tests/check_explorer.cjs","tests/dom_harness.cjs","reports/final.json","docs/style.css"):
    target=check/name;target.parent.mkdir(parents=True,exist_ok=True)
    url="https://raw.githubusercontent.com/Prasanna-K-123/inflation-vintages/"+commit+"/"+name
    with urllib.request.urlopen(url,timeout=30) as response:target.write_bytes(response.read())
(check/"docs/index.html").write_bytes((inflation/"docs/index.html").read_bytes())
data=json.loads((check/"reports/final.json").read_text())
encoded=json.dumps(data,separators=(",",":"),sort_keys=True,allow_nan=False).replace("<","\\u003c")
template=(inflation/"docs/demo.template.html").read_text()
rebuilt=template.replace("__DATA__",encoded).replace("__STYLE__",(check/"docs/style.css").read_text())
assert rebuilt==(inflation/"docs/index.html").read_text(),"Inflation builder drifted from reviewed HTML"
subprocess.run(["node",str(check/"tests/check_explorer.cjs")],check=True)
print(json.dumps({"finance_builder_exact":True,"inflation_builder_exact":True,"existing_numeric_explorer_checks":"passed"}))
