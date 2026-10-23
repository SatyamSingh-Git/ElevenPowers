# eventlog reference

An append-only log of keyed events, stored as a directory of segment files.

## Options

`LogConfig` fields. Passed to `Log.open(directory, config)`.

| Option | Default | Meaning |
|---|---|---|
| `segment_bytes` | `1048576` | The active segment is sealed and a new one started once it reaches this size. |
| `max_key_bytes` | `1024` | Longest key accepted, in bytes after UTF-8 encoding. |
| `max_value_bytes` | `65536` | Longest value accepted, in bytes. |
| `clock` | `ManualClock(0)` | Not a `LogConfig` field but a `Log.open` argument: a callable returning milliseconds, used when `append` gets no `timestamp`. |

## Limits

| Limit | Value | Meaning |
|---|---|---|
| `segment_bytes.min` | `64` | Smaller values raise `ConfigError`. |
| `max_key_bytes.max` | `65535` | The key length field is 16 bits. |

## Segment files

| Field | Value | Meaning |
|---|---|---|
| `segment.name` | `{base_offset:020d}.log` | One file per segment, named by the offset of its first record. |
| `segment.magic` | `EVLG` | First four bytes of every segment. |
| `segment.version` | `1` | Format version byte after the magic. Other versions are refused. |
| `segment.header` | `magic(4) version(u8) base_offset(u64)` | Fixed header before the first record. |
| `segment.header_bytes` | `13` | Size of the header. |
| `byte_order` | `big-endian` | Every integer in segment and index files. |

## Records

Records follow the segment header back to back.

| Field | Value | Meaning |
|---|---|---|
| `record.length` | `u32` | Number of bytes after the length field. |
| `record.crc` | `CRC-32C` | Checksum (Castagnoli) of every byte after the crc field. |
| `record.offset` | `u64` | The record's offset. |
| `record.timestamp` | `u64` | Milliseconds, from the `timestamp` argument or the clock. |
| `record.flags` | `u8` | Bit flags. |
| `record.key_length` | `u16` | Length of the key that follows. |
| `record.key` | `bytes` | The key. |
| `record.value` | `bytes` | The rest of the record. |
| `record.body_overhead` | `23` | Bytes after the length field other than key and value. |
| `flags.tombstone` | `0x01` | Set on records written by `Log.delete`. |

## Index files

| Field | Value | Meaning |
|---|---|---|
| `index.name` | `{base_offset:020d}.idx` | One per segment, beside it. |
| `index.entry` | `offset(u64) position(u32)` | One entry per record; position is the byte position in the segment file. |
| `index.entry_bytes` | `12` | Size of one entry. |

## Recovery

| Behaviour | Value | Meaning |
|---|---|---|
| `recovery.torn_tail` | `truncate` | On open, a record cut short at the end of the newest segment is cut off. |
| `recovery.corrupt` | `CorruptRecord` | A complete record that fails its checksum is never dropped silently. |

## Stats

`stats(directory)` reads the files without opening the log. `format_stats` prints one `name: value` line per field.

| Field | Value | Meaning |
|---|---|---|
| `stats.fields` | `segments records keys tombstones bytes first_offset next_offset` | `LogStats` fields, in order. |
| `stats.bytes` | `segment files` | Total size of segment files, headers included; index files are not counted. |
| `stats.offsets_line` | `offsets: {first_offset}..{next_offset}` | How `format_stats` shows the two offset fields. |

## Errors

Every error derives from `EventLogError`. Messages:

| Error | Message | Raised when |
|---|---|---|
| `ConfigError` | `segment_bytes must be at least 64` | `segment_bytes` below the minimum. |
| `EmptyKey` | `key must not be empty` | Appending with an empty key. |
| `KeyTooLarge` | `key of {size} bytes exceeds max_key_bytes {limit}` | Key longer than `max_key_bytes`. |
| `ValueTooLarge` | `value of {size} bytes exceeds max_value_bytes {limit}` | Value longer than `max_value_bytes`. |
| `OffsetOutOfRange` | `offset {offset} is outside {first}..{next}` | Replaying from before the first offset or past the next one. |
| `UnsupportedFormat` | `{segment}: unsupported format version {version}` | Opening a segment with another format version. |
| `NotASegment` | `{segment}: not an event log segment` | Bad magic or a file shorter than the header. |
| `CorruptRecord` | `corrupt record at position {position} in {segment}` | Checksum or framing failure. |
| `LogClosed` | `log is closed` | Appending after `close`. |
