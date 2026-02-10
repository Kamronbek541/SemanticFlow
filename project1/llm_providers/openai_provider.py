"""
OpenAI GPT-4 provider for knowledge extraction.
"""

import os
import json
from typing import Optional
from openai import OpenAI
from extraction_engine.prompts import MASTER_EXTRACTION_PROMPT, build_extraction_request


class OpenAIProvider:
    """OpenAI GPT-4 integration for extraction."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key (reads from env if not provided)
            model: Model to use (default: gpt-4o-mini, supports 16K output)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
    
    def extract(
        self,
        text: str,
        domain_hint: Optional[str] = None,
        course_title: Optional[str] = None,
        chapter_title: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> dict:
        """
        Extract knowledge from educational text.
        
        Args:
            text: Educational content to extract from
            domain_hint: Optional domain (e.g., "math", "programming")
            course_title: Optional course title
            chapter_title: Optional chapter title
            temperature: Sampling temperature (lower = more deterministic)
            max_tokens: Maximum tokens in response
            
        Returns:
            Extracted knowledge as dictionary
        """
        user_message = build_extraction_request(
            text=text,
            domain_hint=domain_hint,
            course_title=course_title,
            chapter_title=chapter_title
        )
        
        print(f"🔄 Calling OpenAI {self.model}...")
        print(f"📊 Input length: {len(text)} chars")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": MASTER_EXTRACTION_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            result = response.choices[0].message.content
            
            # Parse and validate JSON
            extracted_data = json.loads(result)
            
            print(f"✅ Extraction complete")
            print(f"📈 Extracted {len(extracted_data.get('concepts', []))} concepts")
            print(f"📈 Extracted {len(extracted_data.get('meaning_units', []))} meaning units")
            print(f"📈 Extracted {len(extracted_data.get('skeleton_cards', []))} skeleton cards")
            
            return extracted_data
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Response: {result[:500]}...")
            raise
        except Exception as e:
            print(f"❌ Extraction failed: {e}")
            raise
    
    def estimate_cost(self, text: str) -> dict:
        """
        Estimate extraction cost.
        
        Args:
            text: Input text
            
        Returns:
            Cost estimate dict with input/output tokens and USD cost
        """
        # Rough estimate: ~1 token per 4 characters
        input_tokens = len(MASTER_EXTRACTION_PROMPT + text) // 4
        output_tokens = 4096  # Max output
        
        # GPT-4o-mini pricing (very cheap)
        input_cost_per_1k = 0.00015
        output_cost_per_1k = 0.0006
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        total_cost = input_cost + output_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost_usd": round(input_cost, 4),
            "output_cost_usd": round(output_cost, 4),
            "total_cost_usd": round(total_cost, 4)
        }
