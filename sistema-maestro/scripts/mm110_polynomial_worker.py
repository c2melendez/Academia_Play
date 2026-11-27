"""Resource-bounded adapter for generic exact polynomial checks.

Internal component; does not publish activities or change approved F01.
"""
import json
import subprocess
import sys
from pathlib import Path

WORKER = Path(__file__).resolve()
if __name__ == "__main__":
    sys.path.insert(0, str(WORKER.parent))

from mm110_f01_oracle import Verdict, MAX_LENGTH, MAX_DEGREE
from mm110_f01_oracle_worker import TIMEOUT_SECONDS, MEMORY_BYTES, CPU_SECONDS

OPERATIONS = {"degree":2, "coefficient":3, "division":4, "factor_product":2}
VALID = {
    "degree": {("VERIFIED","EXACT_DEGREE"),("REJECTED","INCORRECT_DEGREE")},
    "coefficient": {("VERIFIED","EXACT_COEFFICIENT"),("REJECTED","INCORRECT_COEFFICIENT")},
    "division": {("VERIFIED","EXACT_DIVISION"),("REJECTED","REMAINDER_DEGREE"),("REJECTED","DIVISION_IDENTITY")},
    "factor_product": {("VERIFIED","EXACT_FACTOR_PRODUCT"),("REJECTED","TRIVIAL_FACTORIZATION"),("REJECTED","FACTOR_IDENTITY")},
}
COMMON = {("REJECTED","INVALID_FORMAT_OR_DOMAIN"),("INCONCLUSIVE","COMPUTATION_LIMIT"),
          ("INCONCLUSIVE","INTERNAL_FAILURE")}
MAX_PAYLOAD = 65536

def _invalid():
    return Verdict("REJECTED","INVALID_FORMAT_OR_DOMAIN")

def _budget():
    return Verdict("INCONCLUSIVE","COMPUTATION_LIMIT")

def _failure():
    return Verdict("INCONCLUSIVE","WORKER_FAILURE")

def _validate(operation,args):
    if not isinstance(operation,str) or operation not in OPERATIONS or len(args)!=OPERATIONS[operation]:
        return _invalid()
    if operation=="degree":
        expression, claimed = args
        if claimed is not None and (type(claimed) is not int or claimed<0):
            return _invalid()
        if claimed is not None and claimed>MAX_DEGREE:
            return _budget()
        expressions = [expression]
    elif operation=="coefficient":
        expression, exponent, claimed = args
        if type(exponent) is not int or exponent<0:
            return _invalid()
        if exponent>MAX_DEGREE:
            return _budget()
        expressions = [expression,claimed]
    elif operation=="division":
        expressions = args
    else:
        expression,factors = args
        if not isinstance(factors,(list,tuple)) or not 2<=len(factors)<=MAX_DEGREE:
            return _invalid()
        expressions = [expression,*factors]
    if not all(isinstance(x,str) for x in expressions):
        return _invalid()
    if any(len(x)>MAX_LENGTH for x in expressions):
        return _budget()
    return None

def verify_isolated(operation,*args):
    rejected = _validate(operation,args)
    if rejected is not None:
        return rejected
    try:
        request = json.dumps([operation,*args],ensure_ascii=True)
        if len(request)>MAX_PAYLOAD:
            return _budget()
        result = subprocess.run(
            [sys.executable,"-I",str(WORKER)],
            input=request,text=True,capture_output=True,
            timeout=TIMEOUT_SECONDS,check=False,
        )
        if result.returncode!=0 or len(result.stdout)>256:
            return _failure()
        payload = json.loads(result.stdout)
        if (not isinstance(payload,list) or len(payload)!=2 or
                not all(isinstance(v,str) for v in payload) or
                tuple(payload) not in VALID[operation]|COMMON):
            return _failure()
        return Verdict(*payload)
    except subprocess.TimeoutExpired:
        return _budget()
    except Exception:
        return _failure()

def main():
    import resource
    resource.setrlimit(resource.RLIMIT_CPU,(CPU_SECONDS,CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_AS,(MEMORY_BYTES,MEMORY_BYTES))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    from mm110_polynomial_checks import verify_degree,verify_coefficient,verify_division,verify_factor_product
    dispatch = {"degree":verify_degree,"coefficient":verify_coefficient,
                "division":verify_division,"factor_product":verify_factor_product}
    raw = sys.stdin.read(MAX_PAYLOAD+1)
    if len(raw)>MAX_PAYLOAD:
        verdict = _budget()
    else:
        data = json.loads(raw)
        if not isinstance(data,list) or not data:
            verdict = _invalid()
        else:
            operation,*args = data
            rejected = _validate(operation,args)
            verdict = rejected if rejected is not None else dispatch[operation](*args)
    print(json.dumps([verdict.status,verdict.reason]))

if __name__=="__main__":
    main()
