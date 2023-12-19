from cli.objects.gitleaks_detection import GitleaksDetectionCollection
from cli.objects.gitleaks_detection import GitleaksDetectionsFailureRule
from cli.objects.gitleaks_detection import GitleaksDetectionsJobFailure


def test_init_gitleaks_detection_collection(gitleaks_detection_iterator):
    assert isinstance(
        GitleaksDetectionCollection.from_iter(gitleaks_detection_iterator),
        GitleaksDetectionCollection,
    )


def test_gitleaks_detection_collection_to_job_failure(gitleaks_detection_collection):
    job_failure = gitleaks_detection_collection.to_job_failure()
    assert isinstance(job_failure, GitleaksDetectionsJobFailure)
    assert job_failure.failure_type
    assert job_failure.step


def test_gitleaks_detection_collection_to_failure_rule(
    default_jira_project_env,
    gitleaks_detection_collection,
):
    failure_rule = gitleaks_detection_collection.to_failure_rule()
    assert isinstance(failure_rule, GitleaksDetectionsFailureRule)
    assert failure_rule.step
    assert failure_rule.classification
    assert failure_rule.failure_type
    assert failure_rule.ignore is False
    assert failure_rule.priority
    assert failure_rule.jira_security_level == "Red Hat Employee"
