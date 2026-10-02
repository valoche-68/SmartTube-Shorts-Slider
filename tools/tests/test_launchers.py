"""Exercise native launchers without downloading code or contacting a TV."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1]


class LauncherTest(unittest.TestCase):
    def launch(self, payload, fail_download=False, arguments=()):
        with tempfile.TemporaryDirectory(prefix='shorts launcher ') as directory:
            folder = Path(directory)
            fixture = folder / 'payload.py'
            fixture.write_text(payload, encoding='utf-8')
            env = dict(os.environ, SMARTTUBE_TEST_PAYLOAD=str(fixture),
                       SMARTTUBE_TEST_FAIL='1' if fail_download else '0',
                       TMPDIR=str(folder), TMP=str(folder), TEMP=str(folder))
            if os.name == 'nt':
                powershell = shutil.which('powershell') or shutil.which('pwsh')
                self.assertIsNotNone(powershell)
                harness = folder / 'test.ps1'
                quote = lambda value: "'" + str(value).replace("'", "''") + "'"
                harness.write_text('''
$ErrorActionPreference = 'Stop'
function Invoke-WebRequest {
    param([string]$Uri, [string]$OutFile, [switch]$UseBasicParsing, [int]$TimeoutSec)
    Copy-Item -LiteralPath $env:SMARTTUBE_TEST_PAYLOAD -Destination $OutFile
    if ($env:SMARTTUBE_TEST_FAIL -eq '1') { throw 'Simulated interrupted download' }
}
& ''' + quote(TOOLS / 'start.ps1') + ' ' + ' '.join(map(quote, arguments)), encoding='utf-8')
                command = [powershell, '-NoProfile', '-NonInteractive', '-File', str(harness)]
            else:
                fake_bin = folder / 'bin'
                fake_bin.mkdir()
                curl = fake_bin / 'curl'
                curl.write_text('''#!/bin/sh
while [ "$#" -gt 0 ]; do
    if [ "$1" = --output ]; then shift; target=$1; fi
    shift
done
cp "$SMARTTUBE_TEST_PAYLOAD" "$target"
if [ "$SMARTTUBE_TEST_FAIL" = 1 ]; then exit 22; fi
''')
                curl.chmod(0o700)
                env['PATH'] = str(fake_bin) + os.pathsep + env['PATH']
                command = ['sh', str(TOOLS / 'start.sh'), *arguments]
            result = subprocess.run(command, input='menu answer\n', text=True,
                                    capture_output=True, env=env, timeout=30)
            self.assertEqual(list(folder.glob('smarttube-assistant.*')), [], 'Temporary download must be removed')
            return result

    def test_menu_input_and_arguments_with_spaces_are_preserved(self):
        result = self.launch('import sys,json\nprint(json.dumps([sys.argv[1:],input()]))\n',
                             arguments=['--profile', 'living room'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [['--profile', 'living room'], 'menu answer'])

    def test_partial_download_is_never_executed(self):
        result = self.launch('print("MUST_NOT_RUN")\n', fail_download=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('MUST_NOT_RUN', result.stdout)

    def test_assistant_failure_is_reported_and_download_is_removed(self):
        result = self.launch('raise SystemExit(7)\n')
        self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
