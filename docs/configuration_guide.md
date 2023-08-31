# Configuring Firewatch

## Table of Contents

* [Configuring Firewatch](#configuring-firewatch)
  * [Jira Issue Creation (`firewatch report`) Configuration](#jira-issue-creation-firewatch-report-configuration)
    * [Required Values](#required-values)
      * [`step`](#step)
      * [`failure_type`](#failuretype)
      * [`classification`](#classification)
      * [`jira_project`](#jiraproject)
    * [Optional Values](#optional-values)
      * [`jira_epic`](#jiraepic)
      * [`jira_component`](#jiracomponent)
      * [`jira_affects_version`](#jiraaffectsversion)
      * [`jira_additional_labels`](#jiraadditionallabels)
      * [`jira_assignee`](#jiraassignee)
      * [`jira_priority`](#jirapriority)
      * [`ignore`](#ignore)
      * [`group`](#group)

## Jira Issue Creation (`firewatch report`) Configuration

Firewatch was designed to allow for users to define which Jira issues get created depending on which failures are found in a OpenShift CI failed run. Using an easy-to-define JSON config, users can easily track issues in their OpenShift CI runs efficiently.

**Example:**

```json
[
    {"step": "exact-step-name", "failure_type": "pod_failure", "classification": "Infrastructure", "jira_project": "PROJECT", "jira_component": "some-component"},
    {"step": "*partial-name*", "failure_type": "all", "classification":  "Misc.", "jira_project": "OTHER", "jira_component": ["component-1", "component-2"], "group": {"name": "some-group", "priority": 1}},
    {"step": "*ends-with-this", "failure_type": "test_failure", "classification": "Test failures", "jira_project": "TEST", "jira_epic": "EPIC-123", "jira_additional_labels": ["test-label-1", "test-label-2"], "group": {"name": "some-group", "priority": 2}},
    {"step": "*ignore*", "failure_type": "test_failure", "classification": "NONE", "jira_project": "NONE", "ignore": "true"},
    {"step": "affects-version", "failure_type": "all", "classification": "Affects Version", "jira_project": "TEST", "jira_epic": "EPIC-123", "jira_affects_version": "4.14"}
]
```

The firewatch configuration can be saved to a file (can be stored wherever you want and named whatever you want, it must be JSON though) or defined in the `FIREWATCH_CONFIG` variable. When using the `report` command, if an argument for `--firewatch_config_path` is not provided, the environment variable will be used.

The firewatch configuration is a list of rules, each rule is defined using the following values:

### Required Values

#### `step`

The exact or partial name of a step in OpenShift CI. Using this value, we can usually determine what may have gone wrong during an OpenShift CI run.

**Example:**

Say you have multiple steps whose names start with `infra-setup-` and you can confidently say that most of the time, if a run fails during one of these steps, it is probably an infrastructure setup issue. You can define a rule to always file a bug in a specific Jira project so the issue can be addressed. The value in this instance would be something like `infra-setup-*`.

- Exact step name: `"step": "exact-step-name"`
- Partial step name:
  - `"step": "some-partial-step-*`: This would match multiple steps like `some-partial-step-1` and `some-partial-step-2`. The `*` value will match any wildcard of any length.
  - `"step": "some-step-?-single-char`: This would match multiple steps like `some-step-1-single-char` and `some-step-2-single-char`. The `?` value will match any single character in the name.

**Notes:**

- The value of this key can be whatever you'd like and can use shell-style wildcards in the definition of this key:
  - `*` – matches everything.
  - `?` – matches any single character.

---

#### `failure_type`

The type of failure you'd like issues to be created for.

**Options:**

- `pod_failure`: A failure where the code being executed in the step (OpenShift CI pod) returns a non-zero exit code (when the `passed` value in [`finished.json`](https://docs.prow.k8s.io/docs/metadata-artifacts/) is set to `false`)
- `test_failure`: A failure where the code being executed in the step produces one or more JUnit files (must have `junit` in the filename) that is in the artifacts (copied into the `$ARTIFACT_DIR`) for the step and any failure is found in the JUnit file(s).
- `all`: Either a `pod_failure` or a `test_failure`.

**Example:**

- `"failure_type": "pod_failure"`
- `"failure_type": "test_failure"`
- `"failure_type": "all"`

**Notes:**

This value **MUST** be one of the options outlined above.

---

#### `classification`

How you'd like to classify the issue in Jira. This is not a formal field in Jira, but will be included in the issue description. This is meant to act as a "best-guess" value for why the failure happened.

**Example:**

- `"classification": "Infrastructure - Cluster Provisioning"`

**Notes:**

This can be any string value and does not affect the way issues are created apart from it being included in the description of the issue.

---

#### `jira_project`

The Jira project you'd like the issue to be filed under. This should just be a string value of the project key.

**Example:**

- `"jira_project": "LPTOCPCI"`

---

### Optional Values

#### `jira_epic`

The epic you would like issues to be related to. This value should just be the ID of the epic you would like to use.

**Example:**

- `"jira_epic": "TEST-1234"`

**Notes:**

- Any epic you use must have the automation user being used in Jira set as a contributor to the epic/project.
  - For OpenShift CI, the default user is currently `interop-test-jenkins interop-test-jenkins`.
- The epic **can** be in a different project than the project defined in the [`jira_project`](#jiraproject) config value.

---

#### `jira_component`

The component/components you would like issues to be added to.

**Example:**

- Using a single component:
  - `"jira_component": "component-name"`
- Using multiple components:
  - `"jira_component": ["component-1", "component-2"]`

**Notes:**

- Please verify the component(s) you are planning on using exist in the project defined in the [`jira_project`](#jiraproject) config value.

---

#### `jira_affects_version`

The version affected by this bug. This will result in the "Affects Version/s" field in Jira to be populated.

**Example:**

- `"jira_affects_version": "4.14"`

**Notes:**

- The version must exist in the project defined in the [`jira_project`](#jiraproject) config value.

---

#### `jira_additional_labels`

A list of additional labels to add to a bug.

**Example:**

- `"jira_additional_labels": ["test-label-1", "test-label-2"]`

**Notes:**

- The Jira API will not allow these strings to have spaces in them.

---

#### `jira_assignee`

The email address of the user you would like a bug assigned to if a bug is created.

**Example:**

- `"jira_assignee": "some-user@redhat.com"`

**Notes:**

- Must be the EMAIL ADDRESS of the user you would like to assign bugs to.

---

#### `jira_priority`

The priority desired for a bug created using this rule.

**Example(s):**

- `"jira_priority": "Blocker"`
- `"jira_priority": "critical"`
- `"jira_priority": "MAJOR"`
- `"jira_priority": "Normal"`
- `"jira_priority": "minor"`

**Notes:**

- This value must be set to one of the following, as they are the only available options in Red Hat's Jira instance (may be expanded):
  - `Blocker`
  - `Critical`
  - `Major`
  - `Normal`
  - `Minor`
- This value is _not_ case-sensitive.

---

#### `ignore`

A value that be set to "true" or "false" and allows the user to define `step`/`failure_type` combinations that should be ignored when creating tickets.

**Example:**

- `"ignore": "true"`
  - Ignore the `step`/`failure_type` combination when a failure is found that matches this rule.
- `"ignore": "false"`
  - Do not ignore the `step`/`failure_type` combination when a failure is found that matches this rule.
  - This is the default behavior of all rules. If set to `false`, it does not need to be defined.

#### `group`

A dictionary object that is used to define the group of rules a specific rule belongs to and the priority of the rule within that group.
This value is useful for when you have one or more steps that are dependent on other steps. If multiple steps are members of the same group,
and they all fail because one of the steps failed, firewatch will look for the highest priority failure and only report on that failure.

The dictionary object should include a string value for `"name"` and an **integer** value for `"priority"`. For example: `"group": {"name": "some-group-name", "priority": 1}`

**Example:**

In this scenario, we have three steps: `step-1`, `step-2`, and `step-3`. If `step-1` fails, it will cause `step-2` and `step-3` to also fail and if `step-2` fails `step-3` will also fail.
Because these steps are all dependent on each other, it makes sense to group them together to avoid multiple Jira issues being created for the same failure.

```json
[
    {"step": "step-1", "failure_type": "all", "classification": "Misc.", "jira_project": "TEST", "group": {"name": "some-group", "priority": 1}},
    {"step": "step-2", "failure_type": "all", "classification": "Misc.", "jira_project": "TEST", "group": {"name": "some-group", "priority": 2}},
    {"step": "step-3", "failure_type": "all", "classification": "Misc.", "jira_project": "TEST", "group": {"name": "some-group", "priority": 3}}
]
```

Using the example configuration above:

- If `step-1` fails causing `step-2` and `step-3` to fail, only the rule for `step-1` will be reported because it has the highest priority.
- If `step-2` fails causing `step-3` to fail, only the rule for `step-2` will be reported because it has the highest priority.
- If `step-3` fails, only the rule for `step-3` will be reported.
