"""
Seed the local Outline installation with a workspace, an admin, and a token.

Outline has no way to create the first user over the API: a workspace is
normally bootstrapped by signing in through an identity provider, and an API
key is then created from the settings screen. Neither is available to an
unattended test run, so the rows are written straight into the database.

Everything is fixed rather than generated, so the script is idempotent and the
credentials it prints are the same on every run - `make outline-up` can be run
repeatedly, and CI does not have to thread a generated token anywhere.

Run through `make outline-up`, after the stack reports healthy.
"""

import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPOSE = ["docker", "compose", "-f", "docker/compose.yaml", "-p", "outline-client"]

URL = "http://localhost:8099"

TEAM_ID = "11111111-1111-4111-8111-111111111111"
USER_ID = "22222222-2222-4222-8222-222222222222"
KEY_ID = "33333333-3333-4333-8333-333333333333"
MEMBER_ID = "44444444-4444-4444-8444-444444444444"
COLLECTION_ID = "55555555-5555-4555-8555-555555555555"

TEAM_NAME = "Integration Tests"
USER_NAME = "Integration Test Admin"
USER_EMAIL = "admin@outline-client.test"

# A second, non-admin account. The membership and role methods cannot be
# exercised against the admin alone: Outline refuses to let a user change their
# own role, invite themselves to a document, or leave a collection without an
# administrator.
MEMBER_NAME = "Integration Test Member"
MEMBER_EMAIL = "member@outline-client.test"

# A baseline collection, so the suite's own collection is never the workspace's
# only one. Outline's `Collection.checkLastCollection` hook refuses to delete
# the last collection in a team, which would otherwise leave the module fixture
# unable to tear itself down on a freshly seeded instance.
COLLECTION_NAME = "Baseline"

# `Collection.DEFAULT_SORT`, which Outline applies in its model rather than the
# database, so a row written here does not get it. Without it, loading a
# published share of a document in the collection fails with a 500.
COLLECTION_SORT = '{"field": "index", "direction": "asc"}'

# Outline's own format: the `ol_api_` prefix followed by 38 word characters.
# `ApiKey.match` rejects anything else before it even looks in the database.
TOKEN = "ol_api_outlineClientIntegrationTests000000001"

# The `apiKeys` table stores the SHA-256 of the token, which is what
# `ApiKey.findByToken` looks the incoming bearer token up by.
TOKEN_HASH = hashlib.sha256(TOKEN.encode()).hexdigest()

SEED_SQL = f"""
BEGIN;

INSERT INTO teams (id, name, "createdAt", "updatedAt")
VALUES ('{TEAM_ID}', '{TEAM_NAME}', now(), now())
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, name, email, "teamId", role, "jwtSecret", "createdAt", "updatedAt", "lastActiveAt")
VALUES (
    '{USER_ID}',
    '{USER_NAME}',
    '{USER_EMAIL}',
    '{TEAM_ID}',
    'admin',
    decode(md5(random()::text) || md5(random()::text), 'hex'),
    now(),
    now(),
    now()
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, name, email, "teamId", role, "jwtSecret", "createdAt", "updatedAt", "lastActiveAt")
VALUES (
    '{MEMBER_ID}',
    '{MEMBER_NAME}',
    '{MEMBER_EMAIL}',
    '{TEAM_ID}',
    'member',
    decode(md5(random()::text) || md5(random()::text), 'hex'),
    now(),
    now(),
    now()
)
ON CONFLICT (id) DO NOTHING;

INSERT INTO collections (
    id, name, description, "urlId", "teamId", "createdById", permission,
    "documentStructure", sharing, index, sort, "createdAt", "updatedAt"
)
VALUES (
    '{COLLECTION_ID}',
    '{COLLECTION_NAME}',
    'Kept so the suite never has to delete the workspace''s last collection.',
    'baselineC0',
    '{TEAM_ID}',
    '{USER_ID}',
    'read_write',
    '[]'::jsonb,
    true,
    'P',
    '{COLLECTION_SORT}'::jsonb,
    now(),
    now()
)
ON CONFLICT (id) DO UPDATE SET sort = EXCLUDED.sort;

INSERT INTO "apiKeys" (id, name, "userId", hash, last4, "createdAt", "updatedAt")
VALUES (
    '{KEY_ID}',
    'integration-tests',
    '{USER_ID}',
    '{TOKEN_HASH}',
    '{TOKEN[-4:]}',
    now(),
    now()
)
ON CONFLICT (id) DO NOTHING;

COMMIT;
"""


# =============================================================================
# FUNCTION: psql
# =============================================================================


def psql(sql: str) -> str:
    """
    Run one statement against the stack's database.

    Returns:
        str: Whatever psql wrote to stdout.
    """
    result = subprocess.run(
        [*COMPOSE, "exec", "-T", "postgres", "psql", "-U", "outline", "-d", "outline"],
        input=sql,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if result.returncode != 0:
        raise SystemExit(f"psql failed:\n{result.stderr}")

    return result.stdout


# =============================================================================
# FUNCTION: main
# =============================================================================


def main() -> int:
    """
    Seed the database and print the credentials the test suite needs.

    Returns:
        int: The process exit code.
    """
    if len(TOKEN.removeprefix("ol_api_")) != 38:
        raise SystemExit("TOKEN is malformed; Outline requires 38 characters")

    psql(SEED_SQL)

    print(f"Outline is ready at {URL}")
    print()
    print("  export OUTLINE_API_URL=" + URL)
    print("  export OUTLINE_API_TOKEN=" + TOKEN)
    print()
    print(f"Signed in as {USER_NAME} <{USER_EMAIL}> of {TEAM_NAME!r}.")
    print(f"A second, non-admin account exists as {MEMBER_NAME} <{MEMBER_EMAIL}>.")
    print(f"A baseline collection exists as {COLLECTION_NAME!r}.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
