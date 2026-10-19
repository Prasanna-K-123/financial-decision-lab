"""Generate research documents from the checked numerical release evidence."""
from pathlib import Path
import json,html,shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

R=Path(__file__).resolve().parents[1];O=R/'artifacts';O.mkdir(exist_ok=True);D=R/'reports'
load=lambda n:json.loads((D/n).read_text())
spread=load('financial_spread.json');cases=load('valuation_scenarios.json');summary=load('evaluation_summary.json');repro=load('clean_reproduction.json');workbook=load('workbook_verification.json');math=load('independent_math_verification.json')
regimes=load('growth_return_regimes.json');reverse=load('reverse_cases.json')
money=lambda x:f'{x:,.0f}';pct=lambda x:f'{x:.1%}'
navy='#203D57';muted='#526677';teal='#006B70'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
fig,ax=plt.subplots(figsize=(7.1,2.7))
for growth,color in [(0,'#506578'),(.02,'#1D7798'),(.04,'#007B68'),(.06,'#A55733')]:
 rows=[x for x in regimes if x['issuer']=='MSFT' and x['assumptions']['growth']==growth]
 ax.plot([x['assumptions']['marginal_roic']*100 for x in rows],[x['value_to_no_growth'] for x in rows],marker='o',ms=3,label=f'{growth:.0%} growth',color=color)
ax.axvline(10,color='#8D4B42',ls=':',lw=1);ax.axhline(1,color='#9BA8B4',lw=.8);ax.axhline(0,color='#CAD1D8',lw=.6)
ax.set(xlabel='Constant marginal ROIC (%)',ylabel='Policy value / no-growth value',title='Growth creates value only above the model’s 10% hurdle')
ax.legend(ncol=4,loc='upper left',frameon=False,fontsize=8);ax.grid(axis='y',alpha=.12);fig.tight_layout(pad=1)
fig.savefig(D/'growth_return_policy.png',dpi=180);fig.savefig(D/'growth_return_policy.svg');plt.close(fig)

fonts=Path(matplotlib.get_data_path())/'fonts/ttf'
for name,file in [('Body','DejaVuSans.ttf'),('BodyBold','DejaVuSans-Bold.ttf'),('BodyItalic','DejaVuSans-Oblique.ttf')]:pdfmetrics.registerFont(TTFont(name,str(fonts/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='BodyItalic',boldItalic='BodyBold')
styles={
 'title':ParagraphStyle('title',fontName='BodyBold',fontSize=24,leading=29,textColor=colors.HexColor(navy),spaceAfter=13),
 'h1':ParagraphStyle('h1',fontName='BodyBold',fontSize=17,leading=21,textColor=colors.HexColor(navy),spaceAfter=11),
 'h2':ParagraphStyle('h2',fontName='BodyBold',fontSize=11,leading=15,textColor=colors.HexColor(navy),spaceBefore=10,spaceAfter=5),
 'body':ParagraphStyle('body',fontName='Body',fontSize=9,leading=13,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='Body',fontSize=7.5,leading=10.5,textColor=colors.HexColor(muted),spaceAfter=6),
 'cell':ParagraphStyle('cell',fontName='Body',fontSize=7.4,leading=10),
 'head':ParagraphStyle('head',fontName='BodyBold',fontSize=7.4,leading=10,textColor=colors.white),
 'eq':ParagraphStyle('eq',fontName='Body',fontSize=9,leading=15,textColor=colors.HexColor(navy),leftIndent=10,spaceAfter=7),
}
W=A4[0]-80
def p(text,kind='body'):return Paragraph(text,styles[kind])
def table(rows,widths):
 data=[[p(str(x),'head' if i==0 else 'cell') for x in row] for i,row in enumerate(rows)]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(navy)),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#8D9AA6')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F0F3F6')])]))
 return t
def footer(canvas,doc):
 canvas.saveState();canvas.setStrokeColor(colors.HexColor('#B5C1CB'));canvas.line(40,34,A4[0]-40,34);canvas.setFont('Body',7);canvas.setFillColor(colors.HexColor(muted));canvas.drawString(40,22,'Prasanna K · '+('Research Portfolio' if 'Research Portfolio' in doc.title else 'Corporate Finance Decision Lab')+' · 19 October 2026');canvas.drawRightString(A4[0]-40,22,str(doc.page));canvas.restoreState()
def pdf(name,story,title):SimpleDocTemplate(str(O/name),pagesize=A4,rightMargin=40,leftMargin=40,topMargin=40,bottomMargin=48,title=title,author='Prasanna K',subject='Audited financial research and conditional operating-policy analysis').build(story,onFirstPage=footer,onLaterPages=footer)
def md(name,text):(D/name).write_text(text.strip()+'\n')
latest={x['issuer']:x for x in spread if x['split']=='final'}

tech=[]
tech +=[p('Corporate Finance<br/>Decision Lab','title'),p('Primary financial statements, cash-generation analysis and growth-funding valuation','h2'),p('Prasanna K · M.A. Actuarial Economics, Madras School of Economics<br/>Research version: 19 October 2026','small')]
tech +=[p('Decision and measured findings','h2'),p('Review the accounting source before trusting a financial number. Then distinguish cash generated by the historical business from the new capital a future growth policy requires. The study links nine annual reports to a reviewed financial spread and a ten-year model with immediate first-year growth funding.')]
tech +=[table([['FY 2025 case','Revenue','EBIT','CFO','Cash investment','CFO less that investment'],['Microsoft','281,724','128,528','136,162','64,551 PPE','71,611'],['Target','104,780','5,117','6,562','3,727 PPE','2,835'],['Infosys','19,277','4,071','4,351','263 PPE + intangibles','4,088 (combined)']],[75,70,66,66,106,W-383]),p('USD millions. Different fiscal calendars. The Infosys combined measure is explicitly separate from pure PPE. None of these historical proxies is FCFF.','small')]
tech +=[p('Microsoft','h2'),p('FY 2025 revenue grew 14.9%, while gross cash PPE spending rose 45.1%. Operating margin reached 45.6%, but CFO less cash PPE fell from USD 74,071m to USD 71,611m. Higher accounting profit did not translate into higher post-PPE cash than the previous year.')]
tech +=[p('Target','h2'),p('FY 2025 revenue fell 1.7% and operating margin was 4.9%, down from 5.2%. CFO less cash PPE fell 36.7%, to USD 2,835m. Its current ratio of 0.94x is an accounting observation, not a standalone solvency conclusion.')]
tech +=[p('Infosys','h2'),p('CFO rose USD 1,203m. The cash-flow bridge separates USD 751m of higher pre-tax operating cash from USD 452m of lower cash taxes. The tax component is 37.6% of the CFO increase; the historical cash increase should not simply be extrapolated as earnings growth.')]
tech +=[p('Extraction result','h2'),p('Both methods returned 33 source-supported correct answers out of 36 final financial targets, with three justified direct-unavailable abstentions. There is no final-year accuracy gain. The two literal-lookup wrong-column errors occur in development, where the stricter method returns 66/72 correct versus 64/72. Control rejections are a separate API-contract check.')]
tech +=[PageBreak(),p('Source and evaluation controls','h1')]
tech +=[table([['Issuer / format','Development','Final','Fiscal end / statement unit'],['Microsoft / 10-K DOCX','FY 2023, FY 2024','FY 2025','30 June / USD millions'],['Target / annual-report PDF','FY 2023, FY 2024','FY 2025','3 Feb 2024; 1 Feb 2025; 31 Jan 2026 / USD millions'],['Infosys / 20-F PDF','FY 2023, FY 2024','FY 2025','31 March / USD millions']],[115,100,55,W-270])]
tech +=[p('Fixed requests and definitions','h2'),p('Nine reports × twelve financial targets =108 targets. Nine reports × three unsupported controls =27 controls. Both methods answer the same 135 requests, yielding 270 recorded responses. Targets comprise six annual flows (revenue, EBIT, consolidated net income, CFO, gross cash PPE and pure D&amp;A) and six fiscal-end balances (assets, liabilities, equity, cash, current assets and current liabilities). Net income and equity include NCI where reported. Cash excludes investments.')]
tech +=[p('Source review','h2'),p('Every original file has a SHA256, byte count, issuer URL, retrieval record, identity, calendar and unit check. DOCX CRC/XML and PDF parsing checks pass. Issuer-hosted versions retrieved later are not certified immutable original SEC accessions. HTTP Last-Modified is not treated as a filing date. Raw reports remain private; the repository publishes numerical facts, short row labels and locators.')]
tech +=[p('Fixed methods and references','h2'),p('The literal baseline searches matching row labels and year columns anywhere in the report. The strict method adds main-statement scope and conflict rejection. They share aliases and audited document metadata. Separately transcribed references supply source cells for evaluation and the reviewed finance model; they are never extractor inputs. Correct consolidated annual MD&amp;A/summary duplicates count as valid baseline provenance.')]
tech +=[table([['Split / method','Financial correct / targets','Financial answered','Controls rejected'],['Development / literal','64 / 72','66','18 / 18'],['Development / strict','66 / 72','66','18 / 18'],['Final / literal','33 / 36','33','9 / 9'],['Final / strict','33 / 36','33','9 / 9']],[130,145,120,W-395])]
tech +=[p('Chronology and limits','h2'),p('The six development reports precede the method freeze. All final predictions were committed before final reference annotation/scoring; frozen code and prediction hashes remain unchanged. This is retrospective: Target FY 2025 cover highlights were incidentally displayed in source identity review. It is not a blind, prospective or unseen-issuer test. There are only three final report clusters, so no population confidence interval is presented. Workflow source annotations are not external human review.')]
tech +=[p('Known error ledger','h2'),p('The literal baseline returns Infosys FY 2023 D&amp;A 466 instead of 524, and FY 2024 D&amp;A 524 instead of 565, because an earlier table’s header positions select the prior-year cell. The final FY 2025 methods tie. All missed, wrong, unavailable and control outcomes remain in the ledger; difficult targets are not removed from denominators.')]
tech +=[PageBreak(),p('Historical cash and accounting controls','h1')]
rows=[['Case','Revenue','EBIT margin','CFO','Cash PPE','CFO − PPE','Combined proxy*']]
for x in spread:
 rows.append([x['id'],money(x['facts']['revenue']),pct(x['reported_operating_margin']),money(x['facts']['cfo']),money(x['facts']['cash_ppe']) if x['facts']['cash_ppe'] is not None else 'n.a.',money(x['cash_generation_cfo_minus_cash_ppe']) if x['cash_generation_cfo_minus_cash_ppe'] is not None else 'n.a.',money(x['cash_generation_after_combined_investment']) if x['cash_generation_after_combined_investment'] is not None else 'n.a.'])
tech +=[table(rows,[82,72,64,72,65,76,W-431]),p('*Infosys only: CFO minus combined PPE/intangibles cash. USD millions, except margins. Report labels are not a common market date. Target FY 2023 has 53 weeks; the other displayed Target years have 52. Values are from each pinned report, not a reconstructed immutable vintage.','small')]
tech +=[p('Three source definitions that matter','h2'),p('<b>Microsoft:</b> the main cash-flow line combines depreciation, amortisation and other. It is unavailable as a direct pure-D&amp;A target. Cash PPE purchases exclude noncash lease additions and acquisitions.<br/><b>Target:</b> no direct total-liabilities line is substituted. The balance control adds separately reported current and noncurrent liabilities before comparing with assets and equity.<br/><b>Infosys:</b> the cash-flow line combines PPE and intangibles. Pure-PPE extraction abstains; the combined spending and its separate cash-generation proxy remain labelled. IFRS lease and interest classifications are retained.')]
tech +=[p('Infosys FY 2024 → FY 2025 cash bridge (USDm)','h2'),table([['Component','FY 2024','FY 2025','Contribution to CFO change'],['Cash generated before tax','4,262','5,013','+751'],['Cash income taxes paid','1,114','662','+452 from lower cash outflow'],['Net operating cash','3,148','4,351','+1,203']],[185,75,75,W-335])]
tech +=[p('Reconciliations','h2'),p('All nine balance identities, nine sums of operating/investing/financing cash plus FX, and nine beginning-to-ending-cash bridges have zero residual at reported million-unit precision. These checks do not rely on making total liabilities an assets-minus-equity plug. They test source consistency; they do not establish operating liquidity or regulatory solvency.')]
tech +=[PageBreak(),p('Growth funding and policy valuation','h1')]
tech +=[p('The model starts at N0=reported EBIT×(1−assumed tax). Growth is fixed for years 1–5 and fades to terminal growth by year 10. New capital paid at time t earns its marginal return in year t+1. The immediate I0 payment prevents free first-year growth. Initial marginal ROIC fades to its terminal rate over funding dates 5–10.')]
tech +=[p('Nt = N(t−1) × (1 + gt)<br/>It = [N(t+1) − Nt] / Rt<br/>V0 = −I0 + Σ(Ft / (1+w)<super>t</super>, t=1…10) + TV10 / (1+w)<super>10</super><br/>Ft = Nt − It; F11 = N11 × (1 − gT/RT); TV10 = F11 / (w − gT)','eq')]
scenario_rows=[['Policy','Initial growth','ROIC initial / terminal','Terminal growth','Policy value','Immediate I0','Terminal share']]
for x in cases:
 a=x['assumptions'];scenario_rows.append([x['issuer']+' '+x['case'],pct(a['growth']),pct(a['marginal_roic'])+' / '+pct(a['terminal_roic']),pct(a['terminal_growth']),money(x['policy_value']),money(x['upfront_investment']),pct(x['terminal_share_of_net_value'])])
tech +=[table(scenario_rows,[99,50,91,55,79,75,W-449]),p('Values in USDm. Common illustrative WACC 10% and normalised tax 25%. Values are operating-policy scenarios before financing, cash/nonoperating assets, NCI, pension and option adjustments. They retain reported EBIT accounting and are not observed enterprise/equity values, share-price targets or market-calibrated forecasts.','small')]
tech +=[p('Sensitivity and reverse cases','h2'),p('Reference-policy sensitivity uses WACC 6%–16% in 1 pp steps and terminal growth 0%–5% in 0.5 pp steps: 121 cases per issuer, 363 total. A49-regime growth/ROIC grid is repeated at each issuer’s profit scale (147 evaluations), not 147 independent economic patterns. Reverse cases target 80%,100% and 120% of reference policy value, solving initial growth only on[0%, 25%]. Seven targets solve; Target and Infosys 80% targets are unreachable in that bracket. No extrapolation or implied market expectation is claimed.')]
tech +=[p('The funding amount is aggregate net growth investment after maintenance, including working-capital and intangible needs on the chosen EBIT basis. It is not a mechanical substitution of historical CFO-minus-PPE for unlevered free cash flow. Comparing I0 with historical post-PPE cash is only a scale diagnostic.')]
tech +=[PageBreak(),p('Independent checks and reproducibility','h1')]
tech +=[Image(str(D/'growth_return_policy.png'),width=W,height=W*2.7/7.1),p('Illustrative constant-return/growth policies. Negative forced-policy value is possible when growth consumes more capital than the specified policy earns; it is not a negative limited-liability equity valuation. At ROIC=WACC, growth is value-neutral after funding I0.','small')]
tech +=[table([['Verification','Recorded result'],['Mathematical boundaries','16 focused tests, including year/scope/currency/hash controls, advance funding, no-growth and ROIC=WACC identities'],['Different valuation formulation','519 case evaluations matched 45-digit Decimal incremental-profit-layer values; maximum difference 3.95×10⁻⁹ USDm'],['Formula workbook','932 numeric reconciliations across all nine cases; active/unselected missing inputs, zero EBIT, invalid spread, input change and saved-file reopening checked'],['Fresh raw-source reconstruction','Nine original reports re-decoded/OCRed; eleven scientific outputs byte-identical; 565.57s wall, max child RSS 553,208 KiB'],['Public numeric reconstruction','Nine outputs rebuilt from published facts and sealed predictions; two original prediction seals checked']],[145,W-145])]
tech +=[p('Independent mathematics, not an external audit','h2'),p('The main model discounts policy cash flows. The independent calculation values each permanent incremental-profit layer as ΔN×(1/WACC−1/ROIC), discounts its funding time, then sums the infinite terminal layers analytically. It uses 45-digit Decimal arithmetic and does not import the model implementation or its ledger. The check tolerance is USD 1 absolute plus 2×10⁻¹² relative. It is a computational cross-check, not third-party professional review.')]
tech +=[p('Execution and source limits','h2'),p('The clean run used Python 3.12.14, PyMuPDF 1.26.6 and Tesseract 5.3.4 with a pinned English trained-data hash. It reused original source bytes; fresh-network or cross-platform reproduction is not established. A separately labelled cached-structure run took 8.71s. Native Excel and human time savings were not measured. The public workbook retains formulas and one active scenario build; it was recalculated, exported and reimported in Artifact Tool.')]
tech +=[p('Primary references','h2'),p('Issuer annual reports: <link href="https://www.microsoft.com/investor/reports/ar25/index.html" color="#006B70">Microsoft</link>, <link href="https://corporate.target.com/investors/annual/annual-reports-and-archive" color="#006B70">Target</link>, <link href="https://www.infosys.com/investors/reports-filings/annual-report/annual-reports.html" color="#006B70">Infosys</link>. Exact nine original-file URLs and per-field locators are in data/sources.json and data/references.json. Growth/reinvestment background: <link href="https://pages.stern.nyu.edu/~adamodar/New_Home_Page/valquestions/growth.htm" color="#006B70">Damodaran, NYU Stern</link>. The exact advance-funding model is defined in this study’s protocol.','small')]
pdf('P7_Technical_Report.pdf',tech,'Corporate Finance Decision Lab — Technical Report')

memo=[p('Cash generation and<br/>capital allocation','title'),p('Decision memo · Prasanna K · 19 October 2026','small'),p('Review the source definition, separate tax/capital-spending effects from earnings, and require an explicit return on the new capital funding growth. The historical evidence and future policy scenarios answer different questions.')]
memo +=[p('Microsoft: profit growth with a higher capital burden','h2'),p('Revenue rose 14.9% in FY 2025, operating margin reached 45.6%, and CFO rose 14.9%. Cash PPE spending rose 45.1% to USD 64,551m. CFO less cash PPE fell 3.3%, to USD 71,611m. Review incremental returns and funding timing before treating higher accounting earnings as a proportional increase in distributable cash.')]
memo +=[p('Target: less cash after investment','h2'),p('FY 2025 revenue fell 1.7%, operating margin declined to 4.9%, and CFO was USD 6,562m. With USD 3,727m cash PPE purchases, the defined post-PPE proxy is USD 2,835m, down 36.7%. The reference growth policy creates only 2.0% more value than its no-growth cash-return reference under the stated assumptions. Growth volume alone is a weak reason to commit capital.')]
memo +=[p('Infosys: examine cash-tax timing','h2'),p('CFO increased 38.2%, to USD 4,351m, while consolidated net income was USD 3,162m versus USD 3,169m. The USD 1,203m CFO increase comprises USD 751m higher pre-tax operating cash and USD 452m lower cash taxes. Do not extrapolate that cash increase as a structural earnings growth rate. The USD 263m investing line includes intangibles, so the USD 4,088m combined proxy is labelled separately from pure-PPE cash generation.')]
memo +=[p('What the data support','h2'),table([['Review','Result'],['Primary reporting inputs','Nine original issuer reports; exact hashes, fiscal calendars, USD-million units and source cells'],['Final extraction check','Both methods 33 supported correct /36 financial targets, with 3 justified abstentions; no final accuracy gain'],['Accounting controls','All nine balance identities, cash-flow sums and ending-cash bridges reconcile'],['Decision-model checks','519 independent Decimal case evaluations and 932 workbook reconciliations']],[160,W-160])]
memo +=[p('Historical CFO-minus-investment figures are accounting proxies, not FCFF or cash available for payout. Fiscal dates differ across firms, and lease/interest classifications are not harmonised. This memo does not estimate a target share price or recommend a security trade.','small'),PageBreak(),p('Use explicit growth-funding hurdles','h1')]
memo +=[p('The model’s first new investment is paid immediately. At a constant marginal ROIC equal to WACC, growth adds no value after funding. Above the hurdle it can add value; below it a forced growth policy destroys value. The terminal contribution and financing requirements therefore matter as much as the growth rate.')]
memo +=[Image(str(D/'growth_return_policy.png'),width=W,height=W*2.7/7.1)]
memo +=[table([['Reference policy','Initial growth / ROIC','Terminal growth / ROIC','Policy value (USDm)','Immediate I0 (USDm)'],['Microsoft','10% /18%','2.5% /12%','1,316,560','53,553'],['Target','2% /12%','2% /10%','39,143','640'],['Infosys','5% /16%','2.5% /12%','35,379','954']],[92,112,117,103,W-424])]
memo +=[p('Illustrative common WACC 10% and normalised tax 25%. These are conditional operating-policy values, before the financing/nonoperating adjustments needed for an enterprise/equity assessment. They retain reported EBIT’s expense/lease basis. Assumed marginal ROIC is not an estimate derived from observed historical ROIC.','small')]
memo +=[p('Questions before an actual investment decision','h2'),p('Which incremental return is supported by operating evidence? What working capital, intangible and fixed capital must be paid before the first growth year? What lease/interest adjustments are required on the chosen EBIT basis? How much of cash conversion reflects tax timing? What growth/return fade is economically sustainable?')]
memo +=[p('Sensitivity, not forecast certainty','h2'),p('The release contains 363 WACC/terminal-growth cases and 147 fixed-regime evaluations. Reference terminal PV shares are 64.2% for Microsoft, 47.0% for Target and 54.6% for Infosys. Two of nine reverse targets are unreachable in the declared[0%, 25%] growth bracket; the model reports that limit instead of extrapolating. No probability weights or market-implied growth claim are attached to these scenarios.')]
memo +=[p('Read the audit trail','h2'),p('<link href="https://github.com/Prasanna-K-123/financial-decision-lab" color="#006B70">Repository, technical report, source locators and formula workbook</link><br/><link href="https://prasanna-k-123.github.io/financial-decision-lab/" color="#006B70">Interactive financial evidence and policy explorer</link>','small')]
pdf('P7_Decision_Memo.pdf',memo,'Cash Generation and Capital Allocation — Decision Memo')

projects=[
('Credit risk and model validation','credit-risk-model-validation','300,000 mortgages and 20.15 million monthly records. Chronological SQL snapshots, censored outcomes, fixed models and economic-stress validation. Better held-out discrimination did not justify unchanged probabilities: calibration failures are disclosed.','Credit risk, model validation, risk analytics'),
('Insurance pricing and reserve uncertainty','insurance-price-reserve-risk','French motor pricing and a separate US auto-reserving study. Fixed pricing comparisons and reserve interval scores expose conditional-calibration and coverage failures. The two populations are not joined.','Actuarial analytics, insurance risk, uncertainty modelling'),
('Causal customer decisions','causal-customer-decisions','A 64,000-customer, three-arm randomized experiment. Frozen policies and doubly robust evaluation did not establish that personalized targeting beats the selected simple campaign. Explicit margin and contact costs are scenarios.','Product analytics, experimentation, causal inference'),
('Treasury ALM and liquidity','treasury-alm','Interest-rate hedging, published Treasury curves and hypothetical benefit cash flows. Four hedge policies, 56 rate stresses and 108 liquidity-runoff cases. Independent Decimal and formula-workbook reconciliations support the modelling.','Treasury, ALM, financial risk'),
('Demand, capital and inventory','demand-inventory','210 historical M5 item-store series link probabilistic forecasts to replenishment under common capital/capacity constraints. Fifteen final weekly origins and overlapping horizons limit inference. Operating effects are simulations, not observed retailer savings.','Business analytics, forecasting, operations and working capital'),
('Indian inflation release vintages','inflation-vintages','48 official releases and 144 vintage observations. An 18-release final check retains persistence: RMSE 0.8185 pp versus 1.6901 for fixed AR(1). Release dates and the later base revision remain separate. No current inflation forecast is claimed.','Economic research, time series, publication-aware data'),
('Corporate Finance Decision Lab','financial-decision-lab','Nine issuer reports, a traced financial spread and a funded-growth policy model. Final extraction: 33 supported correct /36 financial targets for both methods, three justified abstentions. 519 independent valuation checks and a reconciled formula workbook.','Corporate finance, FP&A, financial research and finance data'),
]
guide=[p('Prasanna K','title'),p('Risk, finance and applied economic research','h1'),p('M.A. Actuarial Economics · Madras School of Economics · Class of 2028<br/>Summer 2027 internships · Seven research studies with source-linked evidence','small'),p('The portfolio connects data controls and model comparisons to decisions. Each study includes a technical report, a decision memo and an evidence browser. Historical tests and hypothetical scenarios keep their stated boundaries.')]
for i,(name,repo,desc,role) in enumerate(projects):
 if i==4:guide +=[PageBreak(),p('Research portfolio','h1')]
 guide +=[KeepTogether([p(f'{i+1}. {name}','h2'),p(desc),p(f'{html.escape(role)}<br/><link href="https://github.com/Prasanna-K-123/{repo}" color="#006B70">Code and research</link> · <link href="https://prasanna-k-123.github.io/{repo}/" color="#006B70">Evidence browser</link>','small')])]
guide +=[p('Choose a starting point','h2'),p('Credit/model risk: studies 1 and 4. Insurance: 2 and 4. Corporate finance/FP&amp;A: 7 and 6. Product/business analytics: 3 and 5. Economic research: 6 and 3. The shared standard is traceable source data, explicit information timing, appropriate uncertainty and a decision that follows the evidence.')]
guide +=[p('<link href="https://prasanna-k-123.github.io/financial-decision-lab/portfolio.html" color="#006B70">Open the seven-study portfolio</link> · <link href="https://github.com/Prasanna-K-123" color="#006B70">GitHub</link> · <link href="https://www.linkedin.com/in/prasanna-k-964716384/" color="#006B70">LinkedIn</link>','small')]
pdf('Prasanna_K_Research_Portfolio.pdf',guide,'Prasanna K — Research Portfolio')

# Text alternatives retain the same quantitative definitions and limits.
md('DECISION_MEMO.md','''# Cash generation and capital allocation

Prasanna K · 19 October 2026

Microsoft FY 2025 revenue rose 14.9%, cash PPE 45.1%, and CFO less PPE fell 3.3%
to USD 71,611m. Target’s proxy fell 36.7% to USD 2,835m. Infosys CFO increased
USD 1,203m: USD 751m higher pre-tax operating cash plus USD 452m lower cash taxes.
Infosys PPE/intangibles cash spending is combined; its USD 4,088m cash proxy is
labelled separately and is not pure CFO-minus-PPE or FCFF.

The conditional ten-year policy model pays growth investment before the next
year’s profit. Constant-regime ROIC=WACC must make growth value-neutral. At
illustrative WACC 10% and tax 25%, reference policy values are USD 1,316,560m,
USD 39,143m and USD 35,379m for Microsoft, Target and Infosys. Initial net growth
investments are USD 53,553m, USD 640m and USD 954m. These retain reported EBIT
accounting and precede financing/nonoperating/equity adjustments. They are not
market-calibrated enterprise values, target prices or investment recommendations.

Both extraction methods answer 33/36 final financial targets correctly with
three justified direct-unavailable abstentions. No final accuracy gain is claimed.
The nine unsupported-control checks are separate API-contract rejections.

See the [two-page memo](../artifacts/P7_Decision_Memo.pdf),
[technical report](TECHNICAL_REPORT.md), [source references](../data/references.json)
and [formula workbook](../artifacts/Corporate_Finance_Decision_Lab.xlsx).
''')
md('TECHNICAL_REPORT.md','''# Corporate Finance Decision Lab — technical report

Prasanna K · M.A. Actuarial Economics, MSE · 19 October 2026

The [five-page PDF](../artifacts/P7_Technical_Report.pdf) documents the source
audit, chronological workflow, complete evaluation, financial controls, growth
funding, independent model reconciliation and reproduction boundaries.

## Data and fixed comparison

Microsoft, Target and Infosys FY 2023/24 form six development reports; FY 2025
forms three final report cases. Nine original issuer reports, 108 financial
targets and 27 unsupported controls. All 270 two-method responses are retained.
Report calendars differ and every main monetary unit is USD millions. References
are source transcriptions, not external human review, and are not inference inputs.

Final results: both methods 33 supported correct /36 financial targets, three
direct-unavailable abstentions, nine control rejections. Development: strict 66/72,
literal 64/72; six unavailable targets for each. Valid consolidated annual MD&A
duplicates count as correct baseline provenance. The two development errors are
Infosys D&A prior-year cells. No final superiority or universal extraction claim.

Method code was frozen after development and predictions were committed before
final annotation/scoring. The reports are already public: Target FY 2025 cover
highlights were incidentally displayed in source review. This is not a blind,
prospective or unseen-issuer evaluation. Three final clusters do not justify a
population confidence interval. The public repository is a clean completed-study
import; private build IDs are process records, not external timestamp certification.

## Finance and mathematical checks

All nine balance identities, cash-flow sums and cash bridges reconcile. Target
liabilities use current+noncurrent source subtotals, not an A-E plug. Microsoft
D&A+other is unavailable as pure D&A; Infosys PPE+intangibles is unavailable as
pure cash PPE. Separate combined/derived controls do not replace those targets.
CFO-minus-cash-PPE is a named historical accounting proxy, not FCFF.

Ten-year growth policy: N0=EBIT*(1-tax), It=(N(t+1)-Nt)/Rt and Ft=Nt-It.
V0=-I0+sum(Ft/(1+w)^t,t=1..10)+TV10/(1+w)^10, with
F11=N11*(1-gTerminal/RTerminal) and TV10=F11/(w-gTerminal).
Funding date 0 is real: no free first-year growth. Constant ROIC=WACC makes
growth value-neutral. Assumed ROIC/growth/WACC/tax are scenarios; reported EBIT
expense/lease basis is retained and no equity/market-price bridge is asserted.

Nine scenarios, 363 sensitivity cases, 147 constant-regime evaluations and nine
reverse cases are fixed in the protocol. 519 case evaluations match a separately
implemented 45-digit Decimal incremental-profit-layer formulation. The normalized
49-regime grid repeats at three profit scales; these are not independent data.
Seven reverse targets solve; two 80% targets are unreachable in[0%, 25%] growth.

The formula workbook has 932 numeric reconciliations across all nine cases,
input-change and missing/zero boundaries, independent profit-layer checks and
export/reopen recalculation. Artifact Tool was used; native Excel was not executed.

## Reproduction

A fresh source/code directory repeated all original report decoding/OCR and
reproduced eleven scientific outputs byte for byte in 565.57 seconds. Maximum
child RSS 553,208 KiB; Python 3.12.14, PyMuPDF 1.26.6, Tesseract 5.3.4 and a pinned
English trained-data hash. No source cache of decoded rows was reused.
An 8.71second run with all nine decoded structures cached is reported separately.
No fresh-network, cross-platform, external-review or human-time-saving claim.

The public numeric route rebuilds nine outputs from published facts/sealed
predictions and checks the two prediction hashes. It is not a fresh original
PDF/DOCX audit. See README, source/prediction manifests, complete error ledger,
independent_math_verification.json, workbook_verification.json and
clean_reproduction.json for exact artifacts and scope.

Primary originals are linked in data/sources.json and per-field locators in
data/references.json. Raw copyrighted issuer reports remain private. Growth and
reinvestment background: [Damodaran, NYU Stern](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/valquestions/growth.htm).
''')
md('RECRUITER_GUIDE.md','''# Inspect the study

1. Read the two-page decision memo for the three financial observations.
2. Open the workbook. Use Assumptions D4 to select any of nine company/policy
   cases. Edit the blue growth/return/tax/hurdle inputs; one active schedule
   recalculates and the independent policy identity should remain zero.
3. Follow a financial input to its exact source hash and PDF page/DOCX table row
   in data/references.json. Missing pure/direct targets remain unavailable.
4. Inspect the final extraction ledger. Both methods tie 33/36, not a claimed
   superiority result. Unsupported controls are separate contract tests.
5. Run the public numeric reproduction. A separate pinned-cache raw-source
   reconstruction includes original report decoding and OCR.

The study is relevant to corporate finance, FP&A, financial research, accounting
data quality and model validation. It is an academic/research implementation,
not a claim of proprietary industry experience, original estimator invention,
commercial impact or market-calibrated equity valuation.
''')
(R/'data/portfolio_projects.json').write_text(json.dumps([{'name':name,'repo':repo,'description':desc,'roles':role} for name,repo,desc,role in projects],indent=2)+'\n')
for f in ['P7_Technical_Report.pdf','P7_Decision_Memo.pdf','Prasanna_K_Research_Portfolio.pdf']:print(O/f)
