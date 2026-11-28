from vdbpy.types.albums import AlbumVersion
from vdbpy.types.artists import ArtistVersion
from vdbpy.types.events import ReleaseEventVersion
from vdbpy.types.series import ReleaseEventSeriesVersion
from vdbpy.types.songs import SongVersion
from vdbpy.types.tags import TagVersion
from vdbpy.types.venues import VenueVersion

type EntryVersion = (
    AlbumVersion
    | ArtistVersion
    | SongVersion
    | TagVersion
    | ReleaseEventVersion
    | ReleaseEventSeriesVersion
    | VenueVersion
)
