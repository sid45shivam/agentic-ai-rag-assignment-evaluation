\---

name: submission-analysis

description: Analyzes and classifies student assignment submissions. Use for every new assignment to identify questions, answer types, missing responses, numerical content, and ambiguity before evaluation.

metadata:

&#x20; author: Siddharth Shivam

&#x20; version: "1.0"

\---



\# Submission Analysis



\## Purpose



Understand the structure and content of a student submission before academic evaluation.



\## Inputs



\- Student submission

\- Assignment question or instructions

\- Subject, if available



\## Instructions



1\. Identify all questions or sections.

2\. Match submitted responses to the relevant questions.

3\. Identify unanswered or incomplete sections.

4\. Classify each response as:

&#x20;  - theoretical

&#x20;  - MCQ

&#x20;  - numerical

&#x20;  - case-based

&#x20;  - analytical

&#x20;  - other

5\. Flag calculations requiring independent verification.

6\. Flag ambiguous or unusual responses.

7\. Produce a structured analysis for downstream Skills.



\## Output



Return:



\- assignment identifier

\- questions detected

\- answered/unanswered status

\- answer type

\- numerical verification required

\- ambiguity flags

\- recommended next action



\## Guardrails



\- Do not evaluate academic quality.

\- Do not assign marks.

\- Do not invent missing answers.

\- Do not modify the assignment requirements.

