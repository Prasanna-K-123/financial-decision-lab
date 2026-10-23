// Run the actual embedded app with a small DOM model. Removing focused button
// nodes blurs to body, as observed in the live browser before this repair.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),html=fs.readFileSync(path.join(root,'docs/index.html'),'utf8');
const markup=html.split('<script id="lab-data"')[0],nodes=new Map();
const document={activeElement:null,getElementById:id=>{assert.ok(nodes.has(id),'Missing DOM ID '+id);return nodes.get(id);}};
class Element{
 constructor(id){this.id=id;this.value='';this.hidden=false;this.checked=false;this.dataset={};this.attributes={};this.listeners={};this.children=[];this._html='';this.textContent='';}
 set innerHTML(value){if(this.children.includes(document.activeElement))document.activeElement=body;this._html=value;this.children=[];
  if(this.id==='sensitivity')for(const m of value.matchAll(/<button\b[^>]*data-wacc="([^"]+)"[^>]*data-terminal="([^"]+)"[^>]*aria-label="([^"]+)"[^>]*>/g)){
   const button=new Element('');button.dataset={wacc:m[1],terminal:m[2]};button.attributes['aria-label']=m[3];this.children.push(button);
  }
 }
 get innerHTML(){return this._html;}
 get selectedOptions(){return [{textContent:({MSFT:'Microsoft',TGT:'Target',INFY:'Infosys'})[this.value]||this.value}];}
 addEventListener(type,fn){(this.listeners[type]??=[]).push(fn);}
 fire(type){for(const fn of this.listeners[type]||[])fn({target:this});}
 setAttribute(key,value){this.attributes[key]=value;}
 removeAttribute(key){delete this.attributes[key];}
 closest(selector){assert.equal(selector,'label');return {innerText:this.label||this.id};}
 contains(other){return this.children.includes(other);}
 querySelectorAll(selector){assert.equal(selector,'button');return this.children;}
 focus(options){document.activeElement=this;this.lastFocusOptions=options;}
}
const body=new Element('body');document.activeElement=body;
for(const match of markup.matchAll(/\bid="([^"]+)"/g)){assert.ok(!nodes.has(match[1]),'Duplicate ID '+match[1]);nodes.set(match[1],new Element(match[1]));}
nodes.set('lab-data',new Element('lab-data'));
const el=id=>document.getElementById(id);
for(const match of markup.matchAll(/<input\b[^>]*id="([^"]+)"[^>]*>/g)){
 const node=el(match[1]);for(const key of ['min','max']){const attr=match[0].match(new RegExp(key+'="([^"]+)"'));if(attr)node[key]=attr[1];}
}
el('company').value='MSFT';el('scenario').value='reference';
el('lab-data').textContent=html.match(/<script id="lab-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const code=html.match(/<script id="app-code">([\s\S]*?)<\/script>/)[1];
const context=vm.createContext({document,window:{addEventListener(){}},Intl,Math,Number,Error,console});vm.runInContext(code,context);
let focusChecks=0,policyChecks=0,sourceChecks=0;
const saved=JSON.parse(fs.readFileSync(path.join(root,'reports/valuation_scenarios.json'),'utf8'));
for(const scenario of saved){
 el('company').value=scenario.issuer;el('scenario').value=scenario.case;el('company').fire('change');
 const actual=Number(el('policy-value').textContent.replaceAll(',',''));
 assert.ok(Math.abs(actual-scenario.policy_value)<=.051,'Saved policy display '+scenario.issuer+'/'+scenario.case);policyChecks++;
 assert.ok(el('historical-table').innerHTML.includes('<caption>'));
 assert.ok(el('policy-table').innerHTML.includes('<th scope="row">10</th>'));
 assert.ok(el('policy-status').textContent.includes('Operating-policy value'));
 // Exercise every cell, not only the primary policy. Focus must remain on a
 // connected replacement of the selected pair after the table is recomputed.
 for(let i=0;i<121;i++){
  const button=el('sensitivity').children[i],pair={...button.dataset};button.focus();button.fire('click');
  const active=document.activeElement;
  assert.ok(el('sensitivity').contains(active),'Sensitivity selection lost keyboard focus');
  assert.notEqual(active,button,'Old removed node must not retain focus');
  assert.equal(active.dataset.wacc,pair.wacc);assert.equal(active.dataset.terminal,pair.terminal);
  assert.equal(active.lastFocusOptions.preventScroll,true);
  assert.equal(el('wacc').value,pair.wacc);assert.equal(el('terminal_growth').value,pair.terminal);focusChecks++;
 }
}
// Invalid inputs hide obsolete results, identify the bad field and recover.
el('growth').focus();el('growth').value='';el('growth').fire('input');
assert.equal(el('model-results').hidden,true);assert.equal(el('model-error').hidden,false);
assert.equal(el('growth').attributes['aria-invalid'],'true');assert.equal(el('growth').attributes['aria-describedby'],'model-error');
assert.equal(el('policy-status').textContent,'');
el('growth').value='10';el('growth').fire('input');
assert.equal(el('model-results').hidden,false);assert.equal(el('model-error').hidden,true);assert.equal(document.activeElement,el('growth'));
assert.equal(el('growth').attributes['aria-invalid'],undefined);
el('full-precision').checked=true;el('full-precision').fire('change');assert.match(el('policy-value').textContent,/\.\d{6}$/);
for(const report of JSON.parse(el('lab-data').textContent).spread){
 el('report-case').value=report.id;el('report-case').fire('change');
 assert.ok(el('source-table').innerHTML.includes(report.id.replace('_',' FY')));
 assert.ok(el('source-link').innerHTML.includes(report.url));sourceChecks++;
}
console.log(JSON.stringify({passed:true,saved_policy_displays:policyChecks,sensitivity_focus_checks:focusChecks,source_views:sourceChecks,invalid_input_recovery:true,unrelated_input_focus_preserved:true,precision_toggle:true,scope:'Actual embedded app in a DOM model; native browser focus, layout and accessibility observations are separate.'}));
