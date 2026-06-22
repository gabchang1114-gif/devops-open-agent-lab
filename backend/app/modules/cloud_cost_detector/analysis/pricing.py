"""AWS public list-price constants for monthly cost estimation (USD).

Rates are approximate on-demand US prices; used when Cost Explorer lacks per-resource detail.
"""

EBS_GB_MONTH_USD: dict[str, float] = {
    "gp3": 0.08,
    "gp2": 0.10,
    "standard": 0.10,
    "st1": 0.045,
    "sc1": 0.025,
    "io1": 0.125,
    "io2": 0.125,
}

UNASSOCIATED_EIP_MONTH_USD = 3.65
ALB_BASE_MONTH_USD = 16.20
NLB_BASE_MONTH_USD = 16.20

DEFAULT_EBS_GB_MONTH_USD = 0.10
