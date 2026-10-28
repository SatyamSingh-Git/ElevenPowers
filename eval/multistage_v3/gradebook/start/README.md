# gradebook

A course gradebook for teachers: a course file describes the grading
categories, assignments and rules; rosters and scores come in from CSV files,
an LMS export or a hand-filled score sheet; grades go out as reports, report
cards and the term grades file the registrar's office posts to transcripts.

```
gradebook init-course course.json --code ALG1 --title "Algebra I"
gradebook new course.json
gradebook import roster roster.csv
gradebook import scores scores.csv
gradebook report --format markdown
gradebook export-grades alg1-grades.csv
gradebook transcript s1 alg1-grades.csv bio1-grades.csv
```

Standard library only; Python 3.11 or later. Run the tests with
`PYTHONPATH=src python -m pytest`.

Everything the program promises is listed in `docs/reference.md`.
