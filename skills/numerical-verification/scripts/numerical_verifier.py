import math


def verify_eoq(demand, ordering_cost, holding_cost, student_eoq):
    """
    Verify EOQ using:
        EOQ = sqrt(2DS/H)
    """

    expected_eoq = math.sqrt(
        (2 * demand * ordering_cost) / holding_cost
    )

    difference = abs(student_eoq - expected_eoq)

    # Allow a small rounding tolerance
    tolerance = 1.0

    status = "PASS" if difference <= tolerance else "FAIL"

    return {
        "formula": "sqrt(2DS/H)",
        "expected_eoq": round(expected_eoq, 2),
        "student_eoq": round(student_eoq, 2),
        "difference": round(difference, 2),
        "status": status
    }


if __name__ == "__main__":
    # Demo using Student B's answer
    result = verify_eoq(
        demand=10000,
        ordering_cost=500,
        holding_cost=20,
        student_eoq=500
    )

    print(result)