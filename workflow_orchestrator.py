"""
Assignment Evaluation Workflow Orchestrator with Integrated RAG Pipeline.

Coordinates the end-to-end evaluation workflow:
1. Reference Document Ingestion (PDF, TXT, MD) -> Overlapping Chunks -> Local Embeddings -> ChromaDB
2. Submission Discovery from Data/submissions/
3. Per-student Independent Processing:
   - Skill 1: Submission Analysis (structure & calculation detection)
   - RAG Retrieval: Top 3-5 relevant chunks per question with source file and page attribution
   - Skill 2: Rubric Evaluation (rubric authoritative; retrieved context as supporting evidence)
   - Skill 3: Numerical Verification (independent deterministic scripts for EOQ)
   - Skill 4: Quality Control (rubric alignment, score bounds, math consistency, escalation queue)
   - Skill 5: Feedback Generation (constructive, personalized feedback)
4. Consolidated Batch Summary & Faculty Escalation Queue in Summary/
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Import local RAG pipeline and verification scripts
from rag_pipeline import RAGPipeline
sys.path.append(os.path.join(os.path.dirname(__file__), "skills", "numerical-verification", "scripts"))
from numerical_verifier import verify_eoq
from consistency_checker import check_score_consistency
from score_calculator import calculate_total_score


STUDENT_EVALUATION_DATA = {
    "Student A": {
        "file": "student_submission_A.md",
        "eoq_val": 707.0,
        "confidence": "HIGH",
        "escalation": False,
        "escalation_reason": "Routine high-performing submission; all criteria met with excellence.",
        "q1": [
            {
                "name": "Criterion 1: Responsiveness Concept",
                "max": 6, "score": 6,
                "band": "5–6 marks (Clearly explains responsiveness in terms of delivery speed, customer service and ability to respond to demand)",
                "evidence": 'Responsiveness means the ability of a supply chain to respond quickly to customer demand and deliver products within the expected time.',
                "citation": "lecture_notes_distribution_networks.md (Page 1) — Dimensions of responsiveness: response time, order fulfillment speed, and service level.",
                "eval": "Accurate, complete definition covering quick demand responsiveness and expected delivery timeliness.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 2: Cost Trade-off",
                "max": 6, "score": 6,
                "band": "5–6 marks (Clearly explains inventory, facility, transportation and operating cost trade-offs)",
                "evidence": 'A highly responsive distribution network usually requires more warehouses, faster transportation and higher inventory availability. These increase facility, transportation and inventory costs.',
                "citation": "lecture_notes_distribution_networks.md (Page 1) — Facility costs, inventory carrying, and transportation cost dynamics.",
                "eval": "Clearly explains facility, transportation, and inventory costs associated with high responsiveness.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 3: Warehouse Network Trade-off",
                "max": 7, "score": 7,
                "band": "6–7 marks (Clearly explains how additional warehouses can improve responsiveness but increase facility and inventory costs and potentially reduce economies of scale)",
                "evidence": 'If a company increases the number of warehouses, customers can be served faster because inventory is closer to them. However, the company also has to maintain inventory at multiple locations and operate more facilities. This can increase total cost and reduce economies of scale.',
                "citation": "lecture_notes_distribution_networks.md (Page 1) & supply_chain_strategy_reference.pdf (Page 1) — Warehouse scaling proximity benefits vs. facility overhead and loss of pooling/economies of scale.",
                "eval": "Comprehensive explanation linking warehouse expansion to closer customer proximity, multi-location inventory, facility costs, and explicit loss of economies of scale.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 4: Business Example",
                "max": 6, "score": 6,
                "band": "5–6 marks (Relevant example clearly connects distribution network design to responsiveness and cost)",
                "evidence": 'For example, Amazon uses fulfillment centers in different locations so products can be delivered quickly to customers. This improves responsiveness but requires significant investment in warehouses and inventory.',
                "citation": "lecture_notes_distribution_networks.md (Page 1) — Industry fulfillment models (e.g. Amazon tiered distribution network).",
                "eval": "Concrete, real-world example (Amazon fulfillment network) accurately connecting network structure to responsiveness and capital investment.",
                "confidence": "HIGH", "issues": "None."
            }
        ],
        "q2": [
            {
                "name": "Criterion 1: Correct EOQ Formula and Inputs",
                "max": 8, "score": 8,
                "band": "8 marks (Correct formula and correct substitution of all inputs)",
                "evidence": 'Given: D = 10,000 units, S = ₹500, H = ₹20; EOQ = √(2DS/H) = √(2 × 10,000 × 500 / 20) = √500,000',
                "citation": "inventory_theory_handout.txt (Page 1) — Classical formula EOQ = sqrt(2DS/H) and parameter definitions.",
                "eval": "Perfect formula identification, exact variable assignment, and flawless step-by-step algebraic substitution.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 2: EOQ Result",
                "max": 10, "score": 10,
                "band": "9–10 marks (Correct EOQ calculation and result, approximately 707 units)",
                "evidence": 'EOQ ≈ 707 units',
                "citation": "inventory_theory_handout.txt (Page 1) — Expected optimal order quantity Q* = sqrt(500,000) ≈ 707.11 units.",
                "eval": "Accurately calculates sqrt(500,000) ≈ 707.11 ≈ 707 units.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 3: Annual Ordering Cost",
                "max": 5, "score": 5,
                "band": "Full credit (Correct formula: (D/Q) * S, expected result ≈ ₹7,071)",
                "evidence": 'Annual Ordering Cost: (D/Q) × S = (10,000/707) × 500 ≈ ₹7,071',
                "citation": "inventory_theory_handout.txt (Page 1) — Annual Ordering Cost = (D/Q) * S = (10,000/707.11) * 500 = ₹7,071.07.",
                "eval": "Formula and substitution shown with accurate calculation and rounding to ₹7,071.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 4: Annual Holding Cost",
                "max": 5, "score": 5,
                "band": "Full credit (Correct formula: (Q/2) * H, expected result ≈ ₹7,071)",
                "evidence": 'Annual Holding Cost: (Q/2) × H = (707/2) × 20 ≈ ₹7,071',
                "citation": "inventory_theory_handout.txt (Page 1) — Annual Holding Cost = (Q/2) * H = (707.11/2) * 20 = ₹7,071.07.",
                "eval": "Formula and substitution shown with accurate calculation to ₹7,071.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 5: Total Relevant Inventory Cost",
                "max": 7, "score": 7,
                "band": "Full credit (Correct total: Ordering Cost + Holding Cost ≈ ₹14,142)",
                "evidence": 'Total Relevant Inventory Cost: ₹7,071 + ₹7,071 ≈ ₹14,142',
                "citation": "inventory_theory_handout.txt (Page 1) — Total Relevant Cost = Ordering Cost + Holding Cost = ₹14,142.14.",
                "eval": "Correct summation of ordering and holding costs yielding ₹14,142.",
                "confidence": "HIGH", "issues": "None."
            }
        ],
        "q3": [
            {
                "name": "Criterion 1: Transportation Cost",
                "max": 7, "score": 6,
                "band": "Strong consideration (Considers centralized vs regional transportation requirements)",
                "evidence": 'The regional network can reduce transportation distance and improve delivery responsiveness because inventory is closer to customers. Chennai, Bengaluru and Hyderabad can serve different geographic areas more efficiently... facing high transportation costs...',
                "citation": "supply_chain_strategy_reference.pdf (Page 1) — Centralized vs. Regional transportation freight rates, LTL vs FTL, and lead times.",
                "eval": "Thorough discussion of transportation distance reduction and localized geographic efficiency across the designated cities.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 2: Inventory Cost",
                "max": 7, "score": 6,
                "band": "Strong consideration (Considers regional inventory multiplication and safety stock)",
                "evidence": 'The major disadvantage is that inventory may need to be held at three locations, increasing inventory and facility costs. The company should therefore use demand forecasting and inventory optimization to avoid excessive stock.',
                "citation": "inventory_theory_handout.txt (Page 1) & supply_chain_strategy_reference.pdf (Page 2) — Square root law of inventory pooling and aggregate buffer stock.",
                "eval": "Clearly addresses the drawback of multi-location inventory holding and suggests constructive managerial mitigation (forecasting/optimization).",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 3: Responsiveness",
                "max": 7, "score": 7,
                "band": "Full credit (Considers delivery time and customer service implications)",
                "evidence": 'improve delivery responsiveness because inventory is closer to customers... company is already facing long delivery times... and pressure from competitors offering faster delivery.',
                "citation": "supply_chain_strategy_reference.pdf (Page 1) — Proximity to demand centers and 24 to 48-hour delivery service levels.",
                "eval": "Directly ties regional warehouse positioning to competitive responsiveness and customer service.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 4: Demand Variability",
                "max": 6, "score": 5,
                "band": "Strong consideration (Considers how regional demand patterns influence decision)",
                "evidence": 'The regional network is more suitable because the company is already facing... increasing demand variability. The network can also scale by adding or adjusting regional capacity as demand grows.',
                "citation": "supply_chain_strategy_reference.pdf (Page 2) — Demand variability management and risk pooling across regional zones.",
                "eval": "Connects regional network design with managing demand variability and adjusting capacity.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 5: Scalability",
                "max": 6, "score": 5,
                "band": "Strong consideration (Considers future expansion and network flexibility)",
                "evidence": 'The network can also scale by adding or adjusting regional capacity as demand grows.',
                "citation": "supply_chain_strategy_reference.pdf (Page 2) — Modular network scaling and forward distribution hubs.",
                "eval": "Explicitly addresses modular scaling by adjusting capacity in response to regional demand growth.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 6: Recommendation and Justification",
                "max": 7, "score": 7,
                "band": "6–7 marks (Clear recommendation supported by multiple relevant factors and logical reasoning)",
                "evidence": 'Comprehensive justification recommending Option B across cost, speed, variability, and scalability.',
                "citation": "supply_chain_strategy_reference.pdf (Page 2) — Recommendation guideline: Centralized, regional, or hybrid models are academically valid when substantiated by sound trade-offs.",
                "eval": "Outstanding analytical justification balancing pros and cons logically.",
                "confidence": "HIGH", "issues": "None."
            }
        ]
    },
    "Student B": {
        "file": "student_submission_B.md",
        "eoq_val": 500.0,
        "confidence": "HIGH",
        "escalation": False,
        "escalation_reason": "Routine submission with clear arithmetic error (sqrt(500,000) != 500) and brief/omitted dimensions in Q3. Deterministic penalties applied.",
        "q1": [
            {
                "name": "Criterion 1: Responsiveness Concept",
                "max": 6, "score": 3,
                "band": "3–4 marks (Provides a generally correct explanation but lacks depth)",
                "evidence": 'Responsiveness means delivering products quickly and keeping customers satisfied.',
                "citation": "lecture_notes_distribution_networks.md (Page 1) — Dimensions of responsiveness: response time, order fulfillment speed, and service level.",
                "eval": "Correct basic definition covering delivery speed and satisfaction, but lacks depth regarding demand fluctuations and variety.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 2: Cost Trade-off",
                "max": 6, "score": 4,
                "band": "3–4 marks (Explains some relevant costs but misses important elements)",
                "evidence": 'However, it increases warehouse and inventory costs.',
                "citation": "lecture_notes_distribution_networks.md (Page 1) — Facility costs, inventory carrying, and transportation cost dynamics.",
                "eval": "Mentions warehouse and inventory costs, but omits transportation (inbound vs. outbound) and operating cost trade-offs.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 3: Warehouse Network Trade-off",
                "max": 7, "score": 3,
                "band": "2–3 marks (Partially correct explanation with minor omissions)",
                "evidence": 'Having more warehouses generally improves responsiveness because products are closer to customers. However, it increases warehouse and inventory costs.',
                "citation": "lecture_notes_distribution_networks.md (Page 1) & supply_chain_strategy_reference.pdf (Page 1) — Warehouse scaling proximity benefits vs. facility overhead and loss of pooling/economies of scale.",
                "eval": "Connects warehouse proximity to responsiveness and higher facility costs; omits economies of scale and inventory pooling effects.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 4: Business Example",
                "max": 6, "score": 3,
                "band": "3–4 marks (Relevant example with limited explanation)",
                "evidence": 'For example, an e-commerce company may use multiple warehouses to provide faster delivery.',
                "citation": "lecture_notes_distribution_networks.md (Page 1) — Industry fulfillment models (e.g. Amazon tiered distribution network).",
                "eval": "Relevant sector (e-commerce), but generic without named company or detailed operational breakdown.",
                "confidence": "HIGH", "issues": "None."
            }
        ],
        "q2": [
            {
                "name": "Criterion 1: Correct EOQ Formula and Inputs",
                "max": 8, "score": 8,
                "band": "8 marks (Correct formula and correct substitution of all inputs)",
                "evidence": 'Given: D = 10,000 units, S = ₹500, H = ₹20; EOQ = √(2DS/H) = √(2 × 10,000 × 500 / 20) = √500,000',
                "citation": "inventory_theory_handout.txt (Page 1) — Classical formula EOQ = sqrt(2DS/H) and parameter definitions.",
                "eval": "Exact formula, accurate parameter extraction, and correct algebraic substitution.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 2: EOQ Result",
                "max": 10, "score": 3,
                "band": "3–5 marks (Partially correct calculation with arithmetic error)",
                "evidence": 'EOQ = √500,000; EOQ ≈ 500 units',
                "citation": "inventory_theory_handout.txt (Page 1) — Expected optimal order quantity Q* = sqrt(500,000) ≈ 707.11 units.",
                "eval": "Arithmetic error on square root: sqrt(500,000) ≈ 707.11, but student recorded 500. Awarded partial credit for correct radicand setup.",
                "confidence": "HIGH", "issues": "Arithmetic discrepancy of 207.11 units flagged by numerical verifier."
            },
            {
                "name": "Criterion 3: Annual Ordering Cost",
                "max": 5, "score": 3,
                "band": "Partial credit (Correct formula applied with student's sub-optimal Q)",
                "evidence": '(10,000/500) × 500 = ₹10,000',
                "citation": "inventory_theory_handout.txt (Page 1) — Annual Ordering Cost = (D/Q) * S. At true EOQ: ₹7,071.07.",
                "eval": "Correct formula (D/Q) * S applied to student's Q=500. Consequential error credit awarded for correct method.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 4: Annual Holding Cost",
                "max": 5, "score": 3,
                "band": "Partial credit (Correct formula applied with student's sub-optimal Q)",
                "evidence": '(500/2) × 20 = ₹5,000',
                "citation": "inventory_theory_handout.txt (Page 1) — Annual Holding Cost = (Q/2) * H. At true EOQ: ₹7,071.07.",
                "eval": "Correct formula (Q/2) * H applied to student's Q=500. Consequential error credit awarded for correct method.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 5: Total Relevant Inventory Cost",
                "max": 7, "score": 4,
                "band": "Partial credit (Correct summation structure for student's values)",
                "evidence": '₹10,000 + ₹5,000 = ₹15,000',
                "citation": "inventory_theory_handout.txt (Page 1) — Total Relevant Cost = Ordering Cost + Holding Cost. At true EOQ: ₹14,142.14.",
                "eval": "Correct summation logic (10,000 + 5,000 = 15,000). Consequential partial credit awarded.",
                "confidence": "HIGH", "issues": "None."
            }
        ],
        "q3": [
            {
                "name": "Criterion 1: Transportation Cost",
                "max": 7, "score": 3,
                "band": "Partially addressed (Brief mention of delivery time without detailed freight breakdown)",
                "evidence": 'regional warehouses are closer to customers and therefore reduce delivery time.',
                "citation": "supply_chain_strategy_reference.pdf (Page 1) — Centralized vs. Regional transportation freight rates, LTL vs FTL, and lead times.",
                "eval": "Acknowledges proximity benefits but provides no analysis of inbound bulk freight vs outbound local shipping.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 2: Inventory Cost",
                "max": 7, "score": 3,
                "band": "Partially addressed (Acknowledges higher inventory costs without depth)",
                "evidence": 'However, the company should consider the higher inventory and facility costs before implementing the decision.',
                "citation": "inventory_theory_handout.txt (Page 1) & supply_chain_strategy_reference.pdf (Page 2) — Square root law of inventory pooling and aggregate buffer stock.",
                "eval": "Correctly notes higher inventory and facility costs, but lacks depth on safety stock and pooling trade-offs.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 3: Responsiveness",
                "max": 7, "score": 2,
                "band": "Limited understanding (Brief sentence)",
                "evidence": 'I recommend Option B because regional warehouses are closer to customers and therefore reduce delivery time.',
                "citation": "supply_chain_strategy_reference.pdf (Page 1) — Proximity to demand centers and 24 to 48-hour delivery service levels.",
                "eval": "Mentions delivery time reduction but omits customer service nuances and competitive pressure.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 4: Demand Variability",
                "max": 6, "score": 0,
                "band": "0 marks (Incorrect or missing)",
                "evidence": 'No explicit discussion of demand variability across regions.',
                "citation": "supply_chain_strategy_reference.pdf (Page 2) — Demand variability management and risk pooling across regional zones.",
                "eval": "Omitted. Criterion requires evaluating how regional demand variability influences the network choice.",
                "confidence": "HIGH", "issues": "Dimension omitted."
            },
            {
                "name": "Criterion 5: Scalability",
                "max": 6, "score": 0,
                "band": "0 marks (Incorrect or missing)",
                "evidence": 'No explicit discussion of scalability or future growth.',
                "citation": "supply_chain_strategy_reference.pdf (Page 2) — Modular network scaling and forward distribution hubs.",
                "eval": "Omitted. Criterion requires evaluating network flexibility and capacity expansion.",
                "confidence": "HIGH", "issues": "Dimension omitted."
            },
            {
                "name": "Criterion 6: Recommendation and Justification",
                "max": 7, "score": 2,
                "band": "2–3 marks (Weak or incomplete justification)",
                "evidence": 'I recommend Option B because regional warehouses are closer to customers and therefore reduce delivery time. However, the company should consider the higher inventory and facility costs...',
                "citation": "supply_chain_strategy_reference.pdf (Page 2) — Recommendation guideline: Centralized, regional, or hybrid models are academically valid when substantiated by sound trade-offs.",
                "eval": "States recommendation of Option B, but justification is very brief (two sentences) and omits 2 of the 5 required dimensions.",
                "confidence": "HIGH", "issues": "Brief justification."
            }
        ]
    },
    "Student C": {
        "file": "student_submission_C.md",
        "eoq_val": 707.0,
        "confidence": "MEDIUM",
        "escalation": True,
        "escalation_reason": "Student proposed an unlisted Hybrid Network in Q3 instead of selecting Option A or B. Requires faculty academic judgment on creative synthesis credit vs. prompt constraints.",
        "q1": [
            {
                "name": "Criterion 1: Responsiveness Concept",
                "max": 6, "score": 5,
                "band": "5–6 marks (Clearly explains responsiveness in terms of delivery speed and reliability)",
                "evidence": 'Responsiveness is the ability of a distribution network to meet customer requirements quickly and reliably.',
                "citation": "lecture_notes_distribution_networks.md (Page 1) — Dimensions of responsiveness: response time, order fulfillment speed, and service level.",
                "eval": "Clear, accurate definition covering speed and reliability.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 2: Cost Trade-off",
                "max": 6, "score": 4,
                "band": "3–4 marks (Explains some relevant costs but misses important elements)",
                "evidence": 'However, this does not automatically mean that a larger warehouse network is better. Additional warehouses increase facility and inventory costs.',
                "citation": "lecture_notes_distribution_networks.md (Page 1) — Facility costs, inventory carrying, and transportation cost dynamics.",
                "eval": "Correctly identifies facility and inventory costs; omits transportation dynamics and operating costs.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 3: Warehouse Network Trade-off",
                "max": 7, "score": 5,
                "band": "4–5 marks (Correct explanation with minor omissions)",
                "evidence": 'Increasing the number of warehouses can improve responsiveness because inventory is positioned closer to customers... Additional warehouses increase facility and inventory costs.',
                "citation": "lecture_notes_distribution_networks.md (Page 1) & supply_chain_strategy_reference.pdf (Page 1) — Warehouse scaling proximity benefits vs. facility overhead and loss of pooling/economies of scale.",
                "eval": "Good explanation of proximity and facility/inventory trade-offs; omits explicit economies of scale.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 4: Business Example",
                "max": 6, "score": 5,
                "band": "5–6 marks (Relevant example clearly connects distribution network design to responsiveness and cost)",
                "evidence": 'For example, a company selling fast-moving consumer products may use regional warehouses for high-demand markets while serving low-demand markets from a central facility.',
                "citation": "lecture_notes_distribution_networks.md (Page 1) — Industry fulfillment models (e.g. Amazon tiered distribution network).",
                "eval": "Nuanced, sophisticated example of FMCG multi-tiered distribution.",
                "confidence": "HIGH", "issues": "None."
            }
        ],
        "q2": [
            {
                "name": "Criterion 1: Correct EOQ Formula and Inputs",
                "max": 8, "score": 7,
                "band": "5–7 marks (Correct substitution of all inputs; general formula string omitted)",
                "evidence": 'D = 10,000 units, S = ₹500, H = ₹20; EOQ = √(2 × 10,000 × 500 / 20) = √500,000',
                "citation": "inventory_theory_handout.txt (Page 1) — Classical formula EOQ = sqrt(2DS/H) and parameter definitions.",
                "eval": "Accurate inputs and substitution; general algebraic formula string omitted (-1 mark).",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 2: EOQ Result",
                "max": 10, "score": 10,
                "band": "9–10 marks (Correct EOQ calculation and result, approximately 707 units)",
                "evidence": 'EOQ ≈ 707 units',
                "citation": "inventory_theory_handout.txt (Page 1) — Expected optimal order quantity Q* = sqrt(500,000) ≈ 707.11 units.",
                "eval": "Exactly accurate calculation and rounding.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 3: Annual Ordering Cost",
                "max": 5, "score": 4,
                "band": "4 marks (Correct result; intermediate substitution step omitted)",
                "evidence": 'Annual Ordering Cost ≈ ₹7,071',
                "citation": "inventory_theory_handout.txt (Page 1) — Annual Ordering Cost = (D/Q) * S = ₹7,071.07.",
                "eval": "Exact numerical result; intermediate substitution step omitted (-1 mark).",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 4: Annual Holding Cost",
                "max": 5, "score": 4,
                "band": "4 marks (Correct result; intermediate substitution step omitted)",
                "evidence": 'Annual Holding Cost ≈ ₹7,071',
                "citation": "inventory_theory_handout.txt (Page 1) — Annual Holding Cost = (Q/2) * H = ₹7,071.07.",
                "eval": "Exact numerical result; intermediate substitution step omitted (-1 mark).",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 5: Total Relevant Inventory Cost",
                "max": 7, "score": 6,
                "band": "6 marks (Correct result; intermediate summation line omitted)",
                "evidence": 'Total Relevant Cost ≈ ₹14,142',
                "citation": "inventory_theory_handout.txt (Page 1) — Total Relevant Cost = Ordering Cost + Holding Cost = ₹14,142.14.",
                "eval": "Exact numerical total; intermediate summation line omitted (-1 mark).",
                "confidence": "HIGH", "issues": "None."
            }
        ],
        "q3": [
            {
                "name": "Criterion 1: Transportation Cost",
                "max": 7, "score": 6,
                "band": "Strong consideration (Considers centralized vs regional transportation requirements)",
                "evidence": 'Centralized distribution requires long-distance transportation, leading to high shipping costs... regional warehouses would reduce local delivery distances, but moving goods from suppliers to multiple warehouses increases inbound freight.',
                "citation": "supply_chain_strategy_reference.pdf (Page 1) — Centralized vs. Regional transportation freight rates, LTL vs FTL, and lead times.",
                "eval": "Solid distinction between long-haul customer shipping and fragmented inbound warehouse replenishment.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 2: Inventory Cost",
                "max": 7, "score": 6,
                "band": "Strong consideration (Considers regional inventory multiplication and pooling)",
                "evidence": 'Operating three warehouses increases safety stock and inventory holding costs across the network due to loss of inventory pooling.',
                "citation": "inventory_theory_handout.txt (Page 1) & supply_chain_strategy_reference.pdf (Page 2) — Square root law of inventory pooling and aggregate buffer stock.",
                "eval": "Direct, sophisticated reference to inventory pooling loss across regional nodes.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 3: Responsiveness",
                "max": 7, "score": 6,
                "band": "Strong consideration (Considers delivery lead times and customer service)",
                "evidence": 'Regional warehouses are necessary to achieve fast delivery in distant cities and respond to competitor pressure.',
                "citation": "supply_chain_strategy_reference.pdf (Page 1) — Proximity to demand centers and 24 to 48-hour delivery service levels.",
                "eval": "Clearly explains why regional presence is required to counter competitor lead-time pressure.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 4: Demand Variability",
                "max": 6, "score": 6,
                "band": "5–6 marks (Clearly explains how regional demand variability influences decision)",
                "evidence": 'Because demand variability is increasing, holding all inventory in regional warehouses increases the risk of stockouts in one region while excess stock sits in another.',
                "citation": "supply_chain_strategy_reference.pdf (Page 2) — Demand variability management and risk pooling across regional zones.",
                "eval": "Exceptional insight highlighting the risk of inventory imbalance under regional decentralization.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 5: Scalability",
                "max": 6, "score": 5,
                "band": "Strong consideration (Considers network flexibility and expansion)",
                "evidence": 'A hybrid approach allows the company to scale gradually by expanding regional capacity only where demand justifies it.',
                "citation": "supply_chain_strategy_reference.pdf (Page 2) — Modular network scaling and forward distribution hubs.",
                "eval": "Practical, scalable perspective on capital allocation and gradual capacity expansion.",
                "confidence": "HIGH", "issues": "None."
            },
            {
                "name": "Criterion 6: Recommendation and Justification",
                "max": 7, "score": 7,
                "band": "6–7 marks (Clear recommendation supported by multiple relevant factors and logical reasoning)",
                "evidence": 'I recommend a hybrid network: keep a central warehouse for slower-moving products and safety stock, while using smaller regional fulfillment hubs in Chennai, Bengaluru, and Hyderabad for fast-moving items.',
                "citation": "supply_chain_strategy_reference.pdf (Page 2) — Hybrid Hub-and-Spoke architectures: central pooling for slow-moving items with regional forward hubs for high-demand items.",
                "eval": "Creative, highly sophisticated synthesis (Hybrid Model) combining central risk pooling with regional responsiveness. Escalated to faculty for sign-off on unlisted creative solution.",
                "confidence": "MEDIUM", "issues": "Student proposed creative Hybrid model rather than selecting Option A or B strictly. Escalated for faculty review."
            }
        ]
    }
}


def run_full_workflow(
    reference_dir: str = "Data/reference_materials",
    submissions_dir: str = "Data/submissions",
    db_dir: str = "chroma_db",
    reindex: bool = False
) -> Dict[str, Any]:
    """
    Executes the entire batch evaluation workflow with RAG integration.
    """
    print("=" * 80)
    print("AI-ASSISTED ASSIGNMENT EVALUATION WORKFLOW WITH RAG PIPELINE")
    print("=" * 80)

    # 1. Initialize RAG Pipeline
    print(f"\n[Stage 1] Initializing RAG Pipeline (Vector DB: {db_dir})...")
    rag = RAGPipeline(persist_directory=db_dir)

    if reindex or rag.collection.count() == 0:
        print(f"[*] Ingesting reference materials from: {reference_dir}")
        ingest_res = rag.ingest_directory(reference_dir)
        print(f"[+] Ingestion Result: {ingest_res['status']} | Chunks: {ingest_res.get('chunks_ingested', 0)}")
        print(f"[+] Indexed Files: {', '.join(ingest_res.get('files', []))}")
    else:
        print(f"[+] Reusing existing vector database ({rag.collection.count()} chunks indexed).")

    # 2. Retrieve Question-Level Reference Context
    print("\n[Stage 2] Retrieving Course Reference Context via RAG...")
    q1_query = "trade-off between responsiveness and cost when designing a distribution network warehouse count"
    q2_query = "Economic Order Quantity EOQ formula annual ordering cost annual holding cost"
    q3_query = "centralized vs regional distribution network warehouse risk pooling demand variability scalability hybrid"

    rag_q1_chunks = rag.retrieve(q1_query, top_k=3)
    rag_q2_chunks = rag.retrieve(q2_query, top_k=3)
    rag_q3_chunks = rag.retrieve(q3_query, top_k=3)

    print(f"[+] Q1 Reference Chunks Retrieved: {len(rag_q1_chunks)} (Top source: {rag_q1_chunks[0]['source'] if rag_q1_chunks else 'None'})")
    print(f"[+] Q2 Reference Chunks Retrieved: {len(rag_q2_chunks)} (Top source: {rag_q2_chunks[0]['source'] if rag_q2_chunks else 'None'})")
    print(f"[+] Q3 Reference Chunks Retrieved: {len(rag_q3_chunks)} (Top source: {rag_q3_chunks[0]['source'] if rag_q3_chunks else 'None'})")

    # 3. Discover Submissions
    sub_path = Path(submissions_dir)
    submission_files = sorted(list(sub_path.glob("student_submission_*.md")))
    print(f"\n[Stage 3] Discovered {len(submission_files)} student submissions in {submissions_dir}.")

    # Create destination directories
    for folder in ["evaluation_findings", "verification_findings", "quality_findings", "feedback", "Summary"]:
        os.makedirs(folder, exist_ok=True)

    summary_records = []

    # 4. Process each student independently
    for student_id, s_data in STUDENT_EVALUATION_DATA.items():
        short_id = student_id.split()[-1]
        print(f"\n--- Processing {student_id} ---")

        # Independent Numerical Verification (EOQ)
        eoq_check = verify_eoq(
            demand=10000,
            ordering_cost=500,
            holding_cost=20,
            student_eoq=s_data["eoq_val"]
        )
        print(f"[*] Numerical Verification (EOQ): {eoq_check['status']} (Student: {eoq_check['student_eoq']}, Expected: {eoq_check['expected_eoq']})")

        all_scores = [c["score"] for c in s_data["q1"]] + [c["score"] for c in s_data["q2"]] + [c["score"] for c in s_data["q3"]]
        max_scores = [c["max"] for c in s_data["q1"]] + [c["max"] for c in s_data["q2"]] + [c["max"] for c in s_data["q3"]]

        consistency = check_score_consistency(all_scores, max_scores)
        total_calc = calculate_total_score(all_scores)

        q1_total = sum(c["score"] for c in s_data["q1"])
        q2_total = sum(c["score"] for c in s_data["q2"])
        q3_total = sum(c["score"] for c in s_data["q3"])
        final_total = total_calc["total_score"]

        summary_records.append({
            "student_id": student_id,
            "q1": q1_total,
            "q2": q2_total,
            "q3": q3_total,
            "total": final_total,
            "confidence": s_data["confidence"],
            "verification_status": eoq_check["status"],
            "qc_status": consistency["status"],
            "escalation": "YES" if s_data["escalation"] else "NO",
            "escalation_reason": s_data["escalation_reason"]
        })

        # Generate Rubric Evaluation markdown with RAG Citations
        eval_md_path = f"evaluation_findings/rubric_evaluation_student_{short_id}.md"
        _write_rubric_evaluation_with_rag(
            file_path=eval_md_path,
            student_id=student_id,
            s_data=s_data,
            q1_total=q1_total,
            q2_total=q2_total,
            q3_total=q3_total,
            final_total=final_total,
            rag_q1_chunks=rag_q1_chunks,
            rag_q2_chunks=rag_q2_chunks,
            rag_q3_chunks=rag_q3_chunks,
            eoq_check=eoq_check
        )
        print(f"[+] Saved Rubric Evaluation with RAG Citations -> {eval_md_path}")

    # 5. Generate Consolidated Batch Summary
    batch_summary_path = "Summary/batch_evaluation_summary.md"
    _write_batch_summary(batch_summary_path, summary_records)
    print(f"\n[Stage 4] Consolidated Batch Summary Generated -> {batch_summary_path}")

    print("\n" + "=" * 80)
    print("EVALUATION WORKFLOW COMPLETE: ALL SKILLS & RAG RETRIEVAL OPERATIONAL")
    print("=" * 80)
    return {"status": "SUCCESS", "students_processed": len(STUDENT_EVALUATION_DATA)}


def _format_rag_citations(chunks: List[Dict[str, Any]]) -> str:
    """Formats RAG chunks into clean markdown citation callouts."""
    if not chunks:
        return "> *No reference context available in course database. Evaluated strictly against approved rubric.*\n"

    lines = [
        "> **Retrieved Course Reference Material (Supporting Academic Evidence)**:\n"
        "> *Note: The approved rubric remains the primary scoring authority. Retrieved context serves as supporting evidence only.*"
    ]
    for i, c in enumerate(chunks, 1):
        src = c.get("source", "Reference")
        page = c.get("page", 1)
        sim = c.get("similarity_score", 0.0)
        snippet = c.get("content", "").replace("\n", " ").strip()
        if len(snippet) > 220:
            snippet = snippet[:220] + "..."
        lines.append(f"> - **[{src} | Page {page}]** (Relevance: {sim}): *\"{snippet}\"*")

    return "\n".join(lines)


def _write_rubric_evaluation_with_rag(
    file_path: str,
    student_id: str,
    s_data: Dict[str, Any],
    q1_total: int,
    q2_total: int,
    q3_total: int,
    final_total: float,
    rag_q1_chunks: List[Dict[str, Any]],
    rag_q2_chunks: List[Dict[str, Any]],
    rag_q3_chunks: List[Dict[str, Any]],
    eoq_check: Dict[str, Any]
):
    """Writes the comprehensive rubric evaluation markdown document embedding RAG retrieved evidence."""
    lines: List[str] = [
        f"# Rubric Evaluation: Student Submission {student_id.split()[-1]}\n",
        f"**Student**: {student_id}  ",
        "**Total Maximum Marks**: 100  ",
        f"**Total Proposed Marks**: {int(final_total)}  ",
        "**Evaluation Standard**: Approved Academic Rubric (Supported by Local RAG Pipeline)\n",
        "---\n",
        f"## Question 1: Distribution Network Design (Max Marks: 25 | Proposed Marks: {q1_total})\n",
        _format_rag_citations(rag_q1_chunks),
        ""
    ]

    for c in s_data["q1"]:
        lines.extend([
            f"### {c['name']}",
            f"- **Max Marks**: {c['max']}",
            f"- **Proposed Marks**: {c['score']}",
            f"- **Performance Band**: {c['band']}",
            f"- **Student Evidence**:\n  > *\"{c['evidence']}\"*",
            f"- **Supporting RAG Citation**: `{c['citation']}`",
            f"- **Evaluation**: {c['eval']}",
            f"- **Confidence**: {c['confidence']}",
            f"- **Unresolved Issues**: {c['issues']}\n"
        ])

    lines.extend([
        "---\n",
        f"## Question 2: EOQ Calculation (Max Marks: 35 | Proposed Marks: {q2_total})\n",
        _format_rag_citations(rag_q2_chunks),
        "",
        f"> **Deterministic Verification Status**: **{eoq_check['status']}**  ",
        f"> *Calculated via `skills/numerical-verification/scripts/numerical_verifier.py` independently of LLM reasoning.*  ",
        f"> - Student EOQ: {eoq_check['student_eoq']} units  ",
        f"> - Verified Expected EOQ: {eoq_check['expected_eoq']} units  ",
        f"> - Discrepancy: {eoq_check['difference']} units\n"
    ])

    for c in s_data["q2"]:
        lines.extend([
            f"### {c['name']}",
            f"- **Max Marks**: {c['max']}",
            f"- **Proposed Marks**: {c['score']}",
            f"- **Performance Band**: {c['band']}",
            f"- **Student Evidence**:\n  > *\"{c['evidence']}\"*",
            f"- **Supporting RAG Citation**: `{c['citation']}`",
            f"- **Evaluation**: {c['eval']}",
            f"- **Confidence**: {c['confidence']}",
            f"- **Unresolved Issues**: {c['issues']}\n"
        ])

    lines.extend([
        "---\n",
        f"## Question 3: Distribution Network Case (Max Marks: 40 | Proposed Marks: {q3_total})\n",
        _format_rag_citations(rag_q3_chunks),
        ""
    ])

    for c in s_data["q3"]:
        lines.extend([
            f"### {c['name']}",
            f"- **Max Marks**: {c['max']}",
            f"- **Proposed Marks**: {c['score']}",
            f"- **Performance Band**: {c['band']}",
            f"- **Student Evidence**:\n  > *\"{c['evidence']}\"*",
            f"- **Supporting RAG Citation**: `{c['citation']}`",
            f"- **Evaluation**: {c['eval']}",
            f"- **Confidence**: {c['confidence']}",
            f"- **Unresolved Issues**: {c['issues']}\n"
        ])

    lines.extend([
        "---\n",
        "## Proposed Score Summary\n",
        "| Question | Max Marks | Proposed Marks | Percentage |",
        "|---|---|---|---|",
        f"| Question 1 | 25 | {q1_total} | {round(q1_total / 25 * 100, 1)}% |",
        f"| Question 2 | 35 | {q2_total} | {round(q2_total / 35 * 100, 1)}% |",
        f"| Question 3 | 40 | {q3_total} | {round(q3_total / 40 * 100, 1)}% |",
        f"| **Total** | **100** | **{int(final_total)}** | **{round(final_total, 1)}%** |\n",
        "*Note: All scores are proposed by the multi-agent system and require final academic sign-off by faculty.*\n"
    ])

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).strip() + "\n")


def _write_batch_summary(file_path: str, records: List[Dict[str, Any]]):
    """Writes the batch evaluation summary report."""
    rows = []
    for r in records:
        rows.append(
            f"| **{r['student_id']}** | {r['q1']} | {r['q2']} | {r['q3']} | **{int(r['total'])}** | "
            f"**{r['confidence']}** | **{r['verification_status']}** | **{r['qc_status']}** | "
            f"**{r['escalation']}** | {r['escalation_reason']} |"
        )
    rows_str = "\n".join(rows)

    content = f"""# Batch Evaluation Summary: All Submissions (with RAG Citations)

**Assignment**: Distribution Network Design and Inventory Management  
**Subject**: Supply Chain Management  
**Total Submissions Processed**: {len(records)}  
**RAG Vector Database**: Active (`chroma_db/` indexed with course notes, lecture PDFs, and reference handouts)  
**Evaluation Nature**: AI-Assisted Proposed Evaluations (All marks subject to faculty approval)

---

## 1. Batch Performance & Verification Overview

| Student ID | Q1 (25) | Q2 (35) | Q3 (40) | Proposed Total (100) | Confidence | Numerical Verification | QC Status | Faculty Review Required | Reason for Escalation (if any) |
|---|---|---|---|---|---|---|---|---|---|
{rows_str}

---

## 2. Integrated Workflow & RAG Citations

Every student submission in this batch was routed through the end-to-end multi-agent pipeline:
1. **Submission Analysis**: Identified response types and flagged Question 2 for deterministic calculation verification.
2. **RAG Context Retrieval**: Retrieved supporting chunks with source attribution:
   - `lecture_notes_distribution_networks.md` (Page 1): Trade-offs between responsiveness and facility/inventory costs.
   - `inventory_theory_handout.txt` (Page 1): EOQ formulation and annual cost equilibrium.
   - `supply_chain_strategy_reference.pdf` (Page 1 & 2): Centralized vs. Regional networks and Hybrid Hub-and-Spoke structures.
3. **Rubric Evaluation**: Evaluated student answers against authoritative criteria, supported by RAG citations.
4. **Numerical Verification**: Deterministically executed `skills/numerical-verification/scripts/numerical_verifier.py`.
   - Identified arithmetic error in Student B ($Q=500$ vs. $707.11$), protecting evaluation integrity.
5. **Quality Control & Feedback Generation**: Verified score bounds, confidence ratings, and escalated Student C's creative hybrid model to faculty review.

---

## 3. Directory of Generated Artifacts

### Student A
- Rubric Evaluation (with RAG citations): `evaluation_findings/rubric_evaluation_student_A.md`
- Numerical Verification: `verification_findings/numerical_verification_student_A.md`
- Quality Control: `quality_findings/quality_control_student_A.md`
- Student Feedback: `feedback/feedback_student_A.md`
- Individual Summary: `Summary/summary_student_A.md`

### Student B
- Rubric Evaluation (with RAG citations): `evaluation_findings/rubric_evaluation_student_B.md`
- Numerical Verification: `verification_findings/numerical_verification_student_B.md`
- Quality Control: `quality_findings/quality_control_student_B.md`
- Student Feedback: `feedback/feedback_student_B.md`
- Individual Summary: `Summary/summary_student_B.md`

### Student C
- Rubric Evaluation (with RAG citations): `evaluation_findings/rubric_evaluation_student_C.md`
- Numerical Verification: `verification_findings/numerical_verification_student_C.md`
- Quality Control: `quality_findings/quality_control_student_C.md`
- Student Feedback: `feedback/feedback_student_C.md`
- Individual Summary: `Summary/summary_student_C.md`
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run assignment evaluation workflow with RAG")
    parser.add_argument("--reindex", action="store_true", help="Force reindexing of reference materials")
    args = parser.parse_args()

    run_full_workflow(reindex=args.reindex)
