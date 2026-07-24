DECLARED = set()
CRITICAL = set()
HIT = set()


def declare(*ids, critical=True):
    DECLARED.update(ids)
    if critical:
        CRITICAL.update(ids)


def hit(branch_id):
    HIT.add(branch_id)


def reset():
    HIT.clear()


def snapshot():
    def pct(group):
        return 100.0 if not group else round(100.0 * len(group & HIT) / len(group), 2)
    return {
        "coverage_type": "DECLARED_DECISION_PROBE_COVERAGE",
        "general_python_branch_coverage": "NOT_MEASURED",
        "declared_branches": sorted(DECLARED),
        "critical_branches": sorted(CRITICAL),
        "executed_branches": sorted(HIT),
        "missed_branches": sorted(DECLARED - HIT),
        "declared_decision_probe_coverage_percent": pct(DECLARED),
        "critical_gate_decision_coverage_percent": pct(CRITICAL),
        "correction_specific_branch_coverage_percent": pct(DECLARED),
    }
