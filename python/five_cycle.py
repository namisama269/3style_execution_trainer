"""
Five-comm sequence generator for forced corner 5-cycles.

The workflow mirrors the comm drill generator but adds a structured setup:
1. Trim the corner scheme so only pieces after the buffer remain.
2. Randomly pick four distinct pieces (i, j, k, l).
3. Build three initial comms (ij, kl, and either jk or jl) using randomly
   selected sticker orientations for each referenced piece.
4. Apply those comms to the cube state (using tracer helpers). This should
   leave a 5-cycle involving the buffer; trace it to derive the final two
   comms needed to return to solved state.
"""

import random
import sys
from comm_drill_trainer import (
    CORNER_BUFFER,
    CORNER_LETTER_SCHEME,
    EDGE_BUFFER,
    EDGE_LETTER_SCHEME,
)


def _normalize_forced_pair(forced_pair):
    if forced_pair is None:
        return None
    if isinstance(forced_pair, str):
        pair = forced_pair.strip().upper()
        if len(pair) != 2:
            raise ValueError("Forced pair string must contain exactly two letters.")
        return pair[0], pair[1]
    if isinstance(forced_pair, (tuple, list)):
        if len(forced_pair) != 2:
            raise ValueError("Forced pair must contain exactly two letters.")
        first = str(forced_pair[0]).strip().upper()
        second = str(forced_pair[1]).strip().upper()
        if len(first) != 1 or len(second) != 1:
            raise ValueError("Forced pair entries must be single letters.")
        return first, second
    raise TypeError("Forced pair must be a 2-character string or a 2-item iterable.")

def _normalize_blocks(source):
    if source is None:
        source = CORNER_LETTER_SCHEME
    if isinstance(source, str):
        return [block for block in source.split(" ") if block]
    return list(source)

def _build_scheme_data(blocks):
    if not blocks:
        raise ValueError("Scheme must provide at least one block.")
    block_len = len(blocks[0])
    if block_len == 0:
        raise ValueError("Blocks cannot be empty.")
    letter_to_ref_pos = {}
    for pos, block in enumerate(blocks):
        if len(block) != block_len:
            raise ValueError("All blocks must have the same length.")
        for slot, ch in enumerate(block):
            if ch in letter_to_ref_pos:
                raise ValueError(f"Duplicate letter detected: {ch}")
            letter_to_ref_pos[ch] = (pos, slot)
    return {
        "blocks": blocks,
        "block_len": block_len,
        "letter_to_ref_pos": letter_to_ref_pos,
    }

def _solved_state(data):
    n = len(data["blocks"])
    return list(range(n)), [0] * n

def _letter_at_slot(data, pieces, oris, pos, slot):
    blocks = data["blocks"]
    M = data["block_len"]
    piece = pieces[pos]
    o = oris[pos] % M
    side_idx = (slot - o) % M
    return blocks[piece][side_idx]

def _find_current_slot(data, pieces, oris, letter):
    n = len(data["blocks"])
    M = data["block_len"]
    for pos in range(n):
        for slot in range(M):
            if _letter_at_slot(data, pieces, oris, pos, slot) == letter:
                return (pos, slot)
    raise ValueError(f"Letter {letter} not found in current state.")

def _swap_stickers(data, pieces, oris, A, B):
    M = data["block_len"]
    posA, slotA = _find_current_slot(data, pieces, oris, A)
    posB, slotB = _find_current_slot(data, pieces, oris, B)
    pieceA, oA = pieces[posA], oris[posA] % M
    pieceB, oB = pieces[posB], oris[posB] % M
    sideA = (slotA - oA) % M
    sideB = (slotB - oB) % M
    new_o_for_posA = (slotA - sideB) % M
    new_o_for_posB = (slotB - sideA) % M
    pieces[posA], oris[posA] = pieceB, new_o_for_posA
    pieces[posB], oris[posB] = pieceA, new_o_for_posB

def _three_cycle(data, pieces, oris, a, b, c):
    _swap_stickers(data, pieces, oris, b, c)
    _swap_stickers(data, pieces, oris, a, b)

def _letter_at_home(data, pieces, oris, letter):
    pos, slot = data["letter_to_ref_pos"][letter]
    return _letter_at_slot(data, pieces, oris, pos, slot)

def _trace_from_buffer(data, pieces, oris, buffer_letter, max_steps=200):
    cycle = [buffer_letter]
    cur = buffer_letter
    for _ in range(max_steps):
        nxt = _letter_at_home(data, pieces, oris, cur)
        cycle.append(nxt)
        if nxt == buffer_letter:
            break
        cur = nxt
    return cycle

def _pieces_after_buffer(blocks, buffer_letter):
    raw_blocks = list(blocks)
    buffer_index = next(
        (idx for idx, block in enumerate(raw_blocks) if buffer_letter in block),
        None,
    )
    if buffer_index is None:
        raise ValueError(f"Buffer letter {buffer_letter} was not found in scheme.")
    trimmed = raw_blocks[buffer_index + 1 :]
    if not trimmed:
        raise ValueError("No pieces remain after trimming with the buffer.")
    return trimmed


def _validate_forced_pair(blocks, buffer_letter, forced_pair):
    normalized = _normalize_forced_pair(forced_pair)
    if normalized is None:
        return None
    first, second = normalized
    if first == second:
        raise ValueError("Forced pair letters must be distinct.")
    letter_to_block_idx = {}
    for idx, block in enumerate(blocks):
        for letter in block:
            letter_to_block_idx[letter] = idx
    missing = [letter for letter in normalized if letter not in letter_to_block_idx]
    if missing:
        raise ValueError(f"Forced pair letters {missing} do not exist in the scheme.")
    buffer_idx = letter_to_block_idx.get(buffer_letter)
    if buffer_idx is None:
        raise ValueError(f"Buffer letter {buffer_letter} not found in scheme.")
    for letter in normalized:
        if letter_to_block_idx[letter] <= buffer_idx:
            raise ValueError(
                f"Letter {letter} must reference a piece after the buffer for forced pairs.",
            )
    if letter_to_block_idx[first] == letter_to_block_idx[second]:
        raise ValueError("Forced pair letters cannot belong to the same piece.")
    return normalized


def _random_letter(block, buffer_letter, rng):
    letters = [ch for ch in block if ch != buffer_letter]
    if not letters:
        raise ValueError(f"No usable stickers in block {block!r} after removing buffer.")
    return rng.choice(letters)


def _random_pair(block_a, block_b, buffer_letter, rng):
    return (
        _random_letter(block_a, buffer_letter, rng),
        _random_letter(block_b, buffer_letter, rng),
    )


def _apply_comm_sequence(data, comms, buffer_letter):
    pieces_state, oris_state = _solved_state(data)
    for first, second in comms:
        _three_cycle(data, pieces_state, oris_state, buffer_letter, first, second)
    return pieces_state, oris_state


def _is_buffer_five_cycle(trace, buffer_letter):
    if len(trace) != 6:
        return False
    if trace[0] != buffer_letter or trace[-1] != buffer_letter:
        return False
    unique = trace[:-1]
    return len(unique) == 5 and len(set(unique)) == 5


def basic_five_cycle(
    *,
    buffer_letter=CORNER_BUFFER,
    scheme=None,
    rng=None,
    max_attempts=1000,
    forced_pair=None,
):
    """
    Generate a 5-comm sequence following the specification in the user request.

    Parameters
    ----------
    buffer_letter : str
        Sticker used as the buffer during comm execution.
    scheme : str | Sequence[str] | None
        Either a space-delimited scheme string ("UVJ OIF ..."), a list/tuple of
        blocks like ``["UVJ", "OIF", ...]``, or ``None`` to use the default
        corner scheme.
    rng : random.Random | None
        Optional RNG instance for deterministic testing.
    max_attempts : int
        Number of retries allowed to find a valid 5-cycle setup.

    Returns
    -------
    dict
        ``{"selected_pieces": ..., "comm_sequence": ..., "trace": ...}``.

    Raises
    ------
    RuntimeError
        If the three seeded comms do not yield a buffer-centered 5-cycle.
    """
    rng = rng or random.Random()
    blocks = _normalize_blocks(scheme)
    scheme_data = _build_scheme_data(blocks)
    if buffer_letter not in scheme_data["letter_to_ref_pos"]:
        raise ValueError(f"Buffer letter {buffer_letter} not present in scheme.")
    normalized_pair = _validate_forced_pair(blocks, buffer_letter, forced_pair)
    letter_to_block_idx = {}
    for idx, block in enumerate(blocks):
        for letter in block:
            letter_to_block_idx[letter] = idx
    available_pieces = _pieces_after_buffer(blocks, buffer_letter)
    if len(available_pieces) < 4:
        raise ValueError("Need at least four pieces after the buffer trim.")

    last_failure = None
    attempts = max(1, int(max_attempts))

    for _ in range(attempts):
        selected_pieces = None
        orientation_map = {}

        def record_orientation(piece_a, piece_b, letters):
            orientation_map[piece_a] = letters[0]
            orientation_map[piece_b] = letters[1]
            return tuple(letters)

        if normalized_pair:
            forced_piece_blocks = []
            for letter in normalized_pair:
                block_idx = letter_to_block_idx[letter]
                forced_piece_blocks.append(blocks[block_idx])

            pool = [
                piece
                for piece in available_pieces
                if piece not in forced_piece_blocks
            ]
            if len(pool) < 2:
                last_failure = "Not enough additional pieces available for forced pair."
                continue
            extras = tuple(rng.sample(pool, 2))
            force_into_first = rng.random() < 0.5
            if force_into_first:
                piece_i, piece_j = forced_piece_blocks
                piece_k, piece_l = extras
                first_comm = record_orientation(piece_i, piece_j, normalized_pair)
                second_comm = record_orientation(
                    piece_k,
                    piece_l,
                    _random_pair(piece_k, piece_l, buffer_letter, rng),
                )
            else:
                piece_k, piece_l = forced_piece_blocks
                piece_i, piece_j = extras
                first_comm = record_orientation(
                    piece_i,
                    piece_j,
                    _random_pair(piece_i, piece_j, buffer_letter, rng),
                )
                second_comm = record_orientation(piece_k, piece_l, normalized_pair)
            selected_pieces = tuple(forced_piece_blocks + list(extras))
        else:
            selected = tuple(rng.sample(available_pieces, 4))
            piece_i, piece_j, piece_k, piece_l = selected
            first_comm = record_orientation(
                piece_i,
                piece_j,
                _random_pair(piece_i, piece_j, buffer_letter, rng),
            )
            second_comm = record_orientation(
                piece_k,
                piece_l,
                _random_pair(piece_k, piece_l, buffer_letter, rng),
            )
            selected_pieces = selected

        jk_or_jl = rng.choice(
            (
                (piece_j, piece_k),
                (piece_j, piece_l),
            ),
        )
        third_piece_a, third_piece_b = jk_or_jl
        if randomize_third_orientation:
            third_comm = _random_pair(third_piece_a, third_piece_b, buffer_letter, rng)
        else:
            letter_a = orientation_map.get(third_piece_a)
            letter_b = orientation_map.get(third_piece_b)
            if letter_a is not None and letter_b is not None:
                third_comm = (letter_a, letter_b)
            else:
                third_comm = _random_pair(third_piece_a, third_piece_b, buffer_letter, rng)
        orientation_map[third_piece_a] = third_comm[0]
        orientation_map[third_piece_b] = third_comm[1]

        initial_comms = [first_comm, second_comm, third_comm]

        pieces_state, oris_state = _apply_comm_sequence(scheme_data, initial_comms, buffer_letter)
        trace = _trace_from_buffer(scheme_data, pieces_state, oris_state, buffer_letter)

        if not _is_buffer_five_cycle(trace, buffer_letter):
            last_failure = (
                f"pieces={selected_pieces}, comms={initial_comms}, trace={trace}"
            )
            continue

        cleanup_pairs = [
            (trace[4], trace[3]),
            (trace[2], trace[1]),
        ]

        full_sequence = tuple(initial_comms + cleanup_pairs)
        return {
            "selected_pieces": selected_pieces,
            "comm_sequence": full_sequence,
            "trace": tuple(trace),
        }

    debug_message = "Failed to leave a 5-cycle. " + (last_failure or "No attempts run.")
    print(debug_message, file=sys.stderr)
    raise RuntimeError(debug_message)


def random_shift_comms(comm_sequence, rng=None):
    """
    Return a randomly rotated version of the provided comm sequence.
    Shifting preserves the property that executing all comms returns to solved.
    """
    if not comm_sequence:
        return tuple()
    rng = rng or random.Random()
    seq = list(comm_sequence)
    offset = rng.randrange(len(seq))
    if offset == 0:
        return tuple(seq)
    return tuple(seq[offset:] + seq[:offset])


# Provide an alias that can be accessed via getattr(module, "5cycle")
globals()["5cycle"] = basic_five_cycle


def generate_five_cycle(**kwargs):
    """
    Convenience wrapper: run five_cycle and apply a random rotation to comms.
    """
    result = basic_five_cycle(**kwargs)
    rotated = random_shift_comms(result["comm_sequence"])
    result = dict(result)
    result["comm_sequence"] = rotated
    return result


if __name__ == "__main__":
    print("=== Corner 5-cycle example ===")
    corner_result = basic_five_cycle()
    print("Pieces:", corner_result["selected_pieces"])
    print("Comms (pairs):")
    for first, second in corner_result["comm_sequence"]:
        print(f"{first}{second}")
    print("Trace:", " -> ".join(corner_result["trace"]))

    print("\nRandom shift of generated comms:")
    for first, second in random_shift_comms(corner_result["comm_sequence"]):
        print(f"{first}{second}")

    print("\n=== Edge 5-cycle example ===")
    edge_result = basic_five_cycle(
        buffer_letter=EDGE_BUFFER,
        scheme=EDGE_LETTER_SCHEME,
    )
    print("Pieces:", edge_result["selected_pieces"])
    print("Comms (pairs):")
    for first, second in edge_result["comm_sequence"]:
        print(f"{first}{second}")
    print("Trace:", " -> ".join(edge_result["trace"]))
