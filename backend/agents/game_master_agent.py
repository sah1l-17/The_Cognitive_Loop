"""
Game Master Agent - Cognitively Rigorous Active Recall Generator
===================================================================

ARCHITECTURAL ROLE:
    Generates ONLY active-recall practice games for concepts already understood.
    Operates post-teaching. No explanations, hints, or evaluation logic.

COGNITIVE LEARNING PRINCIPLES:
    • Retrieval practice strengthens memory better than re-reading
    • Desirable difficulty (not confusion) enhances learning
    • Boundary cases reveal depth of understanding
    • Near-miss distractors force discrimination
    • Obvious practice creates illusion of mastery

QUALITY MANDATE:
    Every game must be challenging enough that:
    - Learners must actively discriminate, not guess
    - Edge cases and boundaries are tested
    - Shallow understanding is exposed
    - Pattern memorization fails

SUPPORTED GAME TYPES:
    1. Swipe-Sort: Binary classification with boundary-focused items
    2. Find-the-Impostor: Subtle outlier detection (boundary testing)
    3. Match-Pairs: Relational/functional association testing

OUTPUT CONTRACT:
    Frontend-ready JSON ONLY. No prose. No teaching. No evaluation.
"""

import json
import re
from typing import Dict, Any, List
from core.agent_base import Agent
from services.gemini_client import gemini_flash


class GameMasterAgent(Agent):
    """
    High-quality active-recall game generator with cognitive rigor.
    
    WHY STATELESS: Each game is independent. No learner modeling here.
    WHY JSON-ONLY: Clean separation from UI. No conversational mixing.
    WHY NO TEACHING: Teaching happens in Tutor Agent. This is pure practice.
    """
    
    # ============================================================================
    # ARCHITECTURAL CONSTANTS
    # ============================================================================
    
    SUPPORTED_GAME_TYPES = ["swipe_sort", "impostor", "match_pairs"]
    
    # Game sizing parameters (cognitive load balanced)
    SWIPE_SORT_CARD_RANGE = (6, 8)      # Enough items to test patterns
    IMPOSTOR_OPTIONS_COUNT = 4           # 3 genuine + 1 impostor
    MATCH_PAIRS_RANGE = (3, 5)           # Vocabulary/relationship depth
    
    # Quality thresholds
    MIN_BOUNDARY_ITEMS_RATIO = 0.35      # At least 35% should be edge cases
    
    # Batch generation
    GAMES_PER_BATCH = 2                  # Generate 2 games at a time
    MAX_GENERATION_ATTEMPTS = 3
    
    def __init__(self):
        super().__init__("GameMasterAgent")
        self.model = gemini_flash()
    
    # ============================================================================
    # CORE PUBLIC INTERFACE
    # ============================================================================
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate 2 cognitively rigorous active-recall games in a batch.
        
        INPUT CONTRACT:
        {
            "concept": str,           # Concept name (learner has understood this)
            "nuances": List[str],     # Edge cases, boundaries, weak points
            "game_type": str          # One of: swipe_sort, impostor, match_pairs
        }
        
        OUTPUT CONTRACT:
        Frontend-ready JSON batch containing 2 games. No explanations, hints, or prose.
        
        ARCHITECTURAL GUARANTEES:
        - No teaching or explanations (that's Tutor Agent's job)
        - No answer evaluation (that's Evaluator Agent's job)
        - No conversational text (pure structured data)
        - Stateless operation (no learner modeling)
        - Always generates 2 unique games per request
        
        QUALITY GUARANTEE:
        Games test boundaries, use subtle distractors, and require active thinking.
        Each game in the batch is unique and tests different aspects.
        """
        game_type = input_data.get("game_type")
        concept = input_data.get("concept", "")
        nuances = input_data.get("nuances", [])
        
        # Validate inputs
        if game_type not in self.SUPPORTED_GAME_TYPES:
            raise ValueError(
                f"Unsupported game_type '{game_type}'. "
                f"Must be one of: {', '.join(self.SUPPORTED_GAME_TYPES)}"
            )
        
        if not concept or concept.strip() == "":
            raise ValueError("Concept cannot be empty")
        
        # Route to specialized batch generator
        if game_type == "swipe_sort":
            return await self._generate_swipe_sort_batch(concept, nuances)
        elif game_type == "impostor":
            return await self._generate_impostor_batch(concept, nuances)
        elif game_type == "match_pairs":
            return await self._generate_match_pairs_batch(concept, nuances)
    
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _format_nuance_guidance(self, nuances: List[str]) -> str:
        """
        Format nuance list into guidance for game generation.
        
        WHY: Nuances represent edge cases, weak points, or boundaries that
        should be prioritized in game generation for maximum learning value.
        """
        if not nuances or len(nuances) == 0:
            return ""
        
        # Limit to top 4 nuances to keep prompt focused
        selected_nuances = nuances[:4]
        formatted = "\n\nPRIORITY BOUNDARIES TO TEST:\n"
        for i, nuance in enumerate(selected_nuances, 1):
            formatted += f"   {i}. {nuance}\n"
        
        return formatted
    
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

    def _generate_valid_game(self, prompt: str, expected_game_type: str) -> Dict[str, Any]:
        """Generate a single valid game JSON, retrying when the LLM output is malformed.

        WHY: Once we require answer keys + rationales, occasional LLM formatting drift
        becomes more costly. Retrying with explicit error feedback dramatically improves
        reliability without complicating callers.
        """

        last_error: Exception | None = None
        retry_prompt = prompt
        for attempt in range(1, self.MAX_GENERATION_ATTEMPTS + 1):
            try:
                response = self.model.generate_content(retry_prompt)
                return self._parse_and_validate_json(response.text, expected_game_type)
            except Exception as e:
                last_error = e
                # Add tight corrective instruction while keeping the original spec.
                retry_prompt = (
                    prompt
                    + "\n\nIMPORTANT: Your previous response was invalid. "
                    + f"Error: {str(e)}. "
                    + "Return ONLY valid JSON matching the output schema exactly. "
                    + "Do not include markdown fences or extra text."
                )

        raise ValueError(f"Failed to generate valid '{expected_game_type}' game after {self.MAX_GENERATION_ATTEMPTS} attempts") from last_error
    
    
    # ============================================================================
    # SWIPE-SORT GAME GENERATOR (Binary Classification with Boundary Focus)
    # ============================================================================
    
    async def _generate_swipe_sort_batch(self, concept: str, nuances: List[str]) -> Dict[str, Any]:
        """
        Generate a batch of 2 swipe-sort games.
        """
        games = []
        for i in range(self.GAMES_PER_BATCH):
            game = await self._generate_swipe_sort(concept, nuances, i + 1)
            games.append(game)
        
        return {
            "game_type": "swipe_sort",
            "concept": concept,
            "games": games,
            "total_games": self.GAMES_PER_BATCH
        }
    
    async def _generate_swipe_sort(self, concept: str, nuances: List[str], variation: int = 1) -> Dict[str, Any]:
        """
        Generate boundary-focused binary classification game.
        
        PEDAGOGICAL PURPOSE:
            Test ability to discriminate between opposing categories at their boundaries.
            Shallow understanding: can classify obvious cases
            Deep understanding: can classify edge cases and boundary items
        
        QUALITY REQUIREMENTS:
            • 35%+ of items must be boundary/edge cases
            • Categories must be true opposites or mutually exclusive
            • Avoid trivial textbook examples
            • Items should require reasoning, not pattern matching
        
        WHY ASYNC: Future-proofs for retry logic or quality checks
        """
        
        # Build nuance context for prompt
        nuance_guidance = self._format_nuance_guidance(nuances)
        
        # ========================================================================
        # COGNITIVELY-ENGINEERED PROMPT
        # ========================================================================
        # WHY THIS STRUCTURE:
        # 1. Explicit quality criteria prevent lazy generation
        # 2. Anti-patterns show what NOT to do
        # 3. Examples demonstrate cognitive rigor
        # 4. Boundary emphasis forces edge case testing
        
        prompt = f"""You are an expert educational game designer specializing in active-recall practice.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK: Binary Classification Game (Swipe-Sort)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate a swipe-left/swipe-right classification game for:

CONCEPT: {concept}{nuance_guidance}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COGNITIVE QUALITY REQUIREMENTS (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. CATEGORY DESIGN:
   • Must be true opposites or mutually exclusive groups
   • Must emerge naturally from the concept (not forced)
   • Must be specific to this concept (not generic)
   
2. ITEM SELECTION PHILOSOPHY:
   • 35-40% of items MUST be boundary/edge cases
   • 30-40% should be moderately clear
   • 20-30% can be straightforward (but not trivial)
   • AVOID obvious textbook examples
   • PREFER items that require reasoning about WHY they belong
   
3. BOUNDARY FOCUS:
   Edge cases to include:
   • Items that share properties with both categories
   • Items where the distinction is subtle
   • Items that test common misconceptions
   • Items that require applying the concept's core principle
   
4. COGNITIVE DIFFICULTY:
   • Make items similar enough to require discrimination
   • Use realistic, varied examples (not repetitive patterns)
   • Test understanding, not trivia
   • Avoid ambiguous wording
   
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANTI-PATTERNS (DO NOT GENERATE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Obvious textbook examples (e.g., for "acid vs base": "Lemon juice", "Baking soda")
❌ Pattern-based items that don't test concept understanding
❌ Generic items that could appear in any similar game
❌ Surface-level distinctions (test deep properties, not labels)
❌ Repetitive phrasing across items

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLE: Binary Search Tree (Correct Operations vs Incorrect Operations)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ GOOD (Boundary-focused):
   • "Insert 5 into left subtree when parent is 7" (CORRECT - tests BST property)
   • "Place 12 as right child of 10" (CORRECT - straightforward)
   • "Put 8 to the left of 6" (INCORRECT - boundary: wrong direction)
   • "Insert duplicate value as right child" (INCORRECT - edge case: duplicates)

❌ BAD (Too obvious):
   • "Insert smaller value to the left" (Too obvious - just states the rule)
   • "Insert larger value to the right" (Too obvious)
   
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GENERATION INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Analyze the concept to identify natural opposing categories
2. Generate {self.SWIPE_SORT_CARD_RANGE[0]}-{self.SWIPE_SORT_CARD_RANGE[1]} items
3. Ensure 35%+ are boundary/edge cases
4. Vary surface form and phrasing
5. Make learner apply concept's core principle to classify
6. Create UNIQUE items (variation #{variation} of this game type)
7. Output ONLY the JSON structure below (no prose, no markdown)

OUTPUT FORMAT (STRICT):
{{
  "game_type": "swipe_sort",
  "left_category": "<specific category name>",
  "right_category": "<opposite category name>",
    "cards": ["<item1>", "<item2>", ...],
    "answer_key": {{
        "<item1>": "left",
        "<item2>": "right"
    }},
    "why": {{
        "<item1>": "<one-sentence rationale grounded in the concept>",
        "<item2>": "<one-sentence rationale grounded in the concept>"
    }}
}}

CRITICAL: Return ONLY valid JSON. No explanations. No code blocks. No prose."""

        response = self.model.generate_content(prompt)
        return self._generate_valid_game(prompt, "swipe_sort")
    
    
    # ============================================================================
    # IMPOSTOR GAME GENERATOR (Subtle Boundary Discrimination)
    # ============================================================================
    
    async def _generate_impostor_batch(self, concept: str, nuances: List[str]) -> Dict[str, Any]:
        """
        Generate a batch of 2 impostor games.
        """
        games = []
        for i in range(self.GAMES_PER_BATCH):
            game = await self._generate_impostor(concept, nuances, i + 1)
            games.append(game)
        
        return {
            "game_type": "impostor",
            "concept": concept,
            "games": games,
            "total_games": self.GAMES_PER_BATCH
        }
    
    async def _generate_impostor(self, concept: str, nuances: List[str], variation: int = 1) -> Dict[str, Any]:
        """
        Generate "find the impostor" game with subtle outlier detection.
        
        PEDAGOGICAL PURPOSE:
            Test boundary understanding through near-miss discrimination.
            Shallow understanding: can identify obvious outliers
            Deep understanding: can detect subtle boundary violations
        
        QUALITY REQUIREMENTS:
            • Impostor must be SUBTLE (not obviously wrong)
            • All 4 options should appear related at first glance
            • Learner must reason about WHY impostor doesn't fit
            • Test conceptual boundaries, not surface features
        
        WHY 3+1: Three genuine items establish pattern, impostor tests if
        learner truly understands what makes something belong.
        """
        
        nuance_guidance = self._format_nuance_guidance(nuances)
        
        prompt = f"""You are an expert educational game designer specializing in boundary testing.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK: Find-the-Impostor Game (Subtle Outlier Detection)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate a "spot the impostor" game for:

CONCEPT: {concept}{nuance_guidance}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COGNITIVE QUALITY REQUIREMENTS (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. STRUCTURE:
   • Generate exactly {self.IMPOSTOR_OPTIONS_COUNT} options
   • 3 options are genuinely related to the concept
   • 1 option is the IMPOSTOR (subtle, not obvious)
   
2. IMPOSTOR QUALITY (CRITICAL):
   The impostor MUST:
   • Share surface-level similarities with genuine options
   • Violate a core principle or boundary of the concept
   • Require reasoning to detect (not pattern matching)
   • Test a common misconception or edge case
   • NOT be obviously different at first glance
   
3. GENUINE OPTIONS:
   • Must clearly belong to the concept
   • Should vary in presentation (not formulaic)
   • Should cover different aspects of the concept
   
4. COGNITIVE LOAD:
   • All 4 options should appear plausible initially
   • Learner must think "wait, which one doesn't belong?"
   • Detection requires applying conceptual understanding
   
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANTI-PATTERNS (DO NOT GENERATE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Impostor that is obviously unrelated (e.g., for "sorting algorithms": "Rainbow")
❌ Surface-level impostors (different by label only, not by principle)
❌ Impostors that could be debated (avoid ambiguity)
❌ All genuine options that are too similar (no variety)
❌ Generic textbook examples

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLE: Binary Search Trees (Property Violations)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ GOOD (Subtle impostor):
   Options:
   1. "Left child is 3, parent is 5, right child is 7" (Genuine - valid BST)
   2. "Node 10 has left child 8 and right child 12" (Genuine - valid BST)
   3. "Root 50, left subtree contains 30 and 40" (Genuine - valid BST)
   4. "Parent is 6, left child is 9, right child is 4" (IMPOSTOR - violates BST property)
   
   WHY GOOD: Impostor looks like a BST node description but violates ordering.
   Requires thinking about the property, not surface matching.

❌ BAD (Too obvious):
   Options:
   1. "Node with left and right children"
   2. "Balanced tree structure"
   3. "In-order traversal yields sorted sequence"
   4. "Linked list" (IMPOSTOR - obviously unrelated)
   
   WHY BAD: Impostor is trivially different. No boundary testing.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GENERATION INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Identify the core principle/boundary of the concept
2. Create 3 genuine examples that clearly fit
3. Create 1 impostor that SUBTLY violates the principle
4. Ensure impostor shares surface similarities with genuine options
5. Create UNIQUE options (variation #{variation} of this game type)
6. Output ONLY the JSON structure below (no prose, no markdown)

OUTPUT FORMAT (STRICT):
{{
  "game_type": "impostor",
  "options": ["<option1>", "<option2>", "<option3>", "<option4>"],
    "impostor": "<the impostor option from above list>",
    "why": "<2-4 sentences explaining why this option is the impostor and what principle/boundary it violates>"
}}

CRITICAL: Return ONLY valid JSON. No explanations. No code blocks. No prose."""

        response = self.model.generate_content(prompt)
        return self._generate_valid_game(prompt, "impostor")
    
    
    # ============================================================================
    # MATCH-PAIRS GAME GENERATOR (Relational Understanding)
    # ============================================================================
    
    async def _generate_match_pairs_batch(self, concept: str, nuances: List[str]) -> Dict[str, Any]:
        """
        Generate a batch of 2 match-pairs games.
        """
        games = []
        for i in range(self.GAMES_PER_BATCH):
            game = await self._generate_match_pairs(concept, nuances, i + 1)
            games.append(game)
        
        return {
            "game_type": "match_pairs",
            "concept": concept,
            "games": games,
            "total_games": self.GAMES_PER_BATCH
        }
    
    async def _generate_match_pairs(self, concept: str, nuances: List[str], variation: int = 1) -> Dict[str, Any]:
        """
        Generate term-association matching game testing relational understanding.
        
        PEDAGOGICAL PURPOSE:
            Test vocabulary, terminology, and conceptual relationships.
            Shallow understanding: can match obvious definitions
            Deep understanding: can match functional/relational associations
        
        QUALITY REQUIREMENTS:
            • Prefer functional relationships over simple definitions
            • Test conceptual connections, not memorization
            • Use precise, technical terminology
            • Avoid generic dictionary definitions
        
        WHY KEY-VALUE PAIRS: Simplifies frontend (left column / right column)
        while testing associative recall.
        """
        
        nuance_guidance = self._format_nuance_guidance(nuances)
        
        prompt = f"""You are an expert educational game designer specializing in relational learning.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TASK: Match-Pairs Game (Relational/Functional Association)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generate a matching pairs game for:

CONCEPT: {concept}{nuance_guidance}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COGNITIVE QUALITY REQUIREMENTS (MANDATORY)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. PAIR TYPE PRIORITIES (in order):
   🥇 FUNCTIONAL relationships (what it DOES, how it WORKS)
   🥈 RELATIONAL associations (how concepts CONNECT)
   🥉 PRECISE definitions (technical, not generic)
   ❌ AVOID: Generic dictionary definitions
   
2. TERM SELECTION:
   • Use technical terminology specific to this concept
   • Avoid generic terms that could apply to anything
   • Include terms that test nuanced understanding
   • Vary difficulty across pairs
   
3. ASSOCIATION QUALITY:
   • Associations must require concept understanding
   • Should not be guessable without learning the concept
   • Test relationships, not just vocabulary recall
   • Use precise language (no vague descriptions)
   
4. COGNITIVE LOAD:
   • Generate {self.MATCH_PAIRS_RANGE[0]}-{self.MATCH_PAIRS_RANGE[1]} pairs
   • Mix difficulty levels
   • Ensure matches are unambiguous when concept is understood
   • Make wrong pairings obviously incorrect (for frontend scrambling)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ANTI-PATTERNS (DO NOT GENERATE)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ Generic definitions:
   "Algorithm" → "A step-by-step procedure" (too vague)
   
❌ Surface-level matching:
   "Binary" → "Two" (trivial)
   
❌ Obvious vocabulary:
   "Tree" → "A data structure with nodes" (obvious from term itself)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXAMPLE: Binary Search Trees (Functional & Relational)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ GOOD (Functional/Relational):
{{
  "BST Property": "For any node, left subtree values < node value < right subtree values",
  "In-order Traversal": "Visits nodes in ascending sorted order in a BST",
  "Search Complexity": "O(log n) average case when tree is balanced",
  "Worst Case Degradation": "Tree becomes linear when insertions are sorted, leading to O(n)",
  "Rotation": "Operation to rebalance tree while maintaining BST property"
}}

WHY GOOD: Tests understanding of HOW things work and RELATE, not just WHAT they are.

❌ BAD (Generic/Obvious):
{{
  "BST": "Binary Search Tree",
  "Node": "Part of a tree",
  "Left": "One direction",
  "Right": "Other direction"
}}

WHY BAD: Doesn't test concept understanding. Could be guessed or memorized.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GENERATION INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Identify key technical terms from the concept
2. Create functional/relational associations (not just definitions)
3. Ensure associations test understanding, not memorization
4. Use precise, specific language
5. Create UNIQUE pairs (variation #{variation} of this game type)
6. Output ONLY the JSON structure below (no prose, no markdown)

OUTPUT FORMAT (STRICT):
{{
  "game_type": "match_pairs",
    "pairs": {{
        "<term1>": "<functional/relational association1>",
        "<term2>": "<functional/relational association2>",
        "<term3>": "<functional/relational association3>"
    }},
    "why": {{
        "<term1>": "<one-sentence rationale for why this match is correct>",
        "<term2>": "<one-sentence rationale for why this match is correct>",
        "<term3>": "<one-sentence rationale for why this match is correct>"
    }}
}}

CRITICAL: Return ONLY valid JSON. No explanations. No code blocks. No prose."""

        response = self.model.generate_content(prompt)
        return self._generate_valid_game(prompt, "match_pairs")
    
    # ============================================================================
    # JSON PARSING & VALIDATION
    # ============================================================================
    
    def _clean_json_response(self, text: str) -> str:
        """
        Extract clean JSON from LLM response.
        
        WHY: LLMs often wrap JSON in markdown code blocks or add prose.
        This ensures we get only the raw JSON for parsing, maintaining
        the architectural contract of structured output only.
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
        
        VALIDATION:
        - Parses as valid JSON
        - Contains expected game_type
        - Has required fields for that game type
        
        RAISES:
        ValueError if response is invalid or malformed
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
            
            # Game-specific validation
            self._validate_game_structure(parsed, expected_game_type)
            
            return parsed
            
        except json.JSONDecodeError as e:
            raise ValueError(
                f"LLM returned invalid JSON. "
                f"Parse error: {str(e)}. "
                f"Raw response: {raw_text[:200]}"
            ) from e
    
    def _validate_game_structure(self, game_data: Dict[str, Any], game_type: str):
        """
        Validate game-specific structure requirements.
        
        WHY: Prevents malformed games from reaching the frontend.
        Catches LLM failures early with clear error messages.
        """
        if game_type == "swipe_sort":
            required_fields = ["left_category", "right_category", "cards", "answer_key", "why"]
            for field in required_fields:
                if field not in game_data:
                    raise ValueError(f"Swipe-sort game missing required field: {field}")
            
            if not isinstance(game_data["cards"], list):
                raise ValueError("Swipe-sort 'cards' must be a list")

            if not isinstance(game_data["answer_key"], dict):
                raise ValueError("Swipe-sort 'answer_key' must be an object mapping card->left/right")

            if not isinstance(game_data["why"], dict):
                raise ValueError("Swipe-sort 'why' must be an object mapping card->rationale")
            
            if not (self.SWIPE_SORT_CARD_RANGE[0] <= len(game_data["cards"]) <= self.SWIPE_SORT_CARD_RANGE[1]):
                raise ValueError(
                    f"Swipe-sort must have {self.SWIPE_SORT_CARD_RANGE[0]}-{self.SWIPE_SORT_CARD_RANGE[1]} cards, "
                    f"got {len(game_data['cards'])}"
                )

            # Ensure answer_key/why cover every card.
            for card in game_data["cards"]:
                side = game_data["answer_key"].get(card)
                if side not in ("left", "right"):
                    raise ValueError("Swipe-sort answer_key must map every card to 'left' or 'right'")
                if not isinstance(game_data["why"].get(card), str) or not game_data["why"].get(card):
                    raise ValueError("Swipe-sort why must include a non-empty rationale for every card")
        
        elif game_type == "impostor":
            required_fields = ["options", "impostor", "why"]
            for field in required_fields:
                if field not in game_data:
                    raise ValueError(f"Impostor game missing required field: {field}")
            
            if not isinstance(game_data["options"], list):
                raise ValueError("Impostor 'options' must be a list")
            
            if len(game_data["options"]) != self.IMPOSTOR_OPTIONS_COUNT:
                raise ValueError(
                    f"Impostor game must have exactly {self.IMPOSTOR_OPTIONS_COUNT} options, "
                    f"got {len(game_data['options'])}"
                )
            
            if game_data["impostor"] not in game_data["options"]:
                raise ValueError("Impostor must be one of the options")

            if not isinstance(game_data["why"], str) or not game_data["why"].strip():
                raise ValueError("Impostor 'why' must be a non-empty string")
        
        elif game_type == "match_pairs":
            if "pairs" not in game_data:
                raise ValueError("Match-pairs game missing 'pairs' field")
            
            if not isinstance(game_data["pairs"], dict):
                raise ValueError("Match-pairs 'pairs' must be a dictionary")

            if "why" not in game_data:
                raise ValueError("Match-pairs game missing 'why' field")

            if not isinstance(game_data["why"], dict):
                raise ValueError("Match-pairs 'why' must be a dictionary mapping term->rationale")
            
            if not (self.MATCH_PAIRS_RANGE[0] <= len(game_data["pairs"]) <= self.MATCH_PAIRS_RANGE[1]):
                raise ValueError(
                    f"Match-pairs must have {self.MATCH_PAIRS_RANGE[0]}-{self.MATCH_PAIRS_RANGE[1]} pairs, "
                    f"got {len(game_data['pairs'])}"
                )

            for term in game_data["pairs"].keys():
                if not isinstance(game_data["why"].get(term), str) or not game_data["why"].get(term):
                    raise ValueError("Match-pairs why must include a non-empty rationale for every term")
