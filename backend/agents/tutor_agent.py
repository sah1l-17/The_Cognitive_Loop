"""
Tutor Agent - Teaching & Understanding Verification
====================================================

ROLE: The ONLY agent allowed to teach in the system.

RESPONSIBILITIES:
- Explain concepts using structured content from Ingestion Agent
- Adapt explanation style based on learner confusion levels
- Detect confusion (direct, indirect, frustration, false confidence)
- Verify genuine understanding before allowing practice games
- Gate access to gamified practice (no teaching allowed there)

DOES NOT:
- Perform OCR or content parsing
- Generate quizzes or games
- Evaluate game answers
- Create embeddings or long-term memory
- Access raw PDFs/images
- Make routing decisions

PEDAGOGICAL APPROACH:
- Diagnose learner state before responding
- Adapt depth, vocabulary, and analogy usage dynamically
- Probe understanding without triggering test anxiety
- Distinguish between shallow recognition and deep understanding
- Prevent illusion of mastery through Socratic probing
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core.agent_base import Agent
from services.gemini_client import gemini_flash


class TutorAgent(Agent):
    """
    Advanced adaptive tutor with robust confusion/understanding detection.
    """
    
    # ============================================================================
    # CONFUSION DETECTION PATTERNS
    # ============================================================================
    # WHY: Learners rarely say "I'm confused" directly. We need comprehensive
    # detection across multiple confusion dimensions to provide appropriate support.
    
    # Direct confusion expressions
    CONFUSION_DIRECT = [
        "confused", "don't understand", "dont understand", "do not understand",
        "not understanding", "didn't understand", "didnt understand",
        "doesn't make sense", "doesnt make sense", "lost me", "losing me",
        "not following", "can't follow", "cant follow", "not getting",
        "not getting it", "dont get", "don't get", "not clear",
        "unclear", "doesn't click", "doesnt click", "no idea",
        "have no clue", "totally lost", "completely lost"
    ]
    
    # Indirect confusion (hedging, hesitation)
    CONFUSION_INDIRECT = [
        "kind of confused", "sort of confused", "bit confused", "little confused",
        "somewhat confused", "slightly confused", "not entirely sure",
        "not completely sure", "not totally sure", "partially confused",
        "kinda lost", "sorta lost", "a bit lost", "little lost"
    ]
    
    # Request for simplification (learner knows they need help)
    CONFUSION_SIMPLIFICATION = [
        "simpler", "make it simpler", "simplify", "break it down",
        "step by step", "slow down", "too fast", "too complicated",
        "too complex", "easier way", "explain differently",
        "another way", "different explanation", "rephrase",
        "say that again", "repeat", "one more time", "eli5",
        "explain like", "layman", "plain english", "basic terms"
    ]
    
    # Frustration indicators (emotional confusion)
    CONFUSION_FRUSTRATION = [
        "frustrating", "frustrated", "giving up", "this is hard",
        "this is difficult", "struggling", "stuck", "can't figure",
        "cant figure", "not working", "help", "i'm stuck", "im stuck"
    ]
    
    # False confidence / shallow understanding indicators
    # WHY: These suggest the learner THINKS they understand but may not
    CONFUSION_FALSE_CONFIDENCE = [
        "seems easy", "sounds easy", "looks simple", "got it i think",
        "think i understand", "think i got it", "probably understand",
        "maybe i get", "guess i understand", "suppose i get"
    ]
    
    # Partial understanding signals
    CONFUSION_PARTIAL = [
        "some of it", "part of it", "most of it", "halfway there",
        "almost there", "getting closer", "starting to", "beginning to",
        "except for", "but what about", "but how", "but why",
        "one thing though", "one question", "still wondering"
    ]
    
    # Meta-cognitive awareness (learner knows they're missing something)
    CONFUSION_METACOGNITIVE = [
        "something missing", "what am i missing", "missing something",
        "feel like", "sense that", "not quite right", "close but",
        "on the right track", "am i right", "is this correct",
        "did i get", "is that right"
    ]
    
    # ============================================================================
    # UNDERSTANDING CONFIRMATION PATTERNS
    # ============================================================================
    # WHY: Need to detect GENUINE understanding, not just recognition or repetition.
    # Looking for transfer, application, and deep comprehension signals.
    
    # Explicit direct confirmations
    UNDERSTANDING_EXPLICIT = [
        "i understand", "i understood", "understood", "i get it",
        "i got it", "got it", "makes sense", "that makes sense",
        "clear now", "crystal clear", "perfectly clear", "totally clear",
        "completely clear", "ah i see", "oh i see", "i see now",
        "aha", "ah ha", "a-ha", "ohhh", "ahh", "now i understand",
        "now i get", "finally understand", "finally get it"
    ]
    
    # Implicit understanding (without saying "understand")
    UNDERSTANDING_IMPLICIT = [
        "of course", "obviously", "that's clear", "thats clear",
        "makes perfect sense", "totally makes sense", "yeah that works",
        "yep that works", "right that's", "right thats", "exactly",
        "precisely", "indeed", "absolutely", "definitely"
    ]
    
    # Transfer signals (applying to new contexts - STRONGEST SIGNAL)
    # WHY: Transfer = true understanding. If learner can apply concept elsewhere,
    # they've internalized it beyond mere repetition.
    UNDERSTANDING_TRANSFER = [
        "so that means", "so if i", "that's like", "thats like",
        "similar to", "this is like", "kind of like", "sort of like",
        "i could use this", "could apply", "would work for",
        "reminds me of", "connects to", "relates to", "this explains why",
        "now i know why", "that's why", "thats why"
    ]
    
    # Correct paraphrasing indicators
    # WHY: Paraphrasing in own words = processing, not just memorizing
    UNDERSTANDING_PARAPHRASE = [
        "so basically", "in other words", "what you're saying",
        "what youre saying", "if i understand correctly",
        "let me see if", "so you mean", "you mean that",
        "in my own words", "to put it", "another way to say"
    ]
    
    # Readiness for practice (confidence + eagerness)
    UNDERSTANDING_READINESS = [
        "ready to practice", "ready to try", "want to practice",
        "can i practice", "let me practice", "let's practice",
        "lets practice", "ready for", "bring it on", "i'm ready",
        "im ready", "let's do this", "lets do this", "ready to go",
        "try it out", "test myself", "see if i can"
    ]
    
    # Confidence indicators (metacognitive certainty)
    UNDERSTANDING_CONFIDENCE = [
        "i'm confident", "im confident", "feel confident",
        "pretty sure", "very sure", "quite sure", "certain",
        "definitely understand", "totally get", "completely get",
        "fully understand", "solid on", "comfortable with",
        "know this now", "have it now"
    ]
    
    def __init__(self):
        super().__init__("TutorAgent")
        self.model = gemini_flash()
        
        # Compile all detection patterns
        self.confusion_triggers = (
            self.CONFUSION_DIRECT +
            self.CONFUSION_INDIRECT +
            self.CONFUSION_SIMPLIFICATION +
            self.CONFUSION_FRUSTRATION +
            self.CONFUSION_FALSE_CONFIDENCE +
            self.CONFUSION_PARTIAL +
            self.CONFUSION_METACOGNITIVE
        )
        
        self.understanding_confirmations = (
            self.UNDERSTANDING_EXPLICIT +
            self.UNDERSTANDING_IMPLICIT +
            self.UNDERSTANDING_TRANSFER +
            self.UNDERSTANDING_PARAPHRASE +
            self.UNDERSTANDING_READINESS +
            self.UNDERSTANDING_CONFIDENCE
        )

    async def run(self, input_data, tutor_state):
        """
        Main entry point for tutoring interaction.
        
        INPUT:
            input_data: {
                "question": str,  # Learner's question/statement
                "notes": str      # Structured content from Ingestion Agent
            }
            tutor_state: {
                "confusion_level": float,          # 0.0 → confident, 1.0 → very confused
                "clarification_requests": int,     # Count of clarification requests
                "understood": bool,                # Gating flag for practice
                "last_explanation_style": str      # Previous style used
            }
        
        OUTPUT:
            {
                "agent": str,
                "explanation": str,
                "confusion_level": float,
                "understood": bool,
                "explanation_style": str
            }
        """
        
        question = input_data["question"]
        question_lower = question.lower()
        
        # ========================================================================
        # PHASE 1: DIAGNOSE LEARNER STATE
        # ========================================================================
        # WHY: We must understand the learner's cognitive state BEFORE responding.
        # Different states require different pedagogical approaches.
        
        confusion_detected = self._detect_confusion(question_lower)
        understanding_detected = self._detect_understanding(question_lower)
        
        # Update confusion level based on signals
        if confusion_detected:
            # Increase confusion when detected
            tutor_state["confusion_level"] += 0.2
            tutor_state["clarification_requests"] += 1
        elif understanding_detected:
            # Decrease confusion when understanding is shown
            tutor_state["confusion_level"] = max(
                tutor_state["confusion_level"] - 0.15, 0.0
            )
        else:
            # Slight decay if neutral (no strong signals)
            tutor_state["confusion_level"] = max(
                tutor_state["confusion_level"] - 0.05, 0.0
            )
        
        # Cap confusion level at 1.0
        tutor_state["confusion_level"] = min(tutor_state["confusion_level"], 1.0)
        
        # ========================================================================
        # PHASE 2: DECIDE EXPLANATION STRATEGY
        # ========================================================================
        # WHY: Pedagogical research shows adaptation is key to effective teaching.
        # We adjust depth, vocabulary, analogies, and pacing based on confusion.
        
        explanation_strategy = self._select_explanation_strategy(
            tutor_state["confusion_level"],
            tutor_state["clarification_requests"]
        )
        
        tutor_state["last_explanation_style"] = explanation_strategy["style"]
        
        # ========================================================================
        # PHASE 3: GENERATE ADAPTIVE EXPLANATION
        # ========================================================================
        # WHY: The LLM prompt is our teaching engine. It must be pedagogically
        # sound, adapt to learner state, and avoid common tutoring pitfalls.
        
        explanation_text = await self._generate_explanation(
            question=question,
            notes=input_data["notes"],
            strategy=explanation_strategy,
            tutor_state=tutor_state
        )
        
        # ========================================================================
        # PHASE 4: EVALUATE UNDERSTANDING (GATING DECISION)
        # ========================================================================
        # WHY: We gate access to practice to prevent premature practice on
        # concepts not yet understood. This prevents reinforcing errors.
        
        if understanding_detected:
            # Additional validation: check for false confidence
            if not self._is_false_confidence(question_lower):
                tutor_state["understood"] = True
        
        # ========================================================================
        # PHASE 5: RETURN TEACHING RESULT
        # ========================================================================
        
        return {
            "agent": self.name,
            "explanation": explanation_text,
            "confusion_level": tutor_state["confusion_level"],
            "understood": tutor_state["understood"],
            "explanation_style": explanation_strategy["style"]
        }
    
    def _detect_confusion(self, question_lower: str) -> bool:
        """
        Detect if learner is expressing confusion (any form).
        
        WHY: Confusion detection triggers adaptive support. We cast a wide net
        to catch subtle signals that a learner is struggling.
        """
        return any(trigger in question_lower for trigger in self.confusion_triggers)
    
    def _detect_understanding(self, question_lower: str) -> bool:
        """
        Detect if learner is expressing understanding.
        
        WHY: Understanding signals allow us to reduce scaffolding and prepare
        for practice. We look for genuine comprehension, not just recognition.
        """
        return any(phrase in question_lower for phrase in self.understanding_confirmations)
    
    def _is_false_confidence(self, question_lower: str) -> bool:
        """
        Detect false confidence patterns that suggest shallow understanding.
        
        WHY: Prevent illusion of mastery. Learners often THINK they understand
        when they don't. We need additional probing in these cases.
        """
        return any(phrase in question_lower for phrase in self.CONFUSION_FALSE_CONFIDENCE)
    
    def _select_explanation_strategy(
        self,
        confusion_level: float,
        clarification_count: int
    ) -> dict:
        """
        Select pedagogical strategy based on learner state.
        
        WHY: One-size-fits-all teaching fails. We adapt our approach based on
        how confused the learner is and how many times they've asked for help.
        
        RETURNS:
            {
                "style": str,           # Style label
                "depth": str,           # How deep to explain
                "vocabulary": str,      # Language complexity
                "analogies": str,       # Analogy usage
                "pacing": str,          # How fast to move
                "probing": str          # How to check understanding
            }
        """
        
        # High confusion (>0.6) or many clarifications (>2)
        if confusion_level > 0.6 or clarification_count > 2:
            return {
                "style": "foundational",
                "depth": "start from absolute basics, build one concept at a time",
                "vocabulary": "use simple, everyday words - avoid jargon entirely",
                "analogies": "use multiple concrete analogies from daily life",
                "pacing": "very slow - explain each micro-step explicitly",
                "probing": "ask simple yes/no check-ins, avoid intimidating questions"
            }
        
        # Moderate confusion (0.3-0.6)
        elif confusion_level > 0.3:
            return {
                "style": "simplified",
                "depth": "explain core ideas with clear structure",
                "vocabulary": "use accessible language, define technical terms",
                "analogies": "use one clear analogy to ground the concept",
                "pacing": "moderate - balance detail with clarity",
                "probing": "ask gentle check-for-understanding questions"
            }
        
        # Low confusion (0-0.3) - learner is tracking well
        else:
            return {
                "style": "standard",
                "depth": "normal depth - don't oversimplify",
                "vocabulary": "use appropriate technical vocabulary with context",
                "analogies": "use analogies only when they add precision",
                "pacing": "normal - trust learner can follow",
                "probing": "ask thought-provoking questions to deepen understanding"
            }
    
    async def _generate_explanation(
        self,
        question: str,
        notes: str,
        strategy: dict,
        tutor_state: dict
    ) -> str:
        """
        Generate adaptive explanation using LLM with pedagogically-designed prompt.
        
        WHY: The prompt is where teaching quality is determined. A poorly designed
        prompt creates a shallow chatbot. A well-designed prompt creates a tutor.
        """
        
        # Build context about learner state for the LLM
        learner_state_context = self._build_learner_context(tutor_state)
        
        # ========================================================================
        # PEDAGOGICALLY-ENGINEERED PROMPT
        # ========================================================================
        # WHY: This prompt encodes research-backed teaching principles:
        # - Adaptive depth based on learner state
        # - Socratic probing without anxiety
        # - Clear separation from assessment
        # - Focus on understanding, not performance
        
        prompt = f"""You are an expert tutor with deep knowledge of learning science and pedagogy.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEARNER STATE ANALYSIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{learner_state_context}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEACHING STRATEGY FOR THIS RESPONSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Style: {strategy['style']}
Depth: {strategy['depth']}
Vocabulary: {strategy['vocabulary']}
Analogies: {strategy['analogies']}
Pacing: {strategy['pacing']}
Understanding Check: {strategy['probing']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEARNING MATERIAL (SOURCE OF TRUTH)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{notes}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEARNER'S QUESTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{question}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR TEACHING APPROACH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. TEACHING PRINCIPLES (ALWAYS FOLLOW):
   • Teach based ONLY on the provided learning material above
   • Adapt your explanation to the teaching strategy specified
   • Use the Socratic method - guide thinking, don't just dump information
   • Build on what they already know (zone of proximal development)
   • Make abstract concepts concrete through examples and analogies
   • Address misconceptions directly when detected
   • Normalize confusion - it's part of learning
   • Celebrate progress and insight

2. WHAT YOU MUST DO:
   • Answer their question clearly using the material provided
   • Adapt language complexity to their current state
   • Use examples that make sense in their context
   • Check for understanding with a gentle, non-threatening question
   • Encourage them to connect this to what they already know

3. WHAT YOU MUST NEVER DO:
   • Do NOT quiz them or test their knowledge
   • Do NOT generate practice problems or exercises
   • Do NOT mention games or practice activities
   • Do NOT make them feel stupid for not knowing
   • Do NOT use jargon without explaining it (unless strategy allows)
   • Do NOT add information not in the learning material
   • Do NOT skip the understanding check at the end

4. UNDERSTANDING CHECK GUIDELINES:
   • Ask ONE question at the end to gently probe understanding
   • Make it feel like a conversation, not a test
   • Use phrases like "Does that make sense?" or "Can you see how..." or "What do you think about..."
   • Make it safe to admit confusion
   • Frame it as collaborative thinking, not evaluation

5. TONE:
   • Warm, patient, encouraging
   • Never condescending or impatient
   • Treat confusion as normal and expected
   • Celebrate incremental progress

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Now provide your explanation:"""

        # Generate response from LLM
        response = self.model.generate_content(prompt)
        return response.text
    
    def _build_learner_context(self, tutor_state: dict) -> str:
        """
        Build human-readable context about learner state for LLM prompt.
        
        WHY: Giving the LLM explicit information about learner state enables
        better pedagogical decisions.
        """
        
        confusion_level = tutor_state["confusion_level"]
        clarifications = tutor_state["clarification_requests"]
        understood = tutor_state["understood"]
        
        # Interpret confusion level
        if confusion_level > 0.7:
            confusion_desc = "significantly confused - needs foundational support"
        elif confusion_level > 0.4:
            confusion_desc = "moderately confused - needs clearer explanation"
        elif confusion_level > 0.15:
            confusion_desc = "slightly uncertain - needs minor clarification"
        else:
            confusion_desc = "tracking well - understanding is progressing"
        
        # Build context string
        context = f"""• Confusion Level: {confusion_level:.2f} - {confusion_desc}
• Clarification Requests: {clarifications}
• Concept Understood: {"Yes - learner ready for practice" if understood else "Not yet - still learning"}
• Previous Teaching Style: {tutor_state.get('last_explanation_style', 'None')}"""
        
        return context