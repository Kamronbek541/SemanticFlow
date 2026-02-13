#!/usr/bin/env python3
"""
Main CLI for running knowledge extraction.
Usage: python run_extraction.py --input lecture.txt --output knowledge.json
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv

# Try importing pypdf for PDF support
try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_providers.openai_provider import OpenAIProvider
from extraction_engine.schema import ExtractionOutput
from extraction_engine.markdown_generator import generate_markdown_review, generate_skeleton_card_only
from extraction_engine.chunker import chunk_text, merge_extractions, estimate_tokens


def main():
    parser = argparse.ArgumentParser(description="Extract knowledge from educational content")
    parser.add_argument("--input", "-i", required=True, help="Input text file")
    parser.add_argument("--output", "-o", help="Output JSON file (default: outputs/extraction.json)")
    parser.add_argument("--domain", "-d", help="Domain hint (e.g., math, programming, physics)")
    parser.add_argument("--course", help="Course title")
    parser.add_argument("--chapter", help="Chapter title")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model to use (default: gpt-4o-mini)")
    parser.add_argument("--markdown", "-m", action="store_true", help="Generate markdown review")
    parser.add_argument("--skeleton-only", action="store_true", help="Generate skeleton card only (minimal view)")
    parser.add_argument("--max-chunk-tokens", type=int, default=12000,
                        help="Max tokens per chunk for large documents (default: 12000)")
    parser.add_argument("--limit-pages", type=int, help="Limit number of pages to process (PDF only)")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv("config/.env")
    
    # 1. Read Input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return

    print(f"📖 Reading input from: {input_path}")
    
    text = ""
    if input_path.suffix.lower() == ".pdf":
        if not HAS_PYPDF:
            print("❌ Error: pypdf is not installed. Install it with: pip install pypdf")
            return
        
        try:
            reader = PdfReader(input_path)
            total_pages = len(reader.pages)
            limit = args.limit_pages if args.limit_pages else total_pages
            
            print(f"   PDF has {total_pages} pages. Extracting text from first {limit} pages...")
            
            pdf_text = []
            for i in range(min(limit, total_pages)):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    pdf_text.append(page_text)
            
            text = "\n\n".join(pdf_text)
            print(f"   ✅ Extracted {len(text)} characters from PDF.")
            
        except Exception as e:
            print(f"❌ Error reading PDF: {e}")
            return
    else:
        # Assume text file
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            # Fallback to latin-1 if utf-8 fails
            with open(input_path, "r", encoding="latin-1") as f:
                text = f.read()

    if not text.strip():
        print("❌ Error: Input file is empty or text could not be extracted.")
        return
    
    word_count = len(text.split())
    token_est = estimate_tokens(text)
    print(f"📊 Input size: {len(text)} characters, {word_count} words (~{token_est} tokens)\n")
    
    # Initialize provider
    try:
        provider = OpenAIProvider(model=args.model)
    except ValueError as e:
        print(f"❌ {e}")
        print("💡 Make sure OPENAI_API_KEY is set in config/.env")
        sys.exit(1)
    
    # Split into chunks if needed
    chunks = chunk_text(text, max_tokens=args.max_chunk_tokens)
    num_chunks = len(chunks)
    
    if num_chunks > 1:
        print(f"\n📦 Document split into {num_chunks} chunks for processing\n")
    
    # Process each chunk
    all_extractions = []
    total_start = time.time()
    
    for i, (chunk_text_data, start_char, end_char) in enumerate(chunks):
        if num_chunks > 1:
            print(f"\n{'='*60}")
            print(f"📄 Processing chunk {i+1}/{num_chunks} (chars {start_char}-{end_char})")
            print(f"{'='*60}\n")
        
        # Estimate cost for this chunk
        cost_estimate = provider.estimate_cost(chunk_text_data)
        print(f"💰 Estimated cost for this chunk: ${cost_estimate['total_cost_usd']:.4f}")
        print(f"   Input tokens: ~{cost_estimate['input_tokens']}")
        print(f"   Output tokens: ~{cost_estimate['output_tokens']}\n")
        
        # Run extraction
        try:
            extracted_data = provider.extract(
                text=chunk_text_data,
                domain_hint=args.domain,
                course_title=args.course,
                chapter_title=args.chapter
            )
            all_extractions.append(extracted_data)
        except Exception as e:
            print(f"❌ Extraction failed for chunk {i+1}: {e}")
            if num_chunks > 1:
                print("⚠️ Skipping this chunk and continuing...")
                continue
            else:
                sys.exit(1)
        
        # Rate limit pause between chunks
        if i < num_chunks - 1:
            wait_time = 5
            print(f"\n⏳ Waiting {wait_time}s before next chunk (rate limit)...")
            time.sleep(wait_time)
    
    if not all_extractions:
        print("❌ No chunks were successfully extracted")
        sys.exit(1)
    
    # Merge if multiple chunks
    if len(all_extractions) > 1:
        print(f"\n{'='*60}")
        print(f"🔗 Merging {len(all_extractions)} chunk extractions...")
        print(f"{'='*60}")
        extracted_data = merge_extractions(all_extractions)
    else:
        extracted_data = all_extractions[0]
    
    total_time = time.time() - total_start
    
    # Validate schema
    print("\n🔍 Validating output schema...")
    try:
        validated = ExtractionOutput(**extracted_data)
        print("✅ Schema validation passed")
    except Exception as e:
        print(f"⚠️ Schema validation warning: {e}")
        print("Continuing with raw output...")
    
    # Save JSON
    output_path = Path(args.output) if args.output else Path("outputs/extraction.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n💾 Saving JSON to: {output_path}")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
    
    # Generate markdown if requested
    md_path = None
    if args.markdown or args.skeleton_only:
        if args.skeleton_only:
            markdown_content = generate_skeleton_card_only(extracted_data)
            md_name = output_path.stem + "_skeleton.md"
        else:
            markdown_content = generate_markdown_review(extracted_data, original_text=text[:2000])
            md_name = output_path.stem + "_review.md"
        
        md_path = output_path.parent / md_name
        print(f"📝 Saving markdown to: {md_path}")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
    
    # Summary
    print(f"\n{'='*60}")
    print("✅ EXTRACTION COMPLETE")
    print(f"{'='*60}")
    
    quality = extracted_data.get("quality_checks", {})
    coverage = quality.get("coverage_estimate", {})
    
    print(f"⏱️  Total time: {total_time:.1f}s")
    print(f"📊 Extracted:")
    print(f"   - {coverage.get('major_concepts', 0)} concepts")
    print(f"   - {coverage.get('major_methods', 0)} methods/procedures")
    print(f"   - {coverage.get('major_mistakes', 0)} common mistakes")
    print(f"   - {len(extracted_data.get('skeleton_cards', []))} skeleton cards")
    print(f"   - {len(extracted_data.get('meaning_units', []))} meaning units")
    print(f"   - {len(extracted_data.get('relations_graph', []))} relationships")
    
    if num_chunks > 1:
        print(f"   - Processed in {num_chunks} chunks")
    
    if quality.get("knowledge_islands"):
        print(f"\n⚠️ Found {len(quality['knowledge_islands'])} knowledge islands (disconnected concepts)")
    
    if quality.get("shatalov_constraint_ok"):
        print("\n✅ Shatalov constraints satisfied (5-7 blocks per card)")
    else:
        print("\n⚠️ Shatalov constraints violated")
    
    print(f"\n📁 Output files:")
    print(f"   - JSON: {output_path}")
    if md_path:
        print(f"   - Markdown: {md_path}")
    
    print("\n🎉 Done!")


if __name__ == "__main__":
    main()
