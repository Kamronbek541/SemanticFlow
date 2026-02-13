import json
import os
import argparse
from pathlib import Path

def generate_viewer():
    """Injects extraction.json into viewer_template.html to create a standalone HTML file."""
    
    parser = argparse.ArgumentParser(description="Generate HTML viewer for knowledge graph")
    parser.add_argument("--input", "-i", type=str, default="outputs/extraction.json",
                        help="Path to input JSON extraction file")
    args = parser.parse_args()
    
    # Paths
    base_dir = Path(__file__).parent
    
    # Handle input path (absolute or relative)
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = base_dir / args.input
        
    template_path = base_dir / "templates" / "viewer_template.html"
    
    # Output file name based on input filename
    output_name = input_path.stem + "_view.html"
    output_html_path = input_path.parent / output_name

    print(f"📖 Reading data from: {input_path}")
    
    if not input_path.exists():
        print(f"❌ Error: JSON file not found at {input_path}")
        return

    if not template_path.exists():
        print(f"❌ Error: Template file not found at {template_path}")
        return

    # Read Data
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Read Template
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Inject Data (Dump JSON to string)
    json_str = json.dumps(data, indent=None) # Compact JSON
    final_html = template.replace("{{DATA_PLACEHOLDER}}", json_str)

    # Write Output
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"✅ Generated standalone viewer: {output_html_path}")
    print(f"🚀 Open this file in your browser to explore the knowledge graph!")

if __name__ == "__main__":
    generate_viewer()
