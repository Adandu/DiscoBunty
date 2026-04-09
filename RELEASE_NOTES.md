# DiscoBunty v0.9.8

## New Features

- No new end-user features were added in this release.

## Improvements

- Upgraded the FastAPI and cryptography dependency baseline and moved the container build to Python 3.12 with package upgrades during image build.
- Added security-focused tests for log-path validation and Discord error redaction.

## Bug Fixes

- Fixed the `/logs` access-control path so failed remote path resolution now denies access instead of falling back to the original user-supplied path.
- Stopped returning raw backend exception details to Discord users and replaced them with a reference ID tied to server-side logs.
