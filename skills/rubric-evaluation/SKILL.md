---
name: rubric-evaluation
description: Evaluates student responses against an approved academic rubric and reference material retrieved via RAG. Use after submission analysis for criterion-level scoring and evidence-based evaluation.
metadata:
  author: Siddharth Shivam
  version: "1.1"
---

# Rubric Evaluation

## Purpose

Evaluate student responses against the approved assignment rubric, supported by relevant reference context retrieved from the local RAG pipeline.

## Inputs

- Student submission
- Assignment question
- Approved rubric
- Relevant academic references (retrieved via RAG pipeline with source filenames and page numbers)
- Submission analysis

## Instructions

1. Identify the relevant rubric criterion.
2. Query the RAG pipeline for top 3–5 relevant chunks from approved course notes, lecture PDFs, and reference materials.
3. Locate evidence in the student's response.
4. Compare student evidence with the rubric, consulting retrieved references strictly as supporting academic context.
5. Determine the appropriate performance level.
6. Propose marks within the permitted range.
7. Explain the proposed score using student evidence and record source citations (filename and page).
8. If relevant reference context is unavailable, explicitly flag the limitation and evaluate based on rubric criteria.
9. Flag ambiguous or valid alternative approaches for faculty review.

## Output

Return:

- question
- criterion
- student evidence
- retrieved reference context (source filename & page number)
- evaluation
- proposed marks
- maximum marks
- confidence
- unresolved issues

## Guardrails

- The approved rubric remains the primary scoring authority; retrieved context serves only as supporting evidence.
- Do not invent citations or claim a source supports something it does not.
- If relevant context is unavailable, explicitly flag the limitation.
- Keep deterministic numerical verification independent of the LLM.
- Do not modify marks allocation or rubric thresholds.
- Do not invent evidence or penalize valid alternative approaches that are logically sound.
- Do not release final marks autonomously; faculty retains final academic approval.
