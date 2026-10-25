"""Transparent marketing analytics. Money is integer pence until presentation."""
import math


def segment(recency, frequency, monetary, high_value):
    if recency <= 30 and frequency >= 3:
        return 'Champions'
    if recency > 90 and monetary >= high_value:
        return 'At risk · high value'
    if recency <= 90 and frequency >= 2:
        return 'Loyal shoppers'
    if recency <= 30 and frequency == 1:
        return 'New shoppers'
    return 'Reactivation pool'


def campaign(audience, baseline, lift, aov, margin, discount, cost):
    """Equal-sized target population; discount paid on ALL treatment purchases.

    lift is absolute percentage-point change expressed as a fraction.
    Contribution delta vs no campaign includes baseline discount cannibalization.
    """
    vals = [audience, baseline, lift, aov, margin, discount, cost]
    if not all(isinstance(v, (int, float)) and math.isfinite(v) for v in vals):
        raise ValueError('Inputs must be finite numbers')
    if not (audience >= 0 and aov > 0 and cost >= 0 and 0 <= baseline <= 1
            and 0 <= lift <= 1-baseline and 0 <= discount < 1 and 0 <= margin <= 1):
        raise ValueError('Inputs outside supported bounds')
    conversions = audience * (baseline + lift)
    incremental = audience * lift
    revenue = incremental * aov
    contribution = audience * aov * (lift * margin - (baseline + lift) * discount) - cost
    denominator = audience * aov * (margin - discount)
    break_even = (cost + audience * aov * baseline * discount) / denominator if denominator > 0 else None
    p1, p2 = baseline, baseline + lift
    pooled = (p1+p2)/2
    sample = math.ceil(((1.959964*math.sqrt(2*pooled*(1-pooled))
                         + 0.841621*math.sqrt(p1*(1-p1)+p2*(1-p2)))**2)/(lift**2)) if lift > 0 else None
    return dict(conversions=conversions, incremental_orders=incremental,
                incremental_revenue=revenue, contribution=contribution,
                break_even_lift=break_even, sample_per_arm=sample,
                roi=contribution/cost if cost else None,
                feasible=bool(sample is not None and 2*sample <= audience))
