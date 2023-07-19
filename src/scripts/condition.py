import os
import re
import scripts.git as git
import yaml

from typing import List, Protocol

class Condition(Protocol):
    def test(self) -> bool:
        """
        Checks if the condition is valid
        """
        return False

class ChangedFiles:
    def __init__(self, yaml_value: dict):
        """
        Parses a yaml object to retrieve the necessary informations permitting to test the condition
        """
        self.base_revision = yaml_value.get('base_revision', 'main')
        self.head = os.environ.get('CIRCLE_SHA1', '')
        if self.head == '':
            raise Exception('Environment variable CIRCLE_SHA1 is missing or has no value')

        regex_str = yaml_value.get('regex', None)
        if regex_str is None:
            raise Exception('missing key regex in condition changed_files')
        self.regex = re.compile(regex_str)


    def changed_files(self) -> List[str]:
        """
        Retrieves the list of changed files between the base and the head
        """
        base = self.base_revision
        head = self.head

        print(f'Checking out to base {base}')
        git.checkout(base)  # Checkout base revision to make sure it is available for comparison
        print(f'Checking out to head {head}')
        git.checkout(head)  # return to head commit
        print(f'Merging base {base} into head {head}')
        base = git.merge_base(base, head)

        if head == base:
            print(f'Base is the same as the head, retrieving parent commit as base')
            try:
                # If building on the same branch as BASE_REVISION, we will get the
                # current commit as merge base. In that case try to go back to the
                # first parent, i.e. the last state of this branch before the
                # merge, and use that as the base.
                base = git.parent_commit()
                print(f'New base is {base}')
            except:
                # This can fail if this is the first commit of the repo, so that
                # HEAD~1 actually doesn't resolve. In this case we can compare
                # against this magic SHA below, which is the empty tree. The diff
                # to that is just the first commit as patch.
                base = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
                print(f"No parent commit, using the magic SHA {base} as new base")

        print(f'Comparing {base}...{head}')
        return git.diff_files(base, head)

    def test(self) -> bool:
        """
        Test a regex against a list of file names
        """
        print(f'Searching a file matching regex: {self.regex.pattern}')
        for file in self.changed_files():
            if self.regex.match(file):
                print(f"File {file} matches")
                return True

        print(f"No matches found")
        return False

def build_condition(condition_yaml: dict) -> Condition:
    """
    Build a Condition Protocol using a condition object corresponding to the parsed body
    of the file pointed by the `condition` key
    """
    if 'changed-files' in condition_yaml:
        changed_files_yaml = condition_yaml['changed-files']
        if not isinstance(changed_files_yaml, dict):
            raise Exception(f"Found changed-files condition in {condition_yaml} but type isn't a dictionary")

        return ChangedFiles(changed_files_yaml)
    else:
        raise Exception(f"Could not find a valid condition: expected one of: changed-files")

def test_condition(condition_file_path: str) -> bool:
    """
    Test the condition pointed by the given file
    """
    condition_yaml = {}

    print(f'Testing condition pointed by file {condition_file_path}')
    with open(condition_file_path, 'r') as condition_file:
        condition_yaml = yaml.safe_load(condition_file)

    condition = build_condition(condition_yaml)
    test_result = condition.test()
    print(f"Test returned {test_result}")
    return test_result
