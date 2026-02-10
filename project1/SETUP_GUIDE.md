# Quick Setup Guide

## 1. Install Dependencies

```bash
cd "/Users/kamronbekjurabaev/Desktop/Project_1_Internship Andrey Ustuzhanin"
pip install -r requirements.txt
```

## 2. Add Your OpenAI API Key

Edit `config/.env` and add your API key:

```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

## 3. Run Your First Extraction

```bash
# Test on the sample calculus lecture
python run_extraction.py \
  --input tests/sample_inputs/calculus_lecture.txt \
  --domain math \
  --course "Calculus I" \
  --chapter "Limits and Continuity" \
  --markdown

# Output will be in:
# - outputs/extraction.json (machine-readable graph)
# - outputs/extraction_review.md (human-readable skeleton cards)
```

## 4. Review the Results

Open `outputs/extraction_review.md` to see:
- Extracted concepts with prerequisites and contrasts
- Shatalov skeleton cards (5-7 blocks with memory anchors)
- Relationship graph
- Quality checks (knowledge islands, missing prerequisites)

## 5. Extract Your Own Materials

```bash
# For any text file:
python run_extraction.py --input your_lecture.txt --markdown

# Specify output location:
python run_extraction.py \
  --input your_notes.txt \
  --output my_extraction.json \
  --markdown
```

## Example Workflow

### Step 1: Prepare Your Course Content
Save a chapter or lecture as a `.txt` file (plain text only)

### Step 2: Extract Knowledge
```bash
python run_extraction.py --input chapter1.txt --domain programming --markdown
```

### Step 3: Review Skeleton Cards
Open the markdown file and review the extracted:
- Key concepts and definitions
- Prerequisites (what you need to know first)
- Contrasts (boundaries and failure cases)
- Common mistakes

### Step 4: Study from Skeleton Cards
Use the anchors and seed packs to reconstruct understanding without rereading the full text

### Step 5: Iterate
If extraction quality is poor:
- Provide more specific domain hints
- Split very long chapters into sections
- Adjust the prompt in `extraction_engine/prompts.py`

## Cost Expectations

For a typical 10-page chapter (~5,000 words):
- Input tokens: ~8,000
- Output tokens: ~12,000
- Cost: ~$0.08 - $0.15 per chapter

## Next Steps

1. **Test on your actual course materials**  
   Try different subjects (math, CS, physics, history)
   
2. **Experiment with prompt refinements**  
   Edit `extraction_engine/prompts.py` to improve extraction quality
   
3. **Build your compressed knowledge base**  
   Store all extracted JSON files for later review and linking
   
4. **Create visualizations**  
   Use the JSON output to build prerequisite graphs and concept maps
