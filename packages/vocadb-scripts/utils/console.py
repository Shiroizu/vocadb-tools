def get_parameter(
    prompt_message: str, script_params: list[str] | None = None, integer=False
) -> str:
    """Return parameter given from the command line or through prompting."""
    arg = ""
    if script_params and len(script_params) > 1:
        arg = script_params[1]

    if integer:
        while not arg.isnumeric():
            arg = input(prompt_message)
        return arg

    while not arg:
        arg = input(prompt_message)

    return arg
