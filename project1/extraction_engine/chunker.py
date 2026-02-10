"""
Smart text chunker for large educational documents.
Splits on section/chapter boundaries to preserve context.
"""

import re
from typing import List, Tuple


def estimate_tokens(text: str) -> int:
    """Rough estimate: ~1 token per 4 characters."""
    return len(text) // 4


def find_split_points(text: str) -> List[int]:
    """
    Find natural split points in educational text.
    Look for chapter/section headers, empty lines, module boundaries.
    """
    patterns = [
        r'\n#{1,3}\s+',           # Markdown headers
        r'\n\d+\s+[A-Z]',        # Numbered sections like "4 Modules"
        r'\n\d+\.\d+\s+[A-Z]',  # Sub-sections like "2.3 Core Area"
        r'\nModule Name\s',       # Module boundaries
        r'\n---+\n',              # Horizontal rules
        r'\n\n\n+',              # Multiple empty lines
    ]
    
    split_points = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            split_points.add(match.start())
    
    return sorted(split_points)


def chunk_text(text: str, max_tokens: int = 12000) -> List[Tuple[str, int, int]]:
    """
    Split text into chunks that fit within token limits.
    Tries to split on section boundaries for better context.
    
    Args:
        text: Full document text
        max_tokens: Maximum tokens per chunk (conservative to leave room for prompt)
        
    Returns:
        List of (chunk_text, start_char, end_char)
    """
    total_tokens = estimate_tokens(text)
    
    # If fits in one chunk, return as-is
    if total_tokens <= max_tokens:
        return [(text, 0, len(text))]
    
    print(f"📄 Document is ~{total_tokens} tokens, splitting into chunks of ~{max_tokens} tokens")
    
    split_points = find_split_points(text)
    
    # If no natural split points found, split by paragraph
    if not split_points:
        split_points = [m.start() for m in re.finditer(r'\n\n', text)]
    
    # If still nothing, forceful fixed-size split
    if not split_points:
        max_chars = max_tokens * 4
        split_points = list(range(max_chars, len(text), max_chars))
    
    # Add start and end
    split_points = [0] + [p for p in split_points if 0 < p < len(text)] + [len(text)]
    
    # Merge sections into chunks that fit
    chunks = []
    current_start = 0
    current_end = 0
    
    for i in range(1, len(split_points)):
        next_end = split_points[i]
        section_text = text[current_start:next_end]
        section_tokens = estimate_tokens(section_text)
        
        if section_tokens > max_tokens and current_end > current_start:
            # Save current chunk and start new one
            chunks.append((text[current_start:current_end], current_start, current_end))
            current_start = current_end
        
        current_end = next_end
    
    # Add final chunk
    if current_start < len(text):
        chunks.append((text[current_start:current_end], current_start, current_end))
    
    # Report
    for i, (chunk, start, end) in enumerate(chunks):
        tokens = estimate_tokens(chunk)
        words = len(chunk.split())
        print(f"  📦 Chunk {i+1}/{len(chunks)}: {words} words (~{tokens} tokens), chars {start}-{end}")
    
    return chunks


def merge_extractions(extractions: List[dict]) -> dict:
    """
    Merge multiple chunk extractions into one combined result.
    Re-indexes IDs to avoid collisions.
    
    Args:
        extractions: List of extraction dicts from each chunk
        
    Returns:
        Merged extraction dict
    """
    if len(extractions) == 1:
        return extractions[0]
    
    merged = {
        "meta": extractions[0].get("meta", {}),
        "meaning_units": [],
        "concepts": [],
        "relations_graph": [],
        "skeleton_cards": [],
        "quality_checks": {
            "shatalov_constraint_ok": True,
            "num_blocks_per_card": [],
            "missing_prereqs_warnings": [],
            "knowledge_islands": [],
            "top_contrasts": [],
            "coverage_estimate": {
                "major_concepts": 0,
                "major_methods": 0,
                "major_mistakes": 0
            }
        }
    }
    
    # Track seen concept names to deduplicate
    seen_concepts = {}  # name -> concept_id
    concept_id_map = {}  # old_id -> new_id
    unit_counter = 0
    concept_counter = 0
    relation_counter = 0
    card_counter = 0
    
    for chunk_idx, extraction in enumerate(extractions):
        prefix = f"ch{chunk_idx+1}_"
        
        # Merge meaning units with new IDs
        for unit in extraction.get("meaning_units", []):
            unit_counter += 1
            old_id = unit.get("unit_id", f"U{unit_counter}")
            new_id = f"U{unit_counter}"
            unit["unit_id"] = new_id
            merged["meaning_units"].append(unit)
        
        # Merge concepts (deduplicate by name)
        for concept in extraction.get("concepts", []):
            name = concept.get("name", "").lower().strip()
            old_id = concept.get("concept_id", "")
            
            if name in seen_concepts:
                # Map old ID to existing concept
                concept_id_map[f"{prefix}{old_id}"] = seen_concepts[name]
                concept_id_map[old_id] = seen_concepts[name]
                
                # Merge aliases and info
                existing = next(
                    c for c in merged["concepts"] 
                    if c["concept_id"] == seen_concepts[name]
                )
                for alias in concept.get("aliases", []):
                    if alias not in existing.get("aliases", []):
                        existing.setdefault("aliases", []).append(alias)
            else:
                concept_counter += 1
                new_id = f"C{concept_counter}"
                concept_id_map[f"{prefix}{old_id}"] = new_id
                concept_id_map[old_id] = new_id
                concept["concept_id"] = new_id
                seen_concepts[name] = new_id
                merged["concepts"].append(concept)
        
        # Merge relations
        for rel in extraction.get("relations_graph", []):
            relation_counter += 1
            rel["rel_id"] = f"R{relation_counter}"
            merged["relations_graph"].append(rel)
        
        # Merge skeleton cards
        for card in extraction.get("skeleton_cards", []):
            card_counter += 1
            card["card_id"] = f"S{card_counter}"
            merged["skeleton_cards"].append(card)
        
        # Merge quality checks
        qc = extraction.get("quality_checks", {})
        coverage = qc.get("coverage_estimate", {})
        
        merged["quality_checks"]["num_blocks_per_card"].extend(
            qc.get("num_blocks_per_card", [])
        )
        merged["quality_checks"]["missing_prereqs_warnings"].extend(
            qc.get("missing_prereqs_warnings", [])
        )
        merged["quality_checks"]["knowledge_islands"].extend(
            qc.get("knowledge_islands", [])
        )
        merged["quality_checks"]["top_contrasts"].extend(
            qc.get("top_contrasts", [])
        )
        merged["quality_checks"]["coverage_estimate"]["major_concepts"] += coverage.get("major_concepts", 0)
        merged["quality_checks"]["coverage_estimate"]["major_methods"] += coverage.get("major_methods", 0)
        merged["quality_checks"]["coverage_estimate"]["major_mistakes"] += coverage.get("major_mistakes", 0)
        
        if not qc.get("shatalov_constraint_ok", True):
            merged["quality_checks"]["shatalov_constraint_ok"] = False
    
    # Update meta
    merged["meta"]["compression_notes"] = (
        f"Merged from {len(extractions)} chunks. "
        f"Total: {len(merged['concepts'])} unique concepts, "
        f"{len(merged['meaning_units'])} meaning units, "
        f"{len(merged['skeleton_cards'])} skeleton cards."
    )
    
    print(f"\n🔗 Merged {len(extractions)} chunks:")
    print(f"   - {len(merged['concepts'])} unique concepts (deduplicated)")
    print(f"   - {len(merged['meaning_units'])} meaning units")
    print(f"   - {len(merged['skeleton_cards'])} skeleton cards")
    print(f"   - {len(merged['relations_graph'])} relationships")
    
    return merged
