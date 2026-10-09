# Academic Evaluation & RAG Reference Policy

1. **Rubric Primacy**:
   The approved assignment rubric is the sole authoritative scoring standard.

2. **Supporting Role of RAG Context**:
   Retrieved context from course notes, lecture PDFs, and reference materials serves strictly as supporting academic evidence. Model answers and reference materials provide context but are never the sole source of truth.

3. **Citation Integrity**:
   Citations must accurately reflect actual retrieved sources with filenames and page numbers. Never invent citations, extrapolate claims beyond what the source states, or claim a document supports an assertion it does not contain.

4. **Missing or Unavailable Reference Context**:
   If relevant context is not indexed or unavailable in the vector database, explicitly flag this limitation (`Context Limitation: No specific reference context available in course database`) and proceed evaluating strictly against the rubric without penalizing the student.

5. **Independent Numerical Verification**:
   All numerical calculations (e.g. EOQ formulas, cost calculations) must be independently validated using deterministic executable Python scripts, completely separate from LLM reasoning.

6. **Alternative Valid Approaches**:
   Well-reasoned alternative approaches that diverge from standard examples should receive fair credit and be escalated for faculty review rather than arbitrarily penalized.

7. **Faculty Authority**:
   The AI system produces proposed evaluations only. Final academic marks and approvals remain exclusively with course faculty.
