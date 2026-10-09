# Skill Registry

| Component / Skill | Responsibility | Trigger / Input |
|---|---|---|
| `rag-pipeline` | Ingests PDF/TXT/MD references and retrieves top 3–5 chunks with source attribution | Pre-indexing / Prior to rubric evaluation |
| `submission-analysis` | Understands and classifies student responses and identifies calculation needs | Every student submission |
| `rubric-evaluation` | Evaluates responses against rubric criteria supported by retrieved reference chunks | Every evaluable submission |
| `numerical-verification` | Independently verifies calculations using deterministic Python scripts | Numerical content detected (e.g. EOQ) |
| `quality-control` | Validates proposed scores, rubric alignment, calculation results, and citations | After evaluation and verification |
| `feedback-generation` | Generates personalized, constructive feedback with actionable steps | After QC validation |

## Workflow & Routing Architecture

```text
Approved Reference Materials (PDF, TXT, MD)
       │
       ▼
 [rag_pipeline: Ingestion] ──► Overlapping Chunks ──► Sentence-Transformers ──► Persistent ChromaDB
                                                                                     │
Student Submissions                                                                  │
       │                                                                             │
       ▼                                                                             │
 [submission-analysis] ──────────────────────────────────────────┐                   │
       │                                                         │                   │
       ▼                                                         ▼                   │
 [RAG Retrieval] ◄───────────────────────────────────────────────────────────────────┘
       │  (Top 3–5 chunks per criterion with filename and page attribution)
       ▼
 [rubric-evaluation] (Rubric authoritative; reference context as supporting evidence)
       │
       ├──► Numerical Work Detected ──► [numerical-verification] (Deterministic scripts)
       │                                        │
       ▼                                        ▼
 [quality-control] ◄────────────────────────────┘
       │
       ├──► Passed QC ──► [feedback-generation] ──► [Summary & Faculty Queue]
       │
       └──► Ambiguity / Low Confidence ──► Immediate Escalation to Faculty
```

## Batch Processing Rules

1. Discover all files in `Data/submissions/`.
2. Ensure reference materials in `Data/reference_materials/` are ingested in local ChromaDB.
3. Process each submission independently.
4. Route each submission through submission analysis, RAG retrieval, rubric evaluation, numerical verification (if applicable), QC, and feedback generation.
5. Continue processing remaining submissions if one triggers escalation.
6. Save outputs using the student identifier across dedicated directories.
7. Create a consolidated batch summary and faculty escalation review queue.

## Output Mapping

| Stage / Component | Artifact / Output Folder |
|---|---|
| Reference Vector DB | `chroma_db/` |
| `submission-analysis` | `evaluation_findings/submission_analysis_{student_id}.md` |
| `rubric-evaluation` (with RAG citations) | `evaluation_findings/rubric_evaluation_{student_id}.md` |
| `numerical-verification` | `verification_findings/numerical_verification_{student_id}.md` |
| `quality-control` | `quality_findings/quality_control_{student_id}.md` |
| `feedback-generation` | `feedback/feedback_{student_id}.md` |
| Student Summary & Batch Summary | `Summary/summary_{student_id}.md` & `Summary/batch_evaluation_summary.md` |