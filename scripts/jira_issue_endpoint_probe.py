import json
import os
import subprocess
import sys

import requests

JIRA_CLOUD = "https://redhat.atlassian.net"
ISSUE_URL = f"{JIRA_CLOUD}/rest/api/3/issue"


def _unwrap_kv_payload(data: dict) -> dict:
    inner = data.get("data") or {}
    nested = inner.get("data")
    if isinstance(nested, dict) and ("email" in nested or "token" in nested or "username" in nested):
        return nested
    return inner if isinstance(inner, dict) else {}


def load_credentials_from_vault() -> tuple[str | None, str | None]:
    path = os.environ.get("FIREWATCH_JIRA_VAULT_PATH")
    if not path:
        return None, None
    out = subprocess.check_output(
        ["vault", "kv", "get", "-format=json", path],
        text=True,
    )
    payload = _unwrap_kv_payload(json.loads(out))
    email_key = os.environ.get("FIREWATCH_JIRA_VAULT_EMAIL_FIELD", "email")
    token_key = os.environ.get("FIREWATCH_JIRA_VAULT_TOKEN_FIELD", "token")
    return payload.get(email_key), payload.get(token_key)


def main() -> None:
    print("GET /rest/api/3/issue (no auth)")
    r = requests.get(ISSUE_URL, timeout=30)
    print(f"  status={r.status_code}")
    print(f"  body snippet: {r.text[:200]!r}")
    print()
    print("POST /rest/api/3/issue with empty fields (no auth)")
    r2 = requests.post(
        ISSUE_URL,
        json={"fields": {}},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    print(f"  status={r2.status_code}")
    print(f"  body snippet: {r2.text[:200]!r}")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_TOKEN")
    if (not email or not token) and os.getenv("FIREWATCH_JIRA_VAULT_PATH"):
        ve, vt = load_credentials_from_vault()
        if ve and vt:
            email, token = ve, vt
            print()
            print("Loaded JIRA_EMAIL / JIRA_TOKEN from Vault (FIREWATCH_JIRA_VAULT_PATH).")
    if not email or not token:
        print()
        print(
            "Set JIRA_EMAIL and JIRA_TOKEN, or source scripts/jira_vault_env.sh "
            "(FIREWATCH_JIRA_VAULT_PATH) before running, for an authenticated POST.",
        )
        sys.exit(0)
    print()
    print("POST /rest/api/3/issue with invalid fields (auth)")
    r3 = requests.post(
        ISSUE_URL,
        json={"fields": {}},
        headers={"Content-Type": "application/json"},
        auth=(email, token),
        timeout=30,
    )
    print(f"  status={r3.status_code}")
    print(f"  body snippet: {r3.text[:300]!r}")


if __name__ == "__main__":
    main()
