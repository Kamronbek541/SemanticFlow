# Technical Specification: Knowledge Extraction & Compression System

> **For AI Agents:** This document serves as the "DNA" of the system. Use it to understand, replicate, or extend the extraction logic without needing to re-read the entire codebase.

---

## 1. System Identity & Objective
**Name:** SemanticFlow Extraction Engine
**Core Goal:** Transform linear educational text (lectures, textbooks) into a **compact, machine-actionable knowledge graph** that preserves pedagogical logical structure.
**Key Differentiator:** It does NOT just summarize. It **compresses** using Viktor Shatalov's "Supporting Signals" methodology.

---

## 2. Pedagogical Foundation (Shatalov's Method)
The system enforces strict cognitive constraints to ensure high retention and rapid review.

### 2.1 The "7±2" Rule (Constraint)
- **Constraint:** A single "Skeleton Card" (topic review) must contain **5 to 7 blocks**. No more, no less.
- **Reasoning:** Human working memory limit. If a topic has 20 items, it must be grouped into 5-7 chunks.

### 2.2 Supporting Signals (Anchors)
- **Constraint:** Each block must have **1 to 3 "Anchors"**.
- **Definition:** An anchor is a laconic memory cue (2-5 words, formula, or symbol).
- **Prohibited:** Long sentences, prose, "wall of text".
- **Goal:** The anchor triggers the memory; it does not replace the content.

### 2.3 Knowledge Integrity (Islands)
- **Constraint:** No "Knowledge Islands". Every concept must be connected via:
    - **Prerequisite**: What must be known *before* this?
    - **Contrast**: What is this *not*? (Boundary conditions).
- **Priority:** Prerequisite and Contrast identification is higher priority than simple definitions.

---

## 3. Extraction Pipeline Logic

The system follows a strict 5-step workflow (enforced in `prompts.py`):

### Phase A: Atomization (Meaning Units)
Input text is split into "Meaning Units" based on function, not paragraphs.
**Unit Types:**
1.  **Definition**: Introduces a new term/concept.
2.  **Claim/Theorem**: A statement that requires proof or has conditions.
3.  **Method/Procedure**: A sequence of steps to solve a specific problem.
4.  **Example**: Concrete application of a concept.
5.  **Consequence**: Derived result or implication.
6.  **Warning/Mistake**: Common misconception (Critical for learning).

### Phase B: Concept Extraction
- **Normalization**: Synonyms are mapped to a single Canonical Name (e.g., "Derivative", "Rate of change", "f'" -> "Derivative").
- **Tags**: Concepts are tagged (concept, method, tool, pitfall).

### Phase C: Relationship Extraction
The engine scans for specific "Signal Phrases" to build the graph:
- *Prerequisites*: "recall", "requires", "based on", "assume".
- *Contrasts*: "unlike", "however", "confused with", "fails when".
- *Methods*: "steps", "algorithm", "procedure", "to calculate".

### Phase D: Compression (Skeleton Building)
The engine assembles the "Skeleton Card":
- Groups related units into **Blocks**.
- Selects **Anchors** for each block.
- **Validation**: If blocks < 5 or > 7, the card is invalid (Shatalov violation).

### Phase E: Seed Packing
For each block, the engine generates a "Seed Pack" — minimal info to reconstruct the full idea:
- **Rule**: The core principle.
- **Example**: One archetypal example.
- **Mistake**: One warning about a common error.

---

## 4. Data Model (JSON Schema)

The output is a strict JSON object. See `extraction_engine/schema.py` for Pydantic models.

### Core Objects
1.  **`meaning_units`**: List of atomic content chunks.
2.  **`concepts`**: List of unique entities (nodes).
3.  **`relations_graph`**: List of directed edges (`from`, `to`, `type`, `confidence`).
4.  **`skeleton_cards`**: The compressed view.
    - `blocks`: List[Block] (Min 5, Max 7)
        - `anchors`: List[String] (Max 5 words)
        - `seed_pack`: Object (Rule, Steps, Example)

---

## 5. Prompt Engineering Strategy

The `MASTER_EXTRACTION_PROMPT` uses specific techniques to steer the LLM:

1.  **Context Contextualization**:
    - "You are an information extraction engine..." (Role setting).
    - "Your goal is compact representation..." (Objective setting).

2.  **Adaptive Instructions**:
    - Detailed sub-instructions for EACH unit type.
    - *Example*: "If Unit is `method`, extract: inputs, outputs, numbered steps, failure modes."

3.  **Negative Constraints** (What NOT to do):
    - "Do not quote long passages."
    - "Do not extract generic 'introductory' text."
    - "Do not create blocks with > 3 anchors."

4.  **Output Enforcement**:
    - "Return ONLY valid JSON."
    - Schema is provided explicitly in the prompt to ensure structure compliance.

---

## 6. Future Extension Points

To scale this system, an AI should focus on:

1.  **Multi-File Synthesis**: Combining JSONs from 10 chapters into a super-graph (Course Graph).
2.  **Socratic Tutor**: Using the `skeleton_cards` to quiz the user ("I see anchor X, what does it mean?").
3.  **Visual Renderer**: Converting the JSON graph into Mermaid.js or Graphviz diagrams automatically.
