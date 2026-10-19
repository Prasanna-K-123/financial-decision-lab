'use strict';
let DATA;
const DRIVER_KEYS=['growth','marginal_roic','terminal_roic','terminal_growth','wacc','tax'];
const el=id=>document.getElementById(id);
const esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function calculate(ebit,a){
 const fields=DRIVER_KEYS.map(k=>a[k]);
 if(fields.some(x=>typeof x!=='number'||!Number.isFinite(x))||typeof ebit!=='number'||!Number.isFinite(ebit)||ebit<0)throw Error('All required assumptions and the EBIT anchor must be finite numbers.');
 if(a.growth<-.25||a.growth>.5||a.terminal_growth<0||a.terminal_growth>.08)throw Error('Growth is outside the documented model domain.');
 if(Math.min(a.marginal_roic,a.terminal_roic)<=0||Math.max(a.marginal_roic,a.terminal_roic)>1)throw Error('Marginal ROIC must be above zero and no greater than 100%.');
 if(a.tax<0||a.tax>=1||a.wacc<=0||a.wacc>.5||a.wacc-a.terminal_growth<.0001)throw Error('Use tax below 100% and WACC at least 0.01 percentage points above terminal growth.');
 const n=[ebit*(1-a.tax)],growth=[null],ledger=[];
 for(let t=1;t<=11;t++){const g=t<=5?a.growth:t<=10?a.growth+(a.terminal_growth-a.growth)*(t-5)/5:a.terminal_growth;growth.push(g);n.push(n[t-1]*(1+g));}
 let sum=0,initial;
 for(let t=0;t<=10;t++){
  const r=t<5?a.marginal_roic:a.marginal_roic+(a.terminal_roic-a.marginal_roic)*(t-4)/6;
  const investment=(n[t+1]-n[t])/r,cash=t===0?-investment:n[t]-investment,divisor=(1+a.wacc)**t,pv=cash/divisor;
  if(t===0)initial=investment;else sum+=pv;
  ledger.push({year:t,growth:growth[t],nopat:n[t],marginal_roic:r,next_year_nopat:n[t+1],net_investment:investment,cash_flow:cash,discount_factor:divisor,present_value:pv});
 }
 const terminalCash=n[11]*(1-a.terminal_growth/a.terminal_roic),tv=terminalCash/(a.wacc-a.terminal_growth),terminalPV=tv/(1+a.wacc)**10,value=-initial+sum+terminalPV;
 return {policy_value:value,upfront_investment:initial,annual_cash_pv:sum,terminal_cash_flow:terminalCash,terminal_value_at_horizon:tv,terminal_present_value:terminalPV,base_normalised_nopat:n[0],no_growth_reference:n[0]/a.wacc,terminal_share_of_net_value:Math.abs(value)>1e-12?terminalPV/value:null,ledger:ledger};
}
function money(x,precision){return x===null||x===undefined?'Unavailable':new Intl.NumberFormat('en-US',{minimumFractionDigits:precision,maximumFractionDigits:precision}).format(x);}
function percent(x){return x===null?'n.a.':(x*100).toFixed(1)+'%';}
function selected(){return DATA.cases.find(x=>x.issuer===el('company').value&&x.case===el('scenario').value);}
function precision(){return el('full-precision').checked?6:1;}
function assumptions(){const a={};DRIVER_KEYS.forEach(k=>{const text=el(k).value;if(text==='')throw Error('Enter the required '+el(k).closest('label').innerText.trim()+'.');a[k]=Number(text)/100;});return a;}
function th(x,numeric){return '<th'+(numeric?' class="number"':'')+'>'+esc(x)+'</th>';}
function td(x,numeric){return '<td'+(numeric?' class="number"':'')+'>'+esc(x)+'</td>';}
function historical(){
 const issuer=el('company').value,rows=DATA.spread.filter(x=>x.issuer===issuer),combined=issuer==='INFY';
 const metrics=[['Revenue / total net sales',x=>x.facts.revenue],['Reported operating income',x=>x.facts.operating_income],['Operating margin',x=>percent(x.reported_operating_margin)],['Operating cash flow',x=>x.facts.cfo],[combined?'Cash PPE and intangibles':'Gross cash PPE purchases',x=>combined?x.combined_ppe_intangibles_cash_outflow:x.facts.cash_ppe],[combined?'CFO less combined PPE / intangibles':'CFO less pure cash PPE',x=>combined?x.cash_generation_after_combined_investment:x.cash_generation_cfo_minus_cash_ppe]];
 el('historical-table').innerHTML='<table><thead><tr>'+th('USD millions, except margin')+rows.map(x=>th('FY'+x.fiscal_year,true)).join('')+'</tr></thead><tbody>'+metrics.map(m=>'<tr>'+td(m[0])+rows.map(x=>td(typeof m[1](x)==='number'?money(m[1](x),1):m[1](x),true)).join('')+'</tr>').join('')+'</tbody></table>';
 const max=Math.max.apply(null,rows.map(x=>x.facts.cfo)),height=160,baseline=190;
 let svg='<svg role="img" aria-label="Operating cash flow and cash investment across three fiscal years" viewBox="0 0 900 225"><line x1="25" x2="880" y1="190" y2="190" stroke="#b0bec8"/>';
 rows.forEach((x,i)=>{const inv=combined?x.combined_ppe_intangibles_cash_outflow:x.facts.cash_ppe;[[x.facts.cfo,'#246279'],[inv,'#a86a3d']].forEach((pair,j)=>{const h=pair[0]/max*height,xp=120+i*280+j*65;svg+='<rect x="'+xp+'" y="'+(baseline-h)+'" width="47" height="'+h+'" rx="2" fill="'+pair[1]+'"/><text x="'+(xp+23.5)+'" y="'+(baseline-h-7)+'" text-anchor="middle" font-size="12" fill="#203d57">'+money(pair[0],0)+'</text>';});svg+='<text x="'+(155+i*280)+'" y="216" text-anchor="middle" font-size="14" fill="#203d57">FY'+x.fiscal_year+'</text>';});
 el('historical-plot').innerHTML=svg+'</svg>';el('investment-legend').innerHTML='<span><i style="background:#246279"></i>Operating cash flow</span><span><i style="background:#a86a3d"></i>'+(combined?'Combined PPE / intangibles cash':'Gross cash PPE')+'</span>';
 const insights={MSFT:'FY 2025 cash PPE grew 45.1%, versus 14.9% revenue growth. CFO less cash PPE fell 3.3% to USD 71,611m despite higher operating earnings.',TGT:'FY 2025 operating margin was 4.9%. CFO less cash PPE fell 36.7% to USD 2,835m, as operating cash declined and cash PPE increased.',INFY:'The FY 2025 CFO increase of USD 1,203m includes USD 751m higher pre-tax operating cash and USD 452m lower cash taxes. The tax component is 37.6% of the increase.'};
 el('historical-insight').textContent=insights[issuer];
 el('historical-basis').textContent='Historical accounting proxies, not FCFF or cash available for payout. '+(combined?'Infosys investment is the separately labelled combined PPE/intangibles line. IFRS lease/interest classifications are retained. ':issuer==='TGT'?'Target FY 2023 has 53 weeks; FY 2024 and FY 2025 have 52. ':'Microsoft cash PPE excludes noncash lease additions and acquisitions. ')+'Fiscal ends: '+rows.map(x=>x.period_end).join(', ')+'.';
}
function applyCase(){const c=selected();DRIVER_KEYS.forEach(k=>el(k).value=String(Math.round(c.assumptions[k]*1000000)/10000));historical();renderModel();}
function renderModel(){
 try{
  const a=assumptions(),r=calculate(selected().reported_ebit,a),d=precision();el('model-error').hidden=true;el('model-results').hidden=false;
  el('policy-value').textContent=money(r.policy_value,d);el('initial-investment').textContent=money(r.upfront_investment,d);el('terminal-share').textContent=percent(r.terminal_share_of_net_value);
  const lift=r.no_growth_reference===0?null:r.policy_value/r.no_growth_reference-1;
  el('policy-interpretation').textContent='Relative to the no-growth cash-return reference: '+percent(lift)+'. Initial investment funds next year’s incremental profit; it is not reported cash PPE.'+(r.terminal_cash_flow<0?' This forced policy requires continuing terminal capital injections.':'');
  el('policy-table').innerHTML='<table id="policy-ledger"><thead><tr>'+['Funding time','Normalised NOPAT','Net growth investment','Policy cash flow','Present value'].map((x,j)=>th(x,j>0)).join('')+'</tr></thead><tbody>'+r.ledger.map(x=>'<tr>'+td(x.year)+[x.nopat,x.net_investment,x.cash_flow,x.present_value].map(v=>td(money(v,d),true)).join('')+'</tr>').join('')+'</tbody></table>';
  renderSensitivity(a);
 }catch(error){el('model-results').hidden=true;el('model-error').hidden=false;el('model-error').textContent=error.message;}
}
function renderSensitivity(a){
 const issuer=el('company').value,ebit=selected().reported_ebit,d=precision();let text='<table id="sensitivity-grid"><thead><tr>'+th('WACC / terminal growth');
 for(let g=0;g<=10;g++)text+=th((g*.5).toFixed(1)+'%');text+='</tr></thead><tbody>';
 for(let w=6;w<=16;w++){text+='<tr>'+th(w+'.0%');for(let g=0;g<=10;g++){const value=calculate(ebit,Object.assign({},a,{wacc:w/100,terminal_growth:g/200})).policy_value;text+='<td><button type="button" data-wacc="'+w+'" data-terminal="'+(g*.5)+'" aria-label="WACC '+w+'%, terminal growth '+(g*.5)+'%: '+money(value,d)+' million">'+money(value,d)+'</button></td>';}text+='</tr>';}
 el('sensitivity').innerHTML=text+'</tbody></table>';el('sensitivity').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{el('wacc').value=b.dataset.wacc;el('terminal_growth').value=b.dataset.terminal;renderModel();}));
}
function sourceEvidence(){
 const id=el('report-case').value,m=DATA.spread.find(x=>x.id===id),refs=DATA.references.filter(x=>x.source_id===id&&x.status!=='control'),pred=DATA.predictions.filter(x=>x.source_id===id);
 const labels={revenue:'Revenue',operating_income:'Operating income',net_income:'Consolidated net income',assets:'Assets',liabilities:'Direct liabilities',equity:'Consolidated equity',cash:'Cash only',current_assets:'Current assets',current_liabilities:'Current liabilities',cfo:'Operating cash',cash_ppe:'Pure cash PPE',da:'Pure D&A'};
 const prediction=(field,method)=>{const x=pred.find(y=>y.field===field&&y.method===method);return x.value===null?'Abstain':money(Number(x.value),0);};
 el('source-table').innerHTML='<table><thead><tr>'+['Financial target (USDm)','Reviewed fact','Literal answer','Strict answer','Canonical source cell'].map((x,i)=>th(x,i>0&&i<4)).join('')+'</tr></thead><tbody>'+refs.map(x=>'<tr>'+td(labels[x.field])+td(x.status==='direct'?money(x.value, 0):'Unavailable',true)+td(prediction(x.field,'literal'),true)+td(prediction(x.field,'strict'),true)+td(x.locator+(x.limitation?' · '+x.limitation:''))+'</tr>').join('')+'</tbody></table>';
 el('source-link').innerHTML='<a href="'+esc(m.url)+'" target="_blank" rel="noopener">Read the original '+esc(id.replace('_',' FY'))+' report</a> · Fiscal end '+esc(m.period_end)+'.';
 el('source-identity').textContent='Original-file SHA256: '+m.sha256+'. '+m.bytes.toLocaleString('en-US')+' bytes. Retrieved '+m.retrieved_utc+'. Currency USD, amounts in millions. Issuer-hosted version; immutable original SEC accession equivalence is not asserted.';
}
function boot(){
 DATA=JSON.parse(el('lab-data').textContent);
 el('company').addEventListener('change',applyCase);el('scenario').addEventListener('change',applyCase);DRIVER_KEYS.forEach(k=>el(k).addEventListener('input',renderModel));el('full-precision').addEventListener('change',renderModel);
 el('report-case').innerHTML=DATA.spread.map(x=>'<option value="'+x.id+'">'+x.issuer+' FY'+x.fiscal_year+' · end '+x.period_end+'</option>').join('');el('report-case').value='MSFT_2025';el('report-case').addEventListener('change',sourceEvidence);
 applyCase();sourceEvidence();
}
if(typeof document!=='undefined')boot();
