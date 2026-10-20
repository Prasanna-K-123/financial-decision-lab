const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),read=n=>JSON.parse(fs.readFileSync(path.join(root,n),'utf8'));
const html=fs.readFileSync(path.join(root,'docs/index.html'),'utf8');const code=html.match(/<script id="app-code">([\s\S]*?)<\/script>/)[1];assert.equal(code,fs.readFileSync(path.join(root,'tools/explorer.js'),'utf8'));
const context=vm.createContext({Intl,Math,Number,Error,console});vm.runInContext(code,context);let checked=0,maxError=0;
function same(actual,expected,label){assert.ok(Number.isFinite(actual),label);let e=Math.abs(actual-expected);maxError=Math.max(maxError,e);assert.ok(e<=1e-6+Math.abs(expected)*2e-12,label+': '+actual+' != '+expected);checked++;}
for(const file of ['valuation_scenarios.json','valuation_sensitivity.json','growth_return_regimes.json'])for(const x of read('reports/'+file)){
 context.input={ebit:x.reported_ebit,a:x.assumptions};const r=vm.runInContext('calculate(input.ebit,input.a)',context);same(r.policy_value,x.policy_value,file+'/'+x.issuer);
 if(x.year_ledger){same(r.upfront_investment,x.upfront_investment,'initial investment');x.year_ledger.forEach((y,j)=>['nopat','marginal_roic','next_year_nopat','net_investment','cash_flow','discount_factor','present_value'].forEach(k=>same(r.ledger[j+1][k],y[k],x.issuer+'/year'+y.year+'/'+k)));}
}
let decimalBoundaryCases=0,inputGuardCases=0;
// Whole and fractional percentage assumptions must share the displayed domain.
for(let basisPoints=0;basisPoints<=800;basisPoints++){
 const terminalPercent=basisPoints/100;
 const assumptions={growth:.1,marginal_roic:.18,terminal_roic:.12,terminal_growth:terminalPercent/100,wacc:(terminalPercent+.01)/100,tax:.25};
 context.input={ebit:100,a:assumptions};
 assert.ok(Number.isFinite(vm.runInContext('calculate(input.ebit,input.a).policy_value',context)));
 context.input.a={...assumptions,wacc:(terminalPercent+.009)/100};
 assert.throws(()=>vm.runInContext('calculate(input.ebit,input.a)',context));decimalBoundaryCases+=2;
}
for(const [text,min,max,expected] of [['18',.01,100,.18],['10.25',.01,50,.1025],['25.125',0,99.99,.25125],['0',0,8,0],['-25',-25,50,-.25]]){
 context.parseInput={text,min,max};const result=vm.runInContext('readPercentage(parseInput.text,"Assumption (%)",parseInput.min,parseInput.max)',context);
 assert.equal(result,expected);inputGuardCases++;
}
for(const [text,min,max] of [['',.01,100],['   ',0,100],['0.001',.01,100],['101',.01,100],['99.995',0,99.99],['Infinity',0,100],['NaN',0,100]]){
 context.parseInput={text,min,max};assert.throws(()=>vm.runInContext('readPercentage(parseInput.text,"Assumption (%)",parseInput.min,parseInput.max)',context));inputGuardCases++;
}
const a=read('reports/valuation_scenarios.json')[1].assumptions;context.input={ebit:0,a};same(vm.runInContext('calculate(input.ebit,input.a).policy_value',context),0,'zero EBIT');
for(const patch of [{wacc:a.terminal_growth},{marginal_roic:0},{growth:NaN},{tax:1}]){context.input={ebit:100,a:{...a,...patch}};assert.throws(()=>vm.runInContext('calculate(input.ebit,input.a)',context));}
for(const label of ['Company','Scenario','Report case','Initial profit growth (%)','WACC (%)'])assert.ok(html.includes(label),label);
assert.equal((fs.readFileSync(path.join(root,'docs/portfolio.html'),'utf8').match(/<article>/g)||[]).length,7);
const local=[...html.split('<script id="lab-data"')[0].matchAll(/href="([^"]+)"/g)].map(x=>x[1]).filter(x=>!x.startsWith('http')&&!x.startsWith('#'));
for(const link of local)assert.ok(fs.existsSync(path.join(root,'docs',link)),link);
const result={actual_embedded_script_checked:true,numeric_comparisons:checked,python_case_evaluations:519,max_absolute_error_usd_millions:maxError,zero_and_invalid_boundary_checks:true,local_deliverable_links_present:true,portfolio_studies:7,decimal_boundary_checks:decimalBoundaryCases,percentage_input_guard_checks:inputGuardCases,scope:'Node VM execution of the exact published script; rendered browser, keyboard and live-link checks are separate.'};fs.writeFileSync(path.join(root,'reports/explorer_numeric_verification.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
