"""Bounded subprocess adapter for the F01 exact oracle (local pilot).

No shell, external input files, network calls or arbitrary code evaluation.
OS resource limits are Linux/Unix only; unsupported environments fail closed.
"""
import json
import subprocess
import sys
from pathlib import Path
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from mm110_f01_oracle import Verdict, MAX_LENGTH

TIMEOUT_SECONDS = 3
MEMORY_BYTES = 128 * 1024 * 1024
CPU_SECONDS = 1
WORKER = Path(__file__).resolve()

def compare_isolated(left, right):
    if not isinstance(left, str) or not isinstance(right, str):
        return Verdict("REJECTED", "INVALID_FORMAT_OR_DOMAIN")
    if max(len(left), len(right)) > MAX_LENGTH:
        return Verdict("INCONCLUSIVE", "COMPUTATION_LIMIT")
    try:
        result = subprocess.run(
            [sys.executable, "-I", str(WORKER)],
            input=json.dumps([left, right]), text=True,
            capture_output=True, timeout=TIMEOUT_SECONDS, check=False,
        )
        if result.returncode != 0:
            return Verdict("INCONCLUSIVE", "WORKER_FAILURE")
        payload = json.loads(result.stdout)
        if (not isinstance(payload, list) or len(payload) != 2
                or tuple(payload) not in {
                    ("VERIFIED","EXACT_IDENTITY"),
                    ("REJECTED","UNEQUAL_COEFFICIENTS"),
                    ("REJECTED","INVALID_FORMAT_OR_DOMAIN"),
                    ("INCONCLUSIVE","COMPUTATION_LIMIT"),
                    ("INCONCLUSIVE","INTERNAL_FAILURE")}):
            return Verdict("INCONCLUSIVE", "WORKER_FAILURE")
        return Verdict(*payload)
    except subprocess.TimeoutExpired:
        return Verdict("INCONCLUSIVE", "COMPUTATION_LIMIT")
    except Exception:
        return Verdict("INCONCLUSIVE", "WORKER_FAILURE")

def main():
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    sys.path.insert(0, str(WORKER.parent))
    from mm110_f01_oracle import compare
    left, right = json.loads(sys.stdin.read(8192))
    verdict = compare(left, right)
    print(json.dumps([verdict.status, verdict.reason]))

if __name__ == "__main__":
    main()
