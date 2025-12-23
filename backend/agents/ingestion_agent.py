"""
Ingestion Agent - High-Fidelity Multimodal Knowledge Structuring
===================================================================

ARCHITECTURAL ROLE:
    The FIRST agent in the learning pipeline. Transforms raw multimodal input
    (PDFs, images, handwritten notes, text) into pristine, structured knowledge
    artifacts that serve as the SINGLE SOURCE OF TRUTH for all downstream agents.

CORE PRINCIPLES:
    • FIDELITY > Brevity - preserve meaning exactly, never compress aggressively
    • STRUCTURE > Summary - organize knowledge, don't interpret it
    • COMPLETENESS > Convenience - include everything, even if verbose
    • NEUTRALITY > Pedagogy - extract, don't teach
    • DETERMINISM > Creativity - consistent output format every time

RESPONSIBILITIES:
    - Multimodal perception (PDFs, images, handwritten notes, text)
    - OCR when required (equations, diagrams, handwriting)
    - Faithful content extraction (zero hallucination tolerance)
    - Structural organization (concepts, definitions, examples, diagrams)
    - Produce machine-readable, deterministic knowledge artifact
    - Scale to 20-30 page documents via intelligent chunking

DOES NOT (ARCHITECTURAL BOUNDARIES):
    - Teach or explain concepts beyond source content
    - Simplify or paraphrase for pedagogical reasons
    - Judge correctness, importance, or relevance
    - Add examples, analogies, or external knowledge
    - Create embeddings or vector representations
    - Perform reasoning or inferenceThink like a LIBRARIAN cataloging a book, not a TEACHER explaining it.
"""

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
    Production-grade multimodal ingestion agent with high-fidelity extraction.
    
    WHY THIS MATTERS:
    If ingestion is weak, every downstream agent (Tutor, Game Master, Evaluator)
    operates on corrupted data. This is the foundation of the entire system.
    """
    
    # ============================================================================
    # CONFIGURATION CONSTANTS
    # ============================================================================
    
    # WHY: Gemini Flash supports ~1M input tokens, but we're conservative
    # to leave room for prompt overhead and response generation
    MAX_CHUNK_SIZE = 750000  # characters (~190k tokens with safety margin)
    
    # WHY: Minimum content threshold prevents silent failures
    MIN_OUTPUT_LENGTH = 100  # characters
    
    # WHY: Section headers must be exact for reliable extraction
    SECTION_HEADERS = {
        "concepts": "Core Concepts",
        "definitions": "Definitions",
        "examples": "Examples",
        "diagrams": "Diagram Descriptions",
        "markdown": "Clean Markdown Notes"
    }
    
    def __init__(self):
        super().__init__("IngestionAgent")
        self.model = gemini_flash()

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw multimodal input into structured knowledge artifact.
        
        INPUT CONTRACT:
        {
            "type": "text" | "image" | "pdf",
            "content": str  # raw text, base64 image, or base64 PDF
        }
        
        OUTPUT CONTRACT:
        {
            "core_concepts": List[str],       # Distinct concepts found
            "definitions": List[str],          # Term definitions, formulas
            "examples": List[str],             # Worked examples, use cases
            "diagram_descriptions": List[str], # Visual element descriptions
            "clean_markdown": str              # Structured narrative document
        }
        
        GUARANTEES:
        - Faithful extraction (no hallucination)
        - Consistent structure (deterministic format)
        - Complete preservation (no aggressive summarization)
        - Scales to 20-30 page documents
        """
        
        # ========================================================================
        # INPUT VALIDATION
        # ========================================================================
        # WHY: Fail fast with clear errors rather than silent corruption
        
        if not isinstance(input_data, dict):
            raise ValueError("input_data must be a dictionary")
        
        if 'type' not in input_data or 'content' not in input_data:
            raise ValueError("input_data must have 'type' and 'content' keys")
        
        input_type = input_data['type']
        content = input_data['content']
        
        if not content or (isinstance(content, str) and len(content.strip()) == 0):
            raise ValueError("content cannot be empty")
        
        # ========================================================================
        # MODALITY ROUTING
        # ========================================================================
        # WHY: Different input types require specialized processing strategies
        
        if input_type == 'image':
            result_text = await self._process_image(content)
        elif input_type == 'text':
            # WHY: Size-based routing for optimal performance
            if len(content) > self.MAX_CHUNK_SIZE:
                result_text = await self._process_large_text(content)
            else:
                result_text = await self._process_text(content)
        else:
            raise ValueError(
                f"Unsupported input type: {input_type}. "
                f"Must be 'text' or 'image'"
            )
        
        # ========================================================================
        # STRUCTURED EXTRACTION
        # ========================================================================
        # WHY: Parse LLM output into typed schema for downstream agents
        
        ingestion_result = IngestionResult(
            core_concepts=self._extract_section(result_text, self.SECTION_HEADERS["concepts"]),
            definitions=self._extract_section(result_text, self.SECTION_HEADERS["definitions"]),
            examples=self._extract_section(result_text, self.SECTION_HEADERS["examples"]),
            diagram_descriptions=self._extract_section(result_text, self.SECTION_HEADERS["diagrams"]),
            clean_markdown=result_text
        )
        
        # ========================================================================
        # OUTPUT VALIDATION
        # ========================================================================
        # WHY: Catch processing failures before they propagate downstream
        
        self._validate_output(ingestion_result)
        
        return ingestion_result.dict()

    
    # ============================================================================
    # IMAGE PROCESSING (Multimodal Perception + OCR)
    # ============================================================================
    
    async def _process_image(self, base64_content: str) -> str:
        """
        Process image input using multimodal vision + OCR capabilities.
        
        WHY: Images contain visual semantics (diagrams, spatial layout, handwriting)
        that text-only processing cannot capture. Requires specialized prompt.
        
        HANDLES:
        - Printed text (textbooks, slides, papers)
        - Handwritten notes (equations, diagrams, annotations)
        - Diagrams and charts (flows, graphs, illustrations)
        - Mixed content (text + visuals combined)
        """
        try:
            image_data = base64.b64decode(base64_content)
            image = Image.open(BytesIO(image_data))
        except Exception as e:
            raise ValueError(f"Failed to decode image: {str(e)}")
        
        # ========================================================================
        # HIGH-FIDELITY IMAGE EXTRACTION PROMPT
        # ========================================================================
        # WHY: This prompt encodes strict extraction principles:
        # - Complete OCR (no skipped text)
        # - Spatial awareness (layout preservation)
        # - Visual semantics (diagram understanding)
        # - Zero hallucination (extract only what's visible)
        
        prompt = f"""You are a HIGH-FIDELITY DOCUMENT PERCEPTION SYSTEM.

Your task is MULTIMODAL EXTRACTION ONLY - not teaching, not interpreting.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXTRACTION MANDATE (CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FIDELITY PRINCIPLES:
   • Extract EVERYTHING visible - no summarization, no selection
   • Preserve EXACT wording - no paraphrasing unless illegible
   • Maintain SPATIAL LAYOUT - top-to-bottom, left-to-right ordering
   • Describe VISUAL SEMANTICS - diagrams encode meaning through position

WHAT TO EXTRACT:
   ✓ ALL text (printed, handwritten, typed)
   ✓ ALL equations and mathematical notation (use LaTeX or Unicode)
   ✓ ALL code blocks and pseudocode
   ✓ ALL diagrams, charts, graphs, illustrations
   ✓ ALL tables and structured data
   ✓ ALL annotations, labels, captions
   ✓ ALL headings, subheadings, bullet points

DIAGRAM EXTRACTION (CRITICAL):
   When you see diagrams, charts, or visual elements:
   • Describe the TYPE (flowchart, graph, tree, etc.)
   • List all LABELS and TEXT within the visual
   • Describe ARROWS and connections (what connects to what)
   • Explain SPATIAL RELATIONSHIPS (above, below, branches to, leads to)
   • Note AXES labels if graph/chart
   • Include any COLOR coding if meaning is visual

HANDWRITING HANDLING:
   • Transcribe as accurately as possible
   • Use [illegible] for unreadable portions
   • Preserve sketched diagrams with text descriptions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABSOLUTE PROHIBITIONS (DO NOT VIOLATE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ DO NOT add explanations not present in the image
❌ DO NOT provide context or background knowledge
❌ DO NOT simplify technical content
❌ DO NOT skip sections or content (even if repetitive)
❌ DO NOT teach or clarify concepts
❌ DO NOT add examples not shown in the image
❌ DO NOT interpret or editorialize
❌ DO NOT guess at unclear content - state [unclear] or [illegible]

REMEMBER: You are a SCANNER, not a TEACHER.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT (MANDATORY - Use exact headers)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. {self.SECTION_HEADERS["concepts"]}
[List all distinct topics, technical terms, concepts, theorems mentioned]
- [One concept per line]
- [Extract verbatim from image - don't invent names]
- [Include ALL concepts, even if briefly mentioned]

## 2. {self.SECTION_HEADERS["definitions"]}
[List all explicit definitions, formulas, equations, technical terms defined]
- [Format: "Term: Definition" or "Formula: Expression"]
- [Use mathematical notation exactly as shown]
- [Include ALL definitions, even partial ones]

## 3. {self.SECTION_HEADERS["examples"]}
[List all examples, worked problems, use cases, code samples]
- [Include complete problem statements and solutions]
- [Preserve code/pseudocode formatting]
- [Extract ALL examples shown]

## 4. {self.SECTION_HEADERS["diagrams"]}
[Describe ALL visual elements: diagrams, charts, graphs, illustrations, tables]
- [For each visual element, describe:]
  - Type (flowchart, tree, graph, etc.)
  - All labels and text within it
  - Connections and arrows (what connects to what)
  - Spatial layout (what's above/below/beside what)
  - Any axes, legends, or keys

## 5. {self.SECTION_HEADERS["markdown"]}
[IMPORTANT: Do NOT just repeat sections 1-4 as bullet lists]
[Instead, create a COMPREHENSIVE, WELL-STRUCTURED markdown document]
[This is the detailed study material - organize it narratively]

STRUCTURE REQUIREMENTS:
• Use proper markdown headers (##, ###, ####) to organize topics
• Group related content together logically
• Include ALL text content from the image in narrative form
• Preserve the original ORDERING and FLOW from the image
• Use paragraphs, not just lists
• Include context and explanations AS THEY APPEAR in the image
• Format code blocks with ```
• Format equations with LaTeX or Unicode
• Preserve tables using markdown table syntax

CRITICAL: This section should be COMPLETE and READABLE - someone should be able
to learn from this markdown document alone, without seeing the original image.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Begin extraction now. Output ONLY the structured format above."""

        response = self.model.generate_content([prompt, image])
        return response.text

    
    # ============================================================================
    # TEXT PROCESSING (Structured Content Extraction)
    # ============================================================================
    
    async def _process_text(self, content: str) -> str:
        """
        Process text input with high-fidelity extraction.
        
        WHY: Text is already in machine-readable form, but requires structural
        organization and concept identification without loss of detail.
        
        HANDLES:
        - Plain text notes
        - Markdown documents
        - Extracted PDF text
        - Pasted content from various sources
        """
        
        # ========================================================================
        # HIGH-FIDELITY TEXT EXTRACTION PROMPT
        # ========================================================================
        
        prompt = f"""You are a HIGH-FIDELITY KNOWLEDGE STRUCTURING SYSTEM.

Your task is FAITHFUL EXTRACTION AND ORGANIZATION - not teaching, not interpreting.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXTRACTION MANDATE (CRITICAL)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FIDELITY PRINCIPLES:
   • COMPLETENESS - include ALL content, never summarize aggressively
   • ACCURACY - preserve exact wording, formulas, and technical terms
   • ORDERING - maintain the original logical flow and sequence
   • NEUTRALITY - organize without teaching or adding knowledge

WHAT TO EXTRACT:
   ✓ ALL concepts, topics, and technical terms
   ✓ ALL definitions, formulas, equations (preserve notation exactly)
   ✓ ALL examples, use cases, code samples, worked problems
   ✓ ALL theorems, proofs, algorithms
   ✓ ALL section structure and hierarchical relationships
   ✓ ALL tables, lists, and structured data

STRUCTURE PRESERVATION:
   • Identify the document's inherent organization
   • Preserve section hierarchies and relationships
   • Maintain connections between concepts
   • Keep examples near their corresponding concepts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ABSOLUTE PROHIBITIONS (DO NOT VIOLATE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ DO NOT add explanations not in the source
❌ DO NOT provide external context or background
❌ DO NOT simplify technical content for clarity
❌ DO NOT omit sections, examples, or details
❌ DO NOT paraphrase unnecessarily
❌ DO NOT teach, clarify, or editorialize
❌ DO NOT add your own examples or analogies
❌ DO NOT judge importance or relevance
❌ DO NOT compress content "for readability"

REMEMBER: Extract and organize. Never enhance or interpret.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HANDLING AMBIGUITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When source content is:
• Unclear → Preserve the ambiguity, don't clarify
• Incomplete → Note incompleteness, don't fill gaps
• Contradictory → Include both statements, don't resolve
• Technical → Preserve exactly, don't simplify

When you're uncertain about structure:
• Preserve the original format
• Default to maintaining source ordering
• Use neutral organizational headers

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT (MANDATORY - Use exact headers)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. {self.SECTION_HEADERS["concepts"]}
[Identify ALL distinct concepts, topics, and technical terms]
- [One concept per line - be exhaustive, not selective]
- [Extract names verbatim from source]
- [Include even briefly mentioned concepts]
- [Cover: main topics, subtopics, theorems, algorithms, data structures, etc.]

## 2. {self.SECTION_HEADERS["definitions"]}
[Extract ALL explicit definitions, formulas, equations, technical terms]
- [Format: "Term: Definition" OR use source's format]
- [Preserve mathematical notation EXACTLY (LaTeX, Unicode, or as written)]
- [Include ALL definitions, even informal ones]
- [Preserve formulas with all variables defined]

## 3. {self.SECTION_HEADERS["examples"]}
[Extract ALL examples, use cases, code samples, worked problems]
- [Include complete problem statements AND solutions]
- [Preserve code/pseudocode blocks with formatting]
- [Include use cases, scenarios, applications]
- [Extract ALL examples shown - none are too minor]

## 4. {self.SECTION_HEADERS["diagrams"]}
[Extract descriptions of ANY mentioned diagrams, figures, tables, visual elements]
- [If text references "see figure", "as shown in diagram", describe what it says about it]
- [Include ASCII art or text-based diagrams]
- [Describe tables in terms of structure and content]
- [Note: "No diagrams present" if none mentioned]

## 5. {self.SECTION_HEADERS["markdown"]}
[CRITICAL: Do NOT simply copy sections 1-4 as lists]
[Instead, create a COMPREHENSIVE, WELL-ORGANIZED markdown document]

REQUIREMENTS FOR THIS SECTION:
• Create a complete study document with proper narrative structure
• Use hierarchical headers (##, ###, ####) to organize content
• Group related concepts together logically
• Include ALL content from source in readable paragraph form
• Preserve the ORIGINAL ORDERING and FLOW from source
• Use bullet points, numbered lists, paragraphs as appropriate
• Format code blocks with ``` syntax
• Format equations using LaTeX $$ or inline $
• Create markdown tables for tabular data
• Use blockquotes for important notes or warnings

ORGANIZATION STRATEGY:
• Start with main topic/overview if present
• Follow source's section structure
• Group definitions near concepts they define
• Place examples after concepts they illustrate
• Maintain logical progression from source

COMPLETENESS CHECK:
Someone should be able to learn this material from your markdown alone,
without seeing the original source. Include ALL explanations, details,
and context present in the source.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT CONTENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{content}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Begin extraction now. Output ONLY the structured format above."""

        response = self.model.generate_content(prompt)
        return response.text

    
    # ============================================================================
    # LARGE DOCUMENT PROCESSING (Intelligent Chunking)
    # ============================================================================
    
    async def _process_large_text(self, content: str) -> str:
        """
        Process large documents (20-30 pages) via intelligent chunking.
        
        WHY: Large PDFs exceed context limits. Naive splitting destroys semantic
        coherence. Smart chunking on section boundaries preserves meaning.
        
        STRATEGY:
        1. Split on semantic boundaries (sections, pages, paragraphs)
        2. Process each chunk independently
        3. Merge results preserving structure
        4. Avoid breaking mid-concept or mid-example
        """
        
        print(f"📄 Large document detected ({len(content):,} characters). Chunking...")
        
        # Split into semantic chunks
        chunks = self._intelligent_chunk(content)
        
        print(f"📄 Split into {len(chunks)} chunks for processing")
        
        all_results = []
        
        for i, chunk in enumerate(chunks):
            print(f"  Processing chunk {i+1}/{len(chunks)}...")
            
            # ====================================================================
            # CHUNK-AWARE EXTRACTION PROMPT
            # ====================================================================
            # WHY: Each chunk is processed independently, but must maintain
            # consistent format and avoid assuming context from other chunks
            
            prompt = f"""You are a HIGH-FIDELITY KNOWLEDGE STRUCTURING SYSTEM processing a CHUNK of a larger document.

CONTEXT: This is chunk {i+1} of {len(chunks)} from a multi-part document.

CRITICAL INSTRUCTIONS:
• Process THIS CHUNK independently (no assumptions about other chunks)
• Extract EVERYTHING from this chunk - completeness within scope
• Maintain same quality and structure as single-document processing
• Do NOT add context or explanations beyond this chunk's content

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXTRACTION PRINCIPLES (SAME AS ALWAYS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Extract ALL content from this chunk
• Preserve exact wording and technical terms
• Maintain structure and ordering
• No teaching, no external knowledge
• No aggressive summarization

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT (MANDATORY - Use exact headers)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 1. {self.SECTION_HEADERS["concepts"]}
[All concepts in THIS CHUNK]
- [Extract verbatim - one per line]

## 2. {self.SECTION_HEADERS["definitions"]}
[All definitions in THIS CHUNK]
- [Preserve exact notation and wording]

## 3. {self.SECTION_HEADERS["examples"]}
[All examples in THIS CHUNK]
- [Include complete examples even if they span to next chunk]

## 4. {self.SECTION_HEADERS["diagrams"]}
[Any diagrams mentioned in THIS CHUNK]
- [Describe or note "No diagrams in this chunk"]

## 5. {self.SECTION_HEADERS["markdown"]}
[Comprehensive markdown document from THIS CHUNK]
[Use proper headers, paragraphs, and formatting]
[Include ALL content from this chunk in readable form]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHUNK CONTENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{chunk}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Begin extraction now. Output ONLY the structured format above."""
            
            response = self.model.generate_content(prompt)
            all_results.append(response.text)
        
        print(f"✅ All chunks processed. Merging results...")
        
        # Merge chunks while preserving structure
        merged = self._merge_chunks(all_results)
        
        print(f"✅ Large document processing complete")
        
        return merged
    
    def _intelligent_chunk(self, content: str) -> List[str]:
        """
        Split large content on semantic boundaries to preserve coherence.
        
        WHY: Arbitrary character splits can break:
        - Mid-equation
        - Mid-example
        - Mid-paragraph
        - Mid-concept
        
        Smart splitting on natural boundaries (sections, pages) maintains meaning.
        
        STRATEGY (Priority order):
        1. Split on page markers (from PDF extraction)
        2. Split on section headers (##, ###, etc.)
        3. Split on paragraph boundaries
        4. Last resort: hard character split with overlap
        """
        
        if not content or len(content) <= self.MAX_CHUNK_SIZE:
            return [content]
        
        chunks = []
        
        # ====================================================================
        # STRATEGY 1: Page-based chunking (best for PDFs)
        # ====================================================================
        # WHY: Page boundaries are natural semantic breaks
        
        if "--- Page" in content or "Page " in content[:500]:
            pages = re.split(r'\n?---\s*Page\s+\d+\s*---\n?', content, flags=re.IGNORECASE)
            
            current_chunk = ""
            for page in pages:
                if not page.strip():
                    continue
                
                # Accumulate pages until size limit
                if len(current_chunk) + len(page) < self.MAX_CHUNK_SIZE:
                    current_chunk += "\n\n" + page
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = page
            
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            if chunks:
                return chunks
        
        # ====================================================================
        # STRATEGY 2: Section-based chunking
        # ====================================================================
        # WHY: Markdown headers indicate logical section boundaries
        
        sections = re.split(r'\n(?=#{1,3} )', content)
        
        if len(sections) > 1:
            current_chunk = ""
            for section in sections:
                if not section.strip():
                    continue
                
                if len(current_chunk) + len(section) < self.MAX_CHUNK_SIZE:
                    current_chunk += "\n\n" + section
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = section
            
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            if chunks:
                return chunks
        
        # ====================================================================
        # STRATEGY 3: Paragraph-based chunking
        # ====================================================================
        # WHY: Paragraph boundaries are safer than mid-sentence splits
        
        paragraphs = content.split('\n\n')
        
        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) < self.MAX_CHUNK_SIZE:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # ====================================================================
        # STRATEGY 4: Hard split with overlap (last resort)
        # ====================================================================
        # WHY: Some documents have no natural boundaries. Use overlap to
        # prevent losing context at chunk boundaries.
        
        if not chunks or any(len(c) > self.MAX_CHUNK_SIZE for c in chunks):
            chunks = []
            overlap = 1000  # characters overlap between chunks
            pos = 0
            
            while pos < len(content):
                end = min(pos + self.MAX_CHUNK_SIZE, len(content))
                chunks.append(content[pos:end])
                pos = end - overlap if end < len(content) else end
        
        return chunks if chunks else [content]
    
    def _merge_chunks(self, chunk_results: List[str]) -> str:
        """
        Merge processed chunks into single coherent document.
        
        WHY: Downstream agents expect single unified artifact. Chunk boundaries
        are preserved for debugging but transparent to users.
        
        STRATEGY:
        - Clear chunk markers for debugging
        - Preserve all content
        - Maintain consistent structure
        """
        
        if not chunk_results:
            return ""
        
        if len(chunk_results) == 1:
            return chunk_results[0]
        
        merged = f"# Complete Document\n\n"
        merged += f"*Note: This document was processed in {len(chunk_results)} chunks for scale*\n\n"
        
        for i, chunk_result in enumerate(chunk_results):
            merged += f"\n\n<!-- ═══════════════════════════════════════════════════════ -->\n"
            merged += f"<!-- CHUNK {i+1} of {len(chunk_results)} -->\n"
            merged += f"<!-- ═══════════════════════════════════════════════════════ -->\n\n"
            merged += chunk_result
        
        return merged

    
    # ============================================================================
    # STRUCTURED SECTION EXTRACTION
    # ============================================================================
    
    def _extract_section(self, text: str, section_name: str) -> List[str]:
        """
        Robustly extract sections from LLM output with multiple fallback strategies.
        
        WHY: LLMs may format output inconsistently despite instructions.
        Multiple extraction patterns ensure we capture content regardless of
        minor formatting variations.
        
        STRATEGY:
        1. Try numbered headers (## 1. Section Name)
        2. Try plain headers (## Section Name)
        3. Try with/without colons
        4. Fallback to line-by-line extraction
        5. Return empty list rather than fail
        """
        
        # ====================================================================
        # PATTERN MATCHING (Multiple formats)
        # ====================================================================
        # WHY: Different LLM runs may format slightly differently
        
        patterns = [
            # Numbered header with period: ## 1. Section Name
            rf'##\s*\d+\.\s*{re.escape(section_name)}[:\s]*\n(.*?)(?=\n##\s*\d+\.|\Z)',
            # Plain header: ## Section Name
            rf'##\s*{re.escape(section_name)}[:\s]*\n(.*?)(?=\n##|\Z)',
            # With any heading level (##, ###)
            rf'#{2,3}\s*\d*\.?\s*{re.escape(section_name)}[:\s]*\n(.*?)(?=\n#{2,3}|\Z)',
            # Relaxed: any line containing section name followed by content
            rf'{re.escape(section_name)}[:\s]*\n(.*?)(?=\n[A-Z][a-z]+ [A-Z]|\Z)'
        ]
        
        section_content = None
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                section_content = match.group(1)
                break
        
        if not section_content:
            # Fallback extraction
            return self._fallback_extract(text, section_name)
        
        # ====================================================================
        # ITEM EXTRACTION (Bullet points, dashes, numbers)
        # ====================================================================
        # WHY: Content may be formatted as lists in various styles
        
        lines = section_content.strip().split('\n')
        items = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and meta-instructions
            if not line or line in ['', '(bullet list)', '(if present)', '(one per line)']:
                continue
            
            # Skip section headers that leaked in
            if line.startswith('##') or line.startswith('---'):
                continue
            
            # Remove common list markers
            cleaned = re.sub(r'^[-•*✓]\s*', '', line)
            cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
            cleaned = re.sub(r'^\[.*?\]\s*', '', cleaned)  # Remove [tags]
            cleaned = cleaned.strip()
            
            # Quality filter: skip noise and keep meaningful content
            if cleaned and len(cleaned) > 3 and not cleaned.startswith('['):
                items.append(cleaned)
        
        return items
    
    def _fallback_extract(self, text: str, section_name: str) -> List[str]:
        """
        Fallback extraction when regex patterns fail.
        
        WHY: Last resort to prevent data loss when LLM formats unexpectedly.
        Uses simple line-by-line scanning.
        
        STRATEGY:
        - Scan for section name
        - Collect lines until next section
        - Clean and filter items
        """
        lines = text.splitlines()
        collecting = False
        section = []
        
        for line in lines:
            # Detect section start (case-insensitive, flexible)
            if section_name.lower() in line.lower():
                if line.strip().startswith('#') or line.strip().endswith(':') or '##' in line:
                    collecting = True
                    continue
            
            # Collecting mode
            if collecting:
                # Stop at next major section
                if line.strip().startswith('##'):
                    if section_name.lower() not in line.lower():
                        break
                    else:
                        continue
                
                # Extract and clean
                cleaned = line.strip()
                
                # Skip meta-content and empty lines
                if not cleaned or cleaned in ['', '(bullet list)', '(if present)', '(one per line)']:
                    continue
                
                # Remove list markers
                cleaned = re.sub(r'^[-•*✓]\s*', '', cleaned)
                cleaned = re.sub(r'^\d+\.\s*', '', cleaned)
                cleaned = cleaned.strip()
                
                # Keep meaningful content
                if cleaned and len(cleaned) > 3:
                    section.append(cleaned)
        
        return section
    
    # ============================================================================
    # OUTPUT VALIDATION
    # ============================================================================
    
    def _validate_output(self, result: IngestionResult) -> None:
        """
        Validate that ingestion output meets minimum quality standards.
        
        WHY: Catch catastrophic failures early before they propagate to
        downstream agents (Tutor, Game Master, Evaluator).
        
        CHECKS:
        - Markdown content exists and has substance
        - At least some structured data extracted
        - Format integrity maintained
        
        DOES NOT:
        - Judge content quality or correctness
        - Evaluate pedagogical value
        - Check for completeness (that's subjective)
        """
        
        # ====================================================================
        # CRITICAL CHECKS (Fail fast)
        # ====================================================================
        
        if not result.clean_markdown:
            raise ValueError(
                "Ingestion failed: No markdown content produced. "
                "This indicates a processing failure."
            )
        
        if len(result.clean_markdown) < self.MIN_OUTPUT_LENGTH:
            raise ValueError(
                f"Ingestion produced insufficient content ({len(result.clean_markdown)} chars). "
                f"Minimum {self.MIN_OUTPUT_LENGTH} chars required. "
                "Possible causes: empty input, extraction failure, or prompt misinterpretation."
            )
        
        # ====================================================================
        # WARNING CHECKS (Log but don't fail)
        # ====================================================================
        # WHY: Some legitimate documents may lack certain sections
        # (e.g., pure theory without examples, no diagrams in text)
        
        if not result.core_concepts:
            print("⚠️  Warning: No core concepts extracted - check source content")
        
        if not result.definitions:
            print("⚠️  Warning: No definitions extracted - may be legitimate if source has none")
        
        if not result.examples:
            print("⚠️  Warning: No examples extracted - may be legitimate if source has none")
        
        # ====================================================================
        # QUALITY INDICATORS (Informational)
        # ====================================================================
        
        stats = {
            "concepts": len(result.core_concepts),
            "definitions": len(result.definitions),
            "examples": len(result.examples),
            "diagrams": len(result.diagram_descriptions),
            "markdown_chars": len(result.clean_markdown)
        }
        
        print(f"✅ Ingestion complete: {stats}")
