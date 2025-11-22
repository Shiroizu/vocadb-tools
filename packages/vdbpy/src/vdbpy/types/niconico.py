from dataclasses import dataclass
from datetime import datetime


@dataclass
class NicoVideo:
    id: str
    title: str
    publish_date: datetime
    view_count: int
    like_count: int
    mylist_count: int
