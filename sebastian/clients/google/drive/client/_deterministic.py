"""The one deterministic ordering rule for same-named Drive objects.

Duplicate folder names under one parent, and duplicate file names in one
folder, already exist in the target Drive folder: older versions of the
mietplan sync always created a new file instead of replacing the old one, and
nothing has cleaned up the result (spec V4, decision D13 -- we never delete).

"The existing file" therefore needs a stable definition. The rule is:

    the candidate with the earliest ``createdTime`` wins; ties -- including
    objects that report no ``createdTime`` at all -- are broken by the
    lexicographically smallest ``id``.

Google returns ``createdTime`` as an RFC 3339 UTC timestamp, so comparing the
strings compares instants. The rule is applied with :func:`pick_oldest` for
both folders (when resolving a path) and files (when looking up the target of
a replace), which keeps the lookup and the upload path pointing at the same
object. The other duplicates are left in place.
"""

from typing import Any


def pick_oldest(items: list[dict[str, Any]]) -> str | None:
    """Return the id of the deterministic candidate among ``items``."""
    if not items:
        return None
    oldest = min(
        items,
        key=lambda item: (item.get("createdTime") or "", item.get("id") or ""),
    )
    return oldest.get("id")
