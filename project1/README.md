# Knowledge Extraction System

Automated knowledge extraction and compression for educational content using Shatalov-style methodology.

## 🎯 Purpose

Transform lengthy educational materials (lectures, textbook chapters, course notes) into compact, graph-based representations that preserve concept dependencies and enable fast review and reconstruction.

## ✨ Features

- **Adaptive Extraction**: Handles different content types (definitions, methods, theorems, examples, mistakes)
- **Shatalov Compression**: Creates skeleton cards with 5-7 blocks and 1-3 memory anchors per block
- **Relationship Graphs**: Extracts prerequisites, contrasts, examples, and connections
- **Dual Output**: JSON (machine-readable) + Markdown (human review)
- **Quality Validation**: Detects knowledge islands, missing prerequisites, constraint violations

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up API key
cp config/.env.example config/.env
# Edit config/.env and add your OPENAI_API_KEY
```

### 2. Run Extraction

```bash
# Basic extraction
python run_extraction.py --input tests/sample_inputs/calculus_lecture.txt

# With domain hint and markdown output
python run_extraction.py \
  --input lecture.txt \
  --domain math \
  --course "Calculus I" \
  --chapter "Limits and Continuity" \
  --markdown
```

### 3. Review Output

- **JSON**: `outputs/extraction.json` (machine-readable graph)
- **Markdown**: `outputs/extraction_review.md` (human review with skeleton cards)

## 📊 Output Structure

### JSON Schema

```json
{
  "meta": { "domain": "...", "course_title": "...", ... },
  "concepts": [ { "concept_id": "C1", "name": "...", "prerequisites": [...], ... } ],
  "meaning_units": [ { "unit_id": "U1", "type": "definition", "seeds": {...}, ... } ],
  "skeleton_cards": [ { "card_id": "S1", "topic": "...", "blocks": [...] } ],
  "relations_graph": [ { "type": "prerequisite", "from": "C1", "to": "C2", ... } ],
  "quality_checks": { "shatalov_constraint_ok": true, ... }
}
```

### Skeleton Cards

Each card contains 5-7 blocks with:
- **Anchors**: 1-3 short memory cues (2-5 words)
- **Seeds**: Minimal info to reconstruct the concept
- **Links**: Connections to prerequisites and contrasts

## 🧪 Testing

```bash
# Run on sample inputs
python run_extraction.py --input tests/sample_inputs/calculus_lecture.txt --markdown
python run_extraction.py --input tests/sample_inputs/programming_lecture.txt --markdown

# Compare outputs
ls -lh outputs/
```

## 🎨 Shatalov Methodology

Based on Viktor Shatalov's "supporting signals" (опорные сигналы):

1. **Compression**: One topic = 5-7 blocks
2. **Anchors**: Short associative cues (symbols, keywords, mini-diagrams)
3. **Structure**: Arrows/links over prose
4. **Reconstruction**: Students can rebuild understanding from anchors alone

## 🔧 Configuration

Edit `config/config.yaml`:

```yaml
llm:
  model: "gpt-4-turbo-preview"
  temperature: 0.1

extraction:
  max_blocks_per_card: 7
  min_anchors_per_block: 1
  prioritize_prerequisites: true
```

## 📁 Project Structure

```
.
├── extraction_engine/
│   ├── prompts.py              # Master extraction prompt
│   ├── schema.py               # Pydantic models
│   └── markdown_generator.py  # Human-readable output
├── llm_providers/
│   └── openai_provider.py      # GPT-4 integration
├── tests/
│   └── sample_inputs/          # Test materials
├── config/
│   ├── .env                    # API keys (not in git)
│   └── config.yaml             # System config
├── outputs/                    # Generated files
└── run_extraction.py           # Main CLI
```

## 💰 Cost Estimation

The system estimates costs before extraction:

```
Estimated cost: $0.1234
  Input tokens: ~8,000
  Output tokens: ~16,000
```

GPT-4 Turbo: ~$0.01/1K input + ~$0.03/1K output

## 🎓 Example Use Cases

1. **Textbook Compression**: Extract one chapter → skeleton card for review
2. **Lecture Notes**: Transform 50-page lecture → graph of 20 concepts
3. **Prerequisite Mapping**: Visualize what you need to know before learning X
4. **Mistake Documentation**: Collect common pitfalls and boundaries

## 🐛 Troubleshooting

**Schema validation errors**:
- Check that skeleton cards have 5-7 blocks
- Verify anchors are short (2-5 words)

**Knowledge islands warning**:
- Some concepts have no links → review relationships manually

**Missing API key**:
```bash
export OPENAI_API_KEY="your-key-here"
# or add to config/.env
```

## 📝 License

MIT
