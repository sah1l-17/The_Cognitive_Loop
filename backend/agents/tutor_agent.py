import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from core.agent_base import Agent
from services.gemini_client import gemini_pro

class TutorAgent(Agent):
    def __init__(self):
        super().__init__("TutorAgent")
        self.model = gemini_pro()

    async def run(self, input_data, tutor_state):
        """
        input_data expects:
        {
            "question": str,
            "notes": str
        }
        """

        # -------------------------------
        # 1. Diagnose learner state
        # -------------------------------
        question = input_data["question"].lower()

        confusion_triggers = [
            "don't understand",
            "confused",
            "make it simpler",
            "again",
            "what does this mean"
        ]

        if any(trigger in question for trigger in confusion_triggers):
            tutor_state["confusion_level"] += 0.2
            tutor_state["clarification_requests"] += 1
        else:
            tutor_state["confusion_level"] = max(
                tutor_state["confusion_level"] - 0.1, 0
            )

        tutor_state["confusion_level"] = min(tutor_state["confusion_level"], 1.0)

        # Decide explanation style
        if tutor_state["confusion_level"] > 0.6:
            explanation_style = "very simple, analogy-based"
        elif tutor_state["confusion_level"] > 0.3:
            explanation_style = "simplified"
        else:
            explanation_style = "normal depth"

        tutor_state["last_explanation_style"] = explanation_style

        # -------------------------------
        # 2. Generate explanation
        # -------------------------------
        prompt = f"""
You are an empathetic professor.

Teaching style: {explanation_style}

NOTES:
{input_data['notes']}

STUDENT QUESTION:
{input_data['question']}

Rules:
- Explain clearly
- Use examples if helpful
- Do NOT quiz
- Do NOT mention games
- End by asking ONE gentle check-for-understanding question
"""

        response = self.model.generate_content(prompt)
        explanation_text = response.text

        # -------------------------------
        # 3. Evaluate understanding signal
        # -------------------------------
        understanding_confirmations = [
            "i get it",
            "i understand",
            "makes sense",
            "okay now"
        ]

        if any(phrase in question for phrase in understanding_confirmations):
            tutor_state["understood"] = True

        return {
            "agent": self.name,
            "explanation": explanation_text,
            "confusion_level": tutor_state["confusion_level"],
            "understood": tutor_state["understood"],
            "explanation_style": explanation_style
        }

