"""Run read-before-execution line checks without writing in line folders."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


def fingerprints():
    return {p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for n in range(1, 5) for folder in (Path(f'line-{n}'), Path(f'dist/line-{n}'))
            for p in sorted(folder.rglob('*')) if p.is_file()}


def main():
    before = fingerprints()
    scratch = Path('test/scratch')
    scratch.mkdir(parents=True, exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(dir=scratch, prefix='gathering24-') as temp:
        # The original resolver tests create temporary files beside themselves.
        copy = Path(temp) / 'offline-resolver'
        shutil.copytree('line-4/tools/offline-resolver', copy)
        suites = [(f'line-{n}/tools/{name}', name) for n, names in [
            (1, ['threeway', 'merge-review', 'tree-review', 'review-recheck']),
            (2, ['state-witness', 'header-anchor', 'code-witness', 'proof-set']),
            (3, ['evidence-search', 'corpus-freshness', 'search-receipt', 'evidence-bundle']),
            (4, ['offline-resolver', 'conflict-core'])] for name in names]
        for folder, name in suites:
            test_folder = str(copy) if name == 'offline-resolver' else folder
            args = ['-m', 'unittest', 'discover', '-s', test_folder, '-p', 'test_*.py']
            proc = subprocess.run([sys.executable, '-B', *args], capture_output=True, text=True, timeout=180)
            match = re.search(r'Ran (\d+) tests?', proc.stderr)
            result = {'tool': folder, 'command': 'python3 -B ' + ' '.join(args),
                      'exit': proc.returncode, 'tests': int(match[1]) if match else 0,
                      'summary': proc.stderr[-1500:]}
            results.append(result)
            print(folder, result['tests'], proc.returncode, flush=True)
    demos = [
        ('line-1/tools/threeway/merge.py', ['--demo', '--format', 'json'], 0),
        ('line-1/tools/merge-review/review.py', ['--demo', 'clean', '--format', 'json'], 0),
        ('line-1/tools/merge-review/review.py', ['--demo', 'conflict', '--format', 'json'], 1),
        ('line-1/tools/tree-review/tree_review.py', ['--demo', 'clean', '--format', 'json'], 0),
        ('line-1/tools/tree-review/tree_review.py', ['--demo', 'conflict', '--format', 'json'], 1),
        ('line-2/tools/state-witness/witness.py', ['demo'], 0),
        ('line-2/tools/state-witness/witness.py', ['demo', '--pool'], 0),
        ('line-2/tools/header-anchor/anchor.py', ['demo'], 0),
        ('line-2/tools/code-witness/code_witness.py', ['demo'], 0),
        ('line-3/tools/evidence-search/search.py', ['demo'], 0),
        ('line-3/tools/corpus-freshness/freshness.py', ['demo'], 0),
        ('line-3/tools/search-receipt/receipt.py', ['demo'], 0),
        ('line-4/tools/offline-resolver/resolve.py', ['demo'], 0),
        ('line-4/tools/offline-resolver/resolve.py', ['demo', '--max-steps', '1'], 3),
        ('line-4/tools/conflict-core/core.py', ['demo'], 0),
        ('line-4/tools/conflict-core/core.py', ['demo', '--max-steps', '1'], 3),
    ]
    demos += [(
        'line-1/tools/review-recheck/recheck.py', ['--demo', mode], status)
        for mode, status in [('clean', 0), ('conflict', 0), ('stale', 1), ('tampered', 1)]]
    demos += [('line-2/tools/proof-set/proof_set.py', ['demo'], 0),
              ('line-3/tools/evidence-bundle/bundle.py', ['demo'], 0)]
    trials = []
    for script, args, expected in demos:
        proc = subprocess.run([sys.executable, '-B', script, *args], capture_output=True, text=True, timeout=60)
        trials.append({'command': 'python3 -B ' + ' '.join([script, *args]),
                       'exit': proc.returncode, 'expected_exit': expected,
                       'result': json.loads(proc.stdout) if proc.stdout else None})
        print(script, args, proc.returncode, flush=True)
    after = fingerprints()
    report = {'suites': results, 'demos': trials, 'line_files_unchanged': before == after,
              'protected_files': before,
              'total_tests': sum(r['tests'] for r in results)}
    output = json.dumps(report, indent=2) + '\n'
    assert len(output.encode()) < 100000
    Path('gathering/checks-24.json').write_text(output)
    assert before == after, 'line files changed'
    assert all(r['exit'] == 0 and r['tests'] > 0 for r in results)
    assert all(r['exit'] == r['expected_exit'] for r in trials)


if __name__ == '__main__':
    main()
