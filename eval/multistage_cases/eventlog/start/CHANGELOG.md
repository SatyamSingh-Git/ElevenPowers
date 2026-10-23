# Changelog

## Unreleased

- `eventlog dump --from` defaults to the first offset still in the log.

## 0.3.0

- Compaction by key: sealed segments keep only the latest record of each key.
- `Log.delete` writes tombstones; compaction drops deleted keys.
- `stats` summarises a directory without opening the log.

## 0.2.0

- Recovery truncates a record torn by a crash at the end of the newest segment.
- Offset index files beside each segment.

## 0.1.0

- First release: append, replay and segment rotation.
