import shlex


def parse_bool(val):
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    return str(val).strip().lower() in ("1", "true", "yes", "y", "on")


def join_cmd(cmd):
    try:
        return shlex.join(cmd)
    except AttributeError:
        return " ".join(shlex.quote(c) for c in cmd)


def get_env_vars(env_vars):
    if not env_vars:
        return []
    if isinstance(env_vars, list):
        return env_vars
    return shlex.split(str(env_vars))
