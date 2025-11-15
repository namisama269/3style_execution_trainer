# =========================
#  Uniform-M Puzzle Helpers
# =========================

# --- Scheme (example: corners, M=3) ---
blocks = ["UVJ", "OIF", "ERN", "AZY", "MDL", "HKW", "CSG", "BPT"]  # 8 corners, 3 stickers each
M = len(blocks[0])
if any(len(b) != M for b in blocks):
    raise ValueError("All blocks must have the same length (uniform piece arity).")

# Maps for solved reference (home positions of stickers)
letter_to_ref_piece_side = {}
letter_to_ref_pos_side = {}
for pos, block in enumerate(blocks):
    for side, ch in enumerate(block):
        if ch in letter_to_ref_piece_side:
            raise ValueError(f"Duplicate letter in scheme: {ch}")
        letter_to_ref_piece_side[ch] = (pos, side)  # which piece/side the letter belongs to (in solved)
        letter_to_ref_pos_side[ch] = (pos, side)    # the reference slot (position/slot) in solved

# --- State (pieces, oris) ---
def solved_state(n):
    return list(range(n)), [0]*n  # (pieces, oris)

# --- Visibility / Queries ---
def letter_at_slot(pieces, oris, pos, slot):
    """
    What letter is visible at (pos, slot)?
    If a piece with orientation o sits at pos, the visible side index is (slot - o) mod M.
    """
    piece = pieces[pos]
    o = oris[pos] % M
    side_idx = (slot - o) % M
    return blocks[piece][side_idx]

def view_state_labels(pieces, oris):
    return [''.join(letter_at_slot(pieces, oris, p, s) for s in range(M)) for p in range(len(blocks))]

def find_current_slot(pieces, oris, letter):
    """
    Find (pos, slot) where 'letter' currently appears.
    """
    n = len(blocks)
    for pos in range(n):
        for slot in range(M):
            if letter_at_slot(pieces, oris, pos, slot) == letter:
                return (pos, slot)
    raise ValueError(f"Letter {letter} not found.")

# ================
# Core move logic
# ================

def swap_stickers(pieces, oris, A, B):
    """
    Swap the *current* positions of stickers A and B (sticker 2-cycle),
    updating permutation and orientations.

    If A is at (posA,slotA) on pieceA with orientation oA, the side carrying A is:
        sideA = (slotA - oA) mod M.
    To show A at some target slot 'slotB', set the new orientation so:
        (sideA + oA') mod M == slotB  ->  oA' = (slotB - sideA) mod M.
    Do this symmetrically for B and swap the two pieces.
    """
    posA, slotA = find_current_slot(pieces, oris, A)
    posB, slotB = find_current_slot(pieces, oris, B)

    pieceA, oA = pieces[posA], oris[posA] % M
    pieceB, oB = pieces[posB], oris[posB] % M

    sideA = (slotA - oA) % M
    sideB = (slotB - oB) % M

    new_o_for_posA = (slotA - sideB) % M  # place pieceB so B shows at slotA
    new_o_for_posB = (slotB - sideA) % M  # place pieceA so A shows at slotB

    pieces[posA], oris[posA] = pieceB, new_o_for_posA
    pieces[posB], oris[posB] = pieceA, new_o_for_posB

def three_cycle(pieces, oris, a, b, c):
    """
    Sticker 3-cycle (a b c) implemented as two 2-cycles applied right-to-left:
        first (b c), then (a b).
    """
    swap_stickers(pieces, oris, b, c)
    swap_stickers(pieces, oris, a, b)

# =========================
# Tracer: cycle from buffer
# =========================

def letter_at_home(pieces, oris, letter):
    """
    Read the current letter sitting in the *home* slot of 'letter'
    (i.e., at its solved (pos,slot)).
    """
    pos, slot = letter_to_ref_pos_side[letter]
    return letter_at_slot(pieces, oris, pos, slot)

def trace_from_buffer(pieces, oris, buffer_letter, max_steps=200):
    """
    Trace the sticker cycle induced by the CURRENT state, starting from buffer_letter.

    Rule: next = current letter found at the *home slot* of the current tracer.
          Repeat until we come back to the buffer or we hit max_steps.

    Returns a list like [buffer, x1, x2, ..., buffer] if it closes,
    or [buffer, x1, x2, ...] if it would exceed max_steps.
    """
    cycle = [buffer_letter]
    cur = buffer_letter
    for _ in range(max_steps):
        nxt = letter_at_home(pieces, oris, cur)
        cycle.append(nxt)
        if nxt == buffer_letter:
            break
        cur = nxt
    return cycle

def full_sticker_cycles(pieces, oris):
    """
    Optional helper: decompose the entire sticker permutation into disjoint cycles
    relative to the solved reference. Useful for debugging.
    """
    all_letters = [ch for b in blocks for ch in b]
    unseen = set(all_letters)
    cycles = []
    while unseen:
        start = next(iter(unseen))
        cyc = [start]
        cur = start
        while True:
            nxt = letter_at_home(pieces, oris, cur)
            cyc.append(nxt)
            unseen.discard(cur)
            if nxt == start:
                break
            cur = nxt
        cycles.append(cyc)
        unseen.discard(start)
    return cycles

# ===========
# Demo / test
# ===========

if __name__ == "__main__":
    pieces, oris = solved_state(len(blocks))
    print("REFERENCE:", blocks)
    print("BEFORE   :", view_state_labels(pieces, oris))

    # Apply a 3-cycle on corners: U -> R -> D -> U
    three_cycle(pieces, oris, 'U', 'R', 'D')

    print("AFTER    :", view_state_labels(pieces, oris))

    # Verify on reference slots
    u_ref = letter_to_ref_pos_side['U']
    r_ref = letter_to_ref_pos_side['R']
    d_ref = letter_to_ref_pos_side['D']
    print("\nCheck mapping after (U R D):")
    print(f"At R's ref slot {r_ref}: {letter_at_slot(pieces, oris, *r_ref)}  (expected U)")
    print(f"At D's ref slot {d_ref}: {letter_at_slot(pieces, oris, *d_ref)}  (expected R)")
    print(f"At U's ref slot {u_ref}: {letter_at_slot(pieces, oris, *u_ref)}  (expected D)")

    # --- Tracer from a buffer sticker ---
    buffer = 'U'
    trace = trace_from_buffer(pieces, oris, buffer)
    print(f"\nTrace from buffer '{buffer}': {' -> '.join(trace)}")

    # Optional: show all sticker cycles (including solved 1-cycles)
    print("\nAll sticker cycles (disjoint, non-trivial only):")
    for cyc in full_sticker_cycles(pieces, oris):
        if len(cyc) <= 2:  # skip 1-cycles like A -> A
            continue
        print(" -> ".join(cyc))
