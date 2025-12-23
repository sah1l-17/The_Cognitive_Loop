from agents.ingestion_agent import IngestionAgent
from agents.tutor_agent import TutorAgent
from agents.game_master_agent import GameMasterAgent
from core.session_state import SessionState
from core.routing import decide_route

class OrchestratorAgent:
    def __init__(self):
        self.ingestion_agent = IngestionAgent()
        self.tutor_agent = TutorAgent()
        self.game_master_agent = GameMasterAgent()

    async def handle(self, input_data: dict, session: SessionState):
        """
        Central entry point for ALL user interactions.
        """

        route = decide_route(input_data, session)

        if route == "ingestion":
            result = await self.ingestion_agent.run(input_data)
            session.ingested_content = result
            session.last_agent = "ingestion"
            
            # Extract and set the primary concept
            if result.get("core_concepts") and len(result["core_concepts"]) > 0:
                session.current_concept = result["core_concepts"][0]

            return {
                "status": "ingested",
                "message": "Content processed successfully",
                "concepts_found": result.get("core_concepts", [])
            }

        if route == "tutor":
            tutor_input = {
                "question": input_data["question"],
                "notes": session.ingested_content["clean_markdown"]
            }

            # Prepare tutor state
            tutor_state = {
                "confusion_level": session.confusion_level,
                "clarification_requests": session.clarification_requests,
                "understood": session.understood,
                "last_explanation_style": session.last_explanation_style
            }

            result = await self.tutor_agent.run(
                tutor_input,
                tutor_state
            )

            # Update session with tutor state
            session.confusion_level = tutor_state["confusion_level"]
            session.clarification_requests = tutor_state["clarification_requests"]
            session.understood = tutor_state["understood"]
            session.last_explanation_style = tutor_state["last_explanation_style"]
            session.concept_understood = result["understood"]
            session.last_agent = "tutor"

            return result

        if route == "game_master":
            if not session.concept_understood:
                return {
                    "error": "Concept not yet understood. Practice not allowed."
                }
            
            # Use current concept or extract from content if not set
            concept = session.current_concept
            if not concept and session.ingested_content:
                concepts = session.ingested_content.get("core_concepts", [])
                concept = concepts[0] if concepts else "general knowledge"

            game_input = {
                "concept": concept,
                "nuances": input_data.get("nuances", []),
                "game_type": input_data["game_type"]
            }

            result = await self.game_master_agent.run(game_input)
            session.last_agent = "game_master"

            return result
