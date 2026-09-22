"""Invariants of the web app that are cheap to break and expensive to notice.

These read the source rather than run a browser: the things worth pinning here
are ones a person would remove as noise, or add without realising the cost.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'apps' / 'web'
APP = WEB / 'app'


def pages() -> list:
    return sorted(APP.glob('*/page.tsx'))


class HydrationTests(unittest.TestCase):
    def test_body_suppresses_extension_written_attributes(self):
        """Grammarly and similar extensions write onto <body> before React
        hydrates, and React reports it as a server/client mismatch. Removing
        this brings back a console error on every page load that says nothing
        about this app — with no extension loaded, every page hydrates clean.
        """
        layout = (APP / 'layout.tsx').read_text(encoding='utf-8')
        self.assertRegex(layout, r'<body\s+suppressHydrationWarning>')
        self.assertIn('extension', layout, 'the reason must stay with the flag')

    def test_it_is_not_used_to_quiet_anything_else(self):
        """One level deep, on one element. Anywhere else it would hide a real
        mismatch instead of a third party's."""
        for path in [APP / 'layout.tsx', *pages()]:
            text = path.read_text(encoding='utf-8')
            self.assertLessEqual(text.count('suppressHydrationWarning'), 1, path.name)

    def test_no_component_renders_a_value_that_differs_per_render(self):
        """`Date.now()`, `new Date()` and `Math.random()` in a rendered tree
        produce a genuine hydration mismatch — the kind the suppression above
        must never be reached for."""
        hazards = re.compile(r'\b(Date\.now\(\)|Math\.random\(\)|new Date\(\))')
        for path in [APP / 'layout.tsx', *pages(), *(WEB / 'components').glob('*.tsx')]:
            found = hazards.findall(path.read_text(encoding='utf-8'))
            self.assertFalse(found, f'{path.name}: {found}')


class NavigationTests(unittest.TestCase):
    def test_every_top_level_page_is_reachable_from_the_nav(self):
        """A page nobody can click is a page nobody uses."""
        layout = (APP / 'layout.tsx').read_text(encoding='utf-8')
        linked = set(re.findall(r"href: '/([a-z-]+)'", layout))
        # Dynamic segments are reached from their own list page, not the nav.
        built = {p.parent.name for p in pages() if not p.parent.name.startswith('[')}
        self.assertEqual(built - linked, set(), 'page exists but is not in the nav')

    def test_the_nav_links_nothing_that_does_not_exist(self):
        layout = (APP / 'layout.tsx').read_text(encoding='utf-8')
        for slug in re.findall(r"href: '/([a-z-]+)'", layout):
            self.assertTrue((APP / slug / 'page.tsx').exists(), slug)


class ApiClientTests(unittest.TestCase):
    def test_pages_reach_the_backend_only_through_the_api_module(self):
        """One place that talks to the backend means one place that handles a
        failure, and one place to look when a route moves."""
        for path in pages():
            text = path.read_text(encoding='utf-8')
            self.assertNotIn('fetch(', text, f'{path.parent.name} calls fetch directly')

    def test_the_api_base_is_configurable(self):
        client = (WEB / 'lib' / 'api.ts').read_text(encoding='utf-8')
        self.assertIn('NEXT_PUBLIC_API_BASE', client)


if __name__ == '__main__':
    unittest.main()
