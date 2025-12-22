import base64
import re
from io import BytesIO
from typing import Dict, List, Any
from PIL import Image

from core.agent_base import Agent
from core.ingestion_schema import IngestionResult
from services.gemini_client import gemini_flash


class IngestionAgent(Agent):
    """
    Multimodal ingestion agent for extracting and structuring learning materials.
    
    Responsibilities:
    - Faithfully extract content from PDFs, images, and text
    - Perform OCR when needed
    - Structure knowledge for downstream agents
    
    DOES NOT:
    - Teach or explain concepts
    - Add external knowledge
    - Create embeddings or memories
    - Judge correctness or importance
    """
    
    # WHY: Token limits for Gemini 2.0 Flash (~1M input tokens, but being conservative)
    # Large PDFs need chunking to avoid context overflow
    MAX_CHUNK_SIZE = 800000  # characters (~200k tokens)
    
    def __init__(self):
        super().__init__("IngestionAgent")
        self.model = gemini_flash()

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input and return structured learning content.
        
        Args:
            input_data: {
                "type": "text" | "image",
                "content": str (raw text OR base64 for images)
            }
            
        Returns:
            IngestionResult as dict with core_concepts, definitions, examples, 
            diagram_descriptions, and clean_markdown
        """
        
        # WHY: Type validation prevents silent failures downstream
        if not isinstance(input_data, dict) or 'type' not in input_data or 'content' not in input_data:
            raise ValueError("input_data must have 'type' and 'content' keys")
        
        input_type = input_data['type']
        content = input_data['content']
        
        # WHY: Different modalities require different processing strategies
        if input_type == 'image':
            result_text = await self._process_image(content)
        elif input_type == 'text':
            # WHY: Large documents must be chunked to fit in context window
            if len(content) > self.MAX_CHUNK_SIZE:
                result_text = await self._process_large_text(content)
            else:
                result_text = await self._process_text(content)
        else:
            raise ValueError(f"Unsupported input type: {input_type}")
        
        # WHY: Robust extraction handles various LLM output formats
        # Fallback to full text prevents data loss if extraction fails
        ingestion_result = IngestionResult(
            core_concepts=self._extract_section(result_text, "Core Concepts"),
            definitions=self._extract_section(result_text, "Definitions"),
            examples=self._extract_section(result_text, "Examples"),
            diagram_descriptions=self._extract_section(result_text, "Diagram Descriptions"),
            clean_markdown=result_text
        )
        
        # WHY: Validation ensures downstream agents receive usable data
        self._validate_output(ingestion_result)
        
        return ingestion_result.dict()

    async def _process_image(self, base64_content: str) -> str:
        """
        Process image input using multimodal capabilities.
        
        WHY: Images require OCR and visual understanding that text prompts alone cannot provide.
        """
        try:
            image_data = base64.b64decode(base64_content)
            image = Image.open(BytesIO(image_data))
        except Exception as e:
            raise ValueError(f"Failed to decode image: {e}")
        
        # WHY: Explicit prompt constraints prevent agent from teaching or explaining
        # Emphasis on COMPLETENESS prevents aggressive summarization
        prompt = """You are a DOCUMENT INGESTION AGENT performing multimodal perception ONLY.

YOUR ROLE:
• Extract ALL learning material from this image faithfully
• Perform OCR on text, equations, code, diagrams
• Describe visual elements (charts, diagrams, illustrations)
• Preserve order and hierarchical structure

ABSOLUTE PROHIBITIONS:
• DO NOT explain concepts beyond what's visible
• DO NOT add context, background, or external knowledge
• DO NOT simplify or paraphrase excessively
• DO NOT judge importance or skip content
• DO NOT teach or tutor

COMPLETENESS REQUIREMENT:
• Include EVERYTHING visible in the image
• Preserve technical terms, equations, formulas exactly
• Describe diagrams/charts in detail (labels, axes, relationships)
• Maintain the original sequence of information

OUTPUT FORMAT (MANDATORY - Use exact section headers):

## 1. Core Concepts
- [Extract all main topics, keywords, technical terms]
- [One bullet per concept]

## 2. Definitions
- [Extract all explicit definitions, formulas, equations]
- [Format: "Term: Definition" or "Formula: Expression"]

## 3. Examples
- [Extract all examples, use cases, scenarios, sample problems]
- [Include worked solutions if present]

## 4. Diagram Descriptions
- [Describe all visual elements: charts, graphs, diagrams, illustrations]
- [Include labels, axes, arrows, relationships shown]

## 5. Clean Markdown Notes
[IMPORTANT: Do NOT repeat sections 1-4 here]
[Instead, provide a well-organized, comprehensive markdown document]
[Structure with proper headers (##, ###), paragraphs, and explanations]
[This is the detailed, readable version - organize by topics/themes, not as lists]
[Include all context, explanations, and details in narrative form]
"""
        
        response = self.model.generate_content([prompt, image])
        return response.text

    async def _process_text(self, content: str) -> str:
        """
        Process text input (including extracted PDF text).
        
        WHY: Text processing uses different strategies than image processing.
        """
        
        # WHY: Explicit constraints prevent hallucination and over-summarization
        # Multiple examples of "DO NOT" reinforce the boundary
        prompt = f"""You are a DOCUMENT INGESTION AGENT performing content structuring ONLY.

YOUR ROLE:
• Extract and structure ALL learning material from the provided text
• Preserve technical accuracy, terminology, and detail
• Maintain the original order and logical flow
• Identify and organize key learning elements

ABSOLUTE PROHIBITIONS:
• DO NOT explain concepts beyond what's in the source
• DO NOT add external knowledge, context, or examples
• DO NOT simplify technical content or paraphrase unnecessarily
• DO NOT omit details, examples, or sections
• DO NOT teach, interpret, or editorialize
• DO NOT summarize aggressively - preserve completeness

COMPLETENESS REQUIREMENT:
• Include ALL concepts, definitions, and examples from source
• Preserve ALL technical terms, formulas, and code exactly
• Maintain ALL section structure and ordering from source
• If uncertain about structure, preserve the original format

OUTPUT FORMAT (MANDATORY - Use exact section headers):

## 1. Core Concepts
- [List all main topics, keywords, technical terms, theorems]
- [One concept per bullet - be exhaustive, not selective]

## 2. Definitions
- [List all explicit definitions, formulas, equations, technical terms]
- [Format: "Term: Definition" or use the source's format]
- [Include mathematical notation exactly as given]

## 3. Examples
- [List all examples, use cases, code samples, worked problems]
- [Include all problem-solution pairs]
- [Preserve code/pseudocode blocks]

## 4. Diagram Descriptions
- [If text mentions diagrams, figures, or visual elements, describe them]
- [Include any ASCII art, tables, or structured layouts]

## 5. Clean Markdown Notes
[CRITICAL: Do NOT simply repeat the bullet lists from sections 1-4]
[Instead, create a well-structured, comprehensive markdown document]
[Organize content with clear headers (##, ###), paragraphs, and explanations]
[Present information in narrative/explanatory form with proper context]
[Group related concepts together logically]
[This is the detailed study material - make it readable and well-organized]

INPUT CONTENT:
{content}
"""
        
        response = self.model.generate_content(prompt)
        return response.text

    async def _process_large_text(self, content: str) -> str:
        """
        Process large documents by chunking intelligently.
        
        WHY: Large PDFs (5-10 pages) can exceed context limits.
        Chunking by sections preserves semantic coherence better than arbitrary splits.
        """
        
        # WHY: Split on likely section boundaries to maintain coherence
        # Prefer splitting on headers, double newlines, or page markers
        chunks = self._intelligent_chunk(content)
        
        all_results = []
        
        for i, chunk in enumerate(chunks):
            print(f"Processing chunk {i+1}/{len(chunks)}...")
            
            # WHY: Same constraints apply per chunk, but note this is partial content
            prompt = f"""You are a DOCUMENT INGESTION AGENT processing a PORTION of a larger document.

YOUR ROLE:
• Extract and structure ALL learning material from THIS CHUNK
• This is part {i+1} of {len(chunks)} - process independently
• Maintain completeness within this chunk

PROHIBITIONS:
• DO NOT add external knowledge
• DO NOT explain beyond source content
• DO NOT omit details from this chunk
• DO NOT assume context from other chunks

OUTPUT FORMAT (same structure):

## 1. Core Concepts
- [All concepts in this chunk]

## 2. Definitions
- [All definitions in this chunk]

## 3. Examples
- [All examples in this chunk]

## 4. Diagram Descriptions
- [Any diagrams mentioned in this chunk]

## 5. Clean Markdown Notes
[IMPORTANT: Do NOT repeat sections 1-4 as lists]
[Provide well-structured narrative content from this chunk]
[Use headers and paragraphs, not bullet repetition]

CHUNK CONTENT:
{chunk}
"""
            
            response = self.model.generate_content(prompt)
            all_results.append(response.text)
        
        # WHY: Merge all chunks with clear boundaries for downstream processing
        merged = self._merge_chunks(all_results)
        return merged

    def _intelligent_chunk(self, content: str) -> List[str]:
        """
        Split large content on semantic boundaries.
        
        WHY: Splitting on headers/sections preserves context better than character limits.
        Fallback to size-based chunking prevents infinite chunks.
        """
        chunks = []
        
        # WHY: Try to split on page markers first (from PDF extraction)
        if "--- Page" in content:
            pages = re.split(r'\n--- Page \d+ ---\n', content)
            # WHY: Group pages if individual pages are small
            current_chunk = ""
            for page in pages:
                if len(current_chunk) + len(page) < self.MAX_CHUNK_SIZE:
                    current_chunk += page + "\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = page + "\n"
            if current_chunk:
                chunks.append(current_chunk)
        else:
            # WHY: Fallback to section-based splitting
            sections = re.split(r'\n(?=#{1,3} )', content)
            current_chunk = ""
            for section in sections:
                if len(current_chunk) + len(section) < self.MAX_CHUNK_SIZE:
                    current_chunk += section
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = section
            if current_chunk:
                chunks.append(current_chunk)
        
        # WHY: Safety check - if still too large, use hard splits
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > self.MAX_CHUNK_SIZE:
                # Hard split on paragraphs
                parts = chunk.split('\n\n')
                temp = ""
                for part in parts:
                    if len(temp) + len(part) < self.MAX_CHUNK_SIZE:
                        temp += part + "\n\n"
                    else:
                        if temp:
                            final_chunks.append(temp)
                        temp = part + "\n\n"
                if temp:
                    final_chunks.append(temp)
            else:
                final_chunks.append(chunk)
        
        return final_chunks if final_chunks else [content]

    def _merge_chunks(self, chunk_results: List[str]) -> str:
        """
        Merge processed chunks while preserving structure.
        
        WHY: Downstream agents need a single coherent document.
        Clear chunk boundaries help with debugging.
        """
        merged = "# Complete Document (Merged from Multiple Chunks)\n\n"
        
        for i, chunk in enumerate(chunk_results):
            merged += f"\n<!-- CHUNK {i+1} START -->\n"
            merged += chunk
            merged += f"\n<!-- CHUNK {i+1} END -->\n\n"
        
        return merged

    def _extract_section(self, text: str, section_name: str) -> List[str]:
        """
        Robustly extract sections from LLM output with multiple fallback strategies.
        
        WHY: LLMs may format output inconsistently. Multiple patterns ensure extraction works.
        Regex is more reliable than simple string matching for structured output.
        """
        
        # WHY: Try multiple section header patterns (numbered, plain, with colons)
        patterns = [
            rf'## \d+\.\s*{re.escape(section_name)}[:\s]*\n(.*?)(?=\n## \d+\.|\Z)',
            rf'##\s*{re.escape(section_name)}[:\s]*\n(.*?)(?=\n##|\Z)',
            rf'#{2,3}\s*\d*\.?\s*{re.escape(section_name)}[:\s]*\n(.*?)(?=\n#{2,3}|\Z)',
        ]
        
        section_content = None
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                section_content = match.group(1)
                break
        
        if not section_content:
            # WHY: Fallback to simple line-by-line extraction
            return self._fallback_extract(text, section_name)
        
        # WHY: Extract bullet points or dashed items
        # Support various list formats: "- ", "* ", "• ", or numbered
        lines = section_content.strip().split('\n')
        items = []
        
        for line in lines:
            line = line.strip()
            # WHY: Filter out empty lines and markdown artifacts
            if not line or line in ['', '(bullet list)', '(if present)', '(structured markdown)']:
                continue
            
            # WHY: Clean various bullet point formats
            # Don't strip too aggressively - preserve mathematical symbols and special chars
            cleaned = re.sub(r'^[-•*]\s*', '', line)
            cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
            cleaned = cleaned.strip()
            
            if cleaned and len(cleaned) > 2:  # WHY: Filter noise
                items.append(cleaned)
        
        return items

    def _fallback_extract(self, text: str, section_name: str) -> List[str]:
        """
        Fallback extraction when regex fails.
        
        WHY: Last resort to prevent data loss when LLM formats unexpectedly.
        """
        lines = text.splitlines()
        collecting = False
        section = []
        
        for line in lines:
            # WHY: Case-insensitive matching with flexible formatting
            if section_name.lower() in line.lower() and (line.strip().startswith('#') or line.strip().endswith(':')):
                collecting = True
                continue
            
            if collecting:
                # WHY: Stop at next section header
                if line.strip().startswith('##') and section_name.lower() not in line.lower():
                    break
                
                # WHY: Extract actual content, skip empty lines
                cleaned = line.strip()
                if cleaned and not cleaned in ['', '(bullet list)', '(if present)']:
                    # Remove bullet markers
                    cleaned = re.sub(r'^[-•*]\s*', '', cleaned)
                    cleaned = re.sub(r'^\d+\.\s*', '', cleaned).strip()
                    if cleaned and len(cleaned) > 2:
                        section.append(cleaned)
        
        return section

    def _validate_output(self, result: IngestionResult) -> None:
        """
        Validate that output meets minimum quality standards.
        
        WHY: Catch catastrophic failures early before they propagate downstream.
        Log warnings for empty sections to help debug extraction issues.
        """
        
        # WHY: At least the markdown should always have content
        if not result.clean_markdown or len(result.clean_markdown) < 50:
            raise ValueError("Ingestion produced insufficient content - possible processing failure")
        
        # WHY: Log warnings for empty critical sections (but don't fail - some docs lack examples)
        if not result.core_concepts:
            print("⚠️  Warning: No core concepts extracted")
        
        if not result.definitions:
            print("⚠️  Warning: No definitions extracted")
