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
  first-job-name:
    succeed-by-default: true
  second-job-name:
    succeed-by-default: false
  third-job-name:
    succeed-by-default: true
```
