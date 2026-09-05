from pathlib import Path

from streamlit.testing.v1 import AppTest

from app.llm.fake import FakeLLMProvider
from app.rag.retriever import InMemoryRetriever


def test_chat_displays_streamed_graph_result(monkeypatch):
    class Model(FakeLLMProvider):
        def __init__(self, *args, **kwargs):
            pass
    monkeypatch.setattr("app.llm.ollama.OllamaProvider", Model)
    monkeypatch.setattr("app.health.health_check", lambda *a: {
        "healthy": True, "vector_document_count": 1, "guidance": []})
    monkeypatch.setattr("app.rag.retriever.ChromaRetriever", lambda *a: InMemoryRetriever([
        {"content": "malware isolate preserve evidence process telemetry", "metadata": {"filename": "malware.md"}}]))
    app = AppTest.from_file(Path("app/ui/streamlit_app.py").resolve(), default_timeout=20).run()
    assert not app.exception
    app.chat_input[0].set_value("PowerShell malware executed").run()
    assert not app.exception
    assert any("MEDIUM" in item.value for item in app.markdown)
    assert len(app.session_state["messages"]) == 2
