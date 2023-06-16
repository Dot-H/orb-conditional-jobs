import os
from unittest import TestCase, mock, main

from scripts import patch_workflows_jobs

def build_params(input_config_path: str, output_config_path: str, job_names: list[str]) -> dict:
    return {
        "CIRCLECI_CONFIG_PATH": input_config_path,
        "OUTPUT_CONFIG_PATH": output_config_path,
        "JOBS_LIST": ','.join(job_names)
    }

class TestMain(TestCase):
    @mock.patch.dict(os.environ, build_params(
        os.path.join(os.path.dirname(__file__), "./assets/configs/config.yml"),
        "/tmp/test_main.yml",
        ["failing-job"]))
    def test_main(self):
        """
        Test that it can find and path job in simple workflow
        """
        patch_workflows_jobs.main()
        self.maxDiff = None
        self.assertEqual(open("/tmp/test_main.yml", "r").read(),
        """jobs:
  failing-job:
    docker:
    - image: cimg/base
    steps:
    - run: exit 1
  succeeding-job:
    docker:
    - image: cimg/base
    steps:
    - run: exit 0
version: 2.1
workflows:
  fail:
    jobs:
    - failing-job:
        context: global
        type: approval
    - failing-job:
        context: global
        type: approval
  run-succeed-and-fail:
    jobs:
    - succeeding-job
    - failing-job:
        context: global
        requires:
        - succeeding-job
        type: approval
  succeed:
    jobs:
    - succeeding-job
  version: 2
""")

if __name__ == '__main__':
    main()

