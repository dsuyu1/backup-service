import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET

from test_backup import ROOT, PWSH


class ArtifactTests(unittest.TestCase):
    def test_all_powershell_files_parse(self):
        # Parse only: Windows-only APIs are not executed by this check.
        command = r'''$ErrorActionPreference='Stop'; $bad=0; Get-ChildItem -LiteralPath $env:VISI_SCRIPTS -Filter *.ps1 | ForEach-Object { $tokens=$null; $errors=$null; $null=[System.Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$tokens,[ref]$errors); if ($errors.Count) { $errors | Out-String | Write-Output; $bad++ } }; exit $bad'''
        import os
        p = subprocess.run([str(PWSH), '-NoProfile', '-Command', command], capture_output=True, text=True,
                           env=dict(os.environ, VISI_SCRIPTS=str(ROOT / 'scripts')))
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_exported_task_is_disabled_system_and_overlap_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'task.xml'
            command = [str(PWSH), '-NoProfile', '-File', str(ROOT / 'scripts/Export-VisiTaskXml.ps1'),
                       '-OutputPath', str(path)]
            p = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            doc = ET.parse(path)
            ns = {'t': 'http://schemas.microsoft.com/windows/2004/02/mit/task'}
            def value(xpath): return doc.find(xpath, ns).text
            self.assertEqual(value('t:Settings/t:Enabled'), 'false')
            self.assertEqual(value('t:Settings/t:MultipleInstancesPolicy'), 'IgnoreNew')
            self.assertEqual(value('t:Principals/t:Principal/t:UserId'), 'S-1-5-18')
            self.assertNotIn('Bypass', value('t:Actions/t:Exec/t:Arguments'))
            self.assertIn('pwsh.exe', value('t:Actions/t:Exec/t:Command'))
            again = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(again.returncode, 0)

    def test_example_contains_no_client_credentials(self):
        example = json.loads((ROOT / 'config/backup.example.json').read_text())
        self.assertEqual(example['schemaVersion'], 1)
        self.assertIn('example.org', example['pingUrl'])
        self.assertNotIn('password', example)


if __name__ == '__main__':
    unittest.main(verbosity=2)
