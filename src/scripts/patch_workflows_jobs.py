#!/usr/bin/env python3

import os
import yaml
from typing import List, Any, Union

SKIPED_WORKFLOW_NAME = "skiped-jobs"

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
def jobs_to_update() -> List[str]:
    jobs_as_string = get_mandatory_env('JOBS_LIST')
    return jobs_as_string.split(',')

def as_matching_job(job_value: Union[str, dict], searched_name: str) -> Union[dict, None]:
    if isinstance(job_value, str):
        if job_value == searched_name:
            return { searched_name: None }
        return None

    if searched_name in job_value:
        return job_value
    return None

"""
Mutates the `workflows` attribute in the given config_yaml so that every workflow
which is referencing the given job now makes it wait for a global approval
"""
def move_job_to_skiped_workflow(config_yaml: dict, job_name: str):
    workflows = config_yaml["workflows"]
    for workflow_name, workflow_object in workflows.items():
        if not isinstance(workflow_object, dict):
            continue


        # Find the job
        workflow_jobs: list[dict] = workflow_object["jobs"]
        for idx, job_object in enumerate(workflow_jobs):
            job_object = as_matching_job(job_object, job_name)
            if job_object is None:
                print(f"{workflow_name} does not contain job {job_name}: skipping")
                continue

            # Update its body so that it waits for an approval
            print(f"making job {job_name} wait for an approval in workflow {workflow_name}")
            workflow_jobs[idx] = { **job_object, "context": "global", "type": "approval" }

"""
Description:
    Mutates the config passed as argument
Parameters:
    config_yaml Parsed CircleCi config
Raise:
    An exception when a job is not present in the given config
"""
def update_config(config_yaml: dict, jobs_to_transform: List[str]):
    jobs_object = config_yaml["jobs"]
    if jobs_object is None:
        print(f"config object: \n{config_yaml}")
        raise Exception('expected the config to have a "jobs" object at top level')

    for job_name in jobs_to_transform:
        move_job_to_skiped_workflow(config_yaml, job_name)

def main():
    jobs = jobs_to_update()
    input_config_path = get_mandatory_env('CIRCLECI_CONFIG_PATH')
    output_config_path = get_mandatory_env('OUTPUT_CONFIG_PATH')
    config_yaml = {}

    with open(input_config_path, 'r') as config_file:
        print(f'parsing {input_config_path}')
        config_yaml = yaml.safe_load(config_file)
        print(f'transforming the jobs {jobs} as workflows to manually trigger')
        update_config(config_yaml, jobs)

    with open(output_config_path, 'w') as file:
        yaml.dump(config_yaml, file)

if __name__ == '__main__':
    main()
