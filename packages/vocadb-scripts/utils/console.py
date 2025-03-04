def get_parameter(
    prompt_message: str,
    script_params: list[str] | None = None,
    integer=False,
    default="",
) -> str:
    """Return parameter given from the command line or through prompting."""
    arg = ""
    if script_params and len(script_params) > 1:
        arg = script_params[1]

    if not prompt_message.endswith(": "):
        prompt_message += ": "

    if default:
        prompt_message = prompt_message.replace(": ", f" (default={default}): ")

    if integer:
        while not arg.isnumeric():
            arg = input(prompt_message)
            if not arg.isnumeric() and default:
                print(f"Selecting '{default}'")
                return default
        return arg

    while not arg:
        arg = input(prompt_message)
        if not arg.strip() and default:
            print(f"Selecting '{default}'")
            return default

    return arg


def get_boolean(prompt: str) -> bool:
    while True:
        user_input = input(f"{prompt} (True/False): ").strip().lower()

        if user_input in ["true", "1", "t", "y", "yes"]:
            return True
        if user_input in ["false", "0", "f", "n", "no"]:
            return False

        print("Invalid input. Please enter a valid boolean value (True/False).")
