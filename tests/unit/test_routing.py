from app.agent.routing import route_after_plan, route_after_verification


def test_route_selects_rag_risk_or_generation() -> None:
    assert route_after_plan({"requires_rag": True}) == "rag"
    assert route_after_plan({"requires_rag": False, "requires_risk_analysis": True}) == "risk"
    assert route_after_plan({}) == "generate"


def test_verification_retry_is_bounded() -> None:
    assert route_after_verification({"verification_passed": True}, 2) == "finalize"
    assert route_after_verification({"verification_passed": False, "requires_rag": True, "retry_count": 1}, 2) == "retry"
    assert route_after_verification({"verification_passed": False, "requires_rag": True, "retry_count": 2}, 2) == "finalize"
    assert route_after_verification({"verification_passed": False, "requires_rag": False}, 2) == "finalize"

