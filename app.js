(function () {
  const themeToggle = document.getElementById('themeToggle');
  let isDarkMode = true;

  function syncThemeToggle() {
    if (themeToggle) {
      themeToggle.checked = isDarkMode;
    }
  }

  function applyTheme() {
    document.documentElement.setAttribute('data-bs-theme', isDarkMode ? 'dark' : 'light');
    document.body.classList.toggle('bg-dark', isDarkMode);
    document.body.classList.toggle('text-light', isDarkMode);
    document.body.classList.toggle('bg-light', !isDarkMode);
    document.body.classList.toggle('text-dark', !isDarkMode);
    syncThemeToggle();
  }

  if (themeToggle) {
    themeToggle.addEventListener('change', () => {
      isDarkMode = themeToggle.checked;
      applyTheme();
    });
  }

  applyTheme();

  const PRESETS = {
    wing: {
      label: 'Wings',
      scheme: 'OABCDEFGHIJKLMNPRSTUVWYZ',
      buffer: 'O',
    },
    edge: {
      label: 'Edges',
      scheme: 'UV OI EZ AY KN JG WP BH SM DL CT RF',
      buffer: 'U',
    },
    corner: {
      label: 'Corners',
      scheme: 'UVJ OIF ERN AZY MDL HKW CSG BPT',
      buffer: 'U',
    },
    center: {
      label: 'Centers',
      scheme: 'AEOU ZFGH IJKL VNMP YRST BCDW',
      buffer: 'O',
    },
    'x-center': {
      label: 'X-center',
      scheme: 'AEOU ZFGH IJKL VNMP YRST BCDW',
      buffer: 'O',
    },
    't-center': {
      label: 'T-center',
      scheme: 'AEOU ZFGH IJKL VNMP YRST BCDW',
      buffer: 'O',
    },
    obliques: {
      label: 'Obliques',
      scheme: 'AEOU ZFGH IJKL VNMP YRST BCDW',
      buffer: 'O',
    },
    midges: {
      label: 'Midges',
      scheme: 'UV OI EZ AY KN JG WP BH SM DL CT RF',
      buffer: 'U',
    },
  };

  const pieceSelect = document.getElementById('pieceType');
  const methodSelect = document.getElementById('method');
  const countInput = document.getElementById('count');
  const bufferInput = document.getElementById('buffer');
  const schemeInput = document.getElementById('scheme');
  const requiredPairsInput = document.getElementById('requiredPairs');
  const randomizeOrientationRow = document.getElementById('randomizeOrientationRow');
  const randomizeOrientationToggle = document.getElementById('randomizeOrientation');
  const includeInversesToggle = document.getElementById('includeInverses');
  const form = document.getElementById('generatorForm');
  const resultsSection = document.getElementById('results');
  const pairGrid = document.getElementById('pairGrid');
  const lettersHeading = document.getElementById('lettersHeading');
  const errorBox = document.getElementById('errorBox');

  const STORAGE_PREFIX = 'commDrillTrainer';
  const schemeStorageKey = (type) => `${STORAGE_PREFIX}:scheme:${type}`;
  const bufferStorageKey = (type) => `${STORAGE_PREFIX}:buffer:${type}`;
  const pairStorageKey = (type) => `${STORAGE_PREFIX}:pairs:${type}`;
  const inverseStorageKey = (type) => `${STORAGE_PREFIX}:pairs_inverse:${type}`;
  const orientationStorageKey = (type) => `${STORAGE_PREFIX}:orientation:${type}`;

  function safeGetItem(key) {
    try {
      return window.localStorage?.getItem(key);
    } catch (e) {
      return null;
    }
  }

  function safeSetItem(key, value) {
    try {
      window.localStorage?.setItem(key, value);
    } catch (e) {
      // Ignore storage issues (e.g., privacy mode)
    }
  }

  function randomChoice(array) {
    return array[Math.floor(Math.random() * array.length)];
  }

  const schemeSettings = {};
  const bufferSettings = {};
  const pairSettings = {};
  const inverseSettings = {};
  const orientationSettings = {};
  Object.keys(PRESETS).forEach((type) => {
    schemeSettings[type] = safeGetItem(schemeStorageKey(type)) || PRESETS[type].scheme;
    bufferSettings[type] = safeGetItem(bufferStorageKey(type)) || PRESETS[type].buffer;
    pairSettings[type] = safeGetItem(pairStorageKey(type)) || '';
    const storedInverse = safeGetItem(inverseStorageKey(type));
    inverseSettings[type] = storedInverse === null ? 'true' : storedInverse;
    const storedOrientation = safeGetItem(orientationStorageKey(type));
    orientationSettings[type] = storedOrientation === null ? 'true' : storedOrientation;
  });

  function uniqueLettersFromSchemeText(text) {
    if (!text) return [];
    const upper = text.toUpperCase();
    const seen = new Set();
    const letters = [];
    for (const ch of upper) {
      if (!/[A-Z]/.test(ch)) continue;
      if (seen.has(ch)) continue;
      seen.add(ch);
      letters.push(ch);
    }
    return letters;
  }

  function populateBufferOptions(type, preferredLetter) {
    if (!bufferInput) return;
    const schemeText = schemeInput.value || '';
    const letters = uniqueLettersFromSchemeText(schemeText);
    bufferInput.innerHTML = '';
    letters.forEach((letter) => {
      const option = document.createElement('option');
      option.value = letter;
      option.textContent = letter;
      bufferInput.appendChild(option);
    });

    let desired = (preferredLetter || bufferSettings[type] || '').toUpperCase();
    if (!letters.includes(desired)) {
      const presetDefault = PRESETS[type]?.buffer?.toUpperCase();
      if (presetDefault && letters.includes(presetDefault)) {
        desired = presetDefault;
      } else {
        desired = letters[0] || '';
      }
    }

    bufferInput.disabled = letters.length === 0;
    bufferInput.value = desired || '';

    if (desired) {
      bufferSettings[type] = desired;
      safeSetItem(bufferStorageKey(type), desired);
    }
  }

  function normalizeSchemeBlocks(rawScheme) {
    if (!rawScheme) return [];
    let blocks = rawScheme
      .trim()
      .split(/\s+/)
      .filter(Boolean);
    if (blocks.length === 1 && blocks[0].length > 1) {
      blocks = blocks[0].split('').filter(Boolean);
    }
    return blocks;
  }

  function buildLetterMeta(blocks, bufferLetter) {
    if (!blocks.length) {
      throw new Error('Letter scheme cannot be empty.');
    }
    const letterToMeta = {};
    let bufferBlockIdx = blocks.findIndex((block) => block.includes(bufferLetter));
    if (bufferBlockIdx === -1) {
      throw new Error(`Buffer letter "${bufferLetter}" not found in the scheme.`);
    }
    const trimmedStart = bufferBlockIdx + 1;
    if (trimmedStart >= blocks.length) {
      throw new Error('No pieces remain after trimming with the buffer.');
    }
    blocks.forEach((block, idx) => {
      [...block].forEach((letter) => {
        letterToMeta[letter] = {
          blockIdx: idx,
          usable: idx >= trimmedStart,
        };
      });
    });
    return { letterToMeta, bufferBlockIdx, trimmedStart };
  }

  function parseRequiredPairs(schemeText, bufferLetter, includeInverses) {
    if (!requiredPairsInput) return [];
    const raw = requiredPairsInput.value.trim().toUpperCase();
    if (!raw) return [];
    const tokens = raw.split(/\s+/).filter(Boolean);
    if (!tokens.length) return [];
    const blocks = normalizeSchemeBlocks(schemeText);
    const { letterToMeta, bufferBlockIdx } = buildLetterMeta(blocks, bufferLetter);
    const pairs = [];
    for (const token of tokens) {
      if (token.length !== 2) {
        throw new Error(`Pair "${token}" must contain exactly two letters.`);
      }
      const [first, second] = token.split('');
      if (first === second) {
        throw new Error(`Pair "${token}" cannot repeat the same letter.`);
      }
      const metaFirst = letterToMeta[first];
      const metaSecond = letterToMeta[second];
      if (!metaFirst) {
        throw new Error(`Letter "${first}" from pair "${token}" is not in the scheme.`);
      }
      if (!metaSecond) {
        throw new Error(`Letter "${second}" from pair "${token}" is not in the scheme.`);
      }
      if (!metaFirst.usable || !metaSecond.usable) {
        throw new Error(`Letters in pair "${token}" must be after the buffer piece.`);
      }
      if (metaFirst.blockIdx === metaSecond.blockIdx) {
        throw new Error(`Letters in pair "${token}" cannot be on the same piece.`);
      }
      if (
        metaFirst.blockIdx === bufferBlockIdx ||
        metaSecond.blockIdx === bufferBlockIdx
      ) {
        throw new Error(`Letters in pair "${token}" cannot include the buffer piece.`);
      }
      pairs.push([first, second]);
      if (includeInverses) {
        pairs.push([second, first]);
      }
    }
    return pairs;
  }

  function ensureChainPair(letters, pair) {
    if (!pair || !letters || letters.length < 2) {
      return letters;
    }
    const idx = letters.findIndex(
      (letter, index) =>
        letter === pair[0] &&
        letters[(index + 1) % letters.length] === pair[1],
    );
    if (idx !== -1) {
      const rotated = letters.slice(idx).concat(letters.slice(0, idx));
      return rotated;
    }
    const remaining = letters
      .filter(
        (letter, index) =>
          !(
            letter === pair[0] &&
            letters[(index + 1) % letters.length] === pair[1]
          ),
      )
      .filter((letter) => letter !== pair[0] && letter !== pair[1]);
    const adjusted = [pair[0], pair[1], ...remaining];
    return adjusted.slice(0, letters.length);
  }


  function autoResizeScheme() {
    if (!schemeInput) return;
    schemeInput.style.height = 'auto';
    schemeInput.style.height = `${schemeInput.scrollHeight}px`;
  }

  function applyPreset(type) {
    const preset = PRESETS[type];
    if (!preset) return;
    schemeInput.value = schemeSettings[type] ?? preset.scheme;
    populateBufferOptions(type, bufferSettings[type]);
    if (requiredPairsInput) {
      requiredPairsInput.value = pairSettings[type] ?? '';
    }
    if (includeInversesToggle) {
      includeInversesToggle.checked = inverseSettings[type] !== 'false';
    }
    if (randomizeOrientationToggle) {
      randomizeOrientationToggle.checked = orientationSettings[type] !== 'false';
    }
    countInput.value = methodRequiresFixedCount() ? 5 : 6;
    autoResizeScheme();
  }

  function setPairGridLayout(forFiveCycle) {
    pairGrid.className = 'd-flex gap-2';
    if (forFiveCycle) {
      pairGrid.classList.add('flex-column', 'align-items-start');
    } else {
      pairGrid.classList.add('flex-wrap');
    }
  }

  function renderResults(letters, label) {
    setPairGridLayout(true);
    if (!letters.length) {
      lettersHeading.textContent = 'No letters generated (count was zero).';
      lettersHeading.classList.remove('d-none');
      pairGrid.innerHTML = '';
      resultsSection.classList.remove('d-none');
      return;
    }

    lettersHeading.textContent = '';
    lettersHeading.classList.add('d-none');
    pairGrid.innerHTML = '';
    const pairs = letters.map(
      (letter, idx) => `${letter}${letters[(idx + 1) % letters.length]}`,
    );

    pairs.forEach((pair) => {
      const textNode = document.createElement('div');
      textNode.className = 'fs-2 fw-semibold';
      textNode.textContent = pair;
      pairGrid.appendChild(textNode);
    });

    resultsSection.classList.remove('d-none');
  }

  function renderFiveCycleResults(pairs, label) {
    setPairGridLayout(true);
    lettersHeading.textContent = '';
    lettersHeading.classList.add('d-none');
    pairGrid.innerHTML = '';
    pairs.forEach((pair) => {
      const textNode = document.createElement('div');
      textNode.className = 'fs-2 fw-semibold';
      textNode.textContent = pair;
      pairGrid.appendChild(textNode);
    });
    resultsSection.classList.remove('d-none');
  }

  function clearResults() {
    pairGrid.innerHTML = '';
    resultsSection.classList.add('d-none');
    errorBox.classList.add('d-none');
    errorBox.textContent = '';
    lettersHeading.textContent = '';
    lettersHeading.classList.add('d-none');
  }

  function methodRequiresFixedCount() {
    return methodSelect.value === 'fiveCycle';
  }

  function updateMethodState() {
    if (methodRequiresFixedCount()) {
      countInput.value = 5;
      countInput.disabled = true;
    } else {
      countInput.disabled = false;
    }
    if (randomizeOrientationRow) {
      randomizeOrientationRow.classList.toggle('d-none', !methodRequiresFixedCount());
    }
  }

  function handleGenerate(event) {
    if (event && typeof event.preventDefault === 'function') {
      event.preventDefault();
    }
    errorBox.classList.add('d-none');
    errorBox.textContent = '';

    const type = pieceSelect.value;
    const preset = PRESETS[type];
    const method = methodSelect.value;
    const rawCount = countInput.value.trim();
    const count = methodRequiresFixedCount() ? 5 : Number.parseInt(rawCount, 10);
    const buffer = bufferInput.value.trim().toUpperCase();
    const scheme = schemeInput.value.trim().toUpperCase();

    if (!methodRequiresFixedCount() && (Number.isNaN(count) || count < 0)) {
      errorBox.textContent = 'Please enter a non-negative integer for the count.';
      errorBox.classList.remove('d-none');
      resultsSection.classList.add('d-none');
      return;
    }

    if (buffer.length !== 1) {
      errorBox.textContent = 'Buffer must be exactly one character.';
      errorBox.classList.remove('d-none');
      resultsSection.classList.add('d-none');
      return;
    }

    let requiredPairs = [];
    try {
      const includeInverses =
        includeInversesToggle && typeof includeInversesToggle.checked === 'boolean'
          ? includeInversesToggle.checked
          : true;
      requiredPairs = parseRequiredPairs(scheme, buffer, includeInverses);
    } catch (pairError) {
      errorBox.textContent =
        pairError instanceof Error ? pairError.message : String(pairError);
      errorBox.classList.remove('d-none');
      resultsSection.classList.add('d-none');
      return;
    }
    const requiredPair = requiredPairs.length ? randomChoice(requiredPairs) : null;

    if (requiredPair && method !== 'fiveCycle' && count < 2) {
      errorBox.textContent = 'Need at least two letters to include a required pair.';
      errorBox.classList.remove('d-none');
      resultsSection.classList.add('d-none');
      return;
    }

    const randomizeOrientation =
      randomizeOrientationToggle && method === 'fiveCycle'
        ? randomizeOrientationToggle.checked
        : true;

    try {
      if (method === 'fiveCycle') {
        if (!window.FiveCycle || typeof window.FiveCycle.generateFiveCycle !== 'function') {
          throw new Error('5-cycle generator is unavailable.');
        }
        const result = window.FiveCycle.generateFiveCycle({
          scheme,
          bufferLetter: buffer,
          maxAttempts: 5000,
          randomizeOrientation,
          forcedPair: requiredPair ? requiredPair.join('') : null,
        });
        const pairs = result.comm_sequence.map(
          ([first, second]) => `${first}${second}`,
        );
        renderFiveCycleResults(pairs, preset ? `${preset.label} 5-cycles` : '5-cycles');
      } else {
        const chainGenerator = window.Chain?.generatePieceLetters;
        if (typeof chainGenerator !== 'function') {
          throw new Error('Chain generator is unavailable.');
        }
        const letters = chainGenerator(count, scheme, buffer, 2000);
        const adjustedLetters = ensureChainPair(letters, requiredPair);
        renderResults(adjustedLetters, preset ? preset.label : 'Letters');
      }
    } catch (e) {
      errorBox.textContent = e instanceof Error ? e.message : String(e);
      errorBox.classList.remove('d-none');
      resultsSection.classList.add('d-none');
    }
  }

  form.addEventListener('submit', handleGenerate);
  document.addEventListener('keydown', (event) => {
    const isSchemeField = event.target === schemeInput;
    const isPairsField = event.target === requiredPairsInput;
    if (isSchemeField || isPairsField) {
      return;
    }
    const isTextArea = event.target.tagName === 'TEXTAREA';
    if ((event.code === 'Enter' || event.code === 'Space') && !isTextArea) {
      handleGenerate(event);
    }
  });

  pieceSelect.addEventListener('change', () => {
    applyPreset(pieceSelect.value);
    clearResults();
    updateMethodState();
  });

  methodSelect.addEventListener('change', () => {
    updateMethodState();
    if (methodRequiresFixedCount()) {
      countInput.value = 5;
    }
    clearResults();
  });

  schemeInput.addEventListener('input', () => {
    const currentType = pieceSelect.value;
    const previousBuffer = bufferInput ? bufferInput.value : '';
    schemeSettings[currentType] = schemeInput.value;
    safeSetItem(schemeStorageKey(currentType), schemeSettings[currentType]);
    autoResizeScheme();
    populateBufferOptions(currentType, previousBuffer);
  });

  if (bufferInput) {
    bufferInput.addEventListener('change', () => {
      const currentType = pieceSelect.value;
      bufferSettings[currentType] = bufferInput.value;
      safeSetItem(bufferStorageKey(currentType), bufferSettings[currentType]);
    });
  }

  if (requiredPairsInput) {
    requiredPairsInput.addEventListener('input', () => {
      const currentType = pieceSelect.value;
      pairSettings[currentType] = requiredPairsInput.value;
      safeSetItem(pairStorageKey(currentType), pairSettings[currentType]);
    });
  }

  if (includeInversesToggle) {
    includeInversesToggle.addEventListener('change', () => {
      const currentType = pieceSelect.value;
      inverseSettings[currentType] = includeInversesToggle.checked ? 'true' : 'false';
      safeSetItem(inverseStorageKey(currentType), inverseSettings[currentType]);
    });
  }

  if (randomizeOrientationToggle) {
    randomizeOrientationToggle.addEventListener('change', () => {
      const currentType = pieceSelect.value;
      orientationSettings[currentType] = randomizeOrientationToggle.checked ? 'true' : 'false';
      safeSetItem(orientationStorageKey(currentType), orientationSettings[currentType]);
    });
  }

  applyPreset(pieceSelect.value);
  updateMethodState();
  autoResizeScheme();
})();
