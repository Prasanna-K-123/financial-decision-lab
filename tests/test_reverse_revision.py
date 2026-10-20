"""A nonmonotone counterexample must not become a false no-root claim."""
from dataclasses import replace
import unittest
from finance_lab.valuation import Assumptions, policy_value, reverse_growth


class ReverseStatusChecks(unittest.TestCase):
    def test_reachable_interior_target_with_same_sign_endpoints(self):
        a = Assumptions(.1, .1275497179933333, .4364627536378713,
                        .015114861501384544, wacc=.1804206031051271,
                        horizon=30, high_growth_years=10)
        target = 153.51213426457332
        self.assertGreater(policy_value(100, replace(a, growth=0))['policy_value'], target)
        self.assertGreater(policy_value(100, replace(a, growth=.25))['policy_value'], target)
        self.assertLess(policy_value(100, replace(a, growth=.225))['policy_value'], target)
        self.assertEqual(reverse_growth(100, a, target)['status'], 'not_bracketed')

    def test_monotone_unreachable_status_and_bracketed_root_remain(self):
        for roic in (.08, .10, .15):
            a = Assumptions(.05, roic, roic, .025)
            self.assertEqual(reverse_growth(100, a, 1e7)['status'], 'unreachable_in_declared_bracket')
        a = Assumptions(.05, .15, .12, .025)
        target = policy_value(100, a)['policy_value']
        self.assertEqual(reverse_growth(100, a, target)['status'], 'solved')

    def test_sign_checks_do_not_underflow_for_small_anchors(self):
        a = Assumptions(.05, .15, .12, .025)
        target = policy_value(1e-200, a)['policy_value']
        solved = reverse_growth(1e-200, a, target)
        self.assertEqual(solved['status'], 'solved')
        self.assertAlmostEqual(solved['growth'], .05, places=12)
        self.assertEqual(reverse_growth(1e-200, a, 1e-190)['status'], 'unreachable_in_declared_bracket')

    def test_nonfinite_calculations_are_rejected(self):
        a = Assumptions(.05, .15, .12, .025)
        with self.assertRaises(ValueError):
            policy_value(1e308, a)
        with self.assertRaises(ValueError):
            reverse_growth(1e308, a, 1e308)


if __name__ == '__main__':
    unittest.main()
