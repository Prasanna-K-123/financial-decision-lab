import unittest,tempfile
from pathlib import Path
from finance_lab.documents import Row,Token,checked_bytes,main_statement_window
from finance_lab.extraction import extract,money

class ContractChecks(unittest.TestCase):
 def setUp(self):
  self.m={'id':'TGT_2023','sha256':'test','currency':'USD','fiscal_year':2023,'period_end':'2024-02-03','scale_to_millions':1}
 def row(self,label,values,section='income',group='page:1',line=2):
  return Row(f'{group}:line:{line}',label,tuple([Token(label,10,180)]+[Token(str(v),300+i*100,330+i*100) for i,v in enumerate(values)]),section,group,600)
 def heads(self,years,section='income',group='page:1'):
  return self.row('Year',years,section,group,1)
 def test_instant_calendar_year_differs_from_flow_fiscal_label(self):
  rows=[self.heads([2024,2023],'balance'),self.row('Total assets',[20,10],'balance')]
  self.assertEqual(extract(self.m,rows,'assets',strict=True)['value'],'20')
  rows=[self.heads([2023,2022]),self.row('Revenue',[80,70])]
  self.assertEqual(extract(self.m,rows,'revenue',strict=True)['value'],'80')
 def test_scope_rejects_note_and_conflicting_main_statements(self):
  rows=[self.heads([2023,2022],None),self.row('Revenue',[10,9],None),self.heads([2023,2022],group='page:2'),self.row('Revenue',[20,19],group='page:2')]
  self.assertEqual(extract(self.m,rows,'revenue',strict=False)['value'],'10')
  self.assertEqual(extract(self.m,rows,'revenue',strict=True)['value'],'20')
  rows += [self.heads([2023,2022],group='page:3'),self.row('Revenue',[21,19],group='page:3')]
  self.assertIsNone(extract(self.m,rows,'revenue',strict=True)['value'])
 def test_wrong_currency_and_unsupported_contract(self):
  for key in ['current_share_price','customer_count','undisclosed_future_revenue']:
   self.assertEqual(extract(self.m,[],key,strict=True)['reason'],'outside_supported_financial_contract')
  self.assertEqual(extract(self.m,[],'revenue',strict=True,currency='INR')['reason'],'currency_mismatch')
  with self.assertRaises(ValueError):extract(self.m,[],'made_up',strict=True)
 def test_combined_metrics_are_not_silently_substituted(self):
  rows=[self.heads([2023,2022],'cashflow'),self.row('Depreciation amortization and other',[50,40],'cashflow')]
  self.assertIsNone(extract(self.m,rows,'da',strict=True)['value'])
 def test_note_references_do_not_join_the_row_label(self):
  rows=[Row('page:1:line:1','', (Token('Note',240,270),Token('2023',300,330),Token('2022',400,430)),'cashflow','page:1',600),
        Row('page:1:line:2','',(Token('Depreciation and amortization',10,180),Token('2.7,',220,240),Token('2.8',242,255),Token('and',256,263),Token('2.9',264,270),Token('524',300,330),Token('466',400,430)),'cashflow','page:1',600)]
  self.assertEqual(extract(self.m,rows,'da',strict=True)['value'],'524')
 def test_accounting_sign_and_hash_guard(self):
  self.assertEqual(money('(1,200)'),-1200);self.assertIsNone(money('1,200%'))
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'x';p.write_bytes(b'wrong')
   with self.assertRaises(ValueError):checked_bytes(p,'0'*64)
 def test_later_notes_are_outside_main_statement_window(self):
  rows=[]
  for page,kind in [(10,'income'),(11,'balance'),(12,'cashflow'),(30,'income')]:
   rows.append(self.heads([2023,2022],kind,f'page:{page}'))
  result=main_statement_window(rows)
  self.assertEqual([r.section for r in result],['income','balance','cashflow',None])
if __name__=='__main__':unittest.main()
