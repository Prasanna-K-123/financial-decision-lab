import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import {createRequire} from "node:module";
const require=createRequire(import.meta.url);
const {chromium,firefox}=require("./runtime/node_modules/playwright");
const plan=JSON.parse(fs.readFileSync(new URL("./browser-plan.json",import.meta.url),"utf8"));
const out=path.resolve("audit/browser-evidence");
fs.mkdirSync(out,{recursive:true});
const report={schema:"portfolio-browser-acceptance-v1",started_at:new Date().toISOString(),audit_commit:process.env.GITHUB_SHA,run_id:process.env.GITHUB_RUN_ID,playwright:require("./runtime/node_modules/playwright/package.json").version,pages:[],links:[],failures:[],limits:["Actual headless viewport emulation, not physical devices.","Keyboard samples and geometry checks do not certify every accessibility or visual property.","Scientific validity relies on the separate preserved numeric/source/application audit.","Only user-owned deployed pages/download links are requested; no authentication or external crawling."]};
const fail=(r,kind,detail)=>{const f={page:r.page,browser:r.browser,viewport:r.viewport,kind,detail};r.failures.push(f);report.failures.push(f);};
const text=async p=>(await p.locator("body").innerText()).trim();
const top=async p=>{await p.evaluate(()=>window.scrollTo({top:0,behavior:"instant"}));await p.waitForTimeout(40);};
async function shot(p,name,fullPage=false){await p.screenshot({path:path.join(out,name),fullPage,animations:"disabled"});return name;}
const geometry=async p=>p.evaluate(()=>({width:innerWidth,height:innerHeight,document_width:document.documentElement.scrollWidth,body_width:document.body.scrollWidth,device_pixel_ratio:devicePixelRatio,h1:[...document.querySelectorAll("h1")].map(e=>e.innerText),overflow_candidates:[...document.querySelectorAll("body *")].filter(e=>{const r=e.getBoundingClientRect();if(!r.width||!r.height||r.right<=innerWidth+1||r.left<0)return false;let p=e.parentElement;while(p&&p!==document.body){if(["auto","scroll","hidden","clip"].includes(getComputedStyle(p).overflowX))return false;p=p.parentElement;}return true;}).slice(0,15).map(e=>({tag:e.tagName,id:e.id,class:e.className?.baseVal??e.className,text:(e.innerText||"").slice(0,90),right:e.getBoundingClientRect().right}))}));
async function exercise(p,r,seen){
 for(const el of await p.locator("select,input[type=number],input[type=range],input[type=checkbox]").all()){
  if(!await el.isVisible())continue;
  const m=await el.evaluate(e=>({id:e.id,tag:e.tagName,type:e.type,value:e.value,checked:e.checked,disabled:e.disabled,min:e.min,max:e.max,step:e.step,required:e.required,valid:e.checkValidity(),label:e.labels?.[0]?.innerText||e.getAttribute("aria-label")||"",options:e.tagName==="SELECT"?[...e.options].filter(o=>!o.disabled).map(o=>o.value):[]}));
  if(seen.has(m.id))continue;seen.add(m.id);
  if(!m.valid)fail(r,"invalid_default",m);
  if(!m.label.trim())fail(r,"unnamed_control",m.id);
  const t={...m,checks:[]};r.controls.push(t);
  if(m.disabled){t.skipped="disabled in this state";continue;}
  const before=await text(p);
  if(m.tag==="SELECT"){
   const v=m.options.find(v=>v!==m.value);
   if(v===undefined){t.skipped="single available option";continue;}
   await el.selectOption(v);
   t.checks.push({kind:"select_change",chosen:v,actual:await el.inputValue(),render_text_changed:(await text(p))!==before});
   if(await el.inputValue()!==v)fail(r,"selection_not_applied",{id:m.id,value:v});
   if(r.page==="inflation"&&m.id==="method"){
    const c=p.locator("#hindsight");
    if(await c.count()&&await c.isEnabled()){const orig=await c.isChecked();await c.setChecked(!orig);t.checks.push({kind:"enabled_hindsight_toggle",actual:await c.isChecked()});await c.setChecked(orig);}
   }
   await el.selectOption(m.value);
  }else if(m.type==="range"){
   await el.focus();await p.keyboard.press(Number(m.value)>=Number(m.max)?"ArrowLeft":"ArrowRight");
   const v=await el.inputValue();t.checks.push({kind:"range_keyboard_change",actual:v,render_text_changed:(await text(p))!==before});
   if(v===m.value)fail(r,"range_keyboard_no_change",m.id);
   await el.evaluate((e,v)=>{e.value=v;e.dispatchEvent(new Event("input",{bubbles:true}));e.dispatchEvent(new Event("change",{bubbles:true}));},m.value);
  }else if(m.type==="checkbox"){
   await el.setChecked(!m.checked);t.checks.push({kind:"checkbox_change",actual:await el.isChecked(),render_text_changed:(await text(p))!==before});await el.setChecked(m.checked);
  }else if(m.type==="number"){
   const lo=m.min===""?-100:Number(m.min),hi=m.max===""?100:Number(m.max),step=m.step==="any"||!m.step?0.05:Number(m.step);
   const v=Number(m.value)+step<=hi?Number(m.value)+step:Number(m.value)-step;
   await el.fill(String(v));const ok=await el.evaluate(e=>e.checkValidity());
   t.checks.push({kind:"valid_number_change",actual:await el.inputValue(),valid:ok,render_text_changed:(await text(p))!==before});
   if(!ok)fail(r,"valid_numeric_edit_rejected",{id:m.id,value:v});
   await el.fill(m.value);
   const probes=[];
   if(m.required)probes.push(["missing",""]);
   if(m.min!=="")probes.push(["below_min",String(lo-Math.max(1,Math.abs(lo)*.1))]);
   if(m.max!=="")probes.push(["above_max",String(hi+Math.max(1,Math.abs(hi)*.1))]);
   for(const [kind,value] of probes){
    await el.fill(value);
    const native=await el.evaluate(e=>({valid:e.checkValidity(),missing:e.validity.valueMissing,underflow:e.validity.rangeUnderflow,overflow:e.validity.rangeOverflow,aria_invalid:e.getAttribute("aria-invalid"),describedby:e.getAttribute("aria-describedby")}));
    const a=p.locator("#model-error");const visible=await a.count()?await a.isVisible():null;
    t.checks.push({kind,value,...native,error_visible:visible,error_text:visible?await a.innerText():null});
    if(native.valid)fail(r,"invalid_input_accepted",{id:m.id,kind,value});
    if(r.page==="finance"&&!visible)fail(r,"invalid_input_no_visible_error",{id:m.id,kind,value});
    await el.fill(m.value);
   }
  }
  t.restored_value=await el.inputValue();t.restored_text=(await text(p))===before;
  if(t.restored_value!==m.value)fail(r,"control_not_restored",m.id);
  if(!t.restored_text)r.warnings.push({kind:"text_not_identical_after_restore",id:m.id});
 }
}
const cached=new Map();
async function links(p,r,context){
 r.links=await p.locator("a[href]").evaluateAll(els=>els.map(e=>({href:e.href,text:e.innerText.trim()})));
 for(const l of r.links){
  const u=new URL(l.href);if(u.hostname!=="prasanna-k-123.github.io")continue;
  if(u.pathname===new URL(p.url()).pathname&&u.hash){
   const found=await p.evaluate(id=>Boolean(document.getElementById(decodeURIComponent(id))),u.hash.slice(1));r.anchors.push({href:l.href,found});if(!found)fail(r,"missing_anchor",l.href);continue;
  }
  u.hash="";const url=u.href;
  if(!cached.has(url)){
   let e;
   try{
    const q=await context.request.head(url,{timeout:20000});e={url,status:q.status(),content_type:q.headers()["content-type"]||"",method:"HEAD"};
    if(e.status===405){const g=await context.request.get(url,{headers:{Range:"bytes=0-1023"},timeout:20000});e.status=g.status();e.method="GET";}
    if(/\.(pdf|xlsx)$/i.test(u.pathname)&&e.status===200){
     const g=await context.request.get(url,{headers:{Range:"bytes=0-15"},timeout:20000});const b=await g.body();
     e.sample_status=g.status();e.magic_hex=b.subarray(0,8).toString("hex");e.delivered_bytes=b.length;
     e.signature_ok=/\.pdf$/i.test(u.pathname)?b.subarray(0,5).toString()==="%PDF-":b[0]===0x50&&b[1]===0x4b;
     if(!e.signature_ok)fail(r,"download_wrong_signature",e);
    }
   }catch(error){e={url,error:String(error)};}
   cached.set(url,e);report.links.push(e);
  }
  const e=cached.get(url);if(e.error||e.status>=400)fail(r,"broken_internal_delivery",e);
 }
}
try{
 for(const [engine,launcher] of [["chromium",chromium],["firefox",firefox]]){
  const browser=await launcher.launch({headless:true});
  for(const viewport of [{width:1440,height:1000},{width:390,height:844},{width:320,height:800}]){
   const context=await browser.newContext({viewport,deviceScaleFactor:1,reducedMotion:"reduce",...(engine==="chromium"?{isMobile:viewport.width<500,hasTouch:viewport.width<500}:{})});
   for(const item of plan.pages){
    const p=await context.newPage();p.setDefaultTimeout(12000);
    const r={page:item.id,url:plan.host+item.url,browser:engine,browser_version:browser.version(),viewport,controls:[],tabs:[],anchors:[],keyboard:[],screenshots:[],warnings:[],failures:[],console_errors:[],page_errors:[]};report.pages.push(r);
    p.on("pageerror",e=>r.page_errors.push(String(e)));p.on("console",m=>{if(m.type()==="error")r.console_errors.push(m.text());});
    try{
     const response=await p.goto(r.url,{waitUntil:"networkidle",timeout:30000});r.http_status=response.status();const b=await response.body();
     r.delivered_blob=crypto.createHash("sha1").update("blob "+b.length+"\0").update(b).digest("hex");r.expected_blob=item.expected_blob;
     if(r.delivered_blob!==item.expected_blob)fail(r,"deployed_source_mismatch",{expected:item.expected_blob,delivered:r.delivered_blob});
     if(r.http_status!==200)fail(r,"page_http_status",r.http_status);
     await p.evaluate(()=>document.fonts.ready);
     const h=await p.evaluate(()=>document.documentElement.scrollHeight);
     for(let y=0;y<h;y+=Math.max(500,viewport.height-100)){await p.evaluate(y=>window.scrollTo({top:y,behavior:"instant"}),y);await p.waitForTimeout(25);}
     await top(p);r.geometry=await geometry(p);
     if(r.geometry.width!==viewport.width||r.geometry.height!==viewport.height)fail(r,"viewport_not_applied",r.geometry);
     if(r.geometry.document_width>viewport.width+1)fail(r,"document_horizontal_overflow",r.geometry);
     r.images=await p.locator("img").evaluateAll(els=>els.map(e=>({src:e.currentSrc||e.src,alt:e.alt,complete:e.complete,width:e.naturalWidth,height:e.naturalHeight})));
     for(const img of r.images){if(!img.complete||!img.width)fail(r,"broken_image",img);if(!img.alt.trim())r.warnings.push({kind:"empty_image_alt",src:img.src});}
     if(engine==="chromium"&&[1440,390].includes(viewport.width)){r.screenshots.push(await shot(p,item.id+"-"+engine+"-"+viewport.width+"-top.png"));if(viewport.width===390&&item.id==="hub")r.screenshots.push(await shot(p,"hub-chromium-390-full.png",true));}
     for(let i=0;i<14;i++){await p.keyboard.press("Tab");r.keyboard.push(await p.evaluate(()=>{const e=document.activeElement,s=getComputedStyle(e),b=e.getBoundingClientRect();return {tag:e.tagName,id:e.id,text:(e.innerText||e.getAttribute("aria-label")||"").slice(0,80),focus_visible:e.matches(":focus-visible"),outline_style:s.outlineStyle,outline_width:s.outlineWidth,rect:{x:b.x,y:b.y,width:b.width,height:b.height}};}));}
     if(!r.keyboard.some(k=>k.tag!=="BODY"))fail(r,"no_keyboard_focus_target",null);
     const seen=new Set();await exercise(p,r,seen);
     const activeTab=p.locator('[role="tab"][aria-selected="true"]');const initial=await activeTab.count()?await activeTab.first().getAttribute("id"):null;
     for(const tab of await p.locator('[role="tab"]').all()){await tab.click();const state=await tab.evaluate(e=>({id:e.id,selected:e.getAttribute("aria-selected"),controls:e.getAttribute("aria-controls"),target_visible:!!document.getElementById(e.getAttribute("aria-controls"))&&!document.getElementById(e.getAttribute("aria-controls")).hidden}));r.tabs.push(state);if(state.selected!=="true"||!state.target_visible)fail(r,"tab_not_activated",state);await exercise(p,r,seen);}
     if(initial)await p.locator("#"+initial).click();
     const reset=p.locator("#reset,#reset-scenario");
     if(await reset.count()&&await reset.first().isVisible()){await reset.first().click();r.reset_clicked=true;r.reset_invalid_visible=await p.locator("input:visible,select:visible").evaluateAll(els=>els.filter(e=>!e.checkValidity()).map(e=>e.id));if(r.reset_invalid_visible.length)fail(r,"reset_invalid_input",r.reset_invalid_visible);}
     r.final_geometry=await geometry(p);if(r.final_geometry.document_width>viewport.width+1)fail(r,"post_interaction_horizontal_overflow",r.final_geometry);
     if(engine==="chromium"&&viewport.width===390){const chart=p.locator("svg,figure img,.chart,.plot").first();if(await chart.count()&&await chart.isVisible()){await chart.scrollIntoViewIfNeeded();r.screenshots.push(await shot(p,item.id+"-chromium-390-chart.png"));}}
     if(engine==="chromium"&&viewport.width===1440)await links(p,r,context);
     if(r.page_errors.length)fail(r,"browser_script_error",r.page_errors);
    }catch(error){fail(r,"audit_exception",String(error));try{r.screenshots.push(await shot(p,item.id+"-"+engine+"-"+viewport.width+"-exception.png"));}catch{}}
    await p.close();fs.writeFileSync(path.join(out,"report.json"),JSON.stringify(report,null,2)+"\n");
   }
   await context.close();
  }
  await browser.close();
 }
}catch(error){report.fatal_error=String(error);report.failures.push({kind:"fatal_audit_error",detail:String(error)});}
report.finished_at=new Date().toISOString();report.summary={renders:report.pages.length,controls:report.pages.reduce((n,p)=>n+p.controls.length,0),input_checks:report.pages.reduce((n,p)=>n+p.controls.reduce((m,c)=>m+c.checks.length,0),0),keyboard_stops:report.pages.reduce((n,p)=>n+p.keyboard.length,0),internal_delivery_checks:report.links.length,failures:report.failures.length};
fs.writeFileSync(path.join(out,"report.json"),JSON.stringify(report,null,2)+"\n");
console.log(JSON.stringify({summary:report.summary,failures:report.failures},null,2));process.exitCode=report.failures.length?1:0;
