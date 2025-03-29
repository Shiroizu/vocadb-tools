def split_list(lst, max_length=50):
    return [lst[i : i + max_length] for i in range(0, len(lst), max_length)]


def truncate_string_with_ellipsis(s, max_length, ending="..."):
    if len(s) > max_length:
        return s[:max_length] + ending

    return s
