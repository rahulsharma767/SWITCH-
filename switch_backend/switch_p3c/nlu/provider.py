"""Optional LLM provider for correction interpretation (OpenAI-compatible chat-completions endpoint).

Credentials come from environment variables only. If the provider is unset, times out, errors, or returns malformed
data, `llm_draft` raises ProviderError and the caller falls back to deterministic rules, recording `fallback_reason`.
NOTE: no live provider was available in the development sandbox, so only the failure/validation paths are tested (with fakes).
"""
from __future__ import annotations
import json
from typing import Callable, Optional

from .. import config
from ..contracts import (Ambiguity, Condition, ExpectedBehavior, InterpretRequest, InterpretationProvenance, RequirementDraft, Scope)
from .catalog import Catalog

SYSTEM = ("You convert a household correction into JSON for a smart-home requirement. Output ONLY a JSON object with keys: "
          "title, scope{kind,id}, preconditions[{signal,op,value}], expected_behavior{device_id,capability,relation,value,comparator}|null, "
          "ambiguities[{field,reason,question,options}], heuristic_confidence. relation in must_not_set|must_set|must_remain. "
          "Use ONLY device ids, signals and routines from the provided catalog. If anything is unclear, add an ambiguity instead of guessing. "
          "Never decide PASS/FAIL.")


class ProviderError(Exception):
    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}")
        self.reason, self.detail = reason, detail


class LLMProvider:
    name = "abstract"

    def complete(self, system: str, user: str, timeout_s: float) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class OpenAICompatibleProvider(LLMProvider):
    name = "openai_compatible"

    def __init__(self, base_url: str, api_key: str, model: str, post: Optional[Callable] = None):
        self.base_url, self.api_key, self.model = base_url.rstrip("/"), api_key, model
        self._post = post

    @classmethod
    def from_env(cls) -> Optional["OpenAICompatibleProvider"]:
        if not (config.LLM_BASE_URL and config.LLM_API_KEY and config.LLM_MODEL):
            return None
        return cls(config.LLM_BASE_URL, config.LLM_API_KEY, config.LLM_MODEL)

    def complete(self, system: str, user: str, timeout_s: float) -> str:
        import requests
        post = self._post or requests.post
        try:
            r = post(f"{self.base_url}/chat/completions", timeout=timeout_s,
                     headers={"Authorization": f"Bearer {self.api_key}"},
                     json={"model": self.model, "temperature": 0, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]})
        except requests.Timeout as e:
            raise ProviderError("provider_timeout", str(e))
        except requests.RequestException as e:
            raise ProviderError("provider_unavailable", type(e).__name__)
        if r.status_code != 200:
            raise ProviderError("provider_unavailable", f"http {r.status_code}")
        try:
            return r.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as e:
            raise ProviderError("provider_malformed_response", type(e).__name__)


def llm_draft(provider: LLMProvider, req: InterpretRequest, cat: Catalog) -> RequirementDraft:
    catalog_view = {"devices": {k: v.capabilities for k, v in cat.devices.items()}, "routines": list(cat.routines), "signals": cat.signals}
    user = json.dumps({"statement": req.text, "context": {k: v for k, v in req.context.items() if k in ("selected_device_id", "selected_routine_id")},
                       "catalog": catalog_view}, default=list)
    try:
        raw = provider.complete(SYSTEM, user, config.LLM_TIMEOUT_S)
    except ProviderError:
        raise
    except TimeoutError as e:
        raise ProviderError("provider_timeout", str(e))
    except Exception as e:
        raise ProviderError("provider_unavailable", type(e).__name__)
    if not isinstance(raw, str):
        raise ProviderError("provider_malformed_response", "non-string")
    txt = raw.strip()
    if txt.startswith("```"):
        txt = txt.strip("`")
        txt = txt[txt.find("{"):]
    try:
        obj = json.loads(txt)
    except json.JSONDecodeError as e:
        raise ProviderError("provider_malformed_json", str(e)[:80])
    if not isinstance(obj, dict):
        raise ProviderError("provider_malformed_json", "not an object")
    allowed = {"title", "scope", "preconditions", "expected_behavior", "ambiguities", "heuristic_confidence"}
    extra = set(obj) - allowed
    if extra:
        raise ProviderError("provider_schema_invalid", f"unexpected keys {sorted(extra)}")
    eb = obj.get("expected_behavior")
    d = RequirementDraft(
        household_id=req.household_id, title=str(obj.get("title", ""))[:140] or "LLM draft", source_correction=req.text,
        scope=Scope(**obj["scope"]), preconditions=[Condition(**c) for c in obj.get("preconditions", [])],
        expected_behavior=ExpectedBehavior(**eb) if eb else None,
        ambiguities=[Ambiguity(**a) for a in obj.get("ambiguities", [])],
        provenance=InterpretationProvenance(interpreter="llm_provider", provider_name=provider.name,
                                            heuristic_confidence=min(1.0, max(0.0, float(obj.get("heuristic_confidence", 0.5))))))
    if d.expected_behavior is None and not d.ambiguities:
        d.ambiguities.append(Ambiguity(field="expected_behavior", reason="LLM returned no expected behavior", question="What should happen?"))
    d.needs_clarification = bool(d.ambiguities)
    if d.expected_behavior:
        from .catalog import Catalog as _C  # noqa
        d.room = cat.devices[d.expected_behavior.device_id].room if d.expected_behavior.device_id in cat.devices else None
    return d
