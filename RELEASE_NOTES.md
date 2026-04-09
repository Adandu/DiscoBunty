# DiscoBunty v0.9.3

## New Features

- Added a first-run setup flow so new installs can create the WebUI password from the browser before normal login is enabled.
- Added fleet observability cards in the dashboard for CPU, RAM, disk, uptime, Docker container count, and last backup age.
- Added backup export and restore, an audit log viewer, and bulk server capability checks in the WebUI.

## Improvements

- Added per-server Discord role scoping so sensitive commands can be restricted by host instead of only globally.
- Made dashboard observability refresh configurable with `OBSERVABILITY_REFRESH_MS` and formatted backup age into friendlier values like `3h 12m`.
- Expanded the docs for the new server fields, observability settings, and dashboard behavior.

## Bug Fixes

- Restored compatibility with legacy deployments by automatically migrating an existing `/app/config.json` into the new data directory layout.
- Improved Discord command error handling so permission and autocomplete problems surface more clearly.
