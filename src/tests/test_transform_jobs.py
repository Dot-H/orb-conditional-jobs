"""
**Disclaimer**:
All the boilerplate around the `create_test_case` function is just so that vscode
correctly discovers the tests generated from the TESTS_ROOT_DIRECTORY_PATH.
As of the July 12th 2022, I (dot-h) could not make load_tests work with vscode.

Will iterate on all the directories in `./assets/tests` to create a TestCase per directory.
Each test case will:
- Pass the `circleci-config.yml` file as parameter
- Pass the `jobs-to-transform-config.yml` file as parameter
- Execute the job patching
- Ensure that the output matches the file in `output-config.yml`

So, in order to add a new test case, you'll need to:
1. Create a directory in `./assets/tests`
2. In this directory:
    1. Add `circleci-config.yml` corresponding to the config to patch
    2. Add `jobs-to-transform-config.yml` corresponding to the config used to patch
    3. Add `output-config.yml` corresponding to the expected patched config
"""
import os
from os.path import dirname
from unittest import TestCase, mock

from scripts import patch_workflows_jobs
from scripts.condition import ChangedFiles

TESTS_ROOT_DIRECTORY_PATH: str = os.path.join(os.path.dirname(__file__), "./assets/tests")

def build_params(input_config_path: str, output_config_path: str, jobs_to_transform_config_path: str) -> dict:
    return {
        "CIRCLECI_CONFIG_PATH": input_config_path,
        "OUTPUT_CONFIG_PATH": output_config_path,
        "JOBS_TO_TRANSFORM_CONFIG_PATH": jobs_to_transform_config_path,
        "CIRCLE_SHA1": "4b825dc642cb6eb9a060e54bf8d69288fbee4904",
    }

"""
Method which actually does the test
"""
def run_test(self):
    test_root_directory_path = os.path.join(TESTS_ROOT_DIRECTORY_PATH, self.test_dirname)
    output_path = f"/tmp/test_job_patching_{self.test_dirname}.yml"

    params = build_params(
    os.path.join(test_root_directory_path, "circleci-config.yml"),
    output_path,
    os.path.join(test_root_directory_path, "jobs-to-transform-config.yml"))

    with mock.patch.object(ChangedFiles, 'changed_files') as changed_files_method:
        changed_files_method.return_value = ['.circleci/pipo.yml', 'src/app/poupip.go']
        with mock.patch.dict(os.environ, params):
            patch_workflows_jobs.main()
            self.maxDiff = None
            self.assertEqual(
                open(output_path, "r").read(),
                open(os.path.join(test_root_directory_path, "output-config.yml")).read())

"""
Generates a TestCase which will run a test for the given directory
"""
def create_test_case(dirname: str):
    return type(dirname, (TestCase, ), {
    # data members
    "test_dirname": dirname,

    # member functions
    "runTest": run_test,
})

"""
Iterates over the directories to find all the tests to create and add a
global for each of them.

So if my TEST_ROOT_DIRECTORY_PATH contains the directories 'test-1', 'test-2',
this code will generate the globals 'test-1' and 'test-2' in this module. It
would be equivalent to approximately hardcoding this in python:

class test-1(TestCase):
    test_dirname = 'test-1'

    def runTest(self):
        .... # See the runTest function

class test-2(TestCase):
    test_dirname = 'test-1'

    def runTest(self):
        .... # See the runTest function
"""
tests_dirname = os.listdir(TESTS_ROOT_DIRECTORY_PATH)
for dirname in tests_dirname:
    generatedClass = create_test_case(dirname)
    globals()[generatedClass.__name__] = generatedClass

