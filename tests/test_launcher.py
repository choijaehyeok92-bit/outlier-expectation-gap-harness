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
        """A template with a real key in it is a key in the repository — and a
        placeholder contact is worse than empty: copying the template would
        make the harness send `Your Name your@email.com` to SEC, which is
        exactly what it promises not to do."""
        for line in (ROOT / '.env.example').read_text(encoding='utf-8').splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            name, _, value = stripped.partition('=')
            self.assertEqual(value.strip(), '', f'{name} carries a value')

    def test_the_template_names_every_variable_the_app_reads(self):
        text = (ROOT / '.env.example').read_text(encoding='utf-8')
        for variable in ('SEC_USER_AGENT', 'OPENDART_API_KEY', 'POLYGON_API_KEY',
                         'OPENAI_API_KEY', 'ANTHROPIC_API_KEY'):
            self.assertIn(variable, text, variable)


class EnvLoaderTests(unittest.TestCase):
    """A .env written on Windows, read by the shell launcher.

    Notepad saves UTF-8 with a BOM and CRLF endings. Sourced, that file makes
    its first line a command that does not exist and leaves every value with a
    trailing carriage return — and an API key with \r on the end comes back
    from the vendor as simply invalid, which is a long way from the cause.
    """

    NOTEPAD = (b'\xef\xbb\xbf# keys\r\n'
               b'OPENDART_API_KEY=abc123def456\r\n'
               b'\r\n'
               b'POLYGON_API_KEY="pk_test_xyz"\r\n'
               b'SEC_USER_AGENT=Jane Doe jane@example.com\r\n'
               b'  SPACED   =  padded  \r\n'
               b'not a variable\r\n')

    def load(self, payload: bytes) -> dict:
        import tempfile
        loader = re.search(r'^if \[ -f \.env \]; then$.*?^fi$',
                           (SCRIPTS / 'start.sh').read_text(encoding='utf-8'),
                           re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(loader, 'the .env block moved')
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / '.env').write_bytes(payload)
            script = ('say() { :; }\n' + loader.group(0)
                      + '\npython3 -c "import json,os; print(json.dumps(dict(os.environ)))"')
            result = subprocess.run(['bash', '-c', script], cwd=tmp,
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        import json
        return json.loads(result.stdout)

    def test_a_notepad_written_file_is_read_exactly(self):
        env = self.load(self.NOTEPAD)
        self.assertEqual(env.get('OPENDART_API_KEY'), 'abc123def456')
        self.assertEqual(env.get('POLYGON_API_KEY'), 'pk_test_xyz')
        self.assertEqual(env.get('SEC_USER_AGENT'), 'Jane Doe jane@example.com')

    def test_no_value_keeps_a_carriage_return(self):
        for name, value in self.load(self.NOTEPAD).items():
            self.assertNotIn('\r', value, name)

    def test_the_bom_does_not_become_part_of_a_name(self):
        env = self.load(self.NOTEPAD)
        self.assertFalse([k for k in env if k.startswith('\ufeff')])

    def test_surrounding_space_is_dropped_and_inner_space_is_kept(self):
        env = self.load(self.NOTEPAD)
        self.assertEqual(env.get('SPACED'), 'padded')

    def test_a_line_that_is_not_an_assignment_is_skipped(self):
        env = self.load(self.NOTEPAD)
        self.assertNotIn('not a variable', env)

    def test_the_file_cannot_run_anything(self):
        """Parsed, not sourced: a .env sets variables and does nothing else."""
        env = self.load(b'GOOD=yes\n$(touch pwned)\n`touch pwned2`\n')
        self.assertEqual(env.get('GOOD'), 'yes')
        self.assertFalse((ROOT / 'pwned').exists())
        self.assertFalse((ROOT / 'pwned2').exists())

    def test_the_powershell_loader_strips_the_bom_too(self):
        text = (SCRIPTS / 'start.ps1').read_text(encoding='utf-8-sig')
        self.assertIn('TrimStart([char]0xFEFF)', text)


class SetKeyTests(unittest.TestCase):
    """Putting a credential into .env without it reaching the shell's history.

    The reason this is Python and not a PowerShell one-liner: a key typed as
    part of a command is written by PSReadLine to a plain text file that
    survives reboots. Here the command carries the variable's name and the
    value is typed at a prompt.
    """

    def setUp(self):
        import shutil, tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        (self.home / 'scripts').mkdir()
        shutil.copy(SCRIPTS / 'set_key.py', self.home / 'scripts' / 'set_key.py')
        shutil.copy(ROOT / '.env.example', self.home / '.env.example')

    def run_tool(self, args, stdin=None):
        return subprocess.run([sys.executable, str(self.home / 'scripts' / 'set_key.py'), *args],
                              cwd=self.home, input=stdin, capture_output=True, text=True)

    def env_text(self):
        return (self.home / '.env').read_text(encoding='utf-8')

    def test_a_key_lands_in_the_file(self):
        result = self.run_tool(['OPENDART_API_KEY', '--stdin'], stdin='abc123def456')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('OPENDART_API_KEY=abc123def456', self.env_text())

    def test_the_template_comments_survive(self):
        """The line that explains a key is the line somebody reads when it
        stops working."""
        self.run_tool(['POLYGON_API_KEY', '--stdin'], stdin='pk_test')
        self.assertIn('polygon.io', self.env_text())

    def test_setting_it_twice_replaces_rather_than_duplicates(self):
        self.run_tool(['POLYGON_API_KEY', '--stdin'], stdin='first')
        self.run_tool(['POLYGON_API_KEY', '--stdin'], stdin='second')
        text = self.env_text()
        self.assertEqual(text.count('POLYGON_API_KEY='), 1)
        self.assertIn('POLYGON_API_KEY=second', text)

    def test_surrounding_whitespace_is_dropped(self):
        self.run_tool(['POLYGON_API_KEY', '--stdin'], stdin='   pk_test   ')
        self.assertIn('POLYGON_API_KEY=pk_test\n', self.env_text().replace('\r\n', '\n'))

    def test_an_unknown_variable_is_refused(self):
        result = self.run_tool(['OPENDART_KEY', '--stdin'], stdin='x')
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.home / '.env').exists())

    def test_an_empty_value_changes_nothing(self):
        result = self.run_tool(['POLYGON_API_KEY', '--stdin'], stdin='   ')
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.home / '.env').exists())

    def test_a_pasted_newline_is_refused(self):
        result = self.run_tool(['POLYGON_API_KEY', '--stdin'], stdin='good\nbad')
        self.assertEqual(result.returncode, 1)

    def test_a_value_is_never_printed_back(self):
        secret = 'polygon-DO-NOT-ECHO-0123456789'
        written = self.run_tool(['POLYGON_API_KEY', '--stdin'], stdin=secret)
        listed = self.run_tool(['--list'])
        for result in (written, listed):
            self.assertNotIn(secret, result.stdout)
            self.assertNotIn(secret, result.stderr)
        self.assertIn('설정됨', listed.stdout)

    def test_a_value_cannot_be_passed_on_the_command_line(self):
        """By construction: no flag takes one, because a flag that did would
        put the key in the shell's history."""
        text = (SCRIPTS / 'set_key.py').read_text(encoding='utf-8')
        self.assertNotIn("'--value'", text)
        self.assertNotIn("'--key'", text)
        self.assertIn('getpass', text)

    def test_a_notepad_written_file_is_updated_cleanly(self):
        (self.home / '.env').write_bytes(
            b'\xef\xbb\xbf# keys\r\nPOLYGON_API_KEY=old\r\n')
        self.run_tool(['POLYGON_API_KEY', '--stdin'], stdin='new')
        raw = (self.home / '.env').read_bytes()
        self.assertNotEqual(raw[:3], b'\xef\xbb\xbf', 'the BOM is dropped')
        self.assertIn('POLYGON_API_KEY=new', raw.decode('utf-8'))

    def test_listing_an_absent_file_reports_nothing_as_set(self):
        """With no .env, `lines` is the template — whose placeholders are not
        values. Calling them set would send somebody hunting for a key they
        never supplied."""
        result = self.run_tool(['--list'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('설정됨', result.stdout)


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
