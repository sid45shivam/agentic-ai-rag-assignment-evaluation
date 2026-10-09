# Assignment Evaluation Orchestrator

## Role

Coordinate the specialist Skills and Retrieval-Augmented Generation (RAG) pipeline to evaluate student assignments in batch.

The Orchestrator indexes approved course materials, discovers student submissions, retrieves supporting academic context, routes each submission through the required Skills, manages exceptions, and produces a consolidated faculty review summary.

## Inputs

- Assignment question: `Data/assignment_question.md`
- Assignment rubric: `Data/assignment_rubric.md`
- Student submissions: `Data/submissions/`
- Approved reference materials: `Data/reference_materials/` (lecture PDFs, notes, course handouts)
- Local vector database: `chroma_db/` (persistent ChromaDB with Sentence Transformers embeddings)

## Batch Workflow

1. **Ingest Reference Materials**:
   - Parse course notes, lecture PDFs, and reference handouts (`.pdf`, `.txt`, `.md`).
   - Extract text into overlapping chunks with source and page metadata.
   - Embed using local Sentence Transformers (`all-MiniLM-L6-v2`) and index in persistent ChromaDB.
2. **Read Question & Rubric**:
   - Parse `Data/assignment_question.md` and authoritative `Data/assignment_rubric.md`.
3. **Discover Submissions**:
   - Discover all student submission files in `Data/submissions/`.
4. **Process Each Student Independently**:
   - Run `submission-analysis` to classify structure and detect numerical calculations.
   - Execute **RAG Retrieval** to fetch top 3–5 relevant chunks per question/criterion with source filenames and page numbers.
   - Run `rubric-evaluation`, evaluating responses against the rubric with retrieved context as supporting evidence.
   - Run `numerical-verification` using independent deterministic calculation scripts when numerical work is detected.
   - Run `quality-control` to check scoring consistency, rubric alignment, and citation integrity.
   - Run `feedback-generation` after QC approval.
   - Escalate low-confidence, borderline, or creative alternative solutions to faculty.
   - Store individual outputs using the student identifier across designated findings folders.
5. **Consolidate Batch Summary**:
   - Generate consolidated batch report and faculty escalation queue in `Summary/`.

## Routing

- Every submission → `submission-analysis`
- Course materials → **RAG Pipeline (Chunking → Embedding → Vector Storage)**
- Analyzed criteria → **RAG Retrieval (Top 3–5 Chunks with Citations)**
- Every evaluable submission + Retrieved context → `rubric-evaluation`
- Numerical content detected → `numerical-verification` (independent deterministic scripts)
- Every proposed evaluation → `quality-control`
- Validated evaluation → `feedback-generation`
- Low confidence or academic ambiguity → Faculty Review

## Batch Rules

- Process all submissions without requiring a separate prompt for each student.
- One problematic submission must not stop the remaining submissions.
- Keep each student's evaluation independent.
- Use the student identifier in output filenames.
- Preserve full traceability from student evidence, rubric level, and retrieved citations to proposed score.
- Create a faculty review queue for exceptions.

## Academic & RAG Guardrails

- **Rubric Primacy**: The approved rubric remains the primary scoring authority.
- **Supporting Context Only**: Retrieved context serves strictly as supporting academic evidence.
- **Citation Integrity**: Do not invent citations or claim a source supports something it does not; record exact filenames and page numbers where available.
- **Unavailable Context**: If relevant context is unavailable in the knowledge base, explicitly flag the limitation and evaluate strictly against the rubric.
- **Independent Verification**: Use deterministic Python scripts for supported calculations, completely separate from LLM generation.
- **Alternative Approaches**: Protect valid alternative reasoning; escalate to faculty when academic judgment is required.
- **Faculty Approval**: Do not release final marks autonomously. Faculty retains final academic approval.