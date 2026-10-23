# warden

Role- and attribute-based access policies. Write a policy, ask it whether a
user may do something to a resource, and get an answer with its reason.

```
role viewer
role editor inherits viewer
allow viewer read reports/**
deny editor delete reports/archive/**
allow editor write reports/* when user.dept == resource.dept
```

```python
from warden import Evaluator, Request, User, explain, load_file

decision = Evaluator(load_file("reports.policy")).decide(
    Request(User("alice", ("editor",), {"dept": "ops"}), "write", "reports/q3", {"dept": "ops"}))
print(explain(decision))
```

```
python -m warden check reports.policy alice write reports/q3 --role editor --user-attr dept=ops --resource-attr dept=ops
python -m warden lint reports.policy
python -m warden report audit.jsonl
```

`src/warden/_generated.py` is produced by the action table generator and is
not edited by hand. See `docs/reference.md` for every format, default and message.
