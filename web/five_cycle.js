(function () {
  function normalizeBlocks(source) {
    const blocks = source
      .split(' ')
      .map((block) => block.trim())
      .filter(Boolean);
    if (!blocks.length) {
      return [];
    }
    if (blocks.length === 1 && blocks[0].length > 1) {
      return [...blocks[0]].map((ch) => ch.trim()).filter(Boolean);
    }
    return blocks;
  }

  function buildSchemeData(blocks) {
    if (!blocks.length) {
      throw new Error('Scheme must include at least one block.');
    }
    const blockLen = blocks[0].length;
    if (!blockLen) {
      throw new Error('Blocks cannot be empty.');
    }
    const letterToRefPos = {};
    blocks.forEach((block, pos) => {
      if (block.length !== blockLen) {
        throw new Error('All blocks must have the same length.');
      }
      [...block].forEach((ch, slot) => {
        if (letterToRefPos[ch]) {
          throw new Error(`Duplicate letter detected: ${ch}`);
        }
        letterToRefPos[ch] = [pos, slot];
      });
    });
    return { blocks, blockLen, letterToRefPos };
  }

  function solvedState(data) {
    const n = data.blocks.length;
    return {
      pieces: Array.from({ length: n }, (_, i) => i),
      oris: Array.from({ length: n }, () => 0),
    };
  }

  function letterAtSlot(data, pieces, oris, pos, slot) {
    const piece = pieces[pos];
    const o = ((oris[pos] % data.blockLen) + data.blockLen) % data.blockLen;
    const sideIdx = ((slot - o) % data.blockLen + data.blockLen) % data.blockLen;
    return data.blocks[piece][sideIdx];
  }

  function findCurrentSlot(data, pieces, oris, letter) {
    const n = data.blocks.length;
    for (let pos = 0; pos < n; pos += 1) {
      for (let slot = 0; slot < data.blockLen; slot += 1) {
        if (letterAtSlot(data, pieces, oris, pos, slot) === letter) {
          return [pos, slot];
        }
      }
    }
    throw new Error(`Letter ${letter} not found in current state.`);
  }

  function swapStickers(data, pieces, oris, A, B) {
    const [posA, slotA] = findCurrentSlot(data, pieces, oris, A);
    const [posB, slotB] = findCurrentSlot(data, pieces, oris, B);
    const pieceA = pieces[posA];
    const pieceB = pieces[posB];
    const oA = ((oris[posA] % data.blockLen) + data.blockLen) % data.blockLen;
    const oB = ((oris[posB] % data.blockLen) + data.blockLen) % data.blockLen;
    const sideA = ((slotA - oA) % data.blockLen + data.blockLen) % data.blockLen;
    const sideB = ((slotB - oB) % data.blockLen + data.blockLen) % data.blockLen;
    const newOA = ((slotA - sideB) % data.blockLen + data.blockLen) % data.blockLen;
    const newOB = ((slotB - sideA) % data.blockLen + data.blockLen) % data.blockLen;
    pieces[posA] = pieceB;
    pieces[posB] = pieceA;
    oris[posA] = newOA;
    oris[posB] = newOB;
  }

  function threeCycle(data, pieces, oris, a, b, c) {
    swapStickers(data, pieces, oris, b, c);
    swapStickers(data, pieces, oris, a, b);
  }

  function letterAtHome(data, pieces, oris, letter) {
    const ref = data.letterToRefPos[letter];
    if (!ref) {
      throw new Error(`Letter ${letter} not in scheme.`);
    }
    return letterAtSlot(data, pieces, oris, ref[0], ref[1]);
  }

  function traceFromBuffer(data, pieces, oris, bufferLetter, maxSteps = 200) {
    const cycle = [bufferLetter];
    let current = bufferLetter;
    let steps = 0;
    while (steps < maxSteps) {
      const next = letterAtHome(data, pieces, oris, current);
      cycle.push(next);
      if (next === bufferLetter) break;
      current = next;
      steps += 1;
    }
    return cycle;
  }

  function piecesAfterBuffer(blocks, bufferLetter) {
    const idx = blocks.findIndex((block) => block.includes(bufferLetter));
    if (idx === -1) {
      throw new Error(`Buffer letter ${bufferLetter} not found in scheme.`);
    }
    const trimmed = blocks.slice(idx + 1);
    if (!trimmed.length) {
      throw new Error('No pieces remain after trimming with the buffer.');
    }
    return trimmed;
  }

  function rngChoice(array, rngFn) {
    const idx = Math.floor(rngFn() * array.length);
    return array[idx];
  }

  function shuffleWithRng(array, rngFn) {
    for (let i = array.length - 1; i > 0; i -= 1) {
      const j = Math.floor(rngFn() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
  }

  function sampleWithoutReplacement(array, count, rngFn) {
    if (count > array.length) {
      throw new Error('Not enough items to sample.');
    }
    const pool = [...array];
    shuffleWithRng(pool, rngFn);
    return pool.slice(0, count);
  }

  function randomLetter(block, bufferLetter, rngFn) {
    const letters = [...block].filter((ch) => ch !== bufferLetter);
    if (!letters.length) {
      throw new Error(`No usable stickers remain in block ${block}.`);
    }
    return rngChoice(letters, rngFn);
  }

  function randomPair(blockA, blockB, bufferLetter, rngFn) {
    return [
      randomLetter(blockA, bufferLetter, rngFn),
      randomLetter(blockB, bufferLetter, rngFn),
    ];
  }

  function normalizeForcedPair(pair) {
    if (!pair) return null;
    if (Array.isArray(pair)) {
      if (pair.length !== 2) {
        throw new Error('Forced pair must contain exactly two letters.');
      }
      return pair.map((letter) => String(letter).trim().toUpperCase());
    }
    const str = String(pair).trim().toUpperCase();
    if (str.length !== 2) {
      throw new Error('Forced pair string must contain exactly two letters.');
    }
    return [str[0], str[1]];
  }

  function applyCommSequence(data, comms, bufferLetter) {
    const state = solvedState(data);
    comms.forEach(([a, b]) => {
      threeCycle(data, state.pieces, state.oris, bufferLetter, a, b);
    });
    return state;
  }

  function isBufferFiveCycle(trace, bufferLetter) {
    if (trace.length !== 6) return false;
    if (trace[0] !== bufferLetter || trace[trace.length - 1] !== bufferLetter) {
      return false;
    }
    const unique = trace.slice(0, -1);
    const set = new Set(unique);
    return unique.length === 5 && set.size === 5;
  }

  function randomShiftComms(commSequence, rngFn) {
    if (!commSequence.length) return [];
    const seq = [...commSequence];
    const offset = Math.floor(rngFn() * seq.length);
    if (offset === 0) return seq;
    return seq.slice(offset).concat(seq.slice(0, offset));
  }

  function basicFiveCycle(options = {}) {
    const {
      bufferLetter,
      scheme,
      maxAttempts = 1000,
      rngFn = Math.random,
      forcedPair,
      randomizeOrientation = true,
    } = options;
    if (!bufferLetter) {
      throw new Error('Buffer letter is required for 5-cycle generation.');
    }
    const blocks = normalizeBlocks(scheme || '');
    const schemeData = buildSchemeData(blocks);
    if (!schemeData.letterToRefPos[bufferLetter]) {
      throw new Error(`Buffer letter ${bufferLetter} not present in scheme.`);
    }
    const normalizedForcedPair = normalizeForcedPair(forcedPair);
    const bufferBlockIdx = blocks.findIndex((block) => block.includes(bufferLetter));
    if (normalizedForcedPair) {
      normalizedForcedPair.forEach((letter) => {
        const ref = schemeData.letterToRefPos[letter];
        if (!ref) {
          throw new Error(`Forced pair letter ${letter} not present in scheme.`);
        }
        if (ref[0] <= bufferBlockIdx) {
          throw new Error(`Forced pair letter ${letter} must be after the buffer piece.`);
        }
      });
    }
    const availablePieces = piecesAfterBuffer(blocks, bufferLetter);
    if (availablePieces.length < 4) {
      throw new Error('Need at least four pieces after trimming with the buffer.');
    }

    const attempts = Math.max(1, Math.floor(maxAttempts));
    let lastError = 'No attempts run.';

    for (let attempt = 0; attempt < attempts; attempt += 1) {
      let pieceI;
      let pieceJ;
      let pieceK;
      let pieceL;
      let firstComm;
      let secondComm;
      const orientationMap = new Map();

      const recordOrientation = (pieceA, pieceB, letters) => {
        orientationMap.set(pieceA, letters[0]);
        orientationMap.set(pieceB, letters[1]);
        return letters;
      };

      if (normalizedForcedPair) {
        const forcedPieces = normalizedForcedPair.map((letter) => {
          const [blockIdx] = schemeData.letterToRefPos[letter];
          return blocks[blockIdx];
        });
        const pool = availablePieces.filter(
          (piece) => piece !== forcedPieces[0] && piece !== forcedPieces[1],
        );
        if (pool.length < 2) {
          lastError = 'Not enough additional pieces available for forced pair.';
          continue;
        }
        const extras = sampleWithoutReplacement(pool, 2, rngFn);
        const forceIntoFirst = rngFn() < 0.5;
        if (forceIntoFirst) {
          [pieceI, pieceJ] = forcedPieces;
          [pieceK, pieceL] = extras;
          firstComm = recordOrientation(pieceI, pieceJ, [...normalizedForcedPair]);
          secondComm = recordOrientation(
            pieceK,
            pieceL,
            randomPair(pieceK, pieceL, bufferLetter, rngFn),
          );
        } else {
          [pieceK, pieceL] = forcedPieces;
          [pieceI, pieceJ] = extras;
          firstComm = recordOrientation(
            pieceI,
            pieceJ,
            randomPair(pieceI, pieceJ, bufferLetter, rngFn),
          );
          secondComm = recordOrientation(pieceK, pieceL, [...normalizedForcedPair]);
        }
      } else {
        const selected = sampleWithoutReplacement(availablePieces, 4, rngFn);
        [pieceI, pieceJ, pieceK, pieceL] = selected;
        firstComm = recordOrientation(
          pieceI,
          pieceJ,
          randomPair(pieceI, pieceJ, bufferLetter, rngFn),
        );
        secondComm = recordOrientation(
          pieceK,
          pieceL,
          randomPair(pieceK, pieceL, bufferLetter, rngFn),
        );
      }

      const jkOrJl = rngChoice(
        [
          [pieceJ, pieceK],
          [pieceJ, pieceL],
        ],
        rngFn,
      );
      let thirdComm;
      const [thirdPieceA, thirdPieceB] = jkOrJl;
      if (randomizeOrientation) {
        thirdComm = randomPair(thirdPieceA, thirdPieceB, bufferLetter, rngFn);
      } else {
        const lockedA = orientationMap.get(thirdPieceA);
        const lockedB = orientationMap.get(thirdPieceB);
        if (lockedA && lockedB) {
          thirdComm = [lockedA, lockedB];
        } else {
          thirdComm = randomPair(thirdPieceA, thirdPieceB, bufferLetter, rngFn);
        }
      }
      recordOrientation(thirdPieceA, thirdPieceB, thirdComm);
      const initialComms = [firstComm, secondComm, thirdComm];
      const selectedPieces = [pieceI, pieceJ, pieceK, pieceL];

      const state = applyCommSequence(schemeData, initialComms, bufferLetter);
      const trace = traceFromBuffer(
        schemeData,
        state.pieces,
        state.oris,
        bufferLetter,
      );

      if (!isBufferFiveCycle(trace, bufferLetter)) {
        lastError = `pieces=${selectedPieces.join(',')}, comms=${JSON.stringify(
          initialComms,
        )}, trace=${trace.join('->')}`;
        continue;
      }

      const cleanupPairs = [
        [trace[4], trace[3]],
        [trace[2], trace[1]],
      ];

      return {
        selected_pieces: selectedPieces,
        comm_sequence: initialComms.concat(cleanupPairs),
        trace,
      };
    }

    throw new Error(`Failed to leave a 5-cycle. ${lastError}`);
  }

  function generateFiveCycle(options = {}) {
    const rngFn = options.rngFn || Math.random;
    const result = basicFiveCycle({ ...options, rngFn });
    const rotated = randomShiftComms(result.comm_sequence, rngFn);
    return {
      selected_pieces: result.selected_pieces,
      comm_sequence: rotated,
      trace: result.trace,
    };
  }

  window.FiveCycle = {
    basicFiveCycle,
    generateFiveCycle,
  };
})();
