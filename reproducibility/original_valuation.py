"""Conditional operating-policy value with explicit advance growth funding.

These are scenario inputs, not market estimates. New investment at time t
funds the incremental operating profit at t+1. Initial investment is paid now.
"""
from dataclasses import dataclass, asdict, replace
import math


@dataclass(frozen=True)
class Assumptions:
    growth: float
    marginal_roic: float
    terminal_roic: float
    terminal_growth: float
    wacc: float = 0.10
    tax: float = 0.25
    horizon: int = 10
    high_growth_years: int = 5

    def validate(self):
        values = [self.growth,self.marginal_roic,self.terminal_roic,self.terminal_growth,self.wacc,self.tax]
        if not all(isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x) for x in values):
            raise ValueError('Finite numeric assumptions required')
        if not -0.25 <= self.growth <= 0.50 or not 0 <= self.terminal_growth <= 0.08:
            raise ValueError('Growth outside the stated model domain')
        if min(self.marginal_roic,self.terminal_roic) <= 0 or max(self.marginal_roic,self.terminal_roic)>1:
            raise ValueError('Positive ROIC no greater than100% required')
        if not 0<=self.tax<1 or not 0<self.wacc<=0.50 or self.wacc-self.terminal_growth<0.0001:
            raise ValueError('Tax/WACC domain or terminal discount spread invalid')
        if type(self.horizon) is not int or type(self.high_growth_years) is not int \
                or not 1<=self.high_growth_years<self.horizon<=50:
            raise ValueError('Invalid annual horizon/fade')


CASES = {
 'MSFT': {'downside':(.05,.10,.10,.02),'reference':(.10,.18,.12,.025),'expansion':(.15,.25,.15,.03)},
 'TGT': {'downside':(0,.07,.08,.01),'reference':(.02,.12,.10,.02),'expansion':(.04,.18,.12,.025)},
 'INFY': {'downside':(.02,.10,.10,.02),'reference':(.05,.16,.12,.025),'expansion':(.08,.22,.15,.03)},
}


def policy_value(ebit, assumptions):
    a = assumptions
    a.validate()
    if not isinstance(ebit,(float,int)) or isinstance(ebit,bool) or not math.isfinite(ebit) or ebit<0:
        raise ValueError('Finite nonnegative reported EBIT anchor required')
    n = [float(ebit)*(1-a.tax)]
    growth = [None]
    for year in range(1,a.horizon+2):
        if year<=a.high_growth_years:
            g=a.growth
        elif year<=a.horizon:
            g=a.growth+(a.terminal_growth-a.growth)*(year-a.high_growth_years)/(a.horizon-a.high_growth_years)
        else:
            g=a.terminal_growth
        growth.append(g)
        n.append(n[-1]*(1+g))
    def roic_at(time):
        if time<a.high_growth_years:
            return a.marginal_roic
        return a.marginal_roic+(a.terminal_roic-a.marginal_roic)*(time-a.high_growth_years+1)/(a.horizon-a.high_growth_years+1)
    investment=[(n[t+1]-n[t])/roic_at(t) for t in range(a.horizon+1)]
    years=[]
    for t in range(1,a.horizon+1):
        cash=n[t]-investment[t]
        discount=(1+a.wacc)**t
        years.append({'year':t,'growth':growth[t],'nopat':n[t],'marginal_roic':roic_at(t),
            'next_year_nopat':n[t+1],'net_investment':investment[t],
            'cash_flow':cash,'discount_factor':discount,'present_value':cash/discount,
            'profit_increment_reconciliation':n[t+1]-n[t]-investment[t]*roic_at(t)})
    terminal_cash=n[-1]*(1-a.terminal_growth/a.terminal_roic)
    terminal_value=terminal_cash/(a.wacc-a.terminal_growth)
    terminal_pv=terminal_value/(1+a.wacc)**a.horizon
    cash_pv=sum(x['present_value'] for x in years)
    value=-investment[0]+cash_pv+terminal_pv
    flat=n[0]/a.wacc
    return {'reported_ebit':float(ebit),'assumptions':asdict(a),'base_normalised_nopat':n[0],
        'upfront_investment':investment[0],'annual_cash_pv':cash_pv,'terminal_cash_flow':terminal_cash,
        'terminal_value_at_horizon':terminal_value,'terminal_present_value':terminal_pv,
        'policy_value':value,'no_growth_reference':flat,'incremental_policy_value':value-flat,
        'terminal_share_of_net_value':terminal_pv/value if abs(value)>1e-12 else None,
        'terminal_share_of_positive_gross_pv':terminal_pv/(cash_pv+terminal_pv) if cash_pv+terminal_pv>0 else None,
        'value_per_base_nopat':value/n[0] if n[0] else None,'year_ledger':years}


def reverse_growth(ebit, assumptions, target_value, *, lower=0.0, upper=0.25):
    if not math.isfinite(target_value):
        raise ValueError('Finite target required')
    lo=policy_value(ebit,replace(assumptions,growth=lower))['policy_value']-target_value
    hi=policy_value(ebit,replace(assumptions,growth=upper))['policy_value']-target_value
    if lo*hi>0:
        return {'status':'unreachable_in_declared_bracket','lower':lower,'upper':upper,
                'lower_value':lo+target_value,'upper_value':hi+target_value,'target_value':target_value}
    if lo==0: root=lower
    elif hi==0: root=upper
    else:
        left,right=lower,upper
        for _ in range(100):
            root=(left+right)/2
            mid=policy_value(ebit,replace(assumptions,growth=root))['policy_value']-target_value
            if lo*mid<=0:right=root
            else:left=root;lo=mid
    result=policy_value(ebit,replace(assumptions,growth=root))
    return {'status':'solved','growth':root,'target_value':target_value,
            'reconstructed_value':result['policy_value'],'residual':result['policy_value']-target_value,
            'bracket':[lower,upper]}
