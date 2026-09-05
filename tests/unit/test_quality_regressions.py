import httpx
import pytest

from app.agent.nodes.common import timed
from app.agent.nodes.generator import make_generator
from app.agent.nodes.verifier import make_verifier
from app.agent.schemas import VerificationResult
from app.llm.fake import FakeLLMProvider
from app.llm.ollama import OllamaProvider
from app.rag.graph import build_rag_graph
from app.rag.retriever import InMemoryRetriever
from app.tools.knowledge_search import KnowledgeSearchTool
from evaluation.metrics import evaluate_case, summarize


def test_metrics_reject_invented_source_and_allow_unscored_guidance():
    case = {"id": "guidance", "expected_incident_type": "general_security_question",
            "expected_sources": ["real.md"], "expected_risk_level": None, "required_concepts": ["preserve"]}
    result = {"incident_type": "general_security_question", "verification_passed": True,
              "final_answer": "preserve evidence real.md invented.pdf",
              "reranked_documents": [{"metadata": {"filename": "real.md"}}]}
    record = evaluate_case(case, result)
    assert record["risk_agreement"]
    assert record["source_correctness"] == 0.5
    assert not record["end_to_end_success"]
    result["final_answer"] = "preserve evidence real.md"
    record = evaluate_case(case, result)
    assert record["end_to_end_success"]
    assert summarize([record])["end_to_end_success_rate"] == 1


def test_retry_timings_accumulate(monkeypatch):
    ticks = iter([10.0, 12.5])
    monkeypatch.setattr("app.agent.nodes.common.time.perf_counter", lambda: next(ticks))
    value, timings = timed({"timings": {"generation": 3.0}}, "generation", lambda: "answer")
    assert value == "answer"
    assert timings["generation"] == 5.5


def test_health_requires_exact_model_tag(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: httpx.Response(
        200, json={"models": [{"name": "qwen3:4b"}]}, request=httpx.Request("GET", "http://localhost")))
    assert not OllamaProvider("http://localhost", "qwen3:8b").health()["model_available"]


def test_rag_uses_tool_and_honors_top_k(monkeypatch):
    calls = []
    original = KnowledgeSearchTool.invoke
    def invoke(self, query):
        calls.append(query)
        return original(self, query)
    monkeypatch.setattr(KnowledgeSearchTool, "invoke", invoke)
    documents = [{"content": "malware isolate evidence", "metadata": {"filename": f"{i}.md"}} for i in range(4)]
    result = build_rag_graph(FakeLLMProvider(), InMemoryRetriever(documents), top_k=1).invoke(
        {"user_query": "malware", "max_rag_retries": 0})
    assert calls
    assert len(result["reranked_documents"]) == 1


def test_general_answer_always_has_authoritative_sections():
    class Model(FakeLLMProvider):
        def generate(self, system_prompt, user_prompt):
            return "## Incident classification\nwrong\n## Risk level\nCRITICAL 99/100\n## Immediate recommended actions\nPreserve evidence.\n## Sources used\n- invented.pdf"
    result = make_generator(Model())({"user_query": "guidance", "incident_type": "general_security_question"})
    answer = result["draft_answer"]
    assert "Not calculated" in answer
    assert "general_security_question" in answer
    assert "CRITICAL" not in answer
    assert "invented.pdf" not in answer


def test_verifier_cannot_approve_invented_source():
    class PermissiveModel(FakeLLMProvider):
        def generate_structured(self, *args):
            return VerificationResult(verification_passed=True, grounding_score=1, completeness_score=1)
    result = make_verifier(PermissiveModel())({"user_query": "phishing", "draft_answer": "invented.pdf"})
    assert not result["verification_passed"]
    assert "Unknown source" in result["verification_feedback"]


def test_risk_model_failure_is_not_low_risk():
    from app.agent.nodes.risk_analysis import make_risk_analyzer
    class BrokenModel(FakeLLMProvider):
        def generate_structured(self, *args):
            raise RuntimeError("offline")
    with pytest.raises(RuntimeError, match="Risk assessment unavailable"):
        make_risk_analyzer(BrokenModel())({"user_query": "incident"})
