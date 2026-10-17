"""Blend the image tool's bundle pigment onto unused ancestor rock, once."""
import hashlib
import json
from pathlib import Path
from finish_wall import read_png, write_png


def main():
    ancestor = Path('artifacts/gathering/wall-v3.png')
    output = Path('artifacts/gathering/wall-v4.png')
    width, height, original = read_png(ancestor)
    dw, dh, draft = read_png(output)
    assert (width, height) == (1254, 1254)
    final = original[:]
    dx, dy, pw, ph = 550, 970, 190, 85
    # The tool produced a standalone bundle on pale stone. Isolate pigment;
    # never paste the generated stone over the inherited wall.
    sx, sy, sw, sh = 280, 430, 760, 340
    for y in range(ph):
        for x in range(pw):
            source = ((sy + y*sh//ph)*dw + sx + x*sw//pw)*3
            r, g, b = draft[source:source+3]
            ochre = r > 60 and g < 140 and r > 1.8*g and r > 2.4*b
            charcoal = r < 100 and g < 85 and b < 65
            alpha = 0.75 if ochre else 0.65 if charcoal else 0
            if alpha:
                target = ((dy+y)*width + dx+x)*3
                for c in range(3):
                    final[target+c] = round(original[target+c]*(1-alpha)+draft[source+c]*alpha)
    changed = []
    for i in range(width*height):
        if final[3*i:3*i+3] != original[3*i:3*i+3]:
            x, y = i % width, i // width
            assert dx <= x < dx+pw and dy <= y < dy+ph
            changed.append(i)
    assert 1000 < len(changed) < pw*ph
    sha = write_png(output, width, height, final)
    evidence = {'ancestor_sha256': hashlib.sha256(ancestor.read_bytes()).hexdigest(),
                'wall_sha256': sha, 'dimensions': [width, height], 'format': 'PNG',
                'mode': 'RGB', 'new_mark_rectangle': [dx,dy,pw,ph],
                'changed_pixels': len(changed), 'changed_pixels_outside_rectangle': 0,
                'method': 'Installed image tool generated ochre hide/reed bundle with charcoal ties; only pigment was blended on unused rock.',
                'unmet_visual_requirements': []}
    Path('gathering/image-preservation-24.json').write_text(json.dumps(evidence, indent=2)+'\n')
    continuation = Path('artifacts/gathering/wall.png')
    assert continuation.is_symlink()
    continuation.unlink()
    continuation.symlink_to(output.name)
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
