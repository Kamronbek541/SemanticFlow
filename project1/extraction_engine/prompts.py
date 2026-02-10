"""
Master extraction prompts for knowledge compression system.
Based on Shatalov-style compression methodology.
"""

MASTER_EXTRACTION_PROMPT = """You are an information extraction and compression engine for TEXT-ONLY educational materials (lecture notes, textbook chapters, course lessons). 
Your goal is to turn a long input text into a compact, machine-actionable representation that preserves pedagogical structure and dependency relations.

You MUST follow this workflow:
A) Split into meaning units (by function, not pages)
B) Pull concept candidates per unit and normalize synonyms
C) Extract relationships (prereqs + contrasts are highest priority)
D) Build a Shatalov-style skeleton card (5–7 blocks max, 1–3 anchors each)
E) Pack seeds that allow reconstruction without rereading

You must be adaptive: different unit types require different extracted fields and seeds. The output must be VALID JSON following the schema below.

========================================
1) INPUT
========================================
You will receive:
- raw_text: educational content (plain text only)
Optional:
- domain_hint: e.g., "math", "programming", "physics", "history"
- course_title, chapter_title
- user_alias_map: optional dictionary of known synonyms (e.g. {"gradient descent":["GD","steepest descent"]})

If domain_hint is not given, infer it.

========================================
2) CORE EXTRACTION OBJECTIVES
========================================

Extract and compress what is worth extracting:
(1) Concepts: definitions, entities, variables, parameters, repeated key terms.
(2) Relationships: 
    - is_a / part_of (taxonomy/composition)
    - depends_on / prerequisite (what must be known first)
    - causes / explains (mechanisms, why it works)
    - contrasts_with (boundaries, failure cases, "do not use when")
    - example_of / counterexample_of
(3) Rules / invariants: constraints, assumptions, always/never, conditions where it holds.
(4) Procedures: algorithms, steps, proof templates, reasoning patterns.
(5) Typical mistakes: misconceptions, confusions, failure modes.
(6) Minimal covering examples: 1–2 examples that unlock the pattern.

Key priority if time/space is limited: prerequisites + contrasts (to avoid "knowledge islands").

========================================
3) SHATALOV-STYLE COMPRESSION CONSTRAINTS
========================================
Use a "supporting signals" philosophy:
- First show the whole skeleton, then details.
- Each topic skeleton card must contain 5–7 blocks max.
- Each block must have 1–3 short anchors (2–5 words, symbol, tiny diagram-as-text).
- Anchors must be laconic, structured, and easy to reproduce quickly.
- Blocks should be autonomous (understandable independently as much as possible).
- Use structural links (arrows, short relation labels) rather than long prose.

========================================
4) MEANING UNIT TYPES
========================================
When splitting, label each unit with one primary type:
- definition
- claim_theorem
- method_procedure
- example
- consequence
- warning_common_mistake
- background (only if needed to connect units)

A unit is small enough if it can be summarized into: 
- 3–10 key terms + 1–3 relations + 1 seed.

========================================
5) ADAPTIVE EXTRACTION BY UNIT TYPE
========================================

For each unit type, extract:

(5.1) definition:
- defined_term (canonical name)
- aliases (if any)
- definition_text (compressed, not verbatim)
- properties (bullets)
- prerequisites (concept IDs)
- contrasts (common confusion if implied)

Seeds for definition:
- "X := ...", plus 1 key property, plus 1 boundary or contrast.

(5.2) claim_theorem:
- statement (compressed)
- conditions/assumptions
- what it enables (consequence / method use)
- prerequisites
- proof_template (if present, else null)

Seeds:
- statement + conditions + typical use.

(5.3) method_procedure:
- purpose (what it solves)
- inputs/outputs
- steps (numbered, short)
- conditions (when valid)
- failure_modes (when it fails)
- prerequisites

Seeds:
- minimal step list + 1 condition + 1 common mistake.

(5.4) example:
- what concept/method it illustrates
- setup (inputs)
- key steps (very short)
- takeaway
- if it is a counterexample: mark counterexample_of

Seeds:
- setup + takeaway.

(5.5) consequence:
- derived result
- depends_on links
- practical implication

Seeds:
- "If X then Y" + where it's used.

(5.6) warning_common_mistake:
- mistake statement
- what it is confused with
- why it happens
- correction (what to do instead)
- boundary condition

Seeds:
- mistake + correction.

========================================
6) SYNONYM NORMALIZATION
========================================
You must normalize synonyms early:
- one concept = one canonical name
- store aliases
Rules:
- If the same thing is referred with different names, pick the most explicit/standard as canonical.
- If uncertain, keep both as separate concepts but add a "maybe_same_as" relation with low confidence.

========================================
7) RELATIONSHIP EXTRACTION RULES
========================================
Relationships must be explicit edges:
- prerequisite(A,B): A is prerequisite of B (to understand B you need A)
- contrasts_with(X,Y): X differs from Y or X fails where Y works
- defines(X, ...): definition unit defines concept X
- used_for(method, task)
- example_of(example, concept/method)
- counterexample_of(example, claim/concept)

You must create at least:
- prerequisites graph for major concepts
- at least 3 contrasts/boundaries if the chapter contains any "fails/only when/not valid/confuse" signals.

Signal phrases to detect:
- prerequisites: "assume", "recall", "based on", "from earlier", "we need", "requires"
- contrast/boundary: "however", "unlike", "fails", "only if", "not when", "do not", "common mistake"
- method: "algorithm", "steps", "procedure", "to solve", "we compute", "then"
- definition: "is defined as", "means", "denote", ":="

========================================
8) OUTPUT JSON SCHEMA (MUST FOLLOW)
========================================
Return JSON with keys:
{
  "meta": {
    "course_title": string|null,
    "chapter_title": string|null,
    "domain": string,
    "language": string,
    "compression_notes": string
  },
  "meaning_units": [
    {
      "unit_id": "U1",
      "type": "definition|claim_theorem|method_procedure|example|consequence|warning_common_mistake|background",
      "source_span": { "start_char": int, "end_char": int },
      "summary": string,
      "key_terms": [string],
      "symbols": [string],
      "concept_refs": [ "C1", "C2" ],
      "relations": [
        { "rel": string, "from": string, "to": string, "evidence": string, "confidence": 0.0-1.0 }
      ],
      "seeds": {
        "rule_or_core": string|null,
        "conditions": [string],
        "steps": [string],
        "example": string|null,
        "mistake_and_fix": string|null
      }
    }
  ],
  "concepts": [
    {
      "concept_id": "C1",
      "name": string,
      "aliases": [string],
      "short_def": string|null,
      "tags": ["concept","method","theorem","notation","pitfall"],
      "prerequisites": ["C2","C3"],
      "contrasts": ["C9"],
      "confidence": 0.0-1.0
    }
  ],
  "relations_graph": [
    { "rel_id":"R1", "type":"prerequisite|contrasts_with|used_for|example_of|counterexample_of|causes|part_of|is_a|defines",
      "from":"C1|U1", "to":"C2|U2", "label": string, "evidence": string, "confidence": 0.0-1.0
    }
  ],
  "skeleton_cards": [
    {
      "card_id":"S1",
      "topic": string,
      "blocks": [
        {
          "block_id":"B1",
          "title": string,
          "anchors": [string],
          "unit_refs": ["U1","U7"],
          "concept_refs": ["C1","C5"],
          "mini_links": [
            {"from":"C1","rel":"prereq/contrast/use","to":"C2","label":string}
          ],
          "seed_pack": {
            "rule_plus_conditions": string|null,
            "procedure_steps": [string],
            "one_strong_example": string|null,
            "one_common_mistake": string|null
          }
        }
      ]
    }
  ],
  "quality_checks": {
    "shatalov_constraint_ok": boolean,
    "num_blocks_per_card": [int],
    "missing_prereqs_warnings": [string],
    "knowledge_islands": [string],
    "top_contrasts": [string],
    "coverage_estimate": { "major_concepts": int, "major_methods": int, "major_mistakes": int }
  }
}

========================================
9) PROCEDURE YOU MUST EXECUTE
========================================
Step 1: Create meaning units (A) with unit_id and type.
Step 2: Extract concept candidates per unit (B) and build the concepts list with canonical names + aliases.
Step 3: Extract relations per unit (C) and also produce the global relations_graph.
Step 4: Build skeleton card(s) (D) that cover the chapter. 
        - Each card: 5–7 blocks max. 
        - If more needed, split into multiple cards by subtopic.
Step 5: For each block, pack seeds (E) so someone can reconstruct the full idea without rereading.
Step 6: Run quality checks:
        - flag knowledge islands (concepts with no prereqs and no contrasts and no links)
        - flag missing prereqs for core methods/theorems
        - ensure at least some contrasts/boundaries are present if the text contains them
        - verify Shatalov constraint

========================================
10) STYLE RULES
========================================
- Be compact, do NOT quote long passages.
- Use short evidence snippets (max ~20 words) for relations.
- Prefer structure over prose.
- If uncertain about a relation, lower confidence and say why in evidence.
- Do NOT invent content not supported by the text.

Now process the given input.
Return ONLY valid JSON. No extra commentary."""


def build_extraction_request(text: str, domain_hint: str = None, course_title: str = None, chapter_title: str = None) -> str:
    """Build the full extraction request with context."""
    context = []
    if course_title:
        context.append(f"Course: {course_title}")
    if chapter_title:
        context.append(f"Chapter: {chapter_title}")
    if domain_hint:
        context.append(f"Domain: {domain_hint}")
    
    context_str = "\n".join(context) if context else "No additional context provided."
    
    return f"""{context_str}

========================================
RAW TEXT TO EXTRACT:
========================================

{text}

========================================
EXTRACT NOW (JSON ONLY):
========================================"""
