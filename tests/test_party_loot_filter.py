from __future__ import annotations

from albion_dps.domain.party_registry import PartyRegistry


def test_party_registry_allows_player_name_for_party_members_and_confirmed_self() -> None:
    party = PartyRegistry()
    party.seed_names(["Alice", "Bob"])
    party.set_self_name("SelfGuy", confirmed=True)

    assert party.allows_player_name("Alice")
    assert party.allows_player_name("Bob")
    assert party.allows_player_name("SelfGuy")
    assert not party.allows_player_name("EnemyGuy")
    assert not party.allows_player_name("@MOB_KEEPER")
