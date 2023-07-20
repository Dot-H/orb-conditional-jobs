import subprocess
from typing import List

def checkout(revision: str):
    """
    Helper function for checking out a branch

    :param revision: The revision to checkout
    :type revision: str
    """
    subprocess.run(
        ['git', 'checkout', revision],
        check=True
    )

def merge_base(base: str, head: str) -> str:
    return subprocess.run(
        ['git', 'merge-base', base, head],
        check=True,
        capture_output=True
    ).stdout.decode('utf-8').strip()

def parent_commit() -> str:
    return subprocess.run(
        ['git', 'rev-parse', 'HEAD~1'],
        check=True,
        capture_output=True
    ).stdout.decode('utf-8').strip()

def diff_files(base: str, head: str) -> List[str]:
    return subprocess.run(
        ['git', '-c', 'core.quotepath=false', 'diff', '--name-only', base, head],
        check=True,
        capture_output=True
    ).stdout.decode('utf-8').splitlines()
