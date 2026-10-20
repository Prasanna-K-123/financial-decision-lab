import base64,json,os,pathlib,urllib.request
repo=os.environ["GITHUB_REPOSITORY"]
branch="audit/browser-acceptance-20261020"
expected=os.environ["GITHUB_SHA"]
assert repo=="Prasanna-K-123/financial-decision-lab"
assert os.environ["GITHUB_REF_NAME"]==branch
root=pathlib.Path("audit/browser-evidence")
if not (root/"report.json").is_file():
    raise SystemExit("No browser report produced; nothing published.")
def api(method,route,data=None):
    request=urllib.request.Request("https://api.github.com/repos/"+repo+route,
        data=None if data is None else json.dumps(data).encode(),
        headers={"Authorization":"Bearer "+os.environ["GH_TOKEN"],"Accept":"application/vnd.github+json","Content-Type":"application/json","X-GitHub-Api-Version":"2022-11-28"},method=method)
    with urllib.request.urlopen(request,timeout=60) as response:
        return json.load(response)
ref=api("GET","/git/ref/heads/"+branch)
assert ref["object"]["sha"]==expected,"Audit branch changed; refusing publication."
base=api("GET","/git/commits/"+expected)
files=sorted(root.glob("*.json"))+sorted(root.glob("*.png"))
assert 1<=len(files)<=80
lock=pathlib.Path("audit/runtime/package-lock.json")
if lock.is_file():files.append(lock)
entries=[]
for file in files:
    data=file.read_bytes()
    assert len(data)<6_000_000,"Evidence file exceeded publication bound."
    target="audit/browser-evidence/package-lock.json" if file==lock else file.as_posix()
    blob=api("POST","/git/blobs",{"content":base64.b64encode(data).decode(),"encoding":"base64"})
    entries.append({"path":target,"mode":"100644","type":"blob","sha":blob["sha"]})
tree=api("POST","/git/trees",{"base_tree":base["tree"]["sha"],"tree":entries})
commit=api("POST","/git/commits",{"message":"Record independent browser acceptance evidence","parents":[expected],"tree":tree["sha"]})
ref2=api("GET","/git/ref/heads/"+branch)
assert ref2["object"]["sha"]==expected,"Audit branch changed during publication."
api("PATCH","/git/refs/heads/"+branch,{"sha":commit["sha"],"force":False})
print(json.dumps({"evidence_commit":commit["sha"],"files":len(files),"branch":branch}))
