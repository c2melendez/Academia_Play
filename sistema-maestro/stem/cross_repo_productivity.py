"""STEM-08 extension: replay frozen cross-repository observations, not certification."""
import math
import re
from datetime import datetime

SHA = re.compile(r"[0-9a-f]{40}")
PHASES = ("install", "typecheck", "test", "build")
PHUMA = "c2melendez/desafio-gramatical"
PRODUCTS = ("lite", "plus")
COMMANDS = (["bun", "run", "test"],
            ["node", "--import", "./scripts/ts-resolve.mjs", "scripts/test-m0-critical-mutations.mjs"])
STAGES = (("regresion_suite_existente", "regresion_y_funcional"),
          ("mutaciones_m0_integracion_y_progreso", "mutacion_critica"))

def require(condition, message):
    if not condition:
        raise ValueError(message)

def seconds(step):
    require(step["conclusion"] == "success", "step not executed successfully")
    a, b = (datetime.fromisoformat(step[k].replace("Z", "+00:00")) for k in ("started_at", "completed_at"))
    require(a.tzinfo is not None and b.tzinfo is not None and b >= a, "invalid interval")
    return (b - a).total_seconds()

def number(x):
    require(type(x) in (int, float) and math.isfinite(x) and x >= 0, "invalid duration")
    return x

def identity(row, runs, jobs):
    for key, seen in (("run_id", runs), ("job_id", jobs)):
        n = row[key]
        require(type(n) is int and n > 0 and n not in seen, "duplicate or invalid run/job")
        seen.add(n)
    require(row["conclusion"] == "success", "failed observation")

def phuma(row):
    report = row["report"]
    phase = row["phase"]
    require(row["repository"] == PHUMA and phase in ("before", "after"), "wrong PHUMA scope")
    require(row["event"] == ("pull_request" if phase == "before" else "push"), "wrong event")
    require(type(row["run_attempt"]) is int and row["run_attempt"] > 0, "invalid attempt")
    require(all(SHA.fullmatch(x) for x in (row["head_sha"], report["checkout_sha"])), "invalid checkout identity")
    if phase == "after":
        require(row["head_sha"] == report["checkout_sha"], "push checkout mismatch")
    require(report["schema_version"] == 1 and report["scope"] == "M0-nested-commands", "report scope")
    require(len(report["groups"]) == 2, "missing command groups")
    results = []
    for k, (group, command, names) in enumerate(zip(report["groups"], COMMANDS, STAGES)):
        require(group["command"] == command and group["reuse_authorized"] is False, "unexpected command or reuse")
        calls = group["calls"]
        require([c["stage"] for c in calls] == list(names), "stage order or coverage")
        expected_shared = phase == "after" and k == 0
        total, count = 0, 0
        for i, call in enumerate(calls):
            require(call["status"] == "PASS" and type(call["exit_code"]) is int and call["exit_code"] == 0, "non-success call")
            duration = number(call["observed_seconds"])
            if expected_shared and i == 1:
                require(call["execution_complete"] is False and duration == 0
                        and call["shared_execution_from"] == names[0] and call["stdout_tail_sha256"] is None,
                        "shared obligation is not an execution")
            else:
                require(call["execution_complete"] is True and not call.get("shared_execution_from")
                        and re.fullmatch(r"[0-9a-f]{64}", call["stdout_tail_sha256"] or ""), "missing executed origin")
                total += duration
                count += 1
        require(group["decision"] == ("CONSOLIDATED" if expected_shared else "REVIEW"), "invalid group decision")
        require(group.get("actual_successful_executions", count) == count, "false execution count")
        results.append({"executions": count, "seconds": round(total, 3)})
    require(report.get("shared_obligations", 0) == (1 if phase == "after" else 0), "wrong shared count")
    match = re.fullmatch(r"Tests\s+(\d+) passed \((\d+)\)", row["test_summary"])
    require(match and int(match[1]) == int(match[2]) > 0, "missing passing suite count")
    rdg = row["rdg"]
    keys = ("selected", "registered_pass", "reusable", "revalidation", "review", "new_pass")
    require(all(type(rdg[k]) is int and rdg[k] >= 0 for k in keys), "invalid RDG counts")
    require(rdg["selected"] == rdg["reusable"] + rdg["revalidation"] + rdg["review"]
            and rdg["reusable"] <= rdg["registered_pass"] <= rdg["selected"]
            and rdg["new_pass"] == 0, "RDG accounting mismatch")
    return {"run_id": row["run_id"], "job_id": row["job_id"], "head_sha": row["head_sha"],
            "checkout_sha": report["checkout_sha"], "vitest": results[0], "mutations": results[1],
            "outer_tests_passed": int(match[1]), "rdg": rdg}

def frontend(row):
    product, profile = row["product"], row["profile"]
    require(product in PRODUCTS and profile in ("ci", "cumulative")
            and row["repository"] == "c2melendez/precision-lab-" + product, "invalid frontend scope")
    expected = ["Install dependencies", "Typecheck", "Unit and parity tests" if profile == "ci"
                else "Unit and parity regression", "Production build"]
    require([s["name"] for s in row["phases"]] == expected, "missing or unordered phases")
    durations = dict(zip(PHASES, (seconds(s) for s in row["phases"])))
    log = "\n".join(row["log_excerpt"])
    calls = re.findall(r"STEM frontend phase=(\w+) checkout=([0-9a-f]{40}) node=(\S+) npm=(\S+)", log)
    require(tuple(c[0] for c in calls) == PHASES and len({c[1:] for c in calls}) == 1, "mixed or missing executed checkout")
    locks = re.findall(r"Lockfile SHA256: ([0-9a-f]{64})  package-lock\.json", log)
    require(len(locks) == 4 and len(set(locks)) == 1, "mixed or missing lockfile")
    counts = re.findall(r"Tests\s+(\d+) passed(?: \| (\d+) expected fail)?(?: \| (\d+) todo)? \((\d+)\)", log)
    require(len(counts) == 1, "missing or duplicate suite summary")
    passed, xfail, todo, total = (int(n or 0) for n in counts[0])
    require(passed > 0 and passed + xfail + todo == total, "test accounting mismatch")
    images = re.findall(r"Image: (\S+)", log)
    versions = re.findall(r"Version: (2026\d+\.\S+)", log)
    require(len(images) == 1 and len(versions) == 2, "missing runner image")
    return {"run_id": row["run_id"], "job_id": row["job_id"], "checkout_sha": calls[0][1],
            "node": calls[0][2], "npm": calls[0][3], "lockfile": locks[0],
            "image": images[0], "runner_version": versions[0], "image_version": versions[1],
            "seconds": durations, "passed": passed, "expected_fail": xfail, "todo": todo,
            "total": total, "runner_seconds": sum(durations.values())}

def summarize_cross_repo(data):
    require(data["schema_version"] == 1 and data["scope"] == "observed successful CI; no reuse authorization", "invalid snapshot")
    runs, jobs, ph, products = set(), set(), {}, {p: {} for p in PRODUCTS}
    for row in data["phuma"]:
        identity(row, runs, jobs)
        require(row["phase"] not in ph, "duplicate PHUMA phase")
        ph[row["phase"]] = phuma(row)
    require(set(ph) == {"before", "after"}, "incomplete PHUMA pair")
    before, after = ph["before"], ph["after"]
    require(before["outer_tests_passed"] == after["outer_tests_passed"], "suite count changed")
    require(before["rdg"] == after["rdg"], "RDG scope changed")
    delta = round(before["vitest"]["seconds"] - after["vitest"]["seconds"], 3)
    for row in data["precision"]:
        identity(row, runs, jobs)
        item = frontend(row)
        pair = products[row["product"]]
        require(row["profile"] not in pair, "duplicate frontend profile")
        pair[row["profile"]] = item
    result = {}
    for product, pair in products.items():
        require(set(pair) == {"ci", "cumulative"}, "incomplete frontend pair")
        a, b = pair["ci"], pair["cumulative"]
        same = all(a[k] == b[k] for k in ("checkout_sha", "node", "npm", "lockfile", "passed", "expected_fail", "todo", "total"))
        require(same, "non-comparable frontend pair")
        result[product] = {"profiles": pair, "observed_repeated_phase_seconds": sum(min(a["seconds"][k], b["seconds"][k]) for k in PHASES),
                           "same_image_version": a["image_version"] == b["image_version"],
                           "reuse_authorized": False, "actual_time_saved_seconds": None}
    return {"status": "OBSERVED_ONLY", "phuma": {"runs": ph, "observed_vitest_reduction_seconds": delta,
            "observed_vitest_reduction_percent": round(100 * delta / before["vitest"]["seconds"], 2) if before["vitest"]["seconds"] else None,
            "removed_executions": before["vitest"]["executions"] - after["vitest"]["executions"],
            "causally_attributed_savings_seconds": None, "reuse_authorized": False,
            "new_certified_ids": None}, "precision": result, "certification_transfer": False,
            "limitations": "Historical snapshot; different runners and checkouts; no controlled causal estimate. Counts are software tests, not certifications; TODO/expected fail separate. Repeated-phase time is an opportunity, not actual savings."}
