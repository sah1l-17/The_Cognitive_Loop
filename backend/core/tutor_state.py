def default_tutor_state():
    return {
        "current_concept": None,
        "confusion_level": 0.0,   # 0 → confident, 1 → very confused
        "last_explanation_style": None,
        "clarification_requests": 0,
        "understood": False
    }
