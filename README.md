# Orb Template


[![CircleCI Build Status](https://circleci.com/gh/Dot-H/orb-conditional-jobs.svg?style=shield "CircleCI Build Status")](https://circleci.com/gh/Dot-H/orb-conditional-jobs) [![CircleCI Orb Version](https://badges.circleci.com/orbs/doth/..svg)](https://circleci.com/developer/orbs/orb/doth/.) [![GitHub License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](https://raw.githubusercontent.com/Dot-H/orb-conditional-jobs/master/LICENSE) [![CircleCI Community](https://img.shields.io/badge/community-CircleCI%20Discuss-343434.svg)](https://discuss.circleci.com/c/ecosystem/orbs)

CircleCI orb exposing a command to dynamically make jobs wait for manual triggers.
---

## Use cases

- Ignore jobs depending on which files are modified

### How to

FIXME

**jobs-to-transform-config-path**:
```yaml
jobs:
  # Name of the step in a workflow to make optional
  test-backend:
    # The `test-backend` will succeed by default and you will have a `trigger-test-backend`
    # which will wait for an approval.
    succeed-by-default: true # required
    condition: .circleci/conditional-jobs-conditions/test-backend.yml
  check-packages-security:
    # The `test-backend` step will wait for you to manually trigger the `trigger-test-backend`
    # to run
    succeed-by-default: false
    condition: .circleci/conditional-jobs-conditions/check-packages-security.yml
  test-frontend:
    succeed-by-default: true
    condition: .circleci/conditional-jobs-conditions/test-frontend.yml
```

**.circleci/conditional-jobs-conditions/test-backend.yml**:
```yaml
changed-files:
    # The revision to compare the current one against for the purpose of determining changed files.
    base-revision: main # optional (default: main)
    # The regex to apply on the changed files path
    regex: src/apps/backend # required
```

**.circleci/conditional-jobs-conditions/check-packages-security.yml**:
```yaml
changed-files:
    # The regex to apply on the changed files path
    regex: src/go.sum # required
```

**.circleci/conditional-jobs-conditions/test-frontend.yml**:
```yaml
changed-files:
    # The regex to apply on the changed files path
    regex: src/apps/front # required
```
