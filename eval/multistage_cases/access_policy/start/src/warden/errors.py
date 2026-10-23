class PolicyError(Exception):
    """Anything wrong with a policy or a request made against one."""


class PolicySyntaxError(PolicyError):
    def __init__(self, line, message):
        super().__init__(f"line {line}: {message}")
        self.line = line
        self.message = message


class RoleError(PolicyError):
    pass


class ConditionError(PolicyError):
    pass
