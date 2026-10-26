"""Validate new maintainer-owned commit identities without rejecting contributors."""
import os
from pathlib import Path
import re
import subprocess

CANONICAL_NAME = 'Mateusz Sury'
CANONICAL_EMAIL = '66475105+mateuszsury@users.noreply.github.com'
OWN_EMAILS = {CANONICAL_EMAIL, 'mateuszsury@users.noreply.github.com',
              'mateusz.sury25@gmail.com', 'mateuszsury25@gmail.com',
              'klima-wifi@users.noreply.github.com'}

def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()

def main():
    head = os.environ.get('HEAD_SHA') or 'HEAD'
    base = os.environ.get('BASE_SHA', '')
    # A new branch has no 'before' revision; its PR validates the complete range.
    if base and set(base) != {'0'}:
        known = subprocess.run(['git', 'cat-file', '-e', base + '^{commit}'], capture_output=True).returncode == 0
        # After an intentional history migration, old revisions need not be in
        # a fresh checkout. Validate the replacement history rather than fail.
        commits = git('rev-list', base + '..' + head if known else head).splitlines()
    else:
        commits = [git('rev-parse', head)]
    failures = []
    for sha in commits:
        name, email, message = git('show', '-s', '--format=%an%x00%ae%x00%B', sha).split('\0', 2)
        owned = email in OWN_EMAILS or email.lower() == 'noreply@anthropic.com'
        if owned and (name != CANONICAL_NAME or email != CANONICAL_EMAIL):
            failures.append(sha[:12] + ': use the configured maintainer Git identity')
        if re.search(r'^Co-authored-by:.*noreply@anthropic\.com', message, re.I | re.M):
            failures.append(sha[:12] + ': remove AI co-author attribution from maintainer-owned changes')
    if failures:
        raise SystemExit('\n'.join(failures))
    print(f'Author policy: {len(commits)} new commit(s) checked; real contributors preserved')

if __name__ == '__main__':
    main()
