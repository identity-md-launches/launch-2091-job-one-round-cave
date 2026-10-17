"""Check the shared integrations and copied-source provenance, offline."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


def main():
    results = []
    for name in ('proof-search', 'merge-dependencies', 'proof-handoff'):
        command = [sys.executable, '-B', '-m', 'unittest', 'discover',
                   '-s', 'shared/' + name, '-p', 'test_*.py', '-v']
        proc = subprocess.run(command, capture_output=True, text=True, timeout=180)
        count = re.search(r'Ran (\d+) tests?', proc.stderr)
        results.append({'tool': name, 'command': command, 'exit': proc.returncode,
                        'tests': int(count[1]) if count else 0, 'log': proc.stderr})
        print(name, results[-1]['tests'], proc.returncode)
    root = Path('shared/proof-handoff')
    provenance = json.loads((root / 'PROVENANCE.json').read_text())
    for item in provenance:
        assert hashlib.sha256(Path(item['source']).read_bytes()).hexdigest() == item['sha256']
        assert hashlib.sha256((root / item['copy']).read_bytes()).hexdigest() == item['sha256']
    command = [sys.executable, '-B', str(root / 'handoff.py'), 'check',
               str(root / 'tools/proof-set/examples/zto-and-pool.json'),
               '--block-hash', '0x38dc4deb12174972d332cc1f95008b25ea87434f420ce0a51938e1b28755e9dc',
               '--manifest-sha256', 'a4e9d3fb56c90bf1202ac3d53b8ce7c557febe06d88581a9430a2f6a59f14e8f',
               '--bundle', str(root / 'examples/zto-proof-bundle.json'),
               '--expected-sha256', '57ba25ab26d159efaa1c07dc28c1dc0a0e0914049df9646b46374fd04621089f']
    proc = subprocess.run(command, capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    report = {'suites': results, 'total_tests': sum(r['tests'] for r in results),
              'copied_files_match_sources': len(provenance),
              'example': {'command': command, 'exit': proc.returncode,
                          'result': json.loads(proc.stdout)}}
    Path('gathering/shared-checks-24.json').write_text(json.dumps(report, indent=2)+'\n')
    assert all(r['exit'] == 0 and r['tests'] > 0 for r in results)
    assert report['example']['result']['verified'] is True


if __name__ == '__main__':
    main()
