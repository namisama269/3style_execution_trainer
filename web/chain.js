(function () {
  function shuffle(array) {
    for (let i = array.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }

  function randomChoice(array) {
    return array[Math.floor(Math.random() * array.length)];
  }

  function generatePieceLetters(count, scheme, bufferLetter, maxAttempts = 1000) {
    if (count < 0) {
      throw new Error('Requested count must be non-negative.');
    }
    if (count === 0) {
      return [];
    }

    let rawBlocks = scheme
      .split(' ')
      .map((block) => block.trim())
      .filter(Boolean);

    if (rawBlocks.length === 1 && rawBlocks[0].length > 1) {
      rawBlocks = [...rawBlocks[0]].map((ch) => ch.trim()).filter(Boolean);
    }

    let trimStart = 0;
    if (bufferLetter) {
      for (let i = 0; i < rawBlocks.length; i += 1) {
        if (rawBlocks[i].includes(bufferLetter)) {
          trimStart = i + 1;
          break;
        }
      }
    }

    const trimmedBlocks = rawBlocks.slice(trimStart);
    if (!trimmedBlocks.length) {
      throw new Error('No pieces available after trimming with the buffer.');
    }

    const blockStrings = [];
    const blockLetterTemplates = [];

    for (const block of trimmedBlocks) {
      const letters = [...block].filter((letter) => letter !== bufferLetter);
      if (letters.length) {
        blockStrings.push(block);
        blockLetterTemplates.push(letters);
      }
    }

    if (!blockLetterTemplates.length) {
      throw new Error('No usable letters remain after applying the buffer.');
    }

    if (count > 1 && blockStrings.length <= 1) {
      throw new Error('Not enough distinct blocks to satisfy spacing constraints.');
    }

    const letterToBlockIdx = {};
    blockStrings.forEach((block, idx) => {
      [...block].forEach((letter) => {
        if (letter === bufferLetter) return;
        letterToBlockIdx[letter] = idx;
      });
    });

    const totalLettersPerCycle = blockLetterTemplates.reduce(
      (sum, letters) => sum + letters.length,
      0,
    );
    if (!totalLettersPerCycle) {
      throw new Error('No usable letters remain after applying the buffer.');
    }

    const attemptLimit = Math.max(1, Math.floor(maxAttempts));

    const buildCycle = () => {
      for (let attempt = 0; attempt < attemptLimit; attempt += 1) {
        const working = blockLetterTemplates.map((letters) => shuffle([...letters]));
        const cycle = [];
        let lastIdx = null;
        let remaining = totalLettersPerCycle;

        while (remaining > 0) {
          const candidates = [];
          working.forEach((letters, idx) => {
            if (letters.length && idx !== lastIdx) {
              candidates.push(idx);
            }
          });

          if (!candidates.length) {
            break;
          }

          const idx = randomChoice(candidates);
          const letter = working[idx].pop();
          cycle.push([idx, letter]);
          lastIdx = idx;
          remaining -= 1;
        }

        if (remaining !== 0) {
          continue;
        }

        if (cycle.length > 1 && cycle[0][0] === cycle[cycle.length - 1][0]) {
          const shifts = [];
          for (let i = 1; i < cycle.length - 1; i += 1) {
            shifts.push(i);
          }
          shuffle(shifts);

          let adjusted = null;
          for (const shift of shifts) {
            const rotated = cycle.slice(shift).concat(cycle.slice(0, shift));
            if (rotated[0][0] !== rotated[rotated.length - 1][0]) {
              adjusted = rotated;
              break;
            }
          }

          if (!adjusted) {
            continue;
          }
          return adjusted;
        }

        return cycle;
      }
      return null;
    };

    const rotateForPrevious = (cycle, prevIdx) => {
      if (prevIdx === null || prevIdx === undefined) {
        return cycle;
      }
      if (cycle.length === 1) {
        return cycle[0][0] === prevIdx ? null : cycle;
      }
      const shifts = shuffle([...cycle.keys()]);
      for (const shift of shifts) {
        const rotated = cycle.slice(shift).concat(cycle.slice(0, shift));
        const firstBlock = rotated[0][0];
        const lastBlock = rotated[rotated.length - 1][0];
        if (firstBlock === prevIdx) {
          continue;
        }
        if (firstBlock === lastBlock) {
          continue;
        }
        return rotated;
      }
      return null;
    };

    for (let attempt = 0; attempt < attemptLimit; attempt += 1) {
      const result = [];
      let prevBlockIdx = null;
      let remaining = count;
      let failed = false;

      while (remaining > 0) {
        let cycle = null;
        for (let i = 0; i < attemptLimit; i += 1) {
          const candidate = buildCycle();
          if (!candidate) continue;
          const adjusted = rotateForPrevious(candidate, prevBlockIdx);
          if (!adjusted) continue;
          cycle = adjusted;
          break;
        }

        if (!cycle) {
          failed = true;
          break;
        }

        for (const [blockIdx, letter] of cycle) {
          if (remaining === 0) break;
          if (prevBlockIdx !== null && blockIdx === prevBlockIdx) {
            failed = true;
            break;
          }
          result.push(letter);
          prevBlockIdx = blockIdx;
          remaining -= 1;
        }

        if (failed) break;
      }

      if (failed || result.length < count) {
        continue;
      }

      if (result.length > 1) {
        const firstBlock = letterToBlockIdx[result[0]];
        const lastBlock = letterToBlockIdx[result[result.length - 1]];
        if (
          firstBlock === undefined ||
          lastBlock === undefined ||
          firstBlock === lastBlock
        ) {
          continue;
        }
      }

      return result;
    }

    throw new Error('Unable to satisfy block spacing constraints after multiple attempts.');
  }

  window.Chain = {
    generatePieceLetters,
  };
})();
