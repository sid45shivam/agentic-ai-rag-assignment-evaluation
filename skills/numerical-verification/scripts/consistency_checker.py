def check_score_consistency(criterion_scores, maximum_scores):
    """
    Check whether every criterion score is within its allowed range.
    """

    issues = []

    if len(criterion_scores) != len(maximum_scores):
        return {
            "status": "FAIL",
            "issues": ["Number of scores does not match number of criteria."]
        }

    for i, (score, maximum) in enumerate(
        zip(criterion_scores, maximum_scores), start=1
    ):
        if score < 0:
            issues.append(
                f"Criterion {i}: score cannot be negative."
            )

        if score > maximum:
            issues.append(
                f"Criterion {i}: score {score} exceeds maximum {maximum}."
            )

    status = "PASS" if not issues else "FAIL"

    return {
        "status": status,
        "issues": issues
    }


if __name__ == "__main__":
    demo_scores = [6, 6, 7, 6]
    demo_maximums = [6, 6, 7, 6]

    print(
        check_score_consistency(
            demo_scores,
            demo_maximums
        )
    )