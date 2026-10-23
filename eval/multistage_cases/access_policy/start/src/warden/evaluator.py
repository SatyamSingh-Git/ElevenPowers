"""Deciding requests against a policy: a matching deny beats any matching allow."""
from .actions import ANY_ACTION, canonical_action
from .model import Decision, Request
from .patterns import normalize

REASON_ALLOW = "allowed by rule {number}"
REASON_DENY = "denied by rule {number}"
REASON_DEFAULT = "no rule matched; default is {effect}"


class Evaluator:
    def __init__(self, policy):
        self.policy = policy

    def decide(self, request):
        held = self.policy.roles.expand(request.user.roles)
        action = canonical_action(request.action)
        resource = normalize(request.resource)
        allow = deny = None
        skipped = []
        for rule in self.policy.rules:
            if not (rule.role in held
                    and (ANY_ACTION in rule.actions or action in rule.actions)
                    and rule.pattern.matches(resource)):
                continue
            if rule.condition and not rule.condition.evaluate(request.user.attrs, request.resource_attrs):
                skipped.append(rule)
            elif rule.effect == "deny":
                deny = deny or rule
            else:
                allow = allow or rule
        if deny:
            return Decision(request, False, REASON_DENY.format(number=deny.number), deny, tuple(skipped), held)
        if allow:
            return Decision(request, True, REASON_ALLOW.format(number=allow.number), allow, tuple(skipped), held)
        default = self.policy.default
        return Decision(request, default == "allow", REASON_DEFAULT.format(effect=default), None,
                        tuple(skipped), held)

    def allows(self, user, action, resource, **resource_attrs):
        return self.decide(Request(user, action, resource, resource_attrs)).allowed
