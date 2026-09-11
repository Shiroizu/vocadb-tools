"""SQLAlchemy models mirroring the VocaDB dump tables."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


# -------- main tables -------- #


class Song(Base):
    __tablename__ = "songs"
    id: Mapped[int] = mapped_column(primary_key=True)
    song_type: Mapped[str]
    publish_date: Mapped[str | None]
    length_seconds: Mapped[int | None]
    original_id: Mapped[int | None]
    nico_id: Mapped[str | None]
    min_milli_bpm: Mapped[int | None]
    max_milli_bpm: Mapped[int | None]
    notes: Mapped[str | None]
    notes_eng: Mapped[str | None]
    name_en: Mapped[str | None]


class Album(Base):
    __tablename__ = "albums"
    id: Mapped[int] = mapped_column(primary_key=True)
    disc_type: Mapped[str]
    description: Mapped[str | None]
    description_eng: Mapped[str | None]
    cat_num: Mapped[str | None]
    release_year: Mapped[int | None]
    release_month: Mapped[int | None]
    release_day: Mapped[int | None]
    release_is_empty: Mapped[int | None]
    main_picture_mime: Mapped[str | None]
    name_en: Mapped[str | None]


class Artist(Base):
    __tablename__ = "artists"
    id: Mapped[int] = mapped_column(primary_key=True)
    artist_type: Mapped[str]
    base_voicebank_id: Mapped[int | None]
    release_date: Mapped[str | None]
    description: Mapped[str | None]
    description_eng: Mapped[str | None]
    main_picture_mime: Mapped[str | None]
    name_en: Mapped[str | None]


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str]
    date: Mapped[str | None]
    series_id: Mapped[int | None]
    series_number: Mapped[int | None]
    venue_id: Mapped[int | None]
    venue_name: Mapped[str | None]
    song_list_id: Mapped[int | None]
    description: Mapped[str | None]
    name: Mapped[str | None]
    main_picture_mime: Mapped[str | None]
    name_en: Mapped[str | None]


class EventSeries(Base):
    __tablename__ = "event_series"
    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str]
    description: Mapped[str | None]
    main_picture_mime: Mapped[str | None]
    name_en: Mapped[str | None]


class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(primary_key=True)
    category_name: Mapped[str]
    parent_id: Mapped[int | None]
    description: Mapped[str | None]
    description_eng: Mapped[str | None]
    hide_from_suggestions: Mapped[int]
    targets: Mapped[int | None]
    thumb_mime: Mapped[str | None]
    name_en: Mapped[str | None]


# -------- shared tables -------- #


class EntryName(Base):
    __tablename__ = "entry_names"
    pk: Mapped[int] = mapped_column(primary_key=True)
    entry_type: Mapped[str]
    entry_id: Mapped[int]
    language: Mapped[str]
    value: Mapped[str]


class EntryTranslatedName(Base):
    __tablename__ = "entry_translated_names"
    pk: Mapped[int] = mapped_column(primary_key=True)
    entry_type: Mapped[str]
    entry_id: Mapped[int]
    japanese: Mapped[str | None]
    romaji: Mapped[str | None]
    english: Mapped[str | None]
    default_name: Mapped[str | None]
    default_language: Mapped[str | None]


class EntryCultureCode(Base):
    __tablename__ = "entry_culture_codes"
    pk: Mapped[int] = mapped_column(primary_key=True)
    entry_type: Mapped[str]
    entry_id: Mapped[int]
    code: Mapped[str]


class EntryTag(Base):
    __tablename__ = "entry_tags"
    pk: Mapped[int] = mapped_column(primary_key=True)
    entry_type: Mapped[str]
    entry_id: Mapped[int]
    tag_id: Mapped[int]
    count: Mapped[int]
    tag_name_hint: Mapped[str | None]


class EntryWebLink(Base):
    __tablename__ = "entry_web_links"
    pk: Mapped[int] = mapped_column(primary_key=True)
    entry_type: Mapped[str]
    entry_id: Mapped[int]
    category: Mapped[str]
    description: Mapped[str]
    url: Mapped[str]
    disabled: Mapped[int]


# -------- per-entity helper tables -------- #


class SongArtist(Base):
    __tablename__ = "song_artists"
    pk: Mapped[int] = mapped_column(primary_key=True)
    song_id: Mapped[int]
    artist_id: Mapped[int]
    roles: Mapped[int]
    is_support: Mapped[int]
    name_hint: Mapped[str | None]


class SongPV(Base):
    __tablename__ = "song_pvs"
    pk: Mapped[int] = mapped_column(primary_key=True)
    song_id: Mapped[int]
    service: Mapped[str]
    pv_type: Mapped[str]
    pv_id: Mapped[str]
    name: Mapped[str | None]
    author: Mapped[str | None]
    description: Mapped[str | None]
    length: Mapped[int | None]
    publish_date: Mapped[str | None]
    thumb_url: Mapped[str | None]
    disabled: Mapped[int]
    extended_metadata_json: Mapped[str | None]


class SongEvent(Base):
    __tablename__ = "song_events"
    pk: Mapped[int] = mapped_column(primary_key=True)
    song_id: Mapped[int]
    event_id: Mapped[int]
    name_hint: Mapped[str | None]


class SongAlbum(Base):
    __tablename__ = "song_albums"
    pk: Mapped[int] = mapped_column(primary_key=True)
    song_id: Mapped[int]
    album_id: Mapped[int]
    disc_number: Mapped[int | None]
    track_number: Mapped[int | None]
    name_hint: Mapped[str | None]


class AlbumArtist(Base):
    __tablename__ = "album_artists"
    pk: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int]
    artist_id: Mapped[int]
    roles: Mapped[int]
    is_support: Mapped[int]
    name_hint: Mapped[str | None]


class AlbumSong(Base):
    __tablename__ = "album_songs"
    pk: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int]
    song_id: Mapped[int]
    disc_number: Mapped[int | None]
    track_number: Mapped[int | None]
    name_hint: Mapped[str | None]


class AlbumDisc(Base):
    __tablename__ = "album_discs"
    pk: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int]
    disc_number: Mapped[int | None]
    disc_id: Mapped[int | None]
    media_type: Mapped[str | None]
    name: Mapped[str | None]


class AlbumPV(Base):
    __tablename__ = "album_pvs"
    pk: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int]
    service: Mapped[str]
    pv_type: Mapped[str]
    pv_id: Mapped[str]
    name: Mapped[str | None]
    author: Mapped[str | None]
    description: Mapped[str | None]
    length: Mapped[int | None]
    publish_date: Mapped[str | None]
    thumb_url: Mapped[str | None]
    disabled: Mapped[int]
    extended_metadata_json: Mapped[str | None]


class AlbumIdentifier(Base):
    __tablename__ = "album_identifiers"
    pk: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int]
    value: Mapped[str]


class AlbumEvent(Base):
    __tablename__ = "album_events"
    pk: Mapped[int] = mapped_column(primary_key=True)
    album_id: Mapped[int]
    event_id: Mapped[int]
    name_hint: Mapped[str | None]


class ArtistGroup(Base):
    __tablename__ = "artist_groups"
    pk: Mapped[int] = mapped_column(primary_key=True)
    artist_id: Mapped[int]
    linked_artist_id: Mapped[int]
    link_type: Mapped[str]
    name_hint: Mapped[str | None]


class ArtistMember(Base):
    __tablename__ = "artist_members"
    pk: Mapped[int] = mapped_column(primary_key=True)
    artist_id: Mapped[int]
    member_artist_id: Mapped[int]
    name_hint: Mapped[str | None]


class EventArtist(Base):
    __tablename__ = "event_artists"
    pk: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int]
    artist_id: Mapped[int]
    roles: Mapped[int]
    is_support: Mapped[int]
    name_hint: Mapped[str | None]


class EventPV(Base):
    __tablename__ = "event_pvs"
    pk: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int]
    service: Mapped[str]
    pv_type: Mapped[str]
    pv_id: Mapped[str]
    name: Mapped[str | None]
    author: Mapped[str | None]
    description: Mapped[str | None]
    length: Mapped[int | None]
    publish_date: Mapped[str | None]
    thumb_url: Mapped[str | None]
    disabled: Mapped[int]
    extended_metadata_json: Mapped[str | None]


class TagRelatedTag(Base):
    __tablename__ = "tag_related_tags"
    pk: Mapped[int] = mapped_column(primary_key=True)
    tag_id: Mapped[int]
    related_tag_id: Mapped[int]
    name_hint: Mapped[str | None]


class TagNewTarget(Base):
    __tablename__ = "tag_new_targets"
    pk: Mapped[int] = mapped_column(primary_key=True)
    tag_id: Mapped[int]
    target: Mapped[str]


class Meta(Base):
    __tablename__ = "meta"
    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str]
