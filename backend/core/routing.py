from core.session_state import SessionState


def decide_route(input_data: dict, session: SessionState) -> str:
    """
    Returns which agent should handle the input.
    """

    if input_data["type"] in ["pdf", "image", "text"]:
        return "ingestion"

    if input_data["type"] == "question":
        return "tutor"

    if input_data["type"] == "practice":
        return "game_master"

    raise ValueError("Unknown input type")
