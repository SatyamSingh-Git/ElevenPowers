# 47. Installed should mean active

2026-09-29. After repository scanning and declared-command support shipped, the user asked whether those things would happen automatically when the plugin was installed. The answer was only partly yes: hooks already collected evidence, but command declaration and the large-project budget still required setup.

## Move ordinary setup into the product

The runtime now discovers verification entry points from supported root manifests. Node scripts follow the declared package manager or an unambiguous lockfile; `ci` takes priority over `test`. Pytest configuration, Cargo and Go can supply missing needs. Explicit configuration wins, empty values disable individual needs, and `auto_detect: false` disables discovery. Detection does not write a config file.

SessionStart checks basic health and reports effective commands and scan coverage. It does not run the suite. Missing or stale checks run at completion in guide/strict, and off stays passive. The default scan budget is 256 MiB, with the file limit still 20,000. Source-observation and startup hooks allow 120 seconds for cold scans; prompt/edit guards stay at 20 seconds.

## Automatic execution changed the consequences of old code

Discovery exposed an existing baseline loop that ran every configured command after any tests passed. A normal bug-fix task could therefore trigger an unrelated benchmark or build. Baseline execution now requires both a relevant obligation and matching passing evidence. Shared verification commands are deduplicated within a discharge attempt.

A frontend package manifest also hid a backend pytest declaration because discovery returned too early. Supported manifests now fill missing needs together; genuine native-stack conflicts require a project-selected aggregate command.

The real launcher probe caught another error: a numbered TAP `ok` result was counted as a Go package as well as through the TAP totals. A one-test run became two passes. The parser now excludes numbered TAP results from Go package aggregation. The corrected probe ran `npm run ci`, recorded exactly one passing test, and created no configuration file.

## Evidence and limits

Read-only Snag selection now discovers its commands and covers 4,418 files / 81,841,401 bytes with defaults, in about 1.11 seconds for selection. No custom configuration was used. This does not establish full CI completion or an installed host session.

The broad regression run passed 857 tests with 26 skips and one outdated baseline-cache fixture failure. That fixture had no active task claim; after adding one, its intended cache behavior passed. Final publication checks passed 103 command/execution tests and 63 startup/scanning/hook tests. The full suite was not repeated after the fixture-only correction. All four architecture views rendered.

Three pushes delivered this follow-up: `2636ded` for discovery and execution controls, `fc527d9` for startup and scan defaults, and `a548d03` for documentation. [The validation report](../docs/validation/2026-09-29-automatic-setup.md) carries the details.

The product milestone is now an installed Snag session with its full CI and ordinary edits observed. The lesson is specific: installing the integration should activate its supported conventions, and automation must remain constrained by the task and the evidence it actually has.
