"""
Generate human-readable markdown from extraction output.
Creates Shatalov-style skeleton cards for review and study.
"""

from typing import Dict, Any


def generate_markdown_review(data: Dict[str, Any], original_text: str = None) -> str:
    """
    Generate comprehensive markdown review of extraction.
    
    Args:
        data: Extracted knowledge dictionary
        original_text: Original input text (optional, for reference)
        
    Returns:
        Formatted markdown string
    """
    md_lines = []
    
    # Header
    meta = data.get("meta", {})
    md_lines.append("# Knowledge Extraction Review\n")
    
    if meta.get("course_title"):
        md_lines.append(f"**Course**: {meta['course_title']}  ")
    if meta.get("chapter_title"):
        md_lines.append(f"**Chapter**: {meta['chapter_title']}  ")
    md_lines.append(f"**Domain**: {meta.get('domain', 'Unknown')}  ")
    md_lines.append(f"**Language**: {meta.get('language', 'Unknown')}\n")
    
    if meta.get("compression_notes"):
        md_lines.append(f"> {meta['compression_notes']}\n")
    
    md_lines.append("---\n")
    
    # Quality Checks Summary
    quality = data.get("quality_checks", {})
    coverage = quality.get("coverage_estimate", {})
    
    md_lines.append("## 📊 Extraction Summary\n")
    md_lines.append(f"- **Concepts Extracted**: {coverage.get('major_concepts', 0)}")
    md_lines.append(f"- **Methods/Procedures**: {coverage.get('major_methods', 0)}")
    md_lines.append(f"- **Common Mistakes**: {coverage.get('major_mistakes', 0)}")
    md_lines.append(f"- **Skeleton Cards**: {len(data.get('skeleton_cards', []))}")
    md_lines.append(f"- **Shatalov Constraint Satisfied**: {'✅ Yes' if quality.get('shatalov_constraint_ok') else '❌ No'}\n")
    
    # Warnings
    if quality.get("knowledge_islands"):
        md_lines.append("### ⚠️ Knowledge Islands Detected\n")
        md_lines.append("These concepts have no prerequisite or contrast links:\n")
        for island in quality['knowledge_islands']:
            md_lines.append(f"- {island}")
        md_lines.append("")
    
    if quality.get("missing_prereqs_warnings"):
        md_lines.append("### ⚠️ Missing Prerequisites\n")
        for warning in quality['missing_prereqs_warnings']:
            md_lines.append(f"- {warning}")
        md_lines.append("")
    
    md_lines.append("---\n")
    
    # Skeleton Cards (Main Content)
    skeleton_cards = data.get("skeleton_cards", [])
    md_lines.append("## 🗂️ Skeleton Cards (Shatalov Style)\n")
    
    for card in skeleton_cards:
        md_lines.append(f"### 📋 {card['topic']}\n")
        
        blocks = card.get("blocks", [])
        md_lines.append(f"*{len(blocks)} blocks*\n")
        
        for i, block in enumerate(blocks, 1):
            md_lines.append(f"#### Block {i}: {block['title']}\n")
            
            # Anchors (KEY MEMORY CUES)
            anchors = block.get("anchors", [])
            md_lines.append("**🔑 Anchors (Memory Cues)**:")
            for anchor in anchors:
                md_lines.append(f"- `{anchor}`")
            md_lines.append("")
            
            # Seed pack (reconstruction info)
            seed_pack = block.get("seed_pack", {})
            
            if seed_pack.get("rule_plus_conditions"):
                md_lines.append(f"**Rule**: {seed_pack['rule_plus_conditions']}\n")
            
            if seed_pack.get("procedure_steps"):
                md_lines.append("**Steps**:")
                for step in seed_pack['procedure_steps']:
                    md_lines.append(f"1. {step}")
                md_lines.append("")
            
            if seed_pack.get("one_strong_example"):
                md_lines.append(f"**Example**: {seed_pack['one_strong_example']}\n")
            
            if seed_pack.get("one_common_mistake"):
                md_lines.append(f"**⚠️ Common Mistake**: {seed_pack['one_common_mistake']}\n")
            
            # Mini links (concept connections)
            mini_links = block.get("mini_links", [])
            if mini_links:
                md_lines.append("**Connections**:")
                for link in mini_links:
                    md_lines.append(f"- `{link['from']}` --[{link['rel']}]--> `{link['to']}`: {link['label']}")
                md_lines.append("")
            
            md_lines.append("---\n")
    
    # Concept Glossary
    md_lines.append("## 📚 Concept Glossary\n")
    concepts = data.get("concepts", [])
    
    for concept in concepts:
        md_lines.append(f"### {concept['name']}")
        
        if concept.get("aliases"):
            md_lines.append(f"*Also known as*: {', '.join(concept['aliases'])}")
        
        if concept.get("short_def"):
            md_lines.append(f"\n{concept['short_def']}\n")
        
        if concept.get("prerequisites"):
            md_lines.append(f"**Prerequisites**: {', '.join([f'`{p}`' for p in concept['prerequisites']])}")
        
        if concept.get("contrasts"):
            md_lines.append(f"**Contrasts with**: {', '.join([f'`{c}`' for c in concept['contrasts']])}")
        
        tags = concept.get("tags", [])
        if tags:
            md_lines.append(f"\n*Tags*: {', '.join(tags)}")
        
        md_lines.append("")
    
    # Relationship Graph
    md_lines.append("---\n")
    md_lines.append("## 🔗 Relationship Graph\n")
    
    relations = data.get("relations_graph", [])
    
    # Group by type
    rel_by_type = {}
    for rel in relations:
        rel_type = rel.get("type", "unknown")
        if rel_type not in rel_by_type:
            rel_by_type[rel_type] = []
        rel_by_type[rel_type].append(rel)
    
    for rel_type, rels in rel_by_type.items():
        md_lines.append(f"### {rel_type.replace('_', ' ').title()}\n")
        for rel in rels:
            confidence_icon = "🟢" if rel.get("confidence", 0) > 0.8 else "🟡" if rel.get("confidence", 0) > 0.5 else "🔴"
            md_lines.append(
                f"- {confidence_icon} `{rel['from']}` → `{rel['to']}`: {rel['label']} "
                f"*(confidence: {rel.get('confidence', 0):.2f})*"
            )
        md_lines.append("")
    
    # Top Contrasts (High Priority)
    if quality.get("top_contrasts"):
        md_lines.append("---\n")
        md_lines.append("## 🔥 Key Contrasts & Boundaries\n")
        md_lines.append("*(Critical for avoiding confusion)*\n")
        for contrast in quality['top_contrasts']:
            md_lines.append(f"- {contrast}")
        md_lines.append("")
    
    # Original Text Reference (optional)
    if original_text:
        md_lines.append("---\n")
        md_lines.append("## 📄 Original Text\n")
        md_lines.append("```")
        md_lines.append(original_text[:1000] + ("..." if len(original_text) > 1000 else ""))
        md_lines.append("```\n")
    
    return "\n".join(md_lines)


def generate_skeleton_card_only(data: Dict[str, Any]) -> str:
    """
    Generate minimal skeleton card view (for quick review).
    
    Args:
        data: Extracted knowledge dictionary
        
    Returns:
        Compact markdown with just skeleton cards
    """
    md_lines = []
    
    skeleton_cards = data.get("skeleton_cards", [])
    
    for card in skeleton_cards:
        md_lines.append(f"# {card['topic']}\n")
        
        blocks = card.get("blocks", [])
        
        for block in blocks:
            md_lines.append(f"## {block['title']}\n")
            
            # Just anchors and key links
            anchors = block.get("anchors", [])
            for anchor in anchors:
                md_lines.append(f"**{anchor}**")
            
            mini_links = block.get("mini_links", [])
            if mini_links:
                md_lines.append("")
                for link in mini_links:
                    md_lines.append(f"`{link['from']}` → `{link['to']}`")
            
            md_lines.append("\n---\n")
    
    return "\n".join(md_lines)
