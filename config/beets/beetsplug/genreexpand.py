"""Expand genre tags to include their full hierarchy from a YAML genre tree.

After lastgenre writes a genre (e.g. "Plugg"), this plugin walks up the
tree defined in genres.yaml and rewrites the tag with all ancestors included
(e.g. "Hip-Hop, Trap, Plugg"). It also normalises common Last.fm tag
variants via the aliases section of that file.

Flex attributes written to each item/album:
  genre_pre_expand  — genre string as returned by lastgenre, before expansion
  genre_warnings    — comma-separated list of genres not found in genres.yaml
"""

import yaml
from beets.plugins import BeetsPlugin


class GenreExpandPlugin(BeetsPlugin):
    def __init__(self):
        super().__init__()
        self.config.add({
            "genres_file": "genres.yaml",
            "separator": ", ",
        })
        self._loaded = False
        self._aliases = {}
        # Maps canonical_name.lower() -> (canonical_name, parent_canonical_name | None)
        self._parent_map = {}

        self.register_listener("album_imported", self.on_album_imported)
        self.register_listener("item_imported", self.on_item_imported)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _load(self):
        if self._loaded:
            return
        path = self.config["genres_file"].as_filename()
        with open(path) as f:
            data = yaml.safe_load(f)
        self._aliases = {
            k.lower(): v for k, v in data.get("aliases", {}).items()
        }
        self._build_parent_map(data.get("tree", {}), parent=None)
        self._loaded = True

    def _build_parent_map(self, subtree, parent):
        if not subtree:
            return
        for genre, children in subtree.items():
            self._parent_map[genre.lower()] = (genre, parent)
            if children:
                self._build_parent_map(children, parent=genre)

    # ------------------------------------------------------------------
    # Genre logic
    # ------------------------------------------------------------------

    def _normalize(self, raw):
        """Map a raw Last.fm tag to its canonical name."""
        lower = raw.strip().lower()
        if lower in self._aliases:
            return self._aliases[lower]
        if lower in self._parent_map:
            return self._parent_map[lower][0]
        return raw.strip()

    def _is_known(self, genre):
        return genre.lower() in self._parent_map

    def _ancestors(self, genre):
        """Return [root, ..., parent, genre] for a known genre, else [genre]."""
        lower = genre.lower()
        if lower not in self._parent_map:
            return [genre]
        chain = []
        while lower in self._parent_map:
            canonical, parent = self._parent_map[lower]
            chain.append(canonical)
            if parent is None:
                break
            lower = parent.lower()
        return list(reversed(chain))

    def _expand(self, genre_str, context):
        """Normalise and expand a comma-separated genre string.

        Returns (expanded_str, unknown_genres) where unknown_genres is a list
        of genre names that were not found in genres.yaml.
        """
        self._load()
        separator = self.config["separator"].get(str)
        seen = set()
        result = []
        unknown = []
        for raw in genre_str.split(","):
            canonical = self._normalize(raw)
            if not self._is_known(canonical):
                self._log.warning(
                    "Unknown genre {!r} on {} — add it to genres.yaml and "
                    "re-import to get hierarchy expansion",
                    canonical, context,
                )
                unknown.append(canonical)
            for g in self._ancestors(canonical):
                if g.lower() not in seen:
                    seen.add(g.lower())
                    result.append(g)
        expanded = separator.join(result) if result else genre_str
        return expanded, unknown

    def _apply(self, obj, context):
        """Expand genre on a beets Item or Album, storing flex attributes."""
        if not obj.genre:
            self._log.warning("No genre found for {}", context)
            return
        pre_expand = obj.genre
        obj.genre, unknown = self._expand(obj.genre, context)
        obj.genre_pre_expand = pre_expand
        obj.genre_warnings = ", ".join(unknown) if unknown else ""
        obj.store()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_album_imported(self, lib, album):
        context = "{} - {}".format(album.albumartist, album.album)
        self._apply(album, context)
        # Propagate flex attributes to individual tracks (genre itself is
        # inherited by beets via album.store(), but flex attrs are not)
        for item in album.items():
            item.genre_pre_expand = album.genre_pre_expand
            item.genre_warnings = album.genre_warnings
            item.store()

    def on_item_imported(self, lib, item):
        context = "{} - {}".format(item.artist, item.title)
        self._apply(item, context)
