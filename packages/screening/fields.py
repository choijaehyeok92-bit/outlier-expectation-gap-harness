"""The field registry: the only identifiers a ScreeningSpec is allowed to name.

An allowlist is what keeps an LLM out of the query layer. The model may propose
a filter, but it can only propose one over a field declared in
`config/screening_fields.json`, with the dtype and unit that file gives it. A
field whose backend is not active yet is still a real identifier: naming it
produces an explicit unresolved condition, which is very different from a
filter that quietly disappears.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / 'config' / 'screening_fields.json'
LEXICON_PATH = ROOT / 'config' / 'screening_lexicon.json'


def load_registry(path=None):
    return json.loads(Path(path or REGISTRY_PATH).read_text(encoding='utf-8'))


def load_lexicon(path=None):
    return json.loads(Path(path or LEXICON_PATH).read_text(encoding='utf-8'))


class Registry:
    def __init__(self, data=None):
        self.data = data or load_registry()
        self.fields = {f['id']: f for f in self.data['fields']}
        self.backends = self.data.get('backends', {})

    def __contains__(self, field_id):
        return field_id in self.fields

    def get(self, field_id):
        return self.fields.get(field_id)

    def active_backends(self):
        return {name for name, row in self.backends.items() if row.get('status') == 'active'}

    def is_available(self, field_id, backend):
        field = self.fields.get(field_id)
        return bool(field) and backend in (field.get('backends') or [])

    def requires_harness_run(self, field_id):
        return bool((self.fields.get(field_id) or {}).get('requires_harness_run'))

    def unit(self, field_id):
        return (self.fields.get(field_id) or {}).get('unit')

    def dtype(self, field_id):
        return (self.fields.get(field_id) or {}).get('dtype')

    def describe(self):
        return [{'id': f['id'], 'group': f['group'], 'dtype': f['dtype'], 'unit': f['unit'],
                 'backends': f.get('backends', []),
                 'requires_harness_run': bool(f.get('requires_harness_run')),
                 'available': any(b in self.active_backends() for b in f.get('backends', [])),
                 'note': f.get('note')}
                for f in self.data['fields']]
