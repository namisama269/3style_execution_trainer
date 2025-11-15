from __future__ import annotations

import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SRC = PROJECT_ROOT / "python"
TESTS_DIR = PROJECT_ROOT / "tests"
for path in (PYTHON_SRC, PROJECT_ROOT, TESTS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from comm_drill_trainer import (
    CORNER_BUFFER,
    CORNER_LETTER_SCHEME,
    EDGE_BUFFER,
    EDGE_LETTER_SCHEME,
)  # noqa: E402
from dlin import Tracer, BUFFERS  # noqa: E402
from five_cycle import generate_five_cycle  # noqa: E402
from three_style_algorithms import CORNER_THREE_STYLE, EDGE_THREE_STYLE  # noqa: E402


def _comm_sequence_contains_pair(sequence, pair):
    return any(first == pair[0] and second == pair[1] for first, second in sequence)


def _assert_no_repeats_or_inverses(sequence):
    seen = set()
    for first, second in sequence:
        pair = (first, second)
        inverse = (second, first)
        if pair in seen:
            raise AssertionError(f"Duplicate comm pair detected: {first}{second}")
        if inverse in seen:
            raise AssertionError(
                f"Inverse comm pair detected: {first}{second} vs {second}{first}",
            )
        seen.add(pair)


def trace_edges(scramble: str):
    tracer = Tracer(BUFFERS, trace="edge")
    tracer.scramble_from_string(scramble)
    tracer.trace_cube()
    # print(tracer.tracing)
    return tracer.tracing["edge"]


def run_edge_tests(iterations=1000, rng=None):
    rng = rng or random.Random(42)
    for i in range(iterations):
        result = generate_five_cycle(
            buffer_letter=EDGE_BUFFER,
            scheme=EDGE_LETTER_SCHEME,
            rng=rng,
            max_attempts=5000,
        )
        comm_sequence = result["comm_sequence"]
        _assert_no_repeats_or_inverses(comm_sequence)
        algorithms = []
        for first, second in comm_sequence:
            key = f"{first}{second}"
            if key not in EDGE_THREE_STYLE:
                raise KeyError(f"Missing algorithm for letter pair {key}")
            algorithms.append(EDGE_THREE_STYLE[key])
        scramble = " ".join(algorithms)
        edge_trace = trace_edges(scramble)
        if edge_trace:
            print("Edge failed iteration:", i)
            print("Comms:", comm_sequence)
            print("Tracing:", edge_trace)
            raise AssertionError("Cube does not end in solved state")
    print(f"Passed {iterations} edge tests.")


def run_corner_tests(iterations=1000, rng=None):
    rng = rng or random.Random(42)
    for i in range(iterations):
        corner_result = generate_five_cycle(
            buffer_letter=CORNER_BUFFER,
            scheme=CORNER_LETTER_SCHEME,
            rng=rng,
            max_attempts=5000,
        )
        corner_sequence = corner_result["comm_sequence"]
        _assert_no_repeats_or_inverses(corner_sequence)
        corner_algorithms = []
        for first, second in corner_sequence:
            key = f"{first}{second}"
            if key not in CORNER_THREE_STYLE:
                raise KeyError(f"Missing algorithm for letter pair {key}")
            corner_algorithms.append(CORNER_THREE_STYLE[key])
        corner_scramble = " ".join(corner_algorithms)
        tracer = Tracer(BUFFERS, trace="corner")
        tracer.scramble_from_string(corner_scramble)
        tracer.trace_cube()
        corner_trace = tracer.tracing["corner"]
        if corner_trace:
            print("Corner failed iteration:", i)
            print("Comms:", corner_sequence)
            print("Tracing:", corner_trace)
            raise AssertionError("Cube does not end in solved state")
    print(f"Passed {iterations} corner tests.")


def _random_forced_pair_from_scheme(rng, scheme, buffer_letter):
    blocks = [
        block for block in scheme.split(" ") if block and buffer_letter not in block
    ]
    if len(blocks) < 2:
        raise AssertionError("Not enough blocks after buffer to sample forced pairs.")
    piece_a, piece_b = rng.sample(blocks, 2)
    letter_a = rng.choice([ch for ch in piece_a if ch != buffer_letter])
    letter_b = rng.choice([ch for ch in piece_b if ch != buffer_letter])
    return (letter_a, letter_b)


def verify_forced_pair_integration(rng):
    forced_pair = _random_forced_pair_from_scheme(rng, CORNER_LETTER_SCHEME, CORNER_BUFFER)
    result = generate_five_cycle(
        buffer_letter=CORNER_BUFFER,
        scheme=CORNER_LETTER_SCHEME,
        forced_pair=forced_pair,
        max_attempts=5000,
    )
    assert _comm_sequence_contains_pair(result["comm_sequence"], forced_pair)
    _assert_no_repeats_or_inverses(result["comm_sequence"])


def verify_invalid_forced_pair_rejection():
    try:
        generate_five_cycle(
            buffer_letter=CORNER_BUFFER,
            scheme=CORNER_LETTER_SCHEME,
            forced_pair=("O", "I"),
        )
    except ValueError:
        return
    raise AssertionError("Expected ValueError for invalid forced pair.")


def main():
    rng = random.Random(42)
    run_edge_tests(rng=rng)
    run_corner_tests(rng=rng)
    verify_forced_pair_integration(rng)
    verify_invalid_forced_pair_rejection()


if __name__ == "__main__":
    main()
