from collections.abc import Collection
from collections.abc import Iterator
from dataclasses import asdict
from dataclasses import dataclass
from enum import auto
from enum import Enum
from pathlib import Path
from typing import Any
from typing import Type

from cli.objects.failure import Failure
from cli.objects.failure_rule import FailureRule

GITLEAKS_FAILURE_TYPE = "gitleaks_failure"
DEFAULT_GITLEAKS_FAILED_STEP = "firewatch-report"
DEFAULT_GITLEAKS_FAILED_TEST_NAME = "gitleaks-detect-scan"

RENAME_JSON_KEY_MAP = {
    "lineNumber": "line_number",
    "repoURL": "repo_url",
    "leakURL": "leak_url",
    "commitMessage": "commit_message",
    "offenderEntropy": "offender_entropy",
}


class _Enums(Enum):
    REDACTED = auto()


@dataclass
class GitleaksDetectionsJobFailure(Failure):
    step: str = DEFAULT_GITLEAKS_FAILED_STEP
    failure_type: str = GITLEAKS_FAILURE_TYPE
    failed_test_name: str = DEFAULT_GITLEAKS_FAILED_TEST_NAME
    failed_test_junit_path: str = ""

    def __post_init__(self) -> None:
        super().__init__(
            failure_type=self.failure_type,
            failed_step=self.step,
            failed_test_name=self.failed_test_name,
            failed_test_junit_path=None,
        )


@dataclass
class GitleaksDetectionsFailureRule(FailureRule):
    step: str = DEFAULT_GITLEAKS_FAILED_STEP
    classification: str = "Gitleaks Failure"
    failure_type: str = GITLEAKS_FAILURE_TYPE
    ignore: bool = False
    priority: int = 1
    group_priority: int = 1
    group_name: str = "gitleaks"

    VALID_FAILURE_TYPES = [GITLEAKS_FAILURE_TYPE]

    def __post_init__(self) -> None:
        super().__init__(rule_dict=asdict(self))


@dataclass
class GitleaksDetection:
    line: str | _Enums = ""
    line_number: int | None = None
    offender: str | _Enums = ""
    offender_entropy: int | None = None
    commit: str = ""
    repo: str = ""
    repo_url: str = ""
    leak_url: str = ""
    rule: str = ""
    commit_message: str = ""
    author: str = ""
    email: str = ""
    file: str = ""
    date: str = ""
    tags: str = ""
    REDACTED = _Enums.REDACTED
    redact_contents = True

    @property
    def path(self) -> Path:
        return Path(self.file)

    def __post_init__(self) -> None:
        if self.redact_contents:
            self.line = self.REDACTED
            self.offender = self.REDACTED

    @classmethod
    def from_json(cls, json_obj: dict[str, Any]) -> "GitleaksDetection":
        for old_key, new_key in RENAME_JSON_KEY_MAP.items():
            json_obj[new_key] = json_obj.pop(old_key)
        return cls(**json_obj)


@dataclass
class GitleaksDetectionCollection(Collection[GitleaksDetection]):
    _inner: list[GitleaksDetection]

    def __len__(self) -> int:
        return self._inner.__len__()

    def __iter__(self) -> Iterator[GitleaksDetection]:
        return self._inner.__iter__()

    def __contains__(self, __x: Any) -> bool:
        return self._inner.__contains__(__x)

    @classmethod
    def from_iter(
        cls: "Type[GitleaksDetectionCollection]",
        _it: Iterator[GitleaksDetection],
    ) -> "GitleaksDetectionCollection":
        return cls([_ for _ in _it])

    def to_job_failure(
        self,
        step: str = DEFAULT_GITLEAKS_FAILED_STEP,
    ) -> "GitleaksDetectionsJobFailure":
        return GitleaksDetectionsJobFailure(step=step)

    def to_failure_rule(
        self,
    ) -> "GitleaksDetectionsFailureRule":
        return GitleaksDetectionsFailureRule()

    def iter_detection_paths(self, parent_dir: Path = Path()) -> Iterator[Path]:
        for detection in self._inner:
            yield parent_dir / detection.path
