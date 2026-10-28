"""Different accepted labels must not bypass strict conflict rejection."""
import unittest
from finance_lab.documents import Row, Token
from finance_lab.extraction import extract


class AliasConflictChecks(unittest.TestCase):
    def setUp(self):
        self.meta = {'id':'SYNTHETIC','sha256':'fixture','currency':'USD',
                     'fiscal_year':2025,'period_end':'2025-12-31','scale_to_millions':1}

    def rows(self, second, *, second_scope='income', first_label='Revenue', second_label='Total revenue'):
        def row(label, values, line, group, scope):
            return Row(f'{group}:line:{line}',label,
                       tuple([Token(label,0,180)]+[Token(str(x),300+i*100,330+i*100) for i,x in enumerate(values)]),
                       scope,group,600)
        return [row('Year',[2025,2024],1,'page:1','income'),
                row(first_label,[100,90],2,'page:1','income'),
                row('Year',[2025,2024],1,'page:2',second_scope),
                row(second_label,[second,80],2,'page:2',second_scope)]

    def test_conflicting_aliases_abstain_with_both_locators(self):
        for labels in [('Revenue','Total revenue'),('Net sales','Total revenue')]:
            with self.subTest(labels=labels):
                rows=self.rows(200,first_label=labels[0],second_label=labels[1])
                for ordering in (rows,rows[2:]+rows[:2]):
                    answer=extract(self.meta,ordering,'revenue',strict=True)
                    self.assertIsNone(answer['value'])
                    self.assertEqual(answer['reason'],'conflicting_supported_contexts')
                    self.assertEqual({p['source_value'] for p in answer['provenance']},{'100','200'})
        self.assertEqual(extract(self.meta,self.rows(200),'revenue',strict=False)['value'],'200')

    def test_agreeing_aliases_preserve_canonical_answer(self):
        answer=extract(self.meta,self.rows(100),'revenue',strict=True)
        self.assertEqual(answer['value'],'100')
        self.assertEqual(answer['provenance'][0]['row_label'],'Total revenue')

    def test_note_alias_does_not_create_a_main_statement_conflict(self):
        answer=extract(self.meta,self.rows(200,second_scope=None),'revenue',strict=True)
        self.assertEqual(answer['value'],'100')


if __name__=='__main__':
    unittest.main()
