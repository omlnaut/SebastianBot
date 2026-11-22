from sebastian.domain.mietplan import is_path_prefix, join_path


def test_join_path_uses_a_slash_between_segments():
    assert join_path(["Nebenkostenabrechnung", "2024", "Rechnung.pdf"]) == (
        "Nebenkostenabrechnung/2024/Rechnung.pdf"
    )
    assert join_path(["Rechnung.pdf"]) == "Rechnung.pdf"
    assert join_path([]) == ""


def test_join_path_keeps_empty_segments():
    # The sync's path build strips leading/trailing separators itself; the
    # shared join must not silently change the segments it was given.
    assert join_path(["Miete", "", "Rechnung.pdf"]) == "Miete//Rechnung.pdf"


def test_a_prefix_matches_on_segment_boundaries_not_character_prefixes():
    assert is_path_prefix(["Archiv"], ["Archiv"])
    assert is_path_prefix(["Archiv", "2019"], ["Archiv"])
    assert not is_path_prefix(["Archiv2"], ["Archiv"])
    assert not is_path_prefix(["Archiv2", "2019"], ["Archiv"])
    assert not is_path_prefix(["Archiv"], ["Archiv", "2019"])


def test_an_empty_prefix_matches_every_path():
    assert is_path_prefix([], [])
    assert is_path_prefix(["Archiv"], [])
    assert is_path_prefix(["Archiv", "2019"], [])


def test_the_prefix_must_match_from_the_start_of_the_path():
    assert not is_path_prefix(["Konto", "Archiv"], ["Archiv"])
    assert is_path_prefix(["Archiv", "2019", "Konto"], ["Archiv", "2019"])
