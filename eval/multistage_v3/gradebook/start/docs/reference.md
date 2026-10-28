# Gradebook reference

Every option, default, file format, limit and message the gradebook promises.
The first column is the name, the second its value; the third says where it
applies: the course file, the course grade (`Gradebook.grade`), a file the
gradebook reads or writes, or the command line.

## Course file options

A course file is JSON. `code`, `title`, `categories` and `assignments` are
required; everything below falls back to the value shown.

| name | default | meaning |
|---|---|---|
| `credits` | `1.0` | course file: credits the course carries on a transcript |
| `policy` | `weighted` | course file: scoring policy, `weighted` or `points` |
| `scale` | `standard` | course file: letter scale, `standard` or `pass_fail` |
| `late_rule` | `none` | course file: late rule, `none` or `per_day` |
| `late.per_day` | `10` | course file: percent of an assignment's points lost per day late under `per_day` |
| `late.cap` | `50` | course file: most percent of an assignment's points a late penalty takes |
| `grade_decimals` | `1` | course file: decimals final and category percents are rounded to |
| `weight` | `0` | course file, per category: weight in percent, used by the `weighted` policy |
| `drop_lowest` | `0` | course file, per category: how many of a student's lowest scores are dropped |
| `title` | `{id}` | course file, per assignment: shown in reports; defaults to the assignment id |

## Grading rules

| name | value | meaning |
|---|---|---|
| `rounding` | `half up` | course grade: how final and category percents are rounded |
| `drop_lowest.rank` | `points earned` | course grade: how drop_lowest ranks scores to find the lowest |
| `drop_lowest.keep` | `1` | course grade: drop_lowest always keeps at least this many scores in a category |
| `missing` | `0` | course grade: points counted for work past due with no score |
| `excused.counts` | `no` | course grade: whether excused work counts toward a category |
| `weight_total` | `100` | course file: what category weights must add up to under `weighted` |
| `no_grade` | `blank` | course grade, class report and term grades file: letter for a student with no graded work |
| `gpa_decimals` | `2` | transcript: decimals the GPA is rounded to, half up |

## Limits

| name | value | meaning |
|---|---|---|
| `max_students` | `500` | roster: most students one course holds |
| `max_drop_lowest` | `3` | course file: largest `drop_lowest` a category may set |
| `max_grade_decimals` | `3` | course file: largest `grade_decimals` |
| `max_term_days` | `400` | calendar file: last term day the `day` and `date` commands handle |

## Letter scales

The `standard` scale comes from the district's DGS-2024 grading standard
(`src/gradebook/_generated.py`). A percent earns the first letter whose
minimum it reaches.

| letter | minimum percent | meaning |
|---|---|---|
| `A` | `93` | standard scale |
| `A-` | `90` | standard scale |
| `B+` | `87` | standard scale |
| `B` | `83` | standard scale |
| `B-` | `80` | standard scale |
| `C+` | `77` | standard scale |
| `C` | `73` | standard scale |
| `C-` | `70` | standard scale |
| `D+` | `67` | standard scale |
| `D` | `63` | standard scale |
| `D-` | `60` | standard scale |
| `F` | `0` | standard scale |
| `P` | `60` | pass_fail scale: earns credit, not counted in the GPA |
| `NP` | `0` | pass_fail scale: no credit, not counted in the GPA |

## Grade points

| letter | points | meaning |
|---|---|---|
| `gpa.A` | `4.0` | transcript: grade points for A |
| `gpa.A-` | `3.7` | transcript: grade points for A- |
| `gpa.B+` | `3.3` | transcript: grade points for B+ |
| `gpa.B` | `3.0` | transcript: grade points for B |
| `gpa.B-` | `2.7` | transcript: grade points for B- |
| `gpa.C+` | `2.3` | transcript: grade points for C+ |
| `gpa.C` | `2.0` | transcript: grade points for C |
| `gpa.C-` | `1.7` | transcript: grade points for C- |
| `gpa.D+` | `1.3` | transcript: grade points for D+ |
| `gpa.D` | `1.0` | transcript: grade points for D |
| `gpa.D-` | `0.7` | transcript: grade points for D- |
| `gpa.F` | `0.0` | transcript: grade points for F; F earns no credit |

## Files

| name | value | meaning |
|---|---|---|
| `roster.columns` | `student_id,last_name,first_name` | roster file (`import roster`): required columns |
| `scores.columns` | `student_id,assignment_id,points,submitted_day` | score file (`import scores`, `export-scores`); `submitted_day` is optional |
| `cell.excused` | `EX` | score files, score sheets and LMS exports: cell value that excuses the work |
| `sheet.columns` | `student_id,{assignments}` | score sheet file (`sheet`, `write_score_sheet`): header, assignments in due order |
| `lms.points_possible` | `Points Possible` | LMS export file (`import lms`): row whose points must match the course |
| `grades.columns` | `student_id,name,course,credits,percent,letter` | term grades file (`export-grades`, `export_grades`): header; `percent` is the course grade percent |
| `grades.delimiter` | `,` | term grades file: field delimiter |
| `report.columns` | `student_id,name,percent,letter` | class report (`report`, `class_summary`): columns |
| `gradebook.format` | `1` | gradebook file: format version |

Transcripts (`transcript`, `build_transcript`) are built from posted term
grades files. A course whose letter is blank is listed but counts toward
neither credits nor the GPA.

## Command line

| name | default | meaning |
|---|---|---|
| `--book` | `gradebook.json` | CLI: the gradebook file a command reads and writes |
| `--format` | `text` | CLI `report` and other table commands: `text`, `csv` or `markdown` |
| `--as-of` | `every assignment` | CLI: term day grades are computed as of; work due later does not count |
| `--below` | `70` | CLI `at-risk`: percent to flag students under |
| `exit.error` | `1` | CLI: exit status when a command fails |
| `exit.problems` | `3` | CLI `check`: exit status when problems are found |

## Messages

| name | message | meaning |
|---|---|---|
| `unknown_policy` | `unknown scoring policy {name}; choose weighted or points` | course file: loading a course file that names an unknown policy |
| `unknown_scale` | `unknown letter scale {name}` | course file: unknown `scale` |
| `unknown_late_rule` | `unknown late rule {name}` | course file: unknown `late_rule` |
| `unknown_late_setting` | `unknown late setting {key}` | course file: unknown key under `late` |
| `bad_weights` | `category weights add up to {total}, not 100` | course file: weights under `weighted` |
| `unknown_category` | `assignment {assignment} names unknown category {category}` | course file |
| `duplicate_assignment` | `duplicate assignment {assignment}` | course file |
| `drop_lowest_range` | `{category}: drop_lowest must be between 0 and 3` | course file |
| `unknown_student` | `unknown student {student}` | API and CLI |
| `unknown_assignment` | `unknown assignment {assignment}` | API and CLI |
| `duplicate_student` | `duplicate student {student}` | roster import and API |
| `roster_full` | `a course holds at most {limit} students` | roster import and API |
| `points_out_of_range` | `{assignment}: points {points} outside 0 to {max}` | API; imports put `line {line}: ` in front |
| `bad_points` | `line {line}: cannot read points {value}` | score files, score sheets and LMS exports |
| `missing_column` | `{file}: missing column {column}` | every CSV file the gradebook reads |
| `unknown_import_kind` | `unknown import kind {kind}` | CLI `import` and `Gradebook.import_file` |
| `unknown_format` | `unknown format {name}; choose text, csv or markdown` | CLI `--format` |
| `not_on_transcript` | `student {student} is not in any posted grades file` | CLI `transcript` and `build_transcript` |
| `cli_error` | `error: {message}` | CLI: how any of the messages above is printed, on stderr |
