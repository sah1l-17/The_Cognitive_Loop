"""
Game Master Agent - Gamified Active Recall Generator

Supported Game Types:
1. Swipe-Sort: Binary classification (left/right categories)
2. Find-the-Impostor: Boundary testing (3 genuine + 1 impostor)
3. Match-Pairs: Vocabulary and relationship testing
"""

import json
import re
from typing import Dict, Any, List
from core.agent_base import Agent
from services.gemini_client import gemini_flash


class GameMasterAgent(Agent):
    """
    Stateless game generation agent.
    Generates procedural active-recall games based on concept + nuances.
    """
    
    # Architectural constants
    SUPPORTED_GAME_TYPES = ["swipe_sort", "impostor", "match_pairs"]
    
    # Game difficulty parameters
    SWIPE_SORT_CARD_RANGE = (8, 12)  # Min/max cards
    IMPOSTOR_OPTIONS_COUNT = 4
    MATCH_PAIRS_RANGE = (5, 8)  # Min/max pairs
    
    def __init__(self):
        super().__init__("GameMasterAgent")
        self.model = gemini_flash()
    
    # ============================================================================
    # CORE PUBLIC INTERFACE
    # ============================================================================
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a single active-recall game based on concept and game type.
        
        INPUT CONTRACT:
        {
            "concept": str,           # Concept name (already understood)
            "nuances": List[str],     # Edge cases, weak points, boundaries
            "game_type": str          # One of: swipe_sort, impostor, match_pairs
        }
        
        OUTPUT CONTRACT:
        Frontend-ready JSON matching game schema (no explanations).
        
        ARCHITECTURAL GUARANTEE:
        - No teaching or explanations
        - No answer evaluation
        - No conversational text
        - Stateless operation
        """
        game_type = input_data.get("game_type")
        
        # Validate game type
        if game_type not in self.SUPPORTED_GAME_TYPES:
            raise ValueError(
                f"Unsupported game_type '{game_type}'. "
                f"Must be one of: {', '.join(self.SUPPORTED_GAME_TYPES)}"
            )
        
        # Route to appropriate generator
        if game_type == "swipe_sort":
            return self._generate_swipe_sort(input_data)
        elif game_type == "impostor":
            return self._generate_impostor(input_data)
        elif game_type == "match_pairs":
            return self._generate_match_pairs(input_data)
    
    # ============================================================================
    # JSON PARSING & VALIDATION
    # ============================================================================
    
    def _clean_json_response(self, text: str) -> str:
        """
        Extract clean JSON from LLM response.
        
        WHY: LLMs often wrap JSON in markdown code blocks or add prose.
        This ensures we get only the raw JSON for parsing.
        """
        # Remove markdown code fences
        text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'```\s*', '', text)
        
        # Remove common prose patterns before/after JSON
        # (e.g., "Here is the game:", "Let me know if...")
        text = re.sub(r'^[^{]*', '', text)  # Remove text before first {
        text = re.sub(r'[^}]*$', '', text)  # Remove text after last }
        
        return text.strip()
    
    def _parse_and_validate_json(self, raw_text: str, expected_game_type: str) -> Dict[str, Any]:
        """
        Parse LLM response into JSON and validate structure.
        
        WHY: Ensures architectural contract is maintained - only valid,
        frontend-ready JSON is returned, never malformed or partial data.
        """
        try:
            cleaned = self._clean_json_response(raw_text)
            parsed = json.loads(cleaned)
            
            # Basic schema validation
            if not isinstance(parsed, dict):
                raise ValueError("Response is not a JSON object")
            
            if parsed.get("game_type") != expected_game_type:
                raise ValueError(
                    f"Expected game_type '{expected_game_type}', "
                    f"got '{parsed.get('game_type')}'"
                )
            
            return parsed
            
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM returned invalid JSON. "
                f"Parse error: {str(e)}. "
                f"Raw response: {raw_text[:200]}"
            ) from e
    
    # ============================================================================
    # SWIPE-SORT GAME GENERATOR (Binary Classification)
    # ============================================================================
    
    def _generate_swipe_sort(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate binary classification game (swipe left/right).
        
        PEDAGOGICAL PURPOSE: Test ability to classify items into opposing categories.
        Tests understanding of boundaries between two contrasting groups.
        
        WHY STRICT PROMPT: Prevents LLM from adding explanations or hints.
        Forces deterministic JSON output suitable for immediate UI rendering.
        """
        concept = data['concept']
        nuances = data.get('nuances', [])
        
        # Format nuances for inclusion in prompt if available
        nuances_context = ""
        if nuances:
            nuances_context = f"\nFocus on these aspects: {', '.join(nuances[:3])}"
        
        prompt = f"""You are a game content generator. Output ONLY valid JSON, no explanations.

TASK: Generate a binary classification game for the concept: "{concept}"{nuances_context}

REQUIREMENTS:
1. Infer TWO opposing/contrasting categories from the concept
2. Generate {self.SWIPE_SORT_CARD_RANGE[0]}-{self.SWIPE_SORT_CARD_RANGE[1]} item cards
3. Each card must clearly belong to exactly one category
4. Include subtle distinctions (not obvious choices)
5. NO explanations, hints, or teaching text
6. Output ONLY the JSON structure below

OUTPUT FORMAT (STRICT):
{{
  "game_type": "swipe_sort",
  "left_category": "<category name>",
  "right_category": "<opposite category name>",
  "cards": ["<item1>", "<item2>", ...]
}}

CRITICAL: Return ONLY the JSON object. No markdown, no prose."""

        response = self.model.generate_content(prompt)
        return self._parse_and_validate_json(response.text, "swipe_sort")
    
    # ============================================================================
    # IMPOSTOR GAME GENERATOR (Boundary Testing)
    # ============================================================================
    
    def _generate_impostor(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate "find the impostor" game (spot the outlier).
        
        PEDAGOGICAL PURPOSE: Test boundary understanding and edge case recognition.
        Requires learner to identify subtle differences between related items.
        
        WHY 3+1 STRUCTURE: Three genuine items establish pattern, one impostor
        tests whether learner can detect subtle boundary violations.
        """
        concept = data['concept']
        nuances = data.get('nuances', [])
        
        nuances_context = ""
        if nuances:
            # Use nuances to guide impostor selection (boundary testing)
            nuances_context = f"\nTest these boundaries: {', '.join(nuances[:3])}"
        
        prompt = f"""You are a game content generator. Output ONLY valid JSON, no explanations.

TASK: Generate a "find the impostor" game for the concept: "{concept}"{nuances_context}

REQUIREMENTS:
1. Generate exactly {self.IMPOSTOR_OPTIONS_COUNT} options
2. 3 options must be genuinely related to the concept
3. 1 option is the IMPOSTOR (subtly different, not obviously wrong)
4. The impostor should test boundary understanding
5. Options should be similar enough to require careful thinking
6. NO explanations, hints, or reasoning
7. Output ONLY the JSON structure below

OUTPUT FORMAT (STRICT):
{{
  "game_type": "impostor",
  "options": ["<option1>", "<option2>", "<option3>", "<option4>"],
  "impostor": "<the impostor option from above list>"
}}

CRITICAL: Return ONLY the JSON object. No markdown, no prose."""

        response = self.model.generate_content(prompt)
        return self._parse_and_validate_json(response.text, "impostor")
    
    # ============================================================================
    # MATCH-PAIRS GAME GENERATOR (Association Testing)
    # ============================================================================
    
    def _generate_match_pairs(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate term-definition or concept-association matching game.
        
        PEDAGOGICAL PURPOSE: Test vocabulary, terminology, and conceptual relationships.
        Reinforces connections between terms and their meanings or related concepts.
        
        WHY KEY-VALUE PAIRS: Simplifies frontend rendering (left column, right column).
        Tests recall of associations without providing answers.
        """
        concept = data['concept']
        nuances = data.get('nuances', [])
        
        nuances_context = ""
        if nuances:
            nuances_context = f"\nInclude these aspects: {', '.join(nuances[:4])}"
        
        prompt = f"""You are a game content generator. Output ONLY valid JSON, no explanations.

TASK: Generate a matching pairs game for the concept: "{concept}"{nuances_context}

REQUIREMENTS:
1. Create {self.MATCH_PAIRS_RANGE[0]}-{self.MATCH_PAIRS_RANGE[1]} term-definition or concept-association pairs
2. Pairs must test understanding of terminology, relationships, or vocabulary
3. Terms should be specific to the concept (not generic)
4. Definitions should be concise (1-2 sentences max)
5. Include technical terms where appropriate
6. NO explanations, hints, or teaching text
7. Output ONLY the JSON structure below

OUTPUT FORMAT (STRICT):
{{
  "game_type": "match_pairs",
  "pairs": {{
    "<term1>": "<definition1 or associated concept>",
    "<term2>": "<definition2 or associated concept>",
    ...
  }}
}}

CRITICAL: Return ONLY the JSON object. No markdown, no prose."""

        response = self.model.generate_content(prompt)
        return self._parse_and_validate_json(response.text, "match_pairs")
