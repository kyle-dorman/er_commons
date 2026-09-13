"""Publish a Task 06G initial launch packet and dispatch detached tmux."""

from __future__ import annotations

import argparse
from pathlib import Path

from er_commons.task06g.launch import launch_initial


def main() -> None:
    """Seal all launch inputs before dispatching the exact recorded argv."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution-spec", type=Path, required=True)
    parser.add_argument("--replay-root", type=Path, required=True)
    parser.add_argument("--attempt-root", type=Path, required=True)
    parser.add_argument("--launch-record-root", type=Path, required=True)
    parser.add_argument("--prelaunch-recovery-receipt", type=Path)
    parser.add_argument("--reuse-launch-packet-exact", action="store_true")
    args = parser.parse_args()
    launch_initial(
        args.execution_spec,
        args.replay_root,
        args.attempt_root,
        args.launch_record_root,
        binding_path=args.prelaunch_recovery_receipt,
        reuse_exact=args.reuse_launch_packet_exact,
    )


if __name__ == "__main__":
    main()
