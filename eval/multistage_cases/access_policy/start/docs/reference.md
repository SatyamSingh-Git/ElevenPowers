# warden reference

## Policy text

| key | value | meaning |
| --- | --- | --- |
| `syntax.comment` | `#` | a line starting with this is ignored |
| `syntax.role` | `role <name> [inherits <parent>]` | defines a role |
| `syntax.rule` | `<effect> <role> <actions> <pattern> [when <condition>]` | one rule per line |
| `syntax.default` | `default <effect>` | effect when no rule matches |
| `syntax.actions_separator` | `,` | between actions in a rule |
| `effects` | `allow, deny` | the two rule effects |
| `default_effect` | `deny` | used when a policy sets no default |
| `precedence` | `deny-overrides` | a matching deny wins over any matching allow |
| `role.name` | `[A-Za-z][A-Za-z0-9_-]*` | allowed role names |
| `limit.inheritance_chain` | `8` | most roles in a chain, counting the role itself |

## Actions

| key | value | meaning |
| --- | --- | --- |
| `action.names` | `read, list, write, delete, share, admin` | known actions |
| `action.any` | `*` | in a rule, matches every action |
| `action.aliases` | `view, get: read; ls: list; edit, put: write; remove, rm: delete` | accepted in rules and requests |
| `action.case` | `insensitive` | `READ` is `read` |

## Resource patterns

| key | value | meaning |
| --- | --- | --- |
| `pattern.separator` | `/` | between path segments |
| `pattern.segment_wildcard` | `*` | any characters within one segment |
| `pattern.deep_wildcard` | `**` | zero or more whole segments |
| `pattern.normalize` | `empty segments dropped` | `/a//b/` is `a/b` |

## Conditions

| key | value | meaning |
| --- | --- | --- |
| `condition.namespaces` | `user, resource` | where attribute names may come from |
| `condition.operators` | `== != < <= > >=` | comparison operators |
| `condition.join` | `and` | joins clauses; all must hold |
| `condition.literals` | `"text", numbers, true, false` | constants allowed in a clause |
| `condition.compare` | `as text` | how values are compared |
| `condition.missing` | `false` | a clause naming an absent attribute never holds |

## Data format (dict or `.json` file)

| key | value | meaning |
| --- | --- | --- |
| `dict.schema` | `3` | the only accepted `schema` value |
| `dict.roles` | `{name: parent or null}` | role definitions |
| `dict.rule_fields` | `effect, role, actions, resource, when` | keys of one rule |
| `dict.required` | `effect, role, actions, resource` | keys a rule must have |
| `file.json_suffix` | `.json` | files with this suffix are read as data, others as text |

## Decisions

| key | value | meaning |
| --- | --- | --- |
| `decision.fields` | `request, allowed, reason, rule, near_misses, roles` | attributes of a decision |
| `reason.allow` | `allowed by rule {number}` | reason when an allow rule decided |
| `reason.deny` | `denied by rule {number}` | reason when a deny rule decided |
| `reason.default` | `no rule matched; default is {effect}` | reason when no rule matched |
| `rule.numbering` | `1-based, in policy order` | how rules are numbered |
| `near_misses` | `rules whose condition did not hold` | everything else about them matched |

## Explanations

| key | value | meaning |
| --- | --- | --- |
| `explain.header` | `{verdict} {user} {action} {resource}: {reason}` | first line |
| `explain.verdicts` | `ALLOW, DENY` | verdict words |
| `explain.rule` | `  rule {number} (line {line}): {rule}` | the deciding rule, as written |
| `explain.skipped` | `  rule {number} not applied: {clauses}` | one line per near miss, unmet clauses joined by `and` |

## Audit log

| key | value | meaning |
| --- | --- | --- |
| `log.format` | `JSON lines, keys sorted` | one record per decision |
| `log.mode` | `append` | writing never truncates the log |
| `log.fields` | `action, allowed, reason, resource, rule, user` | keys of each record |
| `log.rule` | `rule number or null` | the deciding rule |

## Report

| key | value | meaning |
| --- | --- | --- |
| `report.header` | `{total} decisions: {allowed} allowed, {denied} denied` | first line |
| `report.user_line` | `{user}  {allowed} allowed  {denied} denied` | one line per user, sorted by name |
| `report.top` | `5` | resources listed under `most denied` |
| `report.order` | `count, then first seen` | order of `most denied` |

## Lint

| key | value | meaning |
| --- | --- | --- |
| `lint.unused-role` | `role {role} is never used` | no rule names it and no role inherits it |
| `lint.redundant-role` | `role {role} adds nothing to {parent}` | no rule names it |
| `lint.shadowed-rule` | `rule {number} can never apply: rule {other} denies it` | an unconditional deny covers the allow |
| `lint.duplicate-rule` | `rule {number} repeats rule {other}` | same effect, roles, actions, pattern, condition |

## Command line

| key | value | meaning |
| --- | --- | --- |
| `cli.check_exit` | `0 allowed, 1 denied, 2 error` | exit status of `warden check` |
| `cli.lint_exit` | `0 clean, 1 findings, 2 error` | exit status of `warden lint` |

## Errors

| key | value | meaning |
| --- | --- | --- |
| `error.line` | `line {line}: {message}` | prefix for errors in policy text |
| `error.dict_rule` | `rule {number}: {message}` | prefix for errors in a data rule |
| `error.unknown_role` | `unknown role: {name}` | |
| `error.duplicate_role` | `role {name} is defined twice` | |
| `error.bad_role_name` | `bad role name: {name}` | |
| `error.role_cycle` | `role cycle: {a} -> {b} -> {a}` | |
| `error.inheritance_chain` | `inheritance chain of {name} is longer than 8 roles` | |
| `error.unknown_action` | `unknown action: {action}` | |
| `error.unknown_effect` | `unknown effect: {effect}` | |
| `error.bad_pattern` | `bad pattern: {pattern}` | |
| `error.rule_shape` | `expected: {rule syntax}` | |
| `error.role_shape` | `expected: {role syntax}` | |
| `error.bad_condition` | `bad condition: {condition}` | |
| `error.bad_operand` | `bad operand: {operand}` | |
| `error.namespace` | `unknown attribute namespace: {namespace}` | |
| `error.missing_field` | `missing field: {field}` | |
| `error.schema` | `unsupported schema: {schema}` | |
