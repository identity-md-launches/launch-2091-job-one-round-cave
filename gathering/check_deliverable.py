"""Validate this gathering's file contract, ancestry and unchanged line files."""
import hashlib
import json
from pathlib import Path
import re
import struct

from check_tools import fingerprints
from finish_wall import read_png


def jpeg_size(raw):
    assert raw[:2] == b'\xff\xd8'
    offset = 2
    while offset < len(raw):
        assert raw[offset] == 255
        while raw[offset] == 255:
            offset += 1
        marker = raw[offset]
        offset += 1
        length = int.from_bytes(raw[offset:offset+2], 'big')
        if marker in (0xc0, 0xc1, 0xc2):
            height, width = struct.unpack('>HH', raw[offset+3:offset+7])
            return width, height
        offset += length
    raise ValueError('missing JPEG dimensions')


def main():
    checks = json.loads(Path('gathering/checks-24.json').read_text())
    assert checks['protected_files'] == fingerprints(), 'line source or record changed'
    assert checks['total_tests'] == 220 and checks['line_files_unchanged']
    assert len(checks['demos']) == 22
    assert all(x['exit'] == x['expected_exit'] for x in checks['demos'])
    shared = json.loads(Path('gathering/shared-checks-24.json').read_text())
    assert shared['total_tests'] == 35 and all(x['exit'] == 0 for x in shared['suites'])
    wall = Path('artifacts/gathering/wall-v4.png')
    width, height, pixels = read_png(wall)
    aw, ah, original = read_png('artifacts/gathering/wall-v3.png')
    assert (width, height) == (aw, ah) == (1254, 1254)
    preservation = json.loads(Path('gathering/image-preservation-24.json').read_text())
    assert hashlib.sha256(wall.read_bytes()).hexdigest() == preservation['wall_sha256']
    dx, dy, pw, ph = preservation['new_mark_rectangle']
    changed = 0
    for i in range(width*height):
        if pixels[3*i:3*i+3] != original[3*i:3*i+3]:
            x, y = i % width, i // width
            assert dx <= x < dx+pw and dy <= y < dy+ph
            changed += 1
    assert changed == preservation['changed_pixels'] == 4234
    assert Path('artifacts/gathering/wall.png').resolve() == wall.resolve()
    record = json.loads(Path('dist/gathering/24.json').read_text())
    assert set(record) == {'name', 'image', 'attributes'}
    assert record['image'] == 'https://api.imd.fun/artifacts/' + preservation['wall_sha256']
    traits = {x['trait_type']: x['value'] for x in record['attributes']}
    assert set(traits) == {'Cave', 'Wall', 'Number', 'Left behind', 'Meaning', 'One thing'}
    assert traits['Cave'] == 'Crystal' and traits['Wall'] == 'Gathering'
    assert type(traits['Number']) is int and traits['Number'] == 24
    assert traits['One thing'] == 'Gathering'
    preview = Path('dist/gathering/24.jpg')
    assert jpeg_size(preview.read_bytes()) == (512, 512)
    assert preview.stat().st_size < 100000
    groups = json.loads(re.search(r'<script id="records" type="application/json">(.*?)</script>',
                                 Path('dist/index.html').read_text(), re.S)[1])
    count = pending = 0
    for group, folder in zip(groups, ['line-1','line-2','line-3','line-4','gathering']):
        paths = sorted(Path('dist', folder).glob('[0-9][0-9].json'), reverse=True)
        expected = [{'number': int(p.stem), 'path': p.relative_to('dist').as_posix(),
                     **json.loads(p.read_text())} for p in paths]
        assert group['records'] == expected
        count += len(paths)
        for r in expected:
            if r['name'] == 'Not painted yet':
                pending += 1
                assert not Path('dist', r['path']).with_suffix('.jpg').exists()
    assert len(groups) == 5 and pending == 100
    assert json.loads(Path('dist/goals.json').read_text()) == [
        {'line': n, 'goal': Path(f'line-{n}/GOAL.md').read_text().strip()} for n in range(1,5)]
    # New source files and records must respect the delivery size limit.
    for folder in ('gathering', 'shared', 'dist'):
        assert all(p.stat().st_size <= 100000 for p in Path(folder).rglob('*') if p.is_file())
    review = {
        'number': 24, 'line_files_and_records_unchanged': True,
        'line_tests_passed': 220, 'expected_demo_statuses': 22, 'shared_tests_passed': 35,
        'gallery_records': count, 'preserved_placeholders': pending,
        'wall': {'path': str(wall), 'dimensions': [width,height], 'format': 'PNG',
                 'mode': 'RGB', 'sha256': preservation['wall_sha256']},
        'preview': {'path': str(preview), 'dimensions': [512,512], 'format': 'JPEG',
                    'bytes': preview.stat().st_size},
        'changed_pixels': changed, 'changed_pixels_outside_rectangle': 0,
        'visual_review': {
            'method': 'Explicit local inspection of finished wall and 512-pixel preview with view_image.',
            'pepe': 'Inherited wide mouth and heavy-lidded eyes preserved.',
            'ancestry': 'All ancestor pictographs outside the new unused-rock patch preserved exactly.',
            'hands': 'No hands or handprints added; no new digits. Ancestor hands concealed.',
            'text_or_prohibited_symbols_observed': False,
            'limitation': 'Small charcoal ties are subdued on dark rock, especially in the preview.'},
        'unmet_visual_requirements': [],
        'coins': 'none; ZTO/IMD already supply the real context, no new token is necessary.'}
    Path('gathering/REVIEW-24.json').write_text(json.dumps(review, indent=2)+'\n')
    print(json.dumps(review, indent=2))


if __name__ == '__main__':
    main()
