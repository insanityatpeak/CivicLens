"""Provider tests use httpx.MockTransport: they check request shape, parsing, error mapping and fallback ORDER, not live behaviour."""
import json

import httpx
import pytest

from civiclens.config import ConfigError, Settings
from civiclens.providers import (
    FallbackChain,
    MockProvider,
    OpenAICompatProvider,
    ProviderError,
    get_provider,
)
from civiclens.providers.base import ModelProvider, ProviderResult


def settings(**kw):
    base = {"providers": ("groq", "openrouter"), "gemini_model": "g", "gemini_api_key": None, "groq_model": "gm",
            "groq_api_key": None, "openrouter_model": "om", "openrouter_api_key": None}
    return Settings(**{**base, **kw})


def provider(handler, name="groq"):
    return OpenAICompatProvider(name, "https://example.test/v1/", "SECRET", "m", client=httpx.Client(transport=httpx.MockTransport(handler)))


def ok(text="{}"):
    return httpx.Response(200, json={"model": "served-model", "choices": [{"message": {"content": text}}],
                                     "usage": {"prompt_tokens": 3, "completion_tokens": 2}})


def test_request_shape_with_image():
    seen = {}

    def handler(req):
        seen["url"], seen["auth"], seen["body"] = str(req.url), req.headers["authorization"], json.loads(req.content)
        return ok("hello")

    res = provider(handler).generate("describe", b"\xff\xd8img", "image/jpeg")
    assert seen["url"] == "https://example.test/v1/chat/completions" and seen["auth"] == "Bearer SECRET"
    parts = seen["body"]["messages"][0]["content"]
    assert parts[0] == {"type": "text", "text": "describe"}
    assert parts[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert res.text == "hello" and res.model == "groq:served-model" and res.usage == {"prompt_tokens": 3, "output_tokens": 2}


def test_text_only_has_no_image_part():
    def handler(req):
        assert len(json.loads(req.content)["messages"][0]["content"]) == 1
        return ok("x")

    provider(handler).generate("hi")


@pytest.mark.parametrize("resp", [httpx.Response(429, text="rate limited"), httpx.Response(500, text="boom"),
                                  httpx.Response(200, text="not json"), httpx.Response(200, json={"choices": []}),
                                  httpx.Response(200, json={"choices": [{"message": {"content": "  "}}]})])
def test_failures_become_provider_errors(resp):
    with pytest.raises(ProviderError):
        provider(lambda r: resp).generate("hi")


def test_429_message_keeps_status_for_friendly_mapping():
    with pytest.raises(ProviderError, match="429"):
        provider(lambda r: httpx.Response(429, text="slow down")).generate("hi")


def test_network_error_becomes_provider_error():
    def handler(req):
        raise httpx.ConnectError("down")

    with pytest.raises(ProviderError, match="ConnectError"):
        provider(handler).generate("hi")


class Stub(ModelProvider):
    def __init__(self, name, fail=False):
        self.name, self.fail, self.calls = name, fail, 0

    def generate(self, prompt, image_bytes=None, mime_type="image/jpeg"):
        self.calls += 1
        if self.fail:
            raise ProviderError(f"{self.name} down")
        return ProviderResult(text=self.name, model=self.name, latency_s=0)


def test_chain_uses_primary_and_skips_fallback_when_healthy():
    a, b = Stub("a"), Stub("b")
    assert FallbackChain([a, b]).generate("x").text == "a" and b.calls == 0


def test_chain_falls_back_in_order_then_reports_all_failures():
    a, b, c = Stub("a", True), Stub("b"), Stub("c")
    assert FallbackChain([a, b, c]).generate("x").text == "b" and c.calls == 0
    with pytest.raises(ProviderError, match="a down.*b down"):
        FallbackChain([Stub("a", True), Stub("b", True)]).generate("x")


def test_get_provider_order_and_skipping():
    s = settings(groq_api_key="g", openrouter_api_key="o")
    chain = get_provider(s)
    assert isinstance(chain, FallbackChain) and [p.name for p in chain.providers] == ["groq", "openrouter"]
    only = get_provider(settings(openrouter_api_key="o"))
    assert isinstance(only, OpenAICompatProvider) and only.name == "openrouter"
    assert get_provider(settings(groq_api_key="g")).name == "groq"


def test_default_chain_is_groq_then_openrouter_then_gemini(monkeypatch):
    for k in ("CIVICLENS_PROVIDER", "GROQ_API_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr("civiclens.config.load_dotenv", lambda: None)
    from civiclens.config import load_settings

    assert load_settings().providers == ("groq", "openrouter", "gemini")
    chain = get_provider(settings(providers=("groq", "openrouter", "gemini"), groq_api_key="g", openrouter_api_key="o", gemini_api_key="k"))
    assert [p.name for p in chain.providers] == ["groq", "openrouter", "gemini"]
    skipped = get_provider(settings(providers=("groq", "openrouter", "gemini"), groq_api_key="g", gemini_api_key="k"))
    assert [p.name for p in skipped.providers] == ["groq", "gemini"]


def test_get_provider_errors_and_mock():
    with pytest.raises(ConfigError, match="GROQ_API_KEY"):
        get_provider(settings())
    with pytest.raises(ValueError, match="Unknown"):
        get_provider(settings(providers=("nope",)))
    assert isinstance(get_provider(settings(providers=("mock",))), MockProvider)


def test_openrouter_reasoning_is_off_by_default_and_sent_in_the_body():
    chain = get_provider(settings(openrouter_api_key="o"))
    assert chain._extra_body == {"reasoning": {"enabled": False}}
    assert get_provider(settings(openrouter_api_key="o", openrouter_reasoning=True))._extra_body == {}


def test_extra_body_is_merged_into_the_request():
    seen = {}

    def handler(req):
        seen.update(json.loads(req.content))
        return ok("x")

    p = OpenAICompatProvider("openrouter", "https://example.test/v1", "k", "m", extra_body={"reasoning": {"enabled": False}},
                             client=httpx.Client(transport=httpx.MockTransport(handler)))
    p.generate("hi")
    assert seen["reasoning"] == {"enabled": False} and seen["model"] == "m"
