"""Executable integration tests: real PowerShell, a local HTTP recorder, and real Kopia.

No cloud account or client data. Python standard library only. Linux fault-injection
stub is an executable, not a mock of PowerShell internals.
"""
import hashlib
import http.server
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
PWSH = Path(os.environ.get('VISI_TEST_PWSH', ROOT / '.tools/powershell/pwsh'))
KOPIA = Path(os.environ.get('VISI_TEST_KOPIA', ROOT / '.tools/kopia/kopia-0.23.1-linux-x64/kopia'))
RUNNER = ROOT / 'scripts/Invoke-VisiBackup.ps1'

STUB = '''#!/usr/bin/env python3
import json,os,sys,time
a=sys.argv[1:]; mode=os.environ.get('VISI_STUB_MODE','ok')
if '--version' in a:
 print('0.0.0' if mode=='version' else '0.23.1'); sys.exit(0)
if mode=='hang': time.sleep(30)
if mode=='exit': sys.exit(7)
if mode=='second-fails' and any(x.endswith('/second') for x in a): sys.exit(7)
if mode=='malformed': print('not json'); sys.exit(0)
if mode=='delay': time.sleep(1)
obj={'id':'fake-id','rootEntry':{'obj':'fake-root','summ':{'numFailed':0}},
     'incompleteReason':'', 'stats':{'errorCount':0,'ignoredErrorCount':0,'fileCount':2,'totalSize':25}}
if mode=='partial': obj['stats']['ignoredErrorCount']=1
if mode=='failed-file': obj['rootEntry']['summ']['numFailed']=1
if mode=='incomplete': obj['incompleteReason']='checkpoint'
if mode=='empty': obj['stats']['fileCount']=0
if 'list' in a and mode=='wrong-id': obj['id']='old-snapshot'
print(json.dumps([obj] if 'list' in a else obj))
'''


class Recorder(http.server.BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.server.events.append((self.path, self.headers.get('Content-Length'), self.command))
        self.send_response(self.server.reply_code)
        if self.server.reply_code == 302:
            self.send_header('Location', '/must-not-follow')
        self.end_headers()

    def log_message(self, *args):
        pass


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='visi-backup-test-')
        self.root = Path(self.tmp.name)
        self.state = self.root / 'state'
        self.state.mkdir(mode=0o700)
        self.source = self.root / 'source with spaces ñ [literal]'
        self.source.mkdir()
        (self.source / 'scope.txt').write_text('Synthetic lab data only.\n')
        self.repo_config = self.root / 'repository.config'
        self.repo_config.write_text('{}')
        self.stub = self.root / 'kopia-stub'
        self.stub.write_text(STUB)
        self.stub.chmod(0o700)
        self.server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Recorder)
        self.server.events = []
        self.server.reply_code = 200
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.settings = dict(schemaVersion=1, jobId='synthetic-test', kopiaPath=str(self.stub),
            expectedKopiaVersion='0.23.1', repositoryConfig=str(self.repo_config),
            stateDirectory=str(self.state), pingUrl=f'http://127.0.0.1:{self.server.server_port}/ping/test-secret',
            pingTimeoutSeconds=1, maxRunSeconds=30,
            sources=[dict(path=str(self.source), minimumFileCount=1, requiredFiles=['scope.txt'])])
        self.config = self.root / 'backup.json'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def command(self):
        self.config.write_text(json.dumps(self.settings))
        return [str(PWSH), '-NoLogo', '-NoProfile', '-NonInteractive', '-File', str(RUNNER),
                '-ConfigFile', str(self.config), '-AllowLocalTestEndpoint']

    def run_backup(self, mode='ok', env=None):
        completed = subprocess.run(self.command(), text=True, capture_output=True, timeout=40,
            env=dict(os.environ, VISI_STUB_MODE=mode, **(env or {})))
        self.assertNotIn('test-secret', completed.stdout + completed.stderr)
        self.assertNotIn(str(self.source), completed.stdout + completed.stderr)
        return completed

    def statuses(self):
        return [path.split('?')[0].rsplit('/', 1)[1] for path, _, _ in self.server.events]

    def assert_failure(self, mode, code=20):
        p = self.run_backup(mode)
        self.assertEqual(p.returncode, code, p.stdout + p.stderr)
        self.assertEqual(self.statuses(), ['start', 'fail'])
        self.assertEqual(json.loads(p.stdout)['backupStatus'], 'failed')

    def test_success_sends_bodyless_status_and_persists_result(self):
        p = self.run_backup()
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.statuses(), ['start', '0'])
        self.assertTrue(all(body in (None, '0') and method == 'HEAD' for _, body, method in self.server.events))
        result = json.loads((self.state / 'last-result.json').read_text(encoding='utf-8-sig'))
        self.assertTrue(result['monitoringDelivered'])
        self.assertEqual(result['snapshots'][0]['fileCount'], 2)
        self.assertEqual(len({p.split('rid=')[1] for p, _, _ in self.server.events}), 1)

    def test_missing_source_fails(self):
        self.settings['sources'][0]['path'] = str(self.root / 'missing')
        self.assert_failure('ok')

    def test_second_source_failure_cannot_be_masked_by_first_success(self):
        second = self.root / 'second'
        second.mkdir()
        self.settings['sources'].append(dict(path=str(second), minimumFileCount=1, requiredFiles=[]))
        self.assert_failure('second-fails')

    def test_duplicate_sources_rejected(self):
        self.settings['sources'].append(dict(self.settings['sources'][0]))
        self.assertEqual(self.run_backup().returncode, 10)
        self.assertEqual(self.statuses(), [])

    def test_state_write_failure_does_not_send_success(self):
        (self.state / 'last-result.json').mkdir()
        p = self.run_backup()
        self.assertEqual(p.returncode, 24, p.stdout + p.stderr)
        self.assertEqual(self.statuses(), ['start', 'fail'])

    def test_missing_required_file_fails(self):
        (self.source / 'scope.txt').unlink()
        self.assert_failure('ok')

    def test_missing_executable_fails(self):
        self.settings['kopiaPath'] = str(self.root / 'not-installed')
        self.assert_failure('ok')

    def test_native_failure_fails(self):
        self.assert_failure('exit')

    def test_partial_read_failure_even_with_exit_zero_fails(self):
        self.assert_failure('partial')

    def test_failed_file_count_fails(self):
        self.assert_failure('failed-file')

    def test_incomplete_snapshot_fails(self):
        self.assert_failure('incomplete')

    def test_empty_snapshot_fails(self):
        self.assert_failure('empty')

    def test_malformed_output_fails(self):
        self.assert_failure('malformed')

    def test_old_snapshot_cannot_be_reported_as_new_success(self):
        self.assert_failure('wrong-id')

    def test_unapproved_version_fails(self):
        self.assert_failure('version')

    def test_process_timeout_kills_job_and_reports_failure(self):
        self.settings['maxRunSeconds'] = 2
        self.assert_failure('hang', 22)

    def test_monitor_failure_does_not_block_backup(self):
        self.server.reply_code = 503
        p = self.run_backup()
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertEqual(json.loads(p.stdout)['backupStatus'], 'succeeded')
        self.assertFalse(json.loads(p.stdout)['monitoringDelivered'])

    def test_monitor_redirect_is_not_followed(self):
        self.server.reply_code = 302
        p = self.run_backup()
        self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
        self.assertEqual(self.statuses(), ['start', '0'])

    def test_plain_http_rejected_without_lab_switch(self):
        p = subprocess.run(self.command()[:-1], capture_output=True, text=True)
        self.assertEqual(p.returncode, 10)
        self.assertEqual(self.statuses(), [])

    def test_non_loopback_http_rejected_even_with_lab_switch(self):
        self.settings['pingUrl'] = 'http://example.invalid/ping/test-secret'
        p = self.run_backup()
        self.assertEqual(p.returncode, 10)

    def test_unknown_config_field_fails_before_pinging(self):
        self.settings['maxRunSecond'] = 12
        p = self.run_backup()
        self.assertEqual(p.returncode, 10)
        self.assertEqual(self.statuses(), [])

    def test_required_file_cannot_escape_source(self):
        self.settings['sources'][0]['requiredFiles'] = ['../outside.txt']
        p = self.run_backup()
        self.assertEqual(p.returncode, 10)

    def test_overlap_does_not_spoof_failure_or_overwrite_active_result(self):
        p1 = subprocess.Popen(self.command(), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=dict(os.environ, VISI_STUB_MODE='delay'))
        try:
            deadline = time.monotonic() + 10
            while not self.server.events and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(self.server.events)
            p2 = self.run_backup()
            self.assertEqual(p2.returncode, 3, p2.stdout + p2.stderr)
            out, err = p1.communicate(timeout=15)
            self.assertEqual(p1.returncode, 0, out + err)
            self.assertEqual(self.statuses(), ['start', '0'])
        finally:
            if p1.poll() is None:
                p1.kill()
                p1.communicate()

    def kopia(self, *args, config=None, password='synthetic-local-test-password', check=True):
        p = subprocess.run([str(KOPIA), '--config-file=' + str(config or self.repo_config),
                            '--no-progress', '--disable-file-logging', *args],
            text=True, capture_output=True, timeout=30,
            env=dict(os.environ, KOPIA_PASSWORD=password, KOPIA_CHECK_FOR_UPDATES='false'))
        if check:
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p

    def prepare_real_repository(self):
        self.repo_config.unlink()
        self.settings['kopiaPath'] = str(KOPIA)
        self.kopia('repository', 'create', 'filesystem', '--path=' + str(self.root / 'encrypted-repository'))
        p = subprocess.run([str(PWSH), '-NoProfile', '-File', str(ROOT / 'scripts/Set-VisiKopiaPolicy.ps1'),
            '-KopiaPath', str(KOPIA), '-RepositoryConfig', str(self.repo_config), '-VssMode', 'never'],
            text=True, capture_output=True,
            env=dict(os.environ, KOPIA_PASSWORD='synthetic-local-test-password'))
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_real_encrypted_backup_verify_fresh_connection_restore_and_historical_recovery(self):
        self.prepare_real_repository()
        (self.source / 'nested').mkdir()
        (self.source / 'nested' / 'invoice ñ.txt').write_text('Synthetic invoice v1\n')
        (self.source / 'binary.bin').write_bytes(bytes(range(256)) * 4096)
        expected = {str(p.relative_to(self.source)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in self.source.rglob('*') if p.is_file()}
        p = self.run_backup(env={'KOPIA_PASSWORD': 'synthetic-local-test-password'})
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        first = json.loads(p.stdout)['snapshots'][0]
        self.kopia('snapshot', 'verify', first['id'], '--verify-files-percent=100')
        (self.source / 'nested' / 'invoice ñ.txt').write_text('simulated unwanted overwrite\n')
        (self.source / 'binary.bin').unlink()
        p = self.run_backup(env={'KOPIA_PASSWORD': 'synthetic-local-test-password'})
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        fresh = self.root / 'replacement-machine.config'
        self.kopia('repository', 'connect', 'filesystem', '--path=' + str(self.root / 'encrypted-repository'), config=fresh)
        restore = self.root / 'new-restore-location'
        self.kopia('snapshot', 'restore', first['rootObjectId'], str(restore),
            '--no-overwrite-files', '--no-overwrite-directories', '--no-overwrite-symlinks', config=fresh)
        actual = {str(p.relative_to(restore)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in restore.rglob('*') if p.is_file()}
        self.assertEqual(actual, expected)
        wrong = self.kopia('repository', 'connect', 'filesystem', '--path=' + str(self.root / 'encrypted-repository'),
            config=self.root / 'wrong-password.config', password='wrong-password', check=False)
        self.assertNotEqual(wrong.returncode, 0)

    def test_real_unreadable_file_cannot_report_success(self):
        self.prepare_real_repository()
        denied = self.source / 'unreadable.txt'
        denied.write_text('synthetic denied file')
        denied.chmod(0)
        try:
            p = self.run_backup(env={'KOPIA_PASSWORD': 'synthetic-local-test-password'})
            self.assertEqual(p.returncode, 20, p.stdout + p.stderr)
            self.assertEqual(self.statuses(), ['start', 'fail'])
        finally:
            denied.chmod(0o600)


if __name__ == '__main__':
    unittest.main(verbosity=2)
