import random

WING_LETTER_SCHEME = "OABCDEFGHIJKLMNPRSTUVWYZ"
CENTER_LETTER_SCHEME = "AEOU ZFGH IJKL VNMP YRST BCDW"
EDGE_LETTER_SCHEME = "UV OI EZ AY KN JG WP BH SM DL CT RF"
CORNER_LETTER_SCHEME = "UVJ OIF ERN AZY MDL HKW CSG BPT"

WING_BUFFER = 'O'
EDGE_BUFFER = 'U'
CENTER_BUFFER = 'O'
CORNER_BUFFER = 'U'

NUM_COMMS = 6

WING_LETTER_SCHEME = ' '.join([x for x in WING_LETTER_SCHEME])


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


def _sequence_contains_pair(sequence, pair):
    if not pair or not sequence or len(sequence) < 2:
        return False
    target = ''.join(pair)
    for idx in range(len(sequence)):
        nxt = sequence[(idx + 1) % len(sequence)]
        if f"{sequence[idx]}{nxt}" == target:
            return True
    return False


def generate_piece_letters(
    count,
    scheme,
    buffer_letter,
    *,
    max_attempts=1000,
    forced_pair=None,
):
    if count < 0:
        raise ValueError("Requested count must be non-negative.")
    if count == 0:
        return []

    normalized_pair = _normalize_forced_pair(forced_pair)
    if normalized_pair and count < 2:
        raise ValueError("Need at least two letters to include a forced pair.")

    raw_blocks = [block for block in scheme.split(' ') if block]

    trim_start = 0
    if buffer_letter:
        for idx, block in enumerate(raw_blocks):
            if buffer_letter in block:
                trim_start = idx + 1
                break

    trimmed_blocks = raw_blocks[trim_start:]

    if not trimmed_blocks:
        raise ValueError("No pieces available after trimming with the buffer.")

    block_strings = []
    block_letter_templates = []

    for block in trimmed_blocks:
        letters = [letter for letter in block if letter != buffer_letter]
        if letters:
            block_strings.append(block)
            block_letter_templates.append(letters)

    if not block_letter_templates:
        raise ValueError("No usable letters remain after applying the buffer.")

    if count > 1 and len(block_strings) <= 1:
        raise ValueError("Not enough distinct blocks to satisfy spacing constraints.")

    letter_to_block_idx = {}
    for idx, block in enumerate(block_strings):
        for letter in block:
            if letter == buffer_letter:
                continue
            letter_to_block_idx[letter] = idx

    total_letters_per_cycle = sum(len(letters) for letters in block_letter_templates)
    if total_letters_per_cycle == 0:
        raise ValueError("No usable letters remain after applying the buffer.")
    cycle_attempt_limit = max(1, int(max_attempts))

    if normalized_pair:
        if normalized_pair[0] == normalized_pair[1]:
            raise ValueError("Forced pair letters must be distinct.")
        missing = [letter for letter in normalized_pair if letter not in letter_to_block_idx]
        if missing:
            raise ValueError(
                f"Forced pair letters {missing} are not available after applying the buffer trim.",
            )
        block_a = letter_to_block_idx[normalized_pair[0]]
        block_b = letter_to_block_idx[normalized_pair[1]]
        if block_a == block_b:
            raise ValueError("Forced pair letters cannot belong to the same piece.")

    def build_cycle():
        for _ in range(cycle_attempt_limit):
            working = [letters.copy() for letters in block_letter_templates]
            for letters in working:
                random.shuffle(letters)

            cycle = []
            last_idx = None
            remaining = total_letters_per_cycle

            while remaining > 0:
                candidates = [i for i, letters in enumerate(working) if letters and i != last_idx]
                if not candidates:
                    break
                idx = random.choice(candidates)
                letter = working[idx].pop()
                cycle.append((idx, letter))
                last_idx = idx
                remaining -= 1

            if remaining != 0:
                continue

            if len(cycle) > 1 and cycle[0][0] == cycle[-1][0]:
                shifts = list(range(1, len(cycle) - 1))
                random.shuffle(shifts)
                adjusted = None
                for shift in shifts:
                    rotated = cycle[shift:] + cycle[:shift]
                    if rotated[0][0] != rotated[-1][0]:
                        adjusted = rotated
                        break
                if adjusted is None:
                    continue
                cycle = adjusted

            return cycle

        return None

    def rotate_for_previous(cycle, prev_idx):
        if prev_idx is None:
            return cycle
        if len(cycle) == 1:
            return None if cycle[0][0] == prev_idx else cycle
        shifts = list(range(len(cycle)))
        random.shuffle(shifts)
        for shift in shifts:
            rotated = cycle[shift:] + cycle[:shift]
            first_block = rotated[0][0]
            last_block = rotated[-1][0]
            if first_block == prev_idx:
                continue
            if len(rotated) > 1 and first_block == last_block:
                continue
            return rotated
        return None

    overall_attempt_limit = max(1, int(max_attempts))

    for _ in range(overall_attempt_limit):
        result = []
        prev_block_idx = None
        remaining = count
        attempt_failed = False

        while remaining > 0:
            cycle = None
            for _ in range(cycle_attempt_limit):
                candidate = build_cycle()
                if candidate is None:
                    continue
                adjusted = rotate_for_previous(candidate, prev_block_idx)
                if adjusted is None:
                    continue
                cycle = adjusted
                break

            if cycle is None:
                attempt_failed = True
                break

            for block_idx, letter in cycle:
                if remaining == 0:
                    break
                if prev_block_idx is not None and block_idx == prev_block_idx:
                    attempt_failed = True
                    break
                result.append(letter)
                prev_block_idx = block_idx
                remaining -= 1

            if attempt_failed:
                break

        if attempt_failed or len(result) < count:
            continue

        if len(result) > 1:
            first_block = letter_to_block_idx.get(result[0])
            last_block = letter_to_block_idx.get(result[-1])
            if first_block is None or last_block is None or first_block == last_block:
                continue

        if normalized_pair and not _sequence_contains_pair(result, normalized_pair):
            continue

        return result

    raise ValueError("Unable to satisfy block spacing constraints after multiple attempts.")


def generate_wings(num_letters, forced_pair=None):
    return generate_piece_letters(
        num_letters,
        WING_LETTER_SCHEME,
        WING_BUFFER,
        forced_pair=forced_pair,
    )


def generate_edges(num_letters, forced_pair=None):
    return generate_piece_letters(
        num_letters,
        EDGE_LETTER_SCHEME,
        EDGE_BUFFER,
        forced_pair=forced_pair,
    )


def generate_centers(num_letters, forced_pair=None):
    return generate_piece_letters(
        num_letters,
        CENTER_LETTER_SCHEME,
        CENTER_BUFFER,
        forced_pair=forced_pair,
    )


def generate_corners(num_letters, forced_pair=None):
    return generate_piece_letters(
        num_letters,
        CORNER_LETTER_SCHEME,
        CORNER_BUFFER,
        forced_pair=forced_pair,
    )


def display(letters):
    for i in range(len(letters) - 1):
        print(f"{letters[i]}{letters[i+1]}")
    print(f"{letters[-1]}{letters[0]}")

if __name__ == "__main__":
    out = generate_edges(NUM_COMMS)
    display(out)
