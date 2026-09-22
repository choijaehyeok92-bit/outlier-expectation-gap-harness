"""The launcher's contract, and the icon it is generated from.

The launcher is shell and PowerShell, so what a Python test can hold is the
part that actually breaks: the two environment variables that have to agree,
the credential file staying out of git, and an icon that can be rebuilt rather
than an opaque blob nobody can change.
"""
import re
import struct
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'


class LauncherTests(unittest.TestCase):
    def test_every_entry_point_exists(self):
        for name in ('start.sh', 'start.command', 'start.ps1', 'start.cmd',
                     'install-shortcut.ps1', 'make_icon.py'):
            self.assertTrue((SCRIPTS / name).exists(), name)

    def test_the_shell_launcher_parses(self):
        for name in ('start.sh', 'start.command'):
            result = subprocess.run(['bash', '-n', str(SCRIPTS / name)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, f'{name}: {result.stderr}')

    def test_both_launchers_set_the_two_variables_that_must_agree(self):
        """NEXT_PUBLIC_API_BASE is baked into the web bundle and WEB_ORIGINS is
        the API's CORS list. Setting one without the other yields a page that
        renders and then fetches nothing, with the evidence only in a console."""
        for name in ('start.sh', 'start.ps1'):
            text = (SCRIPTS / name).read_text(encoding='utf-8')
            self.assertIn('WEB_ORIGINS', text, name)
            self.assertIn('NEXT_PUBLIC_API_BASE', text, name)

    def test_the_windows_launcher_avoids_powershell_7_only_syntax(self):
        """start.cmd runs Windows PowerShell 5.1, where `??` is a parse error."""
        text = (SCRIPTS / 'start.ps1').read_text(encoding='utf-8')
        code = '\n'.join(line for line in text.splitlines()
                         if not line.strip().startswith('#'))
        self.assertNotRegex(code, r'\?\?')

    def test_every_powershell_script_keeps_its_utf8_bom(self):
        """Windows PowerShell 5.1 decodes a BOM-less .ps1 in the system ANSI
        code page. On Korean Windows that is CP949, and this file's own Korean
        strings are what it mis-decodes — the third byte of 중 (EC A4 91) is a
        valid CP949 lead byte, so it swallows the closing quote after it. The
        string then runs on and the parse fails at a brace many lines later
        that has nothing wrong with it. This exact failure has happened."""
        for name in ('start.ps1', 'install-shortcut.ps1'):
            raw = (SCRIPTS / name).read_bytes()
            self.assertEqual(raw[:3], b'\xef\xbb\xbf', f'{name} lost its BOM')

    def test_the_bom_is_what_stands_between_the_scripts_and_that_failure(self):
        """Names the hazard rather than trusting a comment about it: if a
        quote-swallowing sequence is present, a BOM must be too."""
        def swallows_a_quote(raw: bytes) -> bool:
            i = 0
            while i < len(raw) - 1:
                if 0x81 <= raw[i] <= 0xFE:
                    if raw[i + 1] in (0x27, 0x22):        # ' or "
                        return True
                    i += 2
                    continue
                i += 1
            return False

        for name in ('start.ps1', 'install-shortcut.ps1'):
            raw = (SCRIPTS / name).read_bytes()
            body = raw[3:] if raw[:3] == b'\xef\xbb\xbf' else raw
            if swallows_a_quote(body):
                self.assertEqual(raw[:3], b'\xef\xbb\xbf',
                                 f'{name} has a byte pair that eats a quote under CP949 '
                                 'and no BOM to stop it being read that way')

    def test_the_batch_wrapper_is_ascii(self):
        """cmd.exe decodes a .cmd in the console's OEM code page — a third
        encoding nobody chose. A mis-decoded batch file fails in ways that look
        like something else entirely."""
        raw = (SCRIPTS / 'start.cmd').read_bytes()
        raw.decode('ascii')                      # raises if anything is not

    def test_the_windows_files_are_crlf(self):
        for name in ('start.ps1', 'install-shortcut.ps1', 'start.cmd'):
            raw = (SCRIPTS / name).read_bytes()
            self.assertNotIn(b'\n', raw.replace(b'\r\n', b''), f'{name} has a bare LF')

    def test_git_keeps_the_windows_line_endings(self):
        attrs = (ROOT / '.gitattributes').read_text(encoding='utf-8')
        for pattern in ('*.ps1', '*.cmd'):
            self.assertRegex(attrs, re.escape(pattern) + r'\s+text\s+eol=crlf')

    def test_node_tools_are_launched_through_cmd_not_a_resolved_path(self):
        """Node ships both `npx` (an extensionless shim) and `npx.cmd`.
        `Get-Command npx` returns the first, and `Start-Process` cannot execute
        it — "%1은(는) 올바른 Win32 응용 프로그램이 아닙니다". cmd.exe applies
        PATHEXT and finds the .cmd. This has broken once."""
        text = (SCRIPTS / 'start.ps1').read_text(encoding='utf-8-sig')
        for name in ('npm', 'npx'):
            self.assertNotRegex(text, rf'\${name}\w*\.Source',
                                f'{name} must not be invoked by resolved path')
        for match in re.finditer(r'(?:Start-Process|Invoke-Native)\s+(?:-FilePath\s+)?(\S+)', text):
            launcher = match.group(1)
            self.assertNotIn('npx', launcher)
            self.assertNotIn('npm', launcher)

    def test_the_web_server_is_started_via_the_command_processor(self):
        text = (SCRIPTS / 'start.ps1').read_text(encoding='utf-8-sig')
        self.assertRegex(text, r'Start-Process -FilePath \$env:ComSpec')
        self.assertRegex(text, r"'/c',\s*'npx',\s*'next',\s*'dev'")

    def test_the_cmd_wrapper_does_not_change_the_machines_policy(self):
        """Asking somebody to loosen a security setting to launch an app is not
        a reasonable thing to ask, so the bypass is scoped to the one call."""
        text = (SCRIPTS / 'start.cmd').read_text(encoding='utf-8')
        self.assertIn('-ExecutionPolicy Bypass', text)
        self.assertNotIn('Set-ExecutionPolicy', text)

    def test_no_launcher_carries_a_credential(self):
        for name in ('start.sh', 'start.ps1', 'start.cmd', 'install-shortcut.ps1'):
            text = (SCRIPTS / name).read_text(encoding='utf-8')
            self.assertNotRegex(text, r'sk-[A-Za-z0-9]{12,}', name)


class EnvFileTests(unittest.TestCase):
    def test_the_template_is_committed_and_the_secret_is_not(self):
        self.assertTrue((ROOT / '.env.example').exists())
        ignored = (ROOT / '.gitignore').read_text(encoding='utf-8').splitlines()
        self.assertIn('.env', [line.strip() for line in ignored])

    def test_git_actually_ignores_it(self):
        result = subprocess.run(['git', 'check-ignore', '.env'],
                                cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, 'git does not ignore .env')

    def test_the_template_holds_no_value(self):
        """A template with a real key in it is a key in the repository."""
        for line in (ROOT / '.env.example').read_text(encoding='utf-8').splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            name, _, value = stripped.partition('=')
            if name.strip() == 'SEC_USER_AGENT':
                continue            # a contact placeholder, not a credential
            self.assertEqual(value.strip(), '', f'{name} carries a value')

    def test_the_template_names_every_variable_the_app_reads(self):
        text = (ROOT / '.env.example').read_text(encoding='utf-8')
        for variable in ('SEC_USER_AGENT', 'OPENDART_API_KEY', 'POLYGON_API_KEY',
                         'OPENAI_API_KEY', 'ANTHROPIC_API_KEY'):
            self.assertIn(variable, text, variable)


class IconTests(unittest.TestCase):
    def test_the_icon_regenerates_byte_for_byte(self):
        """A committed binary nobody can regenerate is one nobody can change."""
        before = {path: path.read_bytes() for path in
                  (ROOT / 'assets' / 'harness.ico', ROOT / 'assets' / 'harness.png',
                   ROOT / 'apps' / 'web' / 'public' / 'favicon.ico',
                   ROOT / 'apps' / 'web' / 'public' / 'icon.png')}
        subprocess.run([sys.executable, str(SCRIPTS / 'make_icon.py')],
                       cwd=ROOT, capture_output=True, check=True)
        for path, payload in before.items():
            self.assertEqual(path.read_bytes(), payload, path.name)

    def test_the_ico_is_a_valid_container(self):
        raw = (ROOT / 'assets' / 'harness.ico').read_bytes()
        reserved, kind, count = struct.unpack('<HHH', raw[:6])
        self.assertEqual((reserved, kind), (0, 1))
        self.assertGreaterEqual(count, 4)
        for index in range(count):
            entry = raw[6 + 16 * index:22 + 16 * index]
            size, _, _, _, planes, bpp, length, offset = struct.unpack('<BBBBHHII', entry)
            self.assertEqual(bpp, 32)
            self.assertEqual(raw[offset:offset + 8], b'\x89PNG\r\n\x1a\n',
                             'each entry is a PNG payload')
            self.assertLessEqual(offset + length, len(raw))

    def test_the_png_declares_the_size_it_claims(self):
        raw = (ROOT / 'assets' / 'harness.png').read_bytes()
        self.assertEqual(raw[:8], b'\x89PNG\r\n\x1a\n')
        width, height = struct.unpack('>II', raw[16:24])
        self.assertEqual((width, height), (256, 256))


if __name__ == '__main__':
    unittest.main()
