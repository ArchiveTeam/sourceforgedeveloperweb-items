import bz2
import io
import re
import sys
import tarfile

import zstandard

USER_PATTERN = '[0-9a-zA-Z_\-]+'
OPEN_FUNCS = {
    'zst': (zstandard.open, 'r'),
    'bz2': (bz2.open, 'rt')
}


def get_lines(filepath: str):
    if filepath.endswith('.tar.bz2'):
        with tarfile.open(filepath, 'r:bz2') as tf:
            for member in tf:
                with io.TextIOWrapper(tf.extractfile(member), errors='ignore') as f:
                    yield from f
        return None
    if filepath.endswith('.zst'):
        open_func, open_mode = zstandard.open, 'r'
    elif filepath.endswith('.bz2'):
        open_func, open_mode = bz2.open, 'rt'
    else:
        open_func, open_mode = open, 'r'
    with open_func(filepath, open_mode, errors='ignore') as f:
        yield from f


def main(filepath: str):
    print('Processing', filepath)
    items = set()
    add_user = lambda s: items.add('path:{}:/'.format(s))
    for line in get_lines(filepath):
        line = line.strip()
        if re.search(r'^'+USER_PATTERN+'$', line):
            add_user(line)
        for pattern in (
            '/(?:u|users)/('+USER_PATTERN+')',
            '('+USER_PATTERN+r')[@\.]users\.'
        ):
           for s in re.findall(pattern, line):
                add_user(s)
        if re.search('^https?://', line):
            if line.count('/') == 2:
                line += '/'
            result = re.search(
                r'^https?://([^\.]+)\.users\.(?:sourceforge|sf)\.(?:net|io)(/[^#]+)', line)
            if result:
                user, path = result.groups()
                assert re.match('^' + USER_PATTERN + '$', user)
                items.add('path:{}:{}'.format(user, path))
    with open(filepath+'_items.txt', 'w') as f:
        for item in items:
            f.write('{}\n'.format(item))

if __name__ == '__main__':
    for filepath in sys.argv[1:]:
        main(filepath)

