#!/usr/bin/env python3

import os
import yaml
from typing import List, Tuple, Union

SKIPED_WORKFLOW_NAME = "skiped-jobs"

JOB_ALWAYS_SUCCEEDING_NAME="orb-conditional-job-succeed"
JOB_ALWAYS_SUCCEEDING={
    "docker": [
        { "image": "cimg/base" },
    ],
    "steps": [
        { "run": "exit 0" }
    ],
}

class JobConfig:
    def __init__(self, job_name: str, succeed_by_default: bool):
        self.job_name = job_name
        self.succeed_by_default = succeed_by_default


"""
Returns:
    The value present in the environment variable pointed by the given parameter
Raise:
    An exception if the environment variable is unset or empty
"""
def get_mandatory_env(env_name: str) -> str:
    env_value = os.environ.get(env_name)
    if env_value is None or env_value == "":
        raise Exception("expected environment variable {} to be set and non-empty", env_name)

    return env_value

"""
Returns:
    The list of jobs passed to the script
Raise:
    An exception if the environment variable is unset or empty
"""
def jobs_to_update() -> List[JobConfig]:
    out: List[JobConfig] = []

    config_path = get_mandatory_env('JOBS_TO_TRANSFORM_CONFIG_PATH')
    print(f'opening {config_path}')

    print(f'opening {config_path}')
    with open(config_path, 'r') as config_file:
        print(f'parsing {config_file}')
        config_yaml = yaml.safe_load(config_file)

    jobs = config_yaml["jobs"]
    if not isinstance(jobs, dict):
        raise Exception("expected `jobs` to be a dictionary")

    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            raise Exception("expected element in `jobs` to be a dictionary")

        out.append(JobConfig(
            job_name=job_name,
            succeed_by_default=job.get('succeed-by-default', False)))

    return out


"""
Try to see if the item in the `jobs` attribute matches the searched name.

Returns:
    If it matches:
        A tuple containing the attribute name with its content as an object
    If it doesn't
        None

Exemple:
    # Yaml looks like:
    # workflows:
    #   workflow-name:
    #     jobs:
    #     - not-matching
    match_job_item("not-matching", "job-name") == None

    # Yaml looks like:
    # workflows:
    #   workflow-name:
    #     jobs:
    #     - job-name
    match_job_item("job-name", "job-name") == ("job_name", {})

    # Yaml looks like:
    # workflows:
    #   workflow-name:
    #     jobs:
    #     - job-name:
    #       context: global
    match_job_item({"job-name": {"context": "global"}}, "job-name") == ("job-name", {"context": "global"})

    # Yaml looks like:
    # workflows:
    #   workflow-name:
    #     jobs:
    #     - random-name:
    #       context: global
    # .     name: job-name
    match_job_item({"random-name": {"context": "global", "name": "job-name"}}, "job-name") == ("random-name", {"context": "global", "name": "job-name"})
"""
def match_job_item(job_value: Union[str, dict], searched_name: str) -> Union[Tuple[str, dict], None]:
    # Try to match
    # jobs:
    #   - searched_name
    if isinstance(job_value, str):
        if job_value == searched_name:
            return (searched_name, {})
        return None

    # Try to match
    # jobs:
    #   - name-of-a-job:
    # .   name: searched_name
    #
    # OR
    # jobs:
    #   - searched_name:
    # .   ...
    for job_name, job_object in job_value.items():
        if job_name == searched_name or job_object.get("name", "") == searched_name:
            return (job_name, job_object)

    return None

"""
Mutates the `workflows` attribute in the given config_yaml so that every workflow
which is referencing the given job now makes it wait for a global approval
"""
def make_job_wait_for_approval(config_yaml: dict, job_config: JobConfig):
    # Make the always succeeding job available
    config_yaml["jobs"][JOB_ALWAYS_SUCCEEDING_NAME] = JOB_ALWAYS_SUCCEEDING

    workflows = config_yaml["workflows"]
    for workflow_name, workflow_object in workflows.items():
        if not isinstance(workflow_object, dict):
            continue


        updated_jobs: list[dict] = []
        for job_item in workflow_object["jobs"]:
            item_tuple = match_job_item(job_item, job_config.job_name)
            if item_tuple is None:
                updated_jobs.append(job_item)
                continue

            item_name, item_value = item_tuple

            new_job_name = job_config.job_name
            if job_config.succeed_by_default:
                print(f"making job {job_config.job_name} always succeeding in workflow {workflow_name}")
                new_job_name = f"trigger-{job_config.job_name}"
                updated_jobs.append({ JOB_ALWAYS_SUCCEEDING_NAME: { "context": "global", "name": job_config.job_name } })

            # Update the job so that it waits for an approval
            print(f"making job {new_job_name} wait for an approval in workflow {workflow_name}")
            updated_jobs.append({ item_name: { "context": "global", **item_value, "name": new_job_name, "type": "approval" } })

        workflow_object["jobs"] = updated_jobs

"""
Description:
    Mutates the config passed as argument
Parameters:
    config_yaml Parsed CircleCi config
Raise:
    An exception when a job is not present in the given config
"""
def update_config(config_yaml: dict, jobs_to_transform: List[JobConfig]):
    jobs_object = config_yaml["jobs"]
    if jobs_object is None:
        print(f"config object: \n{config_yaml}")
        raise Exception('expected the config to have a "jobs" object at top level')

    for job_config in jobs_to_transform:
        make_job_wait_for_approval(config_yaml, job_config)

def main():
    jobs = jobs_to_update()
    input_config_path = get_mandatory_env('CIRCLECI_CONFIG_PATH')
    output_config_path = get_mandatory_env('OUTPUT_CONFIG_PATH')
    config_yaml = {}

    with open(input_config_path, 'r') as config_file:
        config_yaml = yaml.safe_load(config_file)
        print(f'updating the {jobs} so that they wait for approval')
        update_config(config_yaml, jobs)

    with open(output_config_path, 'w') as file:
        yaml.dump(config_yaml, file)

    print(open(output_config_path, 'r').read())


if __name__ == '__main__':
    main()
