import os
from unittest import TestCase, mock, main

from scripts import patch_workflows_jobs

def build_params(input_config_path: str, output_config_path: str, job_names: list[str]) -> dict:
    return {
        "CIRCLECI_CONFIG_PATH": input_config_path,
        "OUTPUT_CONFIG_PATH": output_config_path,
        "JOBS_LIST": ','.join(job_names)
    }

class JobPatchingTestCases(TestCase):
    TESTS_ROOT_DIRECTORY_PATH: str = os.path.join(os.path.dirname(__file__), "./assets/tests")

    def test_job_patching(self):
        """
        Will iterate on all the directories in `./assets/tests` to create a subtest which will use the
        configs in this directory as if they were passed as argument.
        """
        tests_dirname = os.listdir(self.TESTS_ROOT_DIRECTORY_PATH)

        for test_dirname in tests_dirname:
            test_root_directory_path = os.path.join(self.TESTS_ROOT_DIRECTORY_PATH, test_dirname)
            output_path = f"/tmp/test_job_patching_{test_dirname}.yml"

            with self.subTest(msg=test_dirname):
                params = build_params(
                os.path.join(test_root_directory_path, "circleci-config.yml"),
                output_path,
                ["failing-job"])

                with mock.patch.dict(os.environ, params):
                    patch_workflows_jobs.main()
                    self.maxDiff = None
                    self.assertEqual(
                        open(output_path, "r").read(),
                        open(os.path.join(test_root_directory_path, "output-config.yml")).read())

if __name__ == '__main__':
    main()

