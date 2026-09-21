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
        """Which backends can actually answer today.

        `active` is always on. `conditional` is on only when its declared data
        is present, which is what lets a field like `revenue_cagr_3y` compile
        after `screen build` and stay an explicit unresolved condition before
        it — rather than silently matching nothing either way.
        """
        live = set()
        for name, row in self.backends.items():
            status = row.get('status')
            if status == 'active':
                live.add(name)
            elif status == 'conditional' and self._has_data(row):
                live.add(name)
        return live

    @staticmethod
    def _has_data(backend: dict) -> bool:
        pattern = backend.get('data_glob')
        return bool(pattern) and any(ROOT.glob(pattern))

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
