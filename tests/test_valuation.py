import math
import unittest
from dataclasses import replace
from finance_lab.valuation import Assumptions, policy_value, reverse_growth


class ValuationChecks(unittest.TestCase):
    def test_growth_is_neutral_at_equal_return_and_hurdle(self):
        for growth in (0,.01,.03,.06):
            a=Assumptions(growth,.10,.10,growth)
            self.assertAlmostEqual(policy_value(100,a)['policy_value'],750,places=9)

    def test_no_growth_is_perpetuity_at_every_fade_return(self):
        for r in (.06,.10,.20):
            a=Assumptions(0,r,r,0)
            self.assertAlmostEqual(policy_value(100,a)['policy_value'],750,places=10)

    def test_growth_creates_or_destroys_value_by_return(self):
        low=policy_value(100,Assumptions(.03,.07,.07,.03))
        high=policy_value(100,Assumptions(.03,.15,.15,.03))
        self.assertLess(low['incremental_policy_value'],0)
        self.assertGreater(high['incremental_policy_value'],0)

    def test_first_year_growth_is_funded_at_time_zero(self):
        r=policy_value(100,Assumptions(.10,.20,.12,.025))
        self.assertAlmostEqual(r['upfront_investment'],37.5)
        self.assertAlmostEqual(r['year_ledger'][0]['nopat'],82.5)
        for row in r['year_ledger']:
            self.assertAlmostEqual(row['profit_increment_reconciliation'],0,places=10)
            self.assertAlmostEqual(row['cash_flow']+row['net_investment'],row['nopat'])

    def test_scaling_and_zero_anchor(self):
        a=Assumptions(.05,.15,.12,.025)
        self.assertAlmostEqual(policy_value(200,a)['policy_value'],2*policy_value(100,a)['policy_value'])
        self.assertEqual(policy_value(0,a)['policy_value'],0)

    def test_terminal_cash_uses_terminal_reinvestment(self):
        a=Assumptions(.08,.20,.12,.025);r=policy_value(100,a)
        last=r['year_ledger'][-1]
        self.assertAlmostEqual(last['marginal_roic'],.12)
        self.assertAlmostEqual(r['terminal_cash_flow'],last['next_year_nopat']*(1-.025/.12))

    def test_exact_reverse_and_unreachable(self):
        a=Assumptions(.05,.15,.12,.025);target=policy_value(100,a)['policy_value']
        r=reverse_growth(100,a,target)
        self.assertEqual(r['status'],'solved');self.assertAlmostEqual(r['growth'],.05,places=10)
        self.assertLess(abs(r['residual']),1e-8)
        self.assertEqual(reverse_growth(100,a,target*100)['status'],'unreachable_in_declared_bracket')

    def test_invalid_domains_fail(self):
        a=Assumptions(.05,.15,.12,.025)
        for changes in ({'wacc':.025},{'terminal_roic':0},{'tax':1},{'growth':float('nan')},
                        {'horizon':5},{'marginal_roic':True},{'terminal_growth':-.01}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                policy_value(100,replace(a,**changes))
        for anchor in (-1,float('inf'),True):
            with self.assertRaises(ValueError):policy_value(anchor,a)

    def test_declared_forced_negative_policy_is_not_clipped(self):
        r=policy_value(100,Assumptions(.06,.05,.05,.06))
        self.assertLess(r['policy_value'],0)
        self.assertGreater(r['no_growth_reference'],0)


if __name__=='__main__':unittest.main()
