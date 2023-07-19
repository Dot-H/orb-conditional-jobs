#!/usr/bin/env python3

import os
import yaml

from typing import Iterable, List, Set, Tuple, Union

from scripts.condition import test_condition

SKIPED_WORKFLOW_NAME = "skiped-jobs"

JOB_ALWAYS_SUCCEEDING_NAME="orb-conditional-job-succeed"
JOB_ALWAYS_SUCCEEDING={
    "docker": [
        { "image": "cimg/base:current" },
    ],
    "steps": [
        { "run": "exit 0" }
    ],
}


"""
Configuration accepted by the orb to configure how a job should be patched
"""
class JobConfig:
    def __init__(self, job_name: str, succeed_by_default: bool, condition_file_path: Union[str, None]):
        self.job_name = job_name
        self.succeed_by_default = succeed_by_default
        self.has_condition_passed = test_condition(condition_file_path) if condition_file_path is not None else True

"""
Parses a step in the workflow.jobs list from the circleci config

Exemple:
    # Yaml looks like:
    # workflows:
    #   workflow-name:
    #     jobs:
    #     - job-name
    WorkflowItemNameGenerator("workflow-name", "not-matching") == {
        "job_name" = "job-name",
        "name" = "job-name",
        "config" = {},
    }

    # Yaml looks like:
    # workflows:
    #   workflow-name:
    #     jobs:
    #     - job-name:
    #       context: global
    WorkflowItemNameGenerator("workflow-name", {"job-name": {"context": "global"}}) == {
        "job_name" = "job-name",
        "name" = "job-name",
        "config" = {"context": "global"},
    }

    # Yaml looks like:
    # workflows:
    #   workflow-name:
    #     jobs:
    #     - job-name:
    #       context: global
    # .     name: step-name
    WorkflowItemNameGenerator("workflow-name", {"job-name": {"context": "global", "name": "step-name"}}) == {
        "job_name" = "job-name",
        "name" = "step-name",
        "config" = {"context": "global", "name": "step-name"},
    }
"""
class WorkflowJobStep:
    original: Union[dict, str]
    job_name: str
    name: str
    config: dict

    def __init__(self, step: Union[dict, str]):
        self.original = step

        # Try to match
        # jobs:
        #   - searched_name
        if isinstance(step, str):
            self.job_name = step
            self.name = step
            self.config = {}
            return

        # Sanity check on the config
        if not isinstance(step, dict):
            raise Exception(f"could not parse workflow step {step}: step is neither a dictionary nor a string")
        elif len(step) > 1:
            raise Exception(f"could not parse workflow step {step}: step is a dictionary with more than one element")

        # Try to match
        # jobs:
        #   - name-of-a-job:
        # .   name: searched_name
        #
        # OR
        # jobs:
        #   - searched_name:
        # .   ...
        for job_name, step_config in step.items():
            self.job_name = job_name
            self.name = step_config.get("name", job_name)
            self.config = step_config



"""
Permits to generate new names to put in a workflow.

The class will make sure to generate names which are not already in the workflow
"""
class WorkflowItemNameGenerator:
    def __init__(self, workflow_name: str, job_steps: Iterable[WorkflowJobStep]):
        self.workflow_name = workflow_name
        self.seen_names: Set[str] = set([step.name for step in job_steps])

    def new(self, base: str, prefix:str = "") -> str:
        name = f"{prefix}-{base}"
        i = 1
        while name in self.seen_names:
            suffix = f"dup{i}"
            print(f"name {name} already present in workflow {self.workflow_name}, adding suffix {suffix}")
            name = f"{prefix}-{base}-{suffix}"
            i += 1

        print(f"generating name {name}")
        self.seen_names.add(name)
        return name

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
            succeed_by_default=job.get('succeed-by-default', False),
            condition_file_path=job.get('condition', None)))

    return out

"""
Mutates the `workflows` attribute in the given config_yaml so that every workflow
which is referencing the given job now makes it wait for a global approval
"""
def make_job_wait_for_approval(config_yaml: dict, job_config: JobConfig):
    # Make the always succeeding job available
    config_yaml["jobs"][JOB_ALWAYS_SUCCEEDING_NAME] = JOB_ALWAYS_SUCCEEDING

    workflows = config_yaml["workflows"]
    for workflow_name, workflow_object in workflows.items():
        print(f"looking at workflow {workflow_name}")
        if not isinstance(workflow_object, dict):
            print(f"ignoring: workflow is not an object: {workflow_object}")
            continue


        updated_jobs: List[Union[dict, str]] = []
        workflow_job_steps: List[WorkflowJobStep] = list(map(WorkflowJobStep, workflow_object["jobs"]))
        name_generator = WorkflowItemNameGenerator(workflow_name, workflow_job_steps)

        for step in workflow_job_steps:
            if step.name != job_config.job_name:
                # Not the searched step
                updated_jobs.append(step.original)
                continue

            running_step_name = step.name
            trigger_step_name = name_generator.new(step.name, "trigger")
            if job_config.succeed_by_default:
                print(f"making step {step.name} always succeeding")
                running_step_name = f"running-{step.name}"
                updated_jobs.append({ JOB_ALWAYS_SUCCEEDING_NAME: { "context": "global", "name": step.name } })

            # Insert the trigger job waiting for the approval
            print(f"insert the triggering step {trigger_step_name}")
            updated_jobs.append({ trigger_step_name: { **step.config, "name": trigger_step_name, "type": "approval" }})

            # Update the job so that it waits for the trigger job to be approved
            print(f"making step {running_step_name} wait for the approval of {trigger_step_name}")
            updated_jobs.append({ step.job_name: { "context": "global", **step.config, "name": running_step_name, "requires": [trigger_step_name]} })

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
        if job_config.has_condition_passed:
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
