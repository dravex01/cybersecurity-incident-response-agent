from app.agent.graph import build_agent_graph, initial_state
from app.agent.schemas import IncidentClassification, RiskFactors
from app.config import Settings
from app.llm.fake import FakeLLMProvider
from app.rag.retriever import InMemoryRetriever


def test_end_to_end_fake_llm(tmp_path) -> None:
    settings = Settings(_env_file=None, chroma_path=tmp_path, context_threshold=0.2)
    retriever = InMemoryRetriever(
        [{"content": "malware powershell isolate endpoint preserve evidence investigate process execution", "metadata": {"filename": "malware_response.md"}}]
    )
    result = build_agent_graph(FakeLLMProvider(), retriever, settings).invoke(
        initial_state("Suspicious PowerShell malware executed on a workstation")
    )
    assert result["incident_type"] == "malware"
    assert result["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert result["verification_passed"] is True
    assert "malware_response.md" in result["final_answer"]
    assert len(result["execution_trace"]) >= 10
    assert {"classification", "retrieval", "generation", "verification"} <= result["timings"].keys()


def test_unrelated_query_takes_direct_safe_path(tmp_path) -> None:
    settings = Settings(_env_file=None, chroma_path=tmp_path)
    result = build_agent_graph(FakeLLMProvider(), InMemoryRetriever([]), settings).invoke(
        initial_state("How do I bake a cake?")
    )
    assert result["is_cybersecurity_related"] is False
    assert "scoped to defensive cybersecurity" in result["final_answer"]
    nodes = [item["node"] for item in result["execution_trace"]]
    assert "rag.retrieve_documents" not in nodes


def test_explicit_indicators_recover_weak_structured_outputs(tmp_path) -> None:
    class WeakLLM(FakeLLMProvider):
        def generate_structured(self, system_prompt, user_prompt, schema):
            if schema is IncidentClassification:
                return IncidentClassification(incident_type="unknown", confidence=0.5)
            if schema is RiskFactors:
                return RiskFactors()
            return super().generate_structured(system_prompt, user_prompt, schema)

    settings = Settings(_env_file=None, chroma_path=tmp_path, context_threshold=0.1)
    retriever = InMemoryRetriever(
        [
            {
                "content": "powershell malware isolate endpoint preserve evidence",
                "metadata": {"filename": "malware_response.md"},
            }
        ]
    )
    result = build_agent_graph(WeakLLM(), retriever, settings).invoke(
        initial_state("A Word file launched PowerShell")
    )
    assert result["incident_type"] == "malware"
    assert result["risk_score"] == 20
    assert "20/100" in result["final_answer"]


def test_hungarian_suspicious_login_has_medium_risk(tmp_path) -> None:
    class ConfidentButWrongLLM(FakeLLMProvider):
        def generate_structured(self, system_prompt, user_prompt, schema):
            if schema is IncidentClassification:
                return IncidentClassification(incident_type="unknown", confidence=0.95)
            if schema is RiskFactors:
                return RiskFactors()
            return super().generate_structured(system_prompt, user_prompt, schema)

    settings = Settings(_env_file=None, chroma_path=tmp_path, context_threshold=0.1)
    retriever = InMemoryRetriever(
        [
            {
                "content": "suspicious login validate MFA methods and revoke sessions",
                "metadata": {"filename": "suspicious_login.md"},
            }
        ]
    )
    query = "Egy külföldi IP-ről sikeres belépést és új MFA-eszközt látunk"
    result = build_agent_graph(ConfidentButWrongLLM(), retriever, settings).invoke(
        initial_state(query)
    )
    assert result["incident_type"] == "suspicious_login"
    assert result["risk_score"] == 35
    assert result["risk_level"] == "MEDIUM"
    assert "**suspicious_login**" in result["final_answer"]
    assert "**MEDIUM (35/100)**" in result["final_answer"]


def test_hungarian_customer_export_overrides_out_of_scope_model(tmp_path) -> None:
    class OutOfScopeLLM(FakeLLMProvider):
        def generate_structured(self, system_prompt, user_prompt, schema):
            if schema is IncidentClassification:
                return IncidentClassification(
                    intent="unrelated",
                    incident_type="general_security_question",
                    is_cybersecurity_related=False,
                    requires_rag=False,
                    requires_risk_analysis=False,
                    confidence=0.95,
                )
            if schema is RiskFactors:
                return RiskFactors()
            return super().generate_structured(system_prompt, user_prompt, schema)

    settings = Settings(_env_file=None, chroma_path=tmp_path, context_threshold=0.1)
    retriever = InMemoryRetriever(
        [
            {
                "content": "possible data breach customer export preserve audit logs",
                "metadata": {"filename": "data_breach_response.md"},
            }
        ]
    )
    query = "Egy külső fiók letöltött egy ügyféladat-exportot."
    result = build_agent_graph(OutOfScopeLLM(), retriever, settings).invoke(
        initial_state(query)
    )
    assert result["is_cybersecurity_related"] is True
    assert result["incident_type"] == "data_breach"
    assert result["requires_rag"] is True
    assert result["requires_risk_analysis"] is True
    assert result["risk_score"] == 45
    assert result["risk_level"] == "HIGH"
    assert "scoped to defensive cybersecurity" not in result["final_answer"]
