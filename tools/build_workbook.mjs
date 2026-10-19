import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {Workbook,SpreadsheetFile,FileBlob} from '@oai/artifact-tool';

const project=process.env.FINANCE_LAB_PROJECT,output=process.env.FINANCE_LAB_OUTPUT;
if(!project||!output)throw Error('Set FINANCE_LAB_PROJECT and FINANCE_LAB_OUTPUT.');
const read=async name=>JSON.parse(await fs.readFile(path.join(project,name),'utf8'));
const spread=await read('reports/financial_spread.json'),cases=await read('reports/valuation_scenarios.json');
await fs.mkdir(output,{recursive:true});
const wb=Workbook.create(),policy=wb.worksheets.add('Policy review'),assume=wb.worksheets.add('Assumptions'),statements=wb.worksheets.add('Statements'),audit=wb.worksheets.add('Audit');
const navy='#203D57',light='#EEF2F6',ink='#162B3C',blue='#0000FF',green='#008000';
const money='#,##0.0;(#,##0.0);"-"',difference='[>=0.005]0.00;[<=-0.005](0.00);0.00';
const put=(s,c,v)=>s.getRange(c).values=[[v]],formula=(s,c,f)=>s.getRange(c).formulas=[[f]];
const letter=n=>String.fromCharCode(65+n);
function layout(s,title,last,rows){
 s.showGridLines=false;s.getRange(`A1:${last}${rows}`).format={font:{name:'Arial',size:10,color:ink},rowHeight:21,verticalAlignment:'center'};
 s.getRange(`A1:B${rows}`).format.columnWidth=2;s.getRange(`C1:C${rows}`).format.columnWidth=44;s.getRange(`D1:${last}${rows}`).format.columnWidth=17;
 put(s,'C2',title);s.getRange('C2').format.font={size:14,bold:true,color:navy};s.getRange(`C2:${last}2`).format.borders={bottom:{style:'thin',color:'#BAC4CE'}};
}
function header(s,range){s.getRange(range).format={fill:navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:36,horizontalAlignment:'center',verticalAlignment:'center',borders:{insideVertical:{style:'thin',color:'#FFFFFF'}}};}
function section(s,row,title,last){put(s,`C${row}`,title);s.getRange(`C${row}:${last}${row}`).format={fill:light,font:{bold:true,color:navy},rowHeight:24};}
layout(policy,'Growth funding and operating-policy value','K',39);policy.tabColor=navy;
layout(assume,'Operating-policy assumptions','L',31);assume.tabColor='#6C8398';
layout(statements,'Consolidated annual financial spread (USD millions)','I',114);statements.tabColor='#D7C8B4';
layout(audit,'Policy and financial reconciliations','K',65);
for(const s of [policy,audit]){put(s,'C4','Case selected');formula(s,'D4',"='Assumptions'!D6");s.getRange('D4:F4').format.borders={preset:'outside',style:'dotted',color:'#8D9CA9'};s.getRange('D4').format={font:{color:green,bold:true},horizontalAlignment:'center'};}

// Original facts and their meaningful historical ratios. Missing direct facts stay text.
const fields=['revenue','operating_income','net_income','assets','liabilities','equity','cash','current_assets','current_liabilities','cfo','cash_ppe','da'];
const labels=['Revenue / total net sales','Reported operating income','Consolidated net income','Total assets','Direct total liabilities','Consolidated equity','Cash and cash equivalents','Current assets','Current liabilities','Cash from operating activities','Gross cash PPE purchases','Direct depreciation / amortisation'];
const starts={MSFT:5,TGT:42,INFY:79};
const sourceRows={};
for(const issuer of ['MSFT','TGT','INFY']){
 const start=starts[issuer],observations=spread.filter(x=>x.issuer===issuer);sourceRows[issuer]=start+3;
 statements.getRange(`C${start}:F${start}`).values=[[issuer,...observations.map(x=>'FY:'+String(x.fiscal_year).slice(2))]];header(statements,`C${start}:F${start}`);statements.getRange(`D${start}:F${start}`).setNumberFormat('"FY:"00');
 const extraLabels=['Beginning cash','Investing cash flow','Financing cash flow','FX effect on cash','Reported net cash change','Noncurrent liabilities subtotal','Combined PPE / intangibles cash','Cash operations before tax','Cash income taxes paid'];
 statements.getRange(`C${start+2}:C${start+22}`).values=[...labels,...extraLabels].map(x=>[x]);
 observations.forEach((x,j)=>{
  const col=letter(j+3),e=x.cash_bridge_components;
  const values=fields.map(k=>x.facts[k]??'n.a.').concat([e.cash_begin,e.cash_investing,e.cash_financing,e.fx_cash_flow,e.cash_change,e.noncurrent_liabilities??'n.a.',e.combined_ppe_intangibles??'n.a.',e.cash_generated_from_operations_before_tax??'n.a.',e.cash_taxes_paid??'n.a.']);
  statements.getRange(`${col}${start+2}:${col}${start+22}`).values=values.map(v=>[v]);statements.getRange(`${col}${start+2}:${col}${start+22}`).setNumberFormat(money);statements.getRange(`${col}${start+2}:${col}${start+22}`).format.font.color=blue;statements.getRange(`${col}${start+2}:${col}${start+22}`).format.horizontalAlignment='right';
  const r=k=>`${col}${start+k}`;
  formula(statements,r(24),`=${r(3)}/${r(2)}`);formula(statements,r(25),`=${r(9)}/${r(10)}`);formula(statements,r(26),`=${r(11)}/${r(4)}`);
  formula(statements,r(27),`=IF(ISNUMBER(${r(12)}),${r(11)}-${r(12)},"n.a.")`);formula(statements,r(28),`=IF(ISNUMBER(${r(20)}),${r(11)}-${r(20)},"n.a.")`);
  if(j===0)put(statements,r(29),'n.a.');else formula(statements,r(29),`=${r(2)}/${letter(j+2)}${start+2}-1`);
  formula(statements,r(30),`=${r(11)}+SUM(${r(15)}:${r(17)})-(${r(8)}-${r(14)})`);
  formula(statements,r(31),`=${r(5)}-${issuer==='TGT'?`(${r(10)}+${r(19)})`:r(6)}-${r(7)}`);
  formula(statements,r(32),`=${r(14)}+${r(18)}+${x.cash_bridge_components.cash_change_includes_fx?'0':r(17)}-${r(8)}`);
  put(statements,`H${start+2+j}`,`FY:${String(x.fiscal_year).slice(2)} source`);put(statements,`I${start+2+j}`,x.url);statements.getRange(`I${start+2+j}`).format={wrapText:true,rowHeight:34};
  put(statements,`H${start+7+j}`,`FY:${String(x.fiscal_year).slice(2)} SHA256`);put(statements,`I${start+7+j}`,x.sha256);
 });
 statements.getRange(`D${start+24}:F${start+32}`).format.horizontalAlignment='right';
 const metricLabels=['Operating margin','Current ratio','CFO / consolidated net income','CFO less pure cash PPE','CFO less combined PPE / intangibles','Revenue growth','Cash-flow sum residual','Balance identity residual','Ending-cash bridge residual'];
 statements.getRange(`C${start+24}:C${start+32}`).values=metricLabels.map(x=>[x]);
 for(const off of [24,29])statements.getRange(`D${start+off}:F${start+off}`).setNumberFormat('0.0%');
 for(const off of [25,26])statements.getRange(`D${start+off}:F${start+off}`).setNumberFormat('0.00"x"');
 for(const off of [24,25,26,29])statements.getRange(`C${start+off}:F${start+off}`).format.font.italic=true;
 statements.getRange(`D${start+27}:F${start+28}`).setNumberFormat(money);statements.getRange(`D${start+30}:F${start+32}`).setNumberFormat(difference);
 statements.getRange(`D${start+30}:F${start+32}`).conditionalFormats.addCustom(`ABS(D${start+30})>0.000001`,{fill:'#FCE8E6',font:{color:'#9C0006',bold:true}});
 put(statements,`H${start+12}`,'Statement locators');put(statements,`I${start+12}`,'Numeric references and per-field source locators: data/references.json.');
 const notes=issuer==='MSFT'?['D&A plus other is unavailable as pure D&A.','Cash PPE excludes noncash leases and acquisitions.']:issuer==='TGT'?['Total liabilities control sums current/noncurrent subtotals.','FY:23 has 53 weeks. FY:24 and FY:25 have 52 weeks.']:['PPE cash includes intangibles only in the separately labelled row.','IFRS lease and interest classification is retained.'];
 notes.forEach((v,k)=>put(statements,`I${start+14+k}`,v));
 put(statements,`I${start+18}`,'Cash proxies are historical accounting measures; they are not FCFF.');
}
statements.getRange('G1:G114').format.columnWidth=3;statements.getRange('H1:H114').format.columnWidth=20;statements.getRange('I1:I114').format.columnWidth=98;statements.freezePanes.freezeRows(5);

// One selector and one active driver per assumption, above its nine case inputs.
put(assume,'C4','Case number (1–9)');put(assume,'D4',2);assume.getRange('D4').format={font:{color:blue},fill:light};assume.getRange('D4').dataValidation={rule:{type:'whole',operator:'between',formula1:1,formula2:9}};
put(assume,'C6','Case selected');formula(assume,'D6','=IF(AND(ISNUMBER(D4),D4=INT(D4),D4>=1,D4<=9),INDEX($D$18:$L$18,1,D4),NA())');assume.getRange('D6').format.font.color=green;
assume.getRange('C7:D7').values=[['Driver','Active selection']];header(assume,'C7:D7');
const drivers=[['Initial profit growth','growth',-.25,.5],['Initial marginal ROIC','marginal_roic',0,1],['Terminal marginal ROIC','terminal_roic',0,1],['Terminal profit growth','terminal_growth',0,.08],['WACC','wacc',0,.5],['Normalised tax rate','tax',0,1],['Latest reported EBIT','reported_ebit',0,null]];
put(assume,'C18','Numbered case inputs');assume.getRange('D18:L18').values=[cases.map((x,j)=>`${j+1} ${x.issuer} ${x.case}`)];header(assume,'C18:L18');assume.getRange('D18:L18').format.rowHeight=42;
drivers.forEach(([label,key,low,high],j)=>{
 put(assume,`C${8+j}`,label);put(assume,`C${19+j}`,label);
 cases.forEach((x,k)=>{const c=letter(k+3);if(key==='reported_ebit'){formula(assume,`${c}${19+j}`,`='Statements'!F${sourceRows[x.issuer]}`);assume.getRange(`${c}${19+j}`).format.font.color=green;}else put(assume,`${c}${19+j}`,x.assumptions[key]);});
 const selected=`INDEX($D$${19+j}:$L$${19+j},1,$D$4)`,filled=`COUNTBLANK(INDEX($D$${19+j}:$L$${19+j},1,$D$4))=0`;
 let checks=[filled,`ISNUMBER(${selected})`,`${selected}${[1,2,4].includes(j)?'>':'>='}${low}`];if(high!==null)checks.push(`${selected}${j===5?'<':'<='}${high}`);if(j===4)checks.push(`${selected}-$D$11>=0.0001`);
 formula(assume,`D${8+j}`,`=IF(AND(ISNUMBER($D$4),$D$4=INT($D$4),$D$4>=1,$D$4<=9),IF(AND(${checks.join(',')}),${selected},NA()),NA())`);
});
assume.getRange('D19:L24').format={font:{color:blue},fill:'#F4F7FB'};assume.getRange('D19:L24').setNumberFormat('0.0%');assume.getRange('D8:D13').setNumberFormat('0.0%');assume.getRange('D14').setNumberFormat(money);assume.getRange('D25:L25').setNumberFormat(money);
put(assume,'C28','Growth, marginal ROIC, WACC and tax are illustrative assumptions, not current market estimates.');put(assume,'C30','Blue cells are editable. A blank required active input or invalid terminal spread exposes an error.');

// One operating policy schedule, with capital paid before the next year's growth.
const a=row=>`'Assumptions'!$D$${row}`;
const metrics=['Operating-policy value (USDm)','Immediate growth investment','Year 1–10 cash-flow PV','Terminal present value','No-growth cash-return reference','Value versus no-growth reference','Terminal share of net value','Value / base normalised NOPAT'];
policy.getRange('C6:C13').values=metrics.map(x=>[x]);
formula(policy,'D6','=-D7+D8+D9');formula(policy,'D7','=H21');formula(policy,'D8','=SUM(K22:K31)');formula(policy,'D9','=D36/J31');formula(policy,'D10',`=E21/${a(12)}`);formula(policy,'D11','=IF(D10=0,"n.a.",D6/D10-1)');formula(policy,'D12','=IF(ABS(D6)<0.000000000001,"n.a.",D9/D6)');formula(policy,'D13','=IF(E21=0,"n.a.",D6/E21)');
policy.getRange('D6:D10').setNumberFormat(money);policy.getRange('D11:D12').setNumberFormat('0.0%');policy.getRange('D13').setNumberFormat('0.00"x"');policy.getRange('C6:D6').format.font.bold=true;policy.getRange('C11:D13').format.font.italic=true;
put(policy,'F6','Conditional operating policy before financing/nonoperating adjustments.');put(policy,'F8','Immediate investment funds first-year growth.');put(policy,'F10','Reported EBIT basis retained; no market price or equity target.');put(policy,'F12','Terminal share can exceed 100% when earlier cash flows are negative.');
section(policy,18,'Annual policy schedule (USD millions)','K');policy.getRange('C20:K20').values=[['Year','Profit growth','Normalised NOPAT','Marginal ROIC','Next-year NOPAT','Net investment','Policy cash flow','Discount divisor','Present value']];header(policy,'C20:K20');policy.getRange('C21:C31').format.columnWidth=10;
for(let t=0;t<=10;t++){
 const r=21+t;put(policy,`C${r}`,t);
 if(t===0){put(policy,`D${r}`,'n.a.');formula(policy,`E${r}`,`=${a(14)}*(1-${a(13)})`);}else{formula(policy,`D${r}`,t<=5?`=${a(8)}`:`=${a(8)}+(${a(11)}-${a(8)})*(${t}-5)/5`);formula(policy,`E${r}`,`=E${r-1}*(1+D${r})`);}
 formula(policy,`F${r}`,t<5?`=${a(9)}`:`=${a(9)}+(${a(10)}-${a(9)})*(${t}-4)/6`);
 formula(policy,`G${r}`,t<10?`=E${r+1}`:`=E${r}*(1+${a(11)})`);
 formula(policy,`H${r}`,`=(G${r}-E${r})/F${r}`);formula(policy,`I${r}`,t===0?`=-H${r}`:`=E${r}-H${r}`);formula(policy,`J${r}`,`=(1+${a(12)})^C${r}`);formula(policy,`K${r}`,`=I${r}/J${r}`);
}
policy.getRange('C21:K31').format.horizontalAlignment='right';
policy.getRange('D21:D31').setNumberFormat('0.0%');policy.getRange('F21:F31').setNumberFormat('0.0%');policy.getRange('E21:I31').setNumberFormat(money);policy.getRange('F21:F31').setNumberFormat('0.0%');policy.getRange('J21:J31').setNumberFormat('0.0000');policy.getRange('K21:K31').setNumberFormat(money);
put(policy,'C35','Terminal year-11 policy cash');formula(policy,'D35',`=G31*(1-${a(11)}/${a(10)})`);put(policy,'C36','Terminal value at year 10');formula(policy,'D36',`=D35/(${a(12)}-${a(11)})`);policy.getRange('D35:D36').setNumberFormat(money);
put(policy,'C38','Net investment is a scenario funding requirement, not reported cash PPE or a forecast of observed FCFF.');
// Restore label width after the timeline's numeric column sizing.
policy.getRange('C1:C39').format.columnWidth=44;policy.getRange('F1:F39').format.columnWidth=21;

// Terminal checks never feed assumptions, the policy schedule or outputs.
audit.getRange('C6:C9').values=[['Discounted cash-flow value'],['Independent profit-layer value'],['Policy identity residual'],['Difference from frozen scenario']];formula(audit,'D6',"='Policy review'!D6");formula(audit,'D7','=SUM(I18:I27)+D32+D33');formula(audit,'D8','=D6-D7');formula(audit,'D9',"=D6-INDEX($D$54:$D$62,'Assumptions'!D4)");audit.getRange('D6:D9').setNumberFormat(difference);
put(audit,'F9','Scenario difference can change after edits. The identity residual must remain zero.');
audit.getRange('C17:I17').values=[['Funding time','Incremental NOPAT','Marginal ROIC','Profit-layer factor','Discount divisor','Layer NPV','Layer present value']];header(audit,'C17:I17');
for(let t=0;t<10;t++){const r=18+t,s=21+t;formula(audit,`C${r}`,`='Policy review'!C${s}`);formula(audit,`D${r}`,`='Policy review'!G${s}-'Policy review'!E${s}`);formula(audit,`E${r}`,`='Policy review'!F${s}`);formula(audit,`F${r}`,`=1/${a(12)}-1/E${r}`);formula(audit,`G${r}`,`='Policy review'!J${s}`);formula(audit,`H${r}`,`=D${r}*F${r}`);formula(audit,`I${r}`,`=H${r}/G${r}`);}
audit.getRange('D18:I27').setNumberFormat(money);audit.getRange('E18:E27').setNumberFormat('0.0%');audit.getRange('G18:G27').setNumberFormat('0.0000');
put(audit,'C32','Base profit perpetuity');formula(audit,'D32',`='Policy review'!E21/${a(12)}`);put(audit,'C33','Infinite terminal profit layers');formula(audit,'D33',`='Policy review'!E31*${a(11)}*(1/${a(12)}-1/${a(10)})*(1+${a(12)})/(${a(12)}-${a(11)})/'Policy review'!J31`);audit.getRange('D32:D33').setNumberFormat(money);
section(audit,37,'Financial identity differences (USD millions)','F');audit.getRange('C39:F39').values=[['Report','Assets less liabilities and equity','Cash-flow sum less cash change','Ending-cash bridge']];header(audit,'C39:F39');
spread.forEach((x,j)=>{const r=40+j,s=starts[x.issuer],c=letter(x.fiscal_year-2023+3);put(audit,`C${r}`,x.id);formula(audit,`D${r}`,`='Statements'!${c}${s+31}`);formula(audit,`E${r}`,`='Statements'!${c}${s+30}`);formula(audit,`F${r}`,`='Statements'!${c}${s+32}`);});audit.getRange('D40:F48').setNumberFormat(difference);
section(audit,52,'Frozen Python scenario references (USD millions)','D');put(audit,'C53','Scenario');put(audit,'D53','Sealed value');header(audit,'C53:D53');audit.getRange('C54:D62').values=cases.map(x=>[`${x.issuer} ${x.case}`,x.policy_value]);audit.getRange('D54:D62').setNumberFormat(money);
for(const [s,range,expression] of [[audit,'D8','ABS(D8)>0.000001'],[audit,'D40:F48','ABS(D40)>0.000001']])s.getRange(range).conditionalFormats.addCustom(expression,{fill:'#FCE8E6',font:{color:'#9C0006',bold:true}});

wb.recalculate();
let reconciliations=0;const checked=[];
function close(actual,expected,label){if(typeof actual!=='number'||!Number.isFinite(actual)||Math.abs(actual-expected)>1e-6+Math.abs(expected)*2e-12)throw Error(`${label}: ${actual} != ${expected}`);reconciliations++;}
for(let i=0;i<cases.length;i++){
 put(assume,'D4',i+1);wb.recalculate();const x=cases[i],v=policy.getRange('D6:D13').values.flat();
 const expected=[x.policy_value,x.upfront_investment,x.annual_cash_pv,x.terminal_present_value,x.no_growth_reference,x.incremental_policy_value/x.no_growth_reference,x.terminal_share_of_net_value,x.value_per_base_nopat];v.forEach((n,k)=>close(n,expected[k],`${x.issuer}/${x.case}/summary${k}`));
 x.year_ledger.forEach((y,k)=>{const row=policy.getRange(`C${22+k}:K${22+k}`).values[0];const exp=[y.year,y.growth,y.nopat,y.marginal_roic,y.next_year_nopat,y.net_investment,y.cash_flow,y.discount_factor,y.present_value];row.forEach((n,j)=>close(n,exp[j],`${x.issuer}/${x.case}/year${y.year}/${j}`));});
 close(audit.getRange('D8').values[0][0],0,'Independent Excel identity');close(audit.getRange('D9').values[0][0],0,'Sealed scenario');checked.push({case:`${x.issuer} ${x.case}`,policy_value:v[0]});
}
for(const row of audit.getRange('D40:F48').values)for(const n of row)close(n,0,'Financial identity');
put(assume,'D4',2);const original=assume.getRange('E19').values[0][0];put(assume,'E19',.12);wb.recalculate();const changed=policy.getRange('D6').values[0][0];if(changed===cases[1].policy_value)throw Error('Growth edit did not recalculate');close(audit.getRange('D8').values[0][0],0,'Edited independent identity');put(assume,'E19',original);
// Missing active and unselected inputs, real zero EBIT and invalid spread.
put(assume,'D19',null);wb.recalculate();close(policy.getRange('D6').values[0][0],cases[1].policy_value,'Unselected blank does not block');put(assume,'D19',cases[0].assumptions.growth);
put(assume,'E19',null);wb.recalculate();if(typeof policy.getRange('D6').values[0][0]==='number')throw Error('Active blank hidden as zero');put(assume,'E19',original);
const savedEbit=statements.getRange('F8').values[0][0];put(statements,'F8',0);wb.recalculate();close(policy.getRange('D6').values[0][0],0,'Real zero EBIT');put(statements,'F8',savedEbit);
put(assume,'E23',cases[1].assumptions.terminal_growth);wb.recalculate();if(typeof policy.getRange('D6').values[0][0]==='number')throw Error('Invalid terminal spread hidden');put(assume,'E23',cases[1].assumptions.wacc);
put(assume,'D4',2);wb.recalculate();close(policy.getRange('D6').values[0][0],cases[1].policy_value,'Restored reference case');
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:30},summary:'Final formula error scan'});
await fs.writeFile(path.join(output,'formula_error_scan.ndjson'),errors.ndjson);
const inspect=await wb.inspect({kind:'table',range:'Policy review!C4:K13',include:'values,formulas',tableMaxRows:10,tableMaxCols:9,maxChars:4000});await fs.writeFile(path.join(output,'policy_inspection.ndjson'),inspect.ndjson);
const xlsx=await SpreadsheetFile.exportXlsx(wb);const workbookPath=path.join(output,'Corporate_Finance_Decision_Lab.xlsx');await xlsx.save(workbookPath);
const reopened=await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));reopened.recalculate();close(reopened.worksheets.getItem('Policy review').getRange('D6').values[0][0],cases[1].policy_value,'Export/reopen recalculation');
const images=[['Policy review','C2:K36','policy'],['Assumptions','C2:L30','assumptions'],['Statements','C5:I37','statements_msft'],['Statements','C42:I74','statements_target'],['Statements','C79:I111','statements_infosys'],['Audit','C2:I33','audit_policy'],['Audit','C37:F62','audit_financial']];
for(const [sheetName,range,name] of images){const img=await reopened.render({sheetName,range,scale:1.5,format:'png'});await fs.writeFile(path.join(output,name+'.png'),new Uint8Array(await img.arrayBuffer()));}
const raw=await fs.readFile(workbookPath);const report={workbook_sha256:crypto.createHash('sha256').update(raw).digest('hex'),cases_checked:checked,numeric_reconciliations:reconciliations,independent_excel_profit_layer_identity:true,source_facts_restored:true,input_change_and_blank_zero_boundaries_passed:true,export_reopen_recalculated:true,engine:'Artifact Tool 2.8; native Excel not executed',visual_review_pending:true};await fs.writeFile(path.join(output,'workbook_verification.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({workbookPath,reconciliations,cases:cases.length,export_reopen:true,rendered_views:images.length}));
