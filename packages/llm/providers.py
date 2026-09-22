"""LLM provider abstraction.

The contract is narrow on purpose. A provider is handed a stage name, a prompt
and a JSON Schema, and must return an object that validates against that
schema. It is never asked for SQL, for a metric, for a score or for a Hard Veto
status — those come from the harness and the deterministic compiler — and a
response that does not validate is an error, not something to be repaired.

`FixtureProvider` reads canned responses from disk. It exists so the whole
pipeline can be run and tested offline and deterministically, and so a fixture
can be used to prove that malformed model output is actually rejected.

API keys are read from the environment inside this module and never travel into
a spec, a report or an API response.
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path


class LLMError(RuntimeError):
    """A provider failure phrased for the operator."""


class LLMProvider:
    name = 'abstract'

    def __init__(self, model=None):
        self.model = model

    def complete_json(self, *, stage, prompt, schema, context=None):
        raise NotImplementedError

    def metadata(self, stage):
        return {'stage': stage, 'provider': self.name, 'model': self.model}


def _validate(payload, schema, stage):
    if schema is None:
        return payload
    import jsonschema
    try:
        jsonschema.validate(payload, schema)
    except jsonschema.ValidationError as error:
        raise LLMError(f'{stage}: model output failed schema validation at '
                       f"{'/'.join(str(p) for p in error.absolute_path) or '<root>'}: {error.message}") from error
    return payload


class FixtureProvider(LLMProvider):
    """Deterministic responses from `<root>/<stage>.json`, or from a dict in memory."""

    name = 'fixture'

    def __init__(self, root=None, responses=None, model='fixture-v1'):
        super().__init__(model)
        self.root = Path(root) if root else None
        self.responses = dict(responses or {})

    def complete_json(self, *, stage, prompt, schema, context=None):
        if stage in self.responses:
            payload = self.responses[stage]
        elif self.root is not None:
            # `agent:EV` is a fine stage name and a hostile filename; keep the
            # two apart rather than committing colons to a repository.
            path = self.root / f"{str(stage).replace(':', '_')}.json"
            if not path.exists():
                raise LLMError(f'{stage}: no fixture at {path}')
            payload = json.loads(path.read_text(encoding='utf-8'))
        else:
            raise LLMError(f'{stage}: no fixture configured')
        return _validate(payload, schema, stage)


def _post_json(url, headers, body, timeout=120):
    request = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'),
                                     headers={**headers, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise LLMError(f'{url} -> HTTP {error.code}: {error.read()[:400].decode("utf-8", "replace")}') from error
    except Exception as error:
        raise LLMError(f'{url} -> {type(error).__name__}: {error}') from error


def _extract_json(text, stage):
    text = (text or '').strip()
    if text.startswith('```'):
        text = text.split('```', 2)[1]
        text = text.split('\n', 1)[1] if '\n' in text else text
        text = text.rsplit('```', 1)[0]
    try:
        return json.loads(text)
    except ValueError as error:
        raise LLMError(f'{stage}: provider did not return JSON ({error})') from error


class AnthropicProvider(LLMProvider):
    name = 'anthropic'
    endpoint = 'https://api.anthropic.com/v1/messages'
    version = '2023-06-01'

    def __init__(self, model='claude-opus-5', api_key=None, transport=None, max_tokens=8192):
        super().__init__(model)
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.transport = transport or _post_json
        self.max_tokens = max_tokens

    def complete_json(self, *, stage, prompt, schema, context=None):
        if not self.api_key:
            raise LLMError('ANTHROPIC_API_KEY is not set')
        body = {'model': self.model, 'max_tokens': self.max_tokens,
                'system': ('Return a single JSON object and nothing else. It must validate against the '
                           'supplied JSON Schema. Do not write SQL, do not compute financial metrics, and '
                           'do not produce a score, an archetype or a Hard Veto status.'),
                'messages': [{'role': 'user', 'content': prompt}]}
        payload = self.transport(self.endpoint,
                                 {'x-api-key': self.api_key, 'anthropic-version': self.version}, body)
        blocks = payload.get('content') or []
        text = ''.join(b.get('text', '') for b in blocks if isinstance(b, dict))
        return _validate(_extract_json(text, stage), schema, stage)


class OpenAIProvider(LLMProvider):
    name = 'openai'
    endpoint = 'https://api.openai.com/v1/chat/completions'

    def __init__(self, model='gpt-5.6', api_key=None, transport=None):
        super().__init__(model)
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.transport = transport or _post_json

    def complete_json(self, *, stage, prompt, schema, context=None):
        if not self.api_key:
            raise LLMError('OPENAI_API_KEY is not set')
        body = {'model': self.model, 'response_format': {'type': 'json_object'},
                'messages': [
                    {'role': 'system', 'content': (
                        'Return a single JSON object that validates against the supplied JSON Schema. '
                        'Never write SQL, never compute a financial metric, never produce a score, '
                        'an archetype or a Hard Veto status.')},
                    {'role': 'user', 'content': prompt}]}
        payload = self.transport(self.endpoint, {'Authorization': f'Bearer {self.api_key}'}, body)
        choices = payload.get('choices') or [{}]
        text = ((choices[0].get('message') or {}).get('content')) or ''
        return _validate(_extract_json(text, stage), schema, stage)


PROVIDERS = {'fixture': FixtureProvider, 'anthropic': AnthropicProvider, 'openai': OpenAIProvider}

# What each provider is, and which environment variable holds its credential.
# `default_model` is the class default; it is a starting point, not a list of
# what the vendor offers — this package deliberately holds no model catalogue,
# so a model string it has never heard of is passed through unchanged.
CATALOGUE = {
    'fixture': {'kind': 'offline', 'spends_money': False, 'env_var': None,
                'default_model': 'fixture-v1',
                'note': '디스크에 저장된 응답을 재생한다. 호출도 과금도 없다.'},
    'anthropic': {'kind': 'api', 'spends_money': True, 'env_var': 'ANTHROPIC_API_KEY',
                  'default_model': 'claude-opus-5',
                  'note': '실제 모델. 호출마다 과금된다.'},
    'openai': {'kind': 'api', 'spends_money': True, 'env_var': 'OPENAI_API_KEY',
               'default_model': 'gpt-5.6',
               'note': '실제 모델. 호출마다 과금된다.'},
}


def describe() -> list:
    """Each provider, and whether its credential is present.

    **Never returns a key, a prefix of one, or its length** — only whether one
    is set. A UI needs to know that picking `anthropic` will fail before
    somebody picks it; it does not need the secret in order to know that, and
    this value is served to a browser.
    """
    rows = []
    for name, meta in CATALOGUE.items():
        env_var = meta['env_var']
        rows.append({'name': name, **{k: v for k, v in meta.items() if k != 'env_var'},
                     'env_var': env_var,
                     'configured': True if env_var is None else bool(os.environ.get(env_var))})
    return rows


def resolve_provider(name, model=None, **kwargs):
    if name not in PROVIDERS:
        raise LLMError(f'unknown provider {name!r}; known: {sorted(PROVIDERS)}')
    factory = PROVIDERS[name]
    return factory(model=model, **kwargs) if model else factory(**kwargs)


def provider_from_env(default='fixture', **kwargs):
    """HARNESS_LLM_PROVIDER / HARNESS_LLM_MODEL, defaulting to the offline fixture provider."""
    return resolve_provider(os.environ.get('HARNESS_LLM_PROVIDER', default),
                            os.environ.get('HARNESS_LLM_MODEL'), **kwargs)
