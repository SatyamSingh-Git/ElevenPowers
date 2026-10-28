import pytest

from gradebook.errors import ImportFailed, NotOnTranscript
from gradebook.services.transcript import build_transcript, render_transcript

HEADER = "student_id,name,course,credits,percent,letter\n"


def posted(tmp_path, name, rows):
    path = tmp_path / name
    path.write_text(HEADER + "".join(row + "\n" for row in rows), encoding="utf-8")
    return path


def test_gpa_weights_by_credits(tmp_path):
    files = [
        posted(tmp_path, "alg.csv", ["s1,Ada Lovelace,ALG1,1,93.0,A", "s2,Alan Turing,ALG1,1,71.0,C-"]),
        posted(tmp_path, "art.csv", ["s1,Ada Lovelace,ART,0.5,88.0,B+"]),
    ]
    transcript = build_transcript("s1", files)
    assert [line.course for line in transcript.lines] == ["ALG1", "ART"]
    assert transcript.credits_attempted == 1.5
    assert transcript.credits_earned == 1.5
    assert transcript.gpa == 3.77


def test_ungraded_courses_are_listed_but_not_counted(tmp_path):
    files = [posted(tmp_path, "alg.csv", ["s1,Ada Lovelace,ALG1,1,93.0,A"]),
             posted(tmp_path, "bio.csv", ["s1,Ada Lovelace,BIO1,1,,"])]
    transcript = build_transcript("s1", files)
    assert transcript.line("BIO1").percent is None
    assert transcript.credits_attempted == 1.0
    assert transcript.gpa == 4.0


def test_failing_and_pass_fail(tmp_path):
    files = [posted(tmp_path, "a.csv", ["s1,Ada Lovelace,ALG1,1,50.0,F",
                                        "s1,Ada Lovelace,PE,0.5,75.0,P",
                                        "s1,Ada Lovelace,CHOIR,0.5,40.0,NP"])]
    transcript = build_transcript("s1", files)
    assert transcript.credits_attempted == 2.0
    assert transcript.credits_earned == 0.5
    assert transcript.gpa == 0.0


def test_later_file_wins(tmp_path):
    files = [posted(tmp_path, "old.csv", ["s1,Ada Lovelace,ALG1,1,80.0,B-"]),
             posted(tmp_path, "new.csv", ["s1,Ada Lovelace,ALG1,1,83.0,B"])]
    assert build_transcript("s1", files).line("ALG1").letter == "B"


def test_student_not_posted(tmp_path):
    files = [posted(tmp_path, "alg.csv", ["s1,Ada Lovelace,ALG1,1,93.0,A"])]
    with pytest.raises(NotOnTranscript, match="student s9 is not in any posted grades file"):
        build_transcript("s9", files)


def test_bad_file(tmp_path):
    path = tmp_path / "x.csv"
    path.write_text("student,course\n", encoding="utf-8")
    with pytest.raises(ImportFailed, match="x.csv: missing column student_id"):
        build_transcript("s1", [path])


def test_render(tmp_path):
    files = [posted(tmp_path, "alg.csv", ["s1,Ada Lovelace,ALG1,1,93.0,A"])]
    text = render_transcript(build_transcript("s1", files))
    assert "Transcript for Ada Lovelace (s1)" in text
    assert "GPA: 4.00" in text
