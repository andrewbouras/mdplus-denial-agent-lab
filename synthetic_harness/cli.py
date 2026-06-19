"""Command-line interface for the synthetic simulation harness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .authoring import (
    DEFAULT_PLATFORM_ROOT,
    PolicyIndex,
    author_case,
    load_json,
    unseal_ground_truth,
)
from .arms import prepare_arm, prepare_both_arms
from .episode import Episode
from .patient_actor import (
    create_follow_up,
    prepare_patient_actor,
    record_patient_response,
    relay_block,
)
from .results import ingest_arm_result


def print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def command_init(args: argparse.Namespace) -> None:
    episode = Episode.create(Path(args.episodes_root), label=args.label)
    print_json(
        {
            "episode_id": episode.episode_id,
            "case_id": episode.case_id,
            "episode_path": str(episode.root),
            "patient_workspace": str(episode.root / "patient_workspace"),
        }
    )


def command_log_event(args: argparse.Namespace) -> None:
    episode = Episode(Path(args.episode))
    details = json.loads(args.details) if args.details else {}
    print_json(
        episode.log_event(
            role=args.role,
            arm=args.arm,
            event_type=args.event_type,
            status=args.status,
            summary=args.summary,
            artifacts=args.artifact,
            parent_event_id=args.parent_event_id,
            details=details,
        )
    )


def command_message(args: argparse.Namespace) -> None:
    episode = Episode(Path(args.episode))
    body = Path(args.body_file).read_text(encoding="utf-8") if args.body_file else args.body
    print_json(
        episode.create_message(
            sender=args.sender,
            recipient=args.recipient,
            body=body,
            message_type=args.message_type,
            in_reply_to=args.in_reply_to,
        )
    )


def command_verify(args: argparse.Namespace) -> None:
    result = Episode(Path(args.episode)).verify()
    print_json(result)
    if not result["valid"]:
        raise SystemExit(1)


def command_candidates(args: argparse.Namespace) -> None:
    index = PolicyIndex(Path(args.platform_root))
    print_json(index.candidates(high_confidence_only=not args.include_medium))


def command_author_case(args: argparse.Namespace) -> None:
    episode = Episode(Path(args.episode))
    print_json(
        author_case(
            episode=episode,
            criteria_id=args.criteria_id,
            truth_input=load_json(Path(args.truth)),
            patient_packet=load_json(Path(args.patient_packet)),
            platform_root=Path(args.platform_root),
            controller_keys_root=Path(args.controller_keys_root),
        )
    )


def command_unseal(args: argparse.Namespace) -> None:
    episode = Episode(Path(args.episode))
    print_json(unseal_ground_truth(episode, Path(args.key)))


def command_prepare_patient(args: argparse.Namespace) -> None:
    print_json(prepare_patient_actor(Episode(Path(args.episode))))


def command_record_patient(args: argparse.Namespace) -> None:
    text = Path(args.response_file).read_text(encoding="utf-8")
    print_json(record_patient_response(Episode(Path(args.episode)), text))


def command_follow_up(args: argparse.Namespace) -> None:
    body = Path(args.body_file).read_text(encoding="utf-8") if args.body_file else args.body
    envelope = create_follow_up(Episode(Path(args.episode)), body)
    print(relay_block(envelope))


def command_prepare_arms(args: argparse.Namespace) -> None:
    episode = Episode(Path(args.episode))
    if args.arm == "both":
        print_json(prepare_both_arms(episode, Path.cwd()))
    else:
        print_json(prepare_arm(episode, args.arm, Path.cwd()))


def command_ingest_result(args: argparse.Namespace) -> None:
    print_json(ingest_arm_result(Episode(Path(args.episode)), args.arm))


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Create a new isolated episode")
    init.add_argument("--episodes-root", default="outputs/synthetic_patient_simulations/episodes")
    init.add_argument("--label", default="")
    init.set_defaults(func=command_init)

    event = subparsers.add_parser("log-event", help="Append a system event")
    event.add_argument("--episode", required=True)
    event.add_argument("--role", required=True)
    event.add_argument("--arm", required=True)
    event.add_argument("--event-type", required=True)
    event.add_argument("--status", required=True)
    event.add_argument("--summary", required=True)
    event.add_argument("--artifact", action="append", default=[])
    event.add_argument("--parent-event-id")
    event.add_argument("--details", help="JSON object")
    event.set_defaults(func=command_log_event)

    message = subparsers.add_parser("message", help="Create and log a relay message")
    message.add_argument("--episode", required=True)
    message.add_argument("--sender", required=True)
    message.add_argument("--recipient", required=True)
    body_group = message.add_mutually_exclusive_group(required=True)
    body_group.add_argument("--body")
    body_group.add_argument("--body-file")
    message.add_argument("--message-type", default="conversation")
    message.add_argument("--in-reply-to")
    message.set_defaults(func=command_message)

    verify = subparsers.add_parser("verify", help="Verify message envelopes and hash chains")
    verify.add_argument("--episode", required=True)
    verify.set_defaults(func=command_verify)

    candidates = subparsers.add_parser(
        "list-candidates", help="List policy-backed fixture candidates"
    )
    candidates.add_argument("--platform-root", default=str(DEFAULT_PLATFORM_ROOT))
    candidates.add_argument("--include-medium", action="store_true")
    candidates.set_defaults(func=command_candidates)

    author = subparsers.add_parser(
        "author-case", help="Validate a patient packet and seal policy-anchored truth"
    )
    author.add_argument("--episode", required=True)
    author.add_argument("--criteria-id", required=True)
    author.add_argument("--truth", required=True)
    author.add_argument("--patient-packet", required=True)
    author.add_argument("--platform-root", default=str(DEFAULT_PLATFORM_ROOT))
    author.add_argument(
        "--controller-keys-root",
        default="outputs/synthetic_patient_simulations/controller_keys",
    )
    author.set_defaults(func=command_author_case)

    unseal = subparsers.add_parser(
        "unseal", help="Decrypt ground truth after both arms are frozen"
    )
    unseal.add_argument("--episode", required=True)
    unseal.add_argument("--key", required=True)
    unseal.set_defaults(func=command_unseal)

    prepare_patient = subparsers.add_parser(
        "prepare-patient", help="Create Claude role prompt and initial intake message"
    )
    prepare_patient.add_argument("--episode", required=True)
    prepare_patient.set_defaults(func=command_prepare_patient)

    record_patient = subparsers.add_parser(
        "record-patient-response", help="Validate and record a relayed Claude response"
    )
    record_patient.add_argument("--episode", required=True)
    record_patient.add_argument("--response-file", required=True)
    record_patient.set_defaults(func=command_record_patient)

    follow_up = subparsers.add_parser(
        "follow-up", help="Create a logged patient follow-up and printable relay block"
    )
    follow_up.add_argument("--episode", required=True)
    body_group = follow_up.add_mutually_exclusive_group(required=True)
    body_group.add_argument("--body")
    body_group.add_argument("--body-file")
    follow_up.set_defaults(func=command_follow_up)

    prepare_arms = subparsers.add_parser(
        "prepare-arms", help="Create isolated library-only and/or web-only work orders"
    )
    prepare_arms.add_argument("--episode", required=True)
    prepare_arms.add_argument(
        "--arm",
        choices=["library_only", "web_only", "both"],
        default="both",
    )
    prepare_arms.set_defaults(func=command_prepare_arms)

    ingest_result = subparsers.add_parser(
        "ingest-arm-result", help="Validate, archive, and freeze an agent result"
    )
    ingest_result.add_argument("--episode", required=True)
    ingest_result.add_argument(
        "--arm", choices=["library_only", "web_only"], required=True
    )
    ingest_result.set_defaults(func=command_ingest_result)
    return root


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
