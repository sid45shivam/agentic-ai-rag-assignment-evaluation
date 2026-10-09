\---

name: quality-control

description: Validates proposed assignment evaluations for rubric alignment, evidence, scoring consistency, numerical verification, ambiguity, and confidence. Use after evaluation and verification.

metadata:

&#x20; author: Siddharth Shivam

&#x20; version: "1.0"

\---



\# Quality Control



\## Purpose



Check whether a proposed evaluation is reliable and internally consistent.



\## Inputs



\- Student submission

\- Rubric evaluation

\- Numerical verification, if applicable

\- Approved references



\## Instructions



Check:



1\. Rubric alignment.

2\. Evidence supporting each score.

3\. Score limits.

4\. Total score calculation.

5\. Numerical verification results.

6\. Unsupported assumptions.

7\. Conflicting evidence.

8\. Alternative valid approaches.

9\. Ambiguity.

10\. Confidence.



\## Confidence



\- HIGH: Evaluation is clearly supported.

\- MEDIUM: Some uncertainty exists.

\- LOW: Significant academic judgement is required.



\## Output



Return:



\- QC status

\- issues identified

\- confidence

\- escalation required

\- escalation reason



\## Guardrails



\- Do not hide uncertainty.

\- Do not invent evidence.

\- Do not override faculty policy.

\- Escalate low-confidence academic judgement.

