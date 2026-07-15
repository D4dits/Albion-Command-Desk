from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from albion_dps.capture.replay_pcap import replay_pcap
from albion_dps.protocol.photon_decode import PhotonDecoder
from albion_dps.protocol.protocol16 import Protocol16Error, decode_event_data

LOOT_SUBTYPE_KEY = 252
KNOWN_LOOT_SUBTYPES = {
    29: "EvNewCharacter",
    30: "EvNewEquipmentItem",
    31: "EvNewSiegeBannerItem",
    32: "EvNewSimpleItem",
    98: "EvNewLoot",
    99: "EvAttachItemContainer",
    100: "EvDetachItemContainer",
    143: "EvCharacterStats",
    275: "EvOtherGrabbedLoot (legacy)",
    279: "EvOtherGrabbedLoot",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Albion loot-related subtypes inside a pcap replay."
    )
    parser.add_argument("pcap", help="Path to .pcap file")
    parser.add_argument(
        "--show-samples",
        type=int,
        default=3,
        help="How many sample payload summaries to print per loot subtype",
    )
    args = parser.parse_args()

    pcap_path = Path(args.pcap)
    decoder = PhotonDecoder()
    subtype_counts: Counter[int] = Counter()
    sample_parameters: dict[int, list[str]] = {}
    total_packets = 0
    total_messages = 0
    total_protocol_events = 0

    for packet in replay_pcap(pcap_path):
        total_packets += 1
        for message in decoder.decode_all(packet):
            total_messages += 1
            if message.event_code != 1:
                continue
            try:
                event = decode_event_data(message.payload)
            except Protocol16Error:
                continue
            total_protocol_events += 1
            subtype = event.parameters.get(LOOT_SUBTYPE_KEY)
            if not isinstance(subtype, int):
                subtype = event.code
            if subtype not in KNOWN_LOOT_SUBTYPES:
                continue
            subtype_counts[subtype] += 1
            samples = sample_parameters.setdefault(subtype, [])
            if len(samples) < max(0, args.show_samples):
                keys = ",".join(str(key) for key in sorted(event.parameters))
                samples.append(
                    f"ts={packet.timestamp:.3f} code={event.code} keys=[{keys}] params={event.parameters}"
                )

    print(f"pcap: {pcap_path}")
    print(f"packets: {total_packets}")
    print(f"photon messages: {total_messages}")
    print(f"protocol16 events: {total_protocol_events}")
    print("loot subtype counts:")
    for subtype, count in sorted(subtype_counts.items()):
        label = KNOWN_LOOT_SUBTYPES.get(subtype, "unknown")
        print(f"  {subtype:>3} {label:<24} {count}")
        for sample in sample_parameters.get(subtype, []):
            print(f"    {sample}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
