"""F01 exact polynomial equivalence over Q[x], evaluated as identities on R.
Bounded closed grammar. No eval, floating point or sampled equivalence.
"""
from fractions import Fraction
from dataclasses import dataclass
import re

MAX_LENGTH = 256
MAX_TOKENS = 128
MAX_DEGREE = 16
MAX_BITS = 256
MAX_DEPTH = 24

class Invalid(ValueError):
    pass

class Budget(RuntimeError):
    pass

def clean(p):
    p = {k: v for k, v in p.items() if v}
    if any(k > MAX_DEGREE or max(v.numerator.bit_length(), v.denominator.bit_length()) > MAX_BITS for k, v in p.items()):
        raise Budget("polynomial limit")
    return p

def add(a, b, sign=1):
    r = dict(a)
    for k, v in b.items():
        r[k] = r.get(k, Fraction(0)) + sign*v
    return clean(r)

def mul(a, b):
    r = {}
    for i, v in a.items():
        for j, w in b.items():
            if i+j > MAX_DEGREE:
                raise Budget("degree limit")
            r[i+j] = r.get(i+j, Fraction(0)) + v*w
    return clean(r)

def constant(a):
    if any(k != 0 for k in a):
        raise Invalid("constant required")
    return a.get(0, Fraction(0))

class Parser:
    def __init__(self, text):
        if not isinstance(text, str):
            raise Invalid("text required")
        if len(text) > MAX_LENGTH:
            raise Budget("length limit")
        text = text.replace("−", "-").replace("×", "*").replace("²", "^2").replace("³", "^3")
        self.tokens = re.findall(r"[0-9]+|x|[()+*/^\-]|[^\s]", text)
        if len(self.tokens) > MAX_TOKENS:
            raise Budget("token limit")
        self.i = 0

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def take(self):
        t = self.peek()
        if t is None:
            raise Invalid("unexpected end")
        self.i += 1
        return t

    def expr(self, depth=0):
        if depth > MAX_DEPTH:
            raise Budget("nesting limit")
        a = self.term(depth)
        while self.peek() in ("+", "-"):
            op = self.take()
            a = add(a, self.term(depth), 1 if op == "+" else -1)
        return a

    def term(self, depth):
        a = self.unary(depth)
        while True:
            t = self.peek()
            if t in ("*", "/"):
                self.take()
                if t == "/":
                    start = self.i
                    b = self.unary(depth)
                    if "x" in self.tokens[start:self.i]:
                        raise Invalid("variable denominator")
                    d = constant(b)
                    if d == 0:
                        raise Invalid("zero denominator")
                    a = clean({k: v/d for k,v in a.items()})
                else:
                    a = mul(a, self.unary(depth))
            elif t in ("x", "("):
                a = mul(a, self.unary(depth))
            else:
                return a

    def unary(self, depth):
        if depth > MAX_DEPTH:
            raise Budget("nesting limit")
        if self.peek() in ("+", "-"):
            op = self.take()
            a = self.unary(depth+1)
            return a if op == "+" else {k: -v for k,v in a.items()}
        a = self.atom(depth)
        if self.peek() == "^":
            self.take()
            e = self.take()
            if not re.fullmatch(r"[0-9]+", e):
                raise Invalid("nonnegative integer exponent required")
            n = int(e)
            if n > MAX_DEGREE:
                raise Budget("exponent limit")
            r = {0: Fraction(1)}
            for _ in range(n):
                r = mul(r, a)
            return r
        return a

    def atom(self, depth):
        t = self.take()
        if t == "x":
            return {1: Fraction(1)}
        if re.fullmatch(r"[0-9]+", t):
            return clean({0: Fraction(int(t))})
        if t == "(":
            a = self.expr(depth+1)
            if self.take() != ")":
                raise Invalid("missing closing parenthesis")
            return a
        raise Invalid("unsupported token")

def normalize(text):
    parser = Parser(text)
    p = parser.expr()
    if parser.peek() is not None:
        raise Invalid("unexpected token")
    return p

@dataclass(frozen=True)
class Verdict:
    status: str
    reason: str

def compare(left, right):
    try:
        a, b = normalize(left), normalize(right)
        return Verdict("VERIFIED", "EXACT_IDENTITY") if a == b else Verdict("REJECTED", "UNEQUAL_COEFFICIENTS")
    except Invalid:
        return Verdict("REJECTED", "INVALID_FORMAT_OR_DOMAIN")
    except Budget:
        return Verdict("INCONCLUSIVE", "COMPUTATION_LIMIT")
    except Exception:
        return Verdict("INCONCLUSIVE", "INTERNAL_FAILURE")
