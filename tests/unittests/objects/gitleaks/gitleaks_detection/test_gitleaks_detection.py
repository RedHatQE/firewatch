from cli.objects.gitleaks_detection import GitleaksDetection
from cli.objects.gitleaks_detection import GitleaksDetectionCollection
from cli.objects.gitleaks_detection import GitleaksDetectionsFailureRule
from cli.objects.gitleaks_detection import GitleaksDetectionsJobFailure


def test_init_gitleaks_detection_from_json(gitleaks_detection):
    assert isinstance(gitleaks_detection, GitleaksDetection)
    assert gitleaks_detection.line is GitleaksDetection.REDACTED
    assert gitleaks_detection.offender is GitleaksDetection.REDACTED
    assert gitleaks_detection.line_number == 7
    assert gitleaks_detection.offender_entropy == 5.311
    assert gitleaks_detection.commit_message == "add secrets"
