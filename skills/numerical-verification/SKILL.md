---
name: numerical-verification
description: Independently verifies numerical and deterministic calculations in student assignments using approved formulas and executable scripts. Use when numerical work is detected.
metadata:
  author: Siddharth Shivam
  version: "1.0"
---

# Numerical Verification

## Purpose

Independently verify supported calculations in student assignments.

## Inputs

- Assignment question
- Student calculation
- Relevant data
- Approved formula or method

## Instructions

1. Identify the calculation required.
2. Extract the student's inputs and result.
3. Select the appropriate script from `scripts/`.
4. Execute the script using the required inputs.
5. Compare the verified result with the student's result.
6. Record discrepancies.
7. Report the potential impact on evaluation.

## Output

Return:

- question
- student result
- verified result
- status
- discrepancy
- severity
- evaluation impact

## Guardrails

- Use deterministic scripts where supported.
- Do not invent missing inputs.
- Do not silently correct the student's answer.
- Do not change the rubric.
- Escalate unresolved calculation issues.