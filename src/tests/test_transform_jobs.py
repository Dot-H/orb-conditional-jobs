import os
from unittest import TestCase, mock, main

from scripts import patch_workflows_jobs

def build_params(input_config_path: str, output_config_path: str, jobs_to_transform_config_path: str) -> dict:
    return {
        "CIRCLECI_CONFIG_PATH": input_config_path,
        "OUTPUT_CONFIG_PATH": output_config_path,
        "JOBS_TO_TRANSFORM_CONFIG_PATH": jobs_to_transform_config_path,
    }

class JobPatchingTestCases(TestCase):
    TESTS_ROOT_DIRECTORY_PATH: str = os.path.join(os.path.dirname(__file__), "./assets/tests")

    def test_job_patching(self):
        """
        Will iterate on all the directories in `./assets/tests` to create a subtest per directory.
        Each subtest will:
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
        tests_dirname = os.listdir(self.TESTS_ROOT_DIRECTORY_PATH)

        for test_dirname in tests_dirname:
            test_root_directory_path = os.path.join(self.TESTS_ROOT_DIRECTORY_PATH, test_dirname)
            output_path = f"/tmp/test_job_patching_{test_dirname}.yml"

            with self.subTest(msg=test_dirname):
                params = build_params(
                os.path.join(test_root_directory_path, "circleci-config.yml"),
                output_path,
                os.path.join(test_root_directory_path, "jobs-to-transform-config.yml"))

                with mock.patch.dict(os.environ, params):
                    patch_workflows_jobs.main()
                    self.maxDiff = None
                    self.assertEqual(
                        open(output_path, "r").read(),
                        open(os.path.join(test_root_directory_path, "output-config.yml")).read())

if __name__ == '__main__':
    main()

