def get_parameter(
    prompt_message: str, script_params: list[str] | None = None, integer=False, default=None
) -> str:
    """Return parameter given from the command line or through prompting."""
    arg = ""
    if script_params and len(script_params) > 1:
        arg = script_params[1]

    if not prompt_message.endswith(": "):
        prompt_message += ": "

    if default:
        prompt_message.replace(": ", f": (default={default})")

    if integer:
        while not arg.isnumeric():
            arg = input(prompt_message)
        return arg

    while not arg:
        arg = input(prompt_message)

    return arg
