#!/usr/bin/env python3

"""
Redactor

Replace configured text and regex patterns in a text file.

Usage:
    python redactor.py input.txt replacements.json output.txt

Example config:

{
    "literal": {
        "dundermifflin.com": "corpo.com",
        "Dunder Mifflin": "Corpo"
    },
    "regex": [
        {
            "match": "\\bDunder\\s+Mifflin\\b",
            "replace": "Corpo",
            "ignore_case": true
        },
        {
            "match": "\\b([A-Za-z0-9._%+-]+)@dundermifflin\\.com\\b",
            "replace": "\\1@corpo.com",
            "ignore_case": true
        }
    ]
}
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def load_config(config_path: Path) -> dict[str, Any]:
    """Load and validate the JSON configuration file."""

    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)

    except FileNotFoundError:
        raise ValueError(f"Config file not found: {config_path}")

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in config file {config_path}: {exc}"
        ) from exc

    if not isinstance(config, dict):
        raise ValueError("Config must contain a JSON object.")

    literal = config.get("literal", {})
    regex_rules = config.get("regex", [])

    if not isinstance(literal, dict):
        raise ValueError('"literal" must be a JSON object.')

    for match, replacement in literal.items():
        if not isinstance(match, str) or not isinstance(replacement, str):
            raise ValueError(
                'Every "literal" match and replacement must be a string.'
            )

    if not isinstance(regex_rules, list):
        raise ValueError('"regex" must be a JSON array.')

    for i, rule in enumerate(regex_rules, start=1):

        if not isinstance(rule, dict):
            raise ValueError(f"Regex rule #{i} must be an object.")

        if "match" not in rule:
            raise ValueError(f'Regex rule #{i} is missing "match".')

        if "replace" not in rule:
            raise ValueError(f'Regex rule #{i} is missing "replace".')

        if not isinstance(rule["match"], str):
            raise ValueError(
                f'"match" in regex rule #{i} must be a string.'
            )

        if not isinstance(rule["replace"], str):
            raise ValueError(
                f'"replace" in regex rule #{i} must be a string.'
            )

        if "ignore_case" in rule and not isinstance(
            rule["ignore_case"], bool
        ):
            raise ValueError(
                f'"ignore_case" in regex rule #{i} must be true or false.'
            )

        if "multiline" in rule and not isinstance(
            rule["multiline"], bool
        ):
            raise ValueError(
                f'"multiline" in regex rule #{i} must be true or false.'
            )

        if "dotall" in rule and not isinstance(
            rule["dotall"], bool
        ):
            raise ValueError(
                f'"dotall" in regex rule #{i} must be true or false.'
            )

        # Compile it now so bad patterns fail before processing the file.
        try:
            flags = build_regex_flags(rule)
            re.compile(rule["match"], flags)
        except re.error as exc:
            raise ValueError(
                f"Invalid regex in rule #{i}: {exc}"
            ) from exc

    return config


def build_regex_flags(rule: dict[str, Any]) -> int:
    """Build Python regex flags from a rule."""

    flags = 0

    if rule.get("ignore_case", False):
        flags |= re.IGNORECASE

    if rule.get("multiline", False):
        flags |= re.MULTILINE

    if rule.get("dotall", False):
        flags |= re.DOTALL

    return flags


def apply_literal_replacements(
    text: str,
    replacements: dict[str, str],
) -> tuple[str, list[dict[str, Any]]]:

    stats = []

    for match, replacement in replacements.items():

        count = text.count(match)

        if count:
            text = text.replace(match, replacement)

        stats.append(
            {
                "type": "literal",
                "match": match,
                "replacement": replacement,
                "count": count,
            }
        )

    return text, stats


def apply_regex_replacements(
    text: str,
    rules: list[dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:

    stats = []

    for rule in rules:

        pattern = rule["match"]
        replacement = rule["replace"]
        flags = build_regex_flags(rule)

        regex = re.compile(pattern, flags)

        text, count = regex.subn(replacement, text)

        stats.append(
            {
                "type": "regex",
                "match": pattern,
                "replacement": replacement,
                "count": count,
            }
        )

    return text, stats


def redact_text(
    text: str,
    config: dict[str, Any],
) -> tuple[str, list[dict[str, Any]]]:

    stats = []

    literal = config.get("literal", {})
    regex_rules = config.get("regex", [])

    # Exact string replacements happen first.
    text, literal_stats = apply_literal_replacements(
        text,
        literal,
    )

    stats.extend(literal_stats)

    # Regex rules happen afterwards, in config order.
    text, regex_stats = apply_regex_replacements(
        text,
        regex_rules,
    )

    stats.extend(regex_stats)

    return text, stats


def print_stats(stats: list[dict[str, Any]]) -> None:
    """Print replacement statistics."""

    total = sum(item["count"] for item in stats)

    for item in stats:

        rule_type = item["type"].upper()

        print(
            f'{item["count"]:5}  '
            f'[{rule_type:7}] '
            f'"{item["match"]}" '
            f'-> "{item["replacement"]}"'
        )

    print()
    print(f"Total replacements: {total}")


def main() -> int:

    parser = argparse.ArgumentParser(
        prog="redactor",
        description=(
            "Replace literal strings and regex patterns "
            "in a text file using a JSON configuration."
        ),
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input text file",
    )

    parser.add_argument(
        "config",
        type=Path,
        help="JSON replacement configuration",
    )

    parser.add_argument(
        "output",
        type=Path,
        help="Output text file",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Do not print replacement statistics",
    )

    args = parser.parse_args()

    try:

        config = load_config(args.config)

        try:
            text = args.input.read_text(encoding="utf-8")

        except FileNotFoundError:
            raise ValueError(
                f"Input file not found: {args.input}"
            )

        redacted_text, stats = redact_text(
            text,
            config,
        )

        args.output.write_text(
            redacted_text,
            encoding="utf-8",
        )

        if not args.quiet:

            print(f"Input:  {args.input}")
            print(f"Config: {args.config}")
            print(f"Output: {args.output}")
            print()

            print_stats(stats)

        return 0

    except (ValueError, OSError) as exc:

        print(
            f"redactor: error: {exc}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    sys.exit(main())
