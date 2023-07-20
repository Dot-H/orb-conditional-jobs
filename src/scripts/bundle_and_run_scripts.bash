#!/usr/bin/env bash

# CircleCI does not support importing more than one script file in the orb's command.
# So we need to trick it a little bit.
#
# To do so we put the files in environment variables and then recreate the module
# in this script.
#
# Most of the code is stolen from one of their orb:
# https://github.com/CircleCI-Public/workflow-patching-orb/blob/main/src/scripts/create-parameters.sh

set -e
set -o pipefail

if [ -f .python-version ]; then
    # Create a temp directory
    circleci_temp_dir="$(mktemp -d)"
    # Move .python-version out of the directory
    mv .python-version "$circleci_temp_dir"/.python-version
fi

curl "https://bootstrap.pypa.io/get-pip.py" -o "circleci_get_pip.py"
python3 circleci_get_pip.py --user

python3 -m pip install --user virtualenv

echo "Create python virtual environment for workflow-patching"
virtualenv workflow-patching-venv -p /usr/bin/python3

echo "Activate python virtual environment"
. workflow-patching-venv/bin/activate

# Rebuild the python module
mkdir scripts
touch scripts/__init__.py
echo "${PYTHON_REQUIREMENTS_TXT}" > scripts/requirements.txt
echo "${GIT_PYTHON_SCRIPT}" > scripts/git.py
echo "${CONDITION_PYTHON_SCRIPT}" > scripts/condition.py
echo "${PATCH_PYTHON_SCRIPT}" > scripts/patch_workflows_jobs.py

echo 'Installing requirements'
python3 -m pip install -r scripts/requirements.txt

echo "Patching the workflows"
PYTHONPATH=. python3 scripts/patch_workflows_jobs.py

if [ -f "$circleci_temp_dir"/.python-version ]; then
    # Move .python-version back
    mv "$circleci_temp_dir"/.python-version .python-version
fi

echo "Deactivate python virtual environment for workflow-patching"
deactivate
