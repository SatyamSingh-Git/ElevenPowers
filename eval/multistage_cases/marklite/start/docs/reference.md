# marklite reference

## Options

Fields of `marklite.Options`, with their defaults.

| Option | Default | Meaning |
|---|---|---|
| `heading_ids` | `True` | Give top-level headings an `id` attribute. |
| `toc_max_level` | `3` | Deepest heading level the table of contents lists (1 to 6). |
| `code_class_prefix` | `language-` | Prefix of the class on a fenced code block with a language. |
| `safe_links` | `True` | Replace link and image URLs whose scheme is not safe. |
| `hard_breaks` | `False` | Render every line break inside a paragraph as `<br />`. |

## Syntax

| Markdown | HTML | Notes |
|---|---|---|
| `*text*` | `<em>text</em>` | `_text_` too, but not inside a word. |
| `**text**` | `<strong>text</strong>` | `__text__` too. |
| `[text](url)` | `<a href="url">text</a>` | An optional `"title"` follows the URL. |
| `![alt](url)` | `<img src="url" alt="alt" />` | The alt text is the plain text of the label. |
| `[TOC]` | `<nav class="toc">` | A paragraph holding only the marker becomes the table of contents. |

Fenced code blocks (three or more backticks or tildes), ATX headings, block
quotes, bullet and ordered lists, rules, code spans, autolinks
(`<https://...>`) and entity references are supported. Indented code blocks,
setext headings, tables and HTML blocks are not.

## Escaping and links

| Fact | Value | Meaning |
|---|---|---|
| `escaped_in_text` | `& < > "` | Characters written as entities in text content. |
| `safe_schemes` | `http, https, mailto` | URL schemes kept when `safe_links` is on; URLs without a scheme are always kept. |
| `unsafe_url` | `#` | What replaces a URL with any other scheme. |

## Heading ids and the table of contents

A heading's slug is its plain text in lowercase, letters and digits kept, every
other run of characters turned into a single `-`.

| Fact | Value | Meaning |
|---|---|---|
| `empty_slug` | `heading` | Slug of a heading with no letters or digits. |
| `duplicate_slug` | `{slug}-{n}` | Repeated slugs are numbered from 1 in document order. |
| `TocEntry` | `level, title, anchor` | Fields of each entry `marklite.toc()` returns; `title` is plain text and `anchor` is the heading's id. |

Only top-level headings (not those inside quotes or lists) get ids and appear in
the table of contents. An entry is nested under the closest earlier entry with
a lower level.

## Limits and errors

`MarkliteError` is a `ValueError` with a `line` attribute (1-based, or `None`).
When `line` is set, the message starts with `line {line}: `.

| Fact | Value | Meaning |
|---|---|---|
| `max_heading_level` | `6` | `#` to `######`. |
| `max_input_chars` | `1000000` | Longest input `parse`, `render` and `toc` accept. |
| `input_size_error` | `input exceeds 1000000 characters` | Raised for longer input. |
| `toc_level_error` | `toc_max_level must be between 1 and 6` | Raised by `Options`. |

## Command line

`marklite PATH [-o OUTPUT]` renders `PATH` (or standard input for `-`).

| Flag | Default | Meaning |
|---|---|---|
| `--toc-level` | `3` | Sets `toc_max_level`. |
| `--json-toc` | `off` | Print the table of contents as JSON instead of HTML. |
| `--no-ids` | `off` | Sets `heading_ids` to false. |
| `--unsafe-links` | `off` | Sets `safe_links` to false. |
| `--hard-breaks` | `off` | Sets `hard_breaks` to true. |
| `cli_read_error` | `error: cannot read {path}` | Printed to standard error when the input cannot be read. |
| `cli_error_exit` | `1` | Exit status after any error; other errors print `error: ` and the message. |
