#!/usr/bin/env python3
"""Fail fast when a research script is run on an interpreter it does not support.

The research scripts use ``zip(..., strict=True)``, which needs Python 3.10.  On 3.9
the call raises ``TypeError: zip() takes no keyword arguments`` part way through a run,
after the script has already read its inputs, which reads as a data problem rather than
an environment one.  Calling :func:`require_supported_interpreter` from a script's ``__main__`` block turns
that into an immediate, named failure.  The check deliberately does **not** run at import
time: the functions in these modules are imported by tests that run on 3.9, and importing
them is not what breaks.

This is deliberately narrower than the public sample path.  ``classify_sns_rule_based``,
the sample check and the unit tests run on 3.9, which is what CI exercises; the research
reproduction scripts do not.  See "Execution environments" in the README.
"""

from __future__ import annotations

import sys

MINIMUM = (3, 10)
VERIFIED = ("3.13.9",)
REASON = "zip(..., strict=True), added in Python 3.10"


def require_supported_interpreter() -> None:
    if sys.version_info >= MINIMUM:
        return
    running = ".".join(str(part) for part in sys.version_info[:3])
    minimum = ".".join(str(part) for part in MINIMUM)
    raise SystemExit(
        f"This research script needs Python {minimum} or newer; this interpreter is "
        f"{running} ({sys.executable}).\n"
        f"Reason: {REASON}.\n"
        f"Verified on: {', '.join(VERIFIED)}.\n"
        "The public sample path -- classify_sns_rule_based.py, "
        "sample_data/check_sample_output.py and the unit tests -- does run on 3.9, so a "
        "working sample run does not mean this script will work on the same interpreter."
    )
