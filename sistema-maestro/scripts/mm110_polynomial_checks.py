"""Generic exact polynomial checks. Internal only; no curricular approval implied.

Reuse the bounded F01 grammar. Do not expose these functions to untrusted
student traffic before adding a resource-limited worker protocol.
"""
from fractions import Fraction
from mm110_f01_oracle import (
    normalize, add, mul, Verdict, Invalid, Budget, MAX_DEGREE, MAX_BITS,
)

def _guard(operation):
    try:
        return operation()
    except Invalid:
        return Verdict("REJECTED", "INVALID_FORMAT_OR_DOMAIN")
    except Budget:
        return Verdict("INCONCLUSIVE", "COMPUTATION_LIMIT")
    except Exception:
        return Verdict("INCONCLUSIVE", "INTERNAL_FAILURE")

def verify_degree(expression, claimed):
    """None represents the undefined degree of the zero polynomial."""
    def run():
        if claimed is not None and (type(claimed) is not int or claimed < 0):
            raise Invalid("degree must be a nonnegative integer or None")
        p = normalize(expression)
        actual = max(p) if p else None
        return (Verdict("VERIFIED", "EXACT_DEGREE") if claimed == actual
                else Verdict("REJECTED", "INCORRECT_DEGREE"))
    return _guard(run)

def verify_coefficient(expression, exponent, claimed):
    """Accept an exact constant expression, never a float or variable."""
    def run():
        if type(exponent) is not int or exponent < 0:
            raise Invalid("invalid exponent")
        if exponent > MAX_DEGREE:
            raise Budget("degree limit")
        p = normalize(expression)
        q = normalize(claimed)
        if any(k != 0 for k in q):
            raise Invalid("coefficient must be constant")
        return (Verdict("VERIFIED", "EXACT_COEFFICIENT")
                if p.get(exponent, Fraction(0)) == q.get(0, Fraction(0))
                else Verdict("REJECTED", "INCORRECT_COEFFICIENT"))
    return _guard(run)

def verify_division(dividend, divisor, quotient, remainder):
    """Check Euclidean division in Q[x], not equality of rational functions."""
    def run():
        d, v, q, r = map(normalize, (dividend, divisor, quotient, remainder))
        if not v:
            raise Invalid("zero divisor")
        if r and max(r) >= max(v):
            return Verdict("REJECTED", "REMAINDER_DEGREE")
        if add(mul(v, q), r) != d:
            return Verdict("REJECTED", "DIVISION_IDENTITY")
        return Verdict("VERIFIED", "EXACT_DIVISION")
    return _guard(run)

def verify_factor_product(expression, factors):
    """Verify a nontrivial product supplied as separate factor expressions.

    This checks equivalence and at least two nonconstant factors, NOT
    irreducibility, completeness, or the syntactic form of a single answer.
    """
    def run():
        if not isinstance(factors, (tuple, list)) or not 2 <= len(factors) <= MAX_DEGREE:
            raise Invalid("bounded factor sequence required")
        target = normalize(expression)
        if not target:
            raise Invalid("zero polynomial")
        polys = [normalize(f) for f in factors]
        if any(not p for p in polys):
            raise Invalid("zero factor")
        if sum(max(p) > 0 for p in polys) < 2:
            return Verdict("REJECTED", "TRIVIAL_FACTORIZATION")
        product = {0: Fraction(1)}
        for p in polys:
            product = mul(product, p)
        return (Verdict("VERIFIED", "EXACT_FACTOR_PRODUCT") if product == target
                else Verdict("REJECTED", "FACTOR_IDENTITY"))
    return _guard(run)
