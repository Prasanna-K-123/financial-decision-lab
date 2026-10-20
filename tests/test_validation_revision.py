"""Decimal boundary regressions, separate from the original frozen test set."""
from dataclasses import replace
import math
import unittest
from finance_lab.valuation import Assumptions, policy_value


class SpreadBoundaryChecks(unittest.TestCase):
    def test_exact_declared_spread_accepts_both_decimal_constructions(self):
        for index in range(801):
            percent = index / 100
            terminal = percent / 100
            for wacc in (terminal + 0.0001, (percent + 0.01) / 100):
                with self.subTest(terminal=terminal, wacc=wacc):
                    a = Assumptions(.1, .18, .12, terminal, wacc=wacc)
                    self.assertTrue(math.isfinite(policy_value(100, a)['policy_value']))

    def test_materially_insufficient_spread_still_fails(self):
        for index in range(801):
            percent = index / 100
            a = Assumptions(.1, .18, .12, percent / 100)
            for wacc in ((percent + 0.009) / 100, percent / 100):
                with self.subTest(terminal=a.terminal_growth, wacc=wacc):
                    with self.assertRaises(ValueError):
                        policy_value(100, replace(a, wacc=wacc))


if __name__ == '__main__':
    unittest.main()
