def calculate_total_score(scores):
    """
    Calculate the total proposed score from criterion scores.
    """

    total = sum(scores)

    return {
        "criterion_scores": scores,
        "total_score": round(total, 2)
    }


if __name__ == "__main__":
    demo_scores = [
        6, 6, 7, 6,       # Q1
        8, 10, 5, 5, 7,   # Q2
        7, 7, 7, 6, 6, 7  # Q3
    ]

    result = calculate_total_score(demo_scores)

    print(result)