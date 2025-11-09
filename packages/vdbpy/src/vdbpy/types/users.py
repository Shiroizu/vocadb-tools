from typing import Any, Literal

type UserId = int
type UserGroup = Literal[
    "Admin", "Moderator", "Trusted", "Regular", "Limited", "Nothing"
]
# Disabled User: active = false


type User = dict[Any, Any]  # TODO implement
