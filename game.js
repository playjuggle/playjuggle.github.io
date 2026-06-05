// ---------------------------------------------------------------------------
// HOW TO ADD A PUZZLE
// ---------------------------------------------------------------------------
// Add one entry to PUZZLE_ROWS per date, keyed "YYYY-MM-DD".
//
// Each entry needs:
//   theme — display name, title case (e.g. "Under the Sea")
//   row   — six comma-separated items:
//             • Items 1–5 are the five puzzle words.
//             • Item 6 is the final word (no asterisks).
//
// Asterisk rules:
//   • Write the word normally, then place * immediately after each
//     circled letter.  The * is stripped to get the answer.
//   • Exactly 6 asterisks total must appear across items 1–5.
//   • Bonus letters collected in word order (left-to-right within each
//     word) must be an anagram of the final word.
//   • Repeated letters are allowed everywhere.
//
// Example:
//   row: "MU*SSEL, OYSTER*, TRENC*H*, MARLI*N, SPON*GE, URCHIN"
//   MU*SSEL  → MUSSEL,  circled U  (index 1)
//   OYSTER*  → OYSTER,  circled R  (index 5)
//   TRENC*H* → TRENCH,  circled C (index 4) and H (index 5)
//   MARLI*N  → MARLIN,  circled I  (index 4)
//   SPON*GE  → SPONGE,  circled N  (index 3)
//   Bonus: U, R, C, H, I, N → URCHIN ✓
//
// Testing:
//   ?date=YYYY-MM-DD   preview any puzzle date without affecting progress
//   ?reset             clear saved progress for the active date
//
// WORD_LIST (wordlist.js) gates valid wrong guesses.
// Puzzle answers and the final word are always accepted even if absent
// from WORD_LIST — no need to duplicate them there.
// ---------------------------------------------------------------------------

const PUZZLE_ROWS = {
  "2026-06-08": {
  theme: "What's for Dessert?",
  row: "C*OOKI*E, GE*L*ATO, SUNDA*E, PASTR*Y, MOUSSE, ECLAIR"
  },
  "2026-06-07": {
  theme: "The Veggie Garden",
  row: "C*ELERY, GA*R*LIC, TO*MATO, POT*ATO, PEPPER*, CARROT"
  },
  "2026-06-06": {
  theme: "Outer Space",
  row: "R*OC*KET, GA*LAXY, METEOR*, PLANE*T*, COSMOS, CRATER"
  },
  "2026-06-05": {
  theme: "Hail Mary",
  row: "KIC*K*ER, HELMET*, PLA*YER, JERSE*Y, HUDDL*E, TACKLE"
  },
  "2026-06-04": {
  theme: "X Marks the Spot",
  row: "PAR*ROT, CA*NNON, ANCHO*R, IS*L*AND, PI*STOL, SAILOR"
  },
  "2026-06-03": {
  theme: "Once Upon a Time",
  row: "KNI*GHT, WIZAR*D, THR*ONE, CA*STLE, PR*IN*CE, DRAGON"
  },
  "2026-06-02": {
  theme: "Animal Kingdom",
  row: "JAGU*AR, RABBIT*, PAR*ROT, L*IZARD, MONKE*Y, TURTLE"
  },
  "2026-06-01": {
  theme: "Class is in Session",
  row: "CR*AYON, PE*NCIL, LES*SON, MA*RKER*, RE*CESS, ERASER"
  },
  "2026-05-31": {
  theme: "Airplane Mode",
  row: "WI*N*DOW, RUN*WAY, FLIG*HT, JE*TLAG, TICKE*T, ENGINE"
  },
  "2026-05-30": {
  theme: "Airplane Mode",
  row: "WI*N*DOW, RUN*WAY, FLIG*HT, JE*TLAG, TICKE*T, ENGINE"
  },
  "2026-05-26": {
  theme: "Breakfast",
  row: "C*EREAL, YO*GURT, WAF*F*LE, OME*LET, ORANGE*, COFFEE",
  },
  "2026-05-25": {
    theme: "Under the Sea",
    row: "TU*RTLE, OYSTER*, ANC*H*OR, SHRI*MP, SALMON*, URCHIN",
  },
  "2026-05-24": {
    theme: "Around the House",
    //         CLOSET[4]=E   FRIDGE[3]=D,[4]=G   CARPET[1]=A   PANTRY[2]=N   SHOWER[5]=R → GARDEN
    row:   "CLOSE*T, FRID*G*E, CA*RPET, PAN*TRY, SHOWER*, GARDEN",
  },
};

// ─── Row parser ───────────────────────────────────────────────────────────────

function parsePuzzleRow(date, theme, row) {
  const items = row.split(',').map(s => s.trim().toUpperCase());

  if (items.length !== 6) {
    console.warn(`[JUGGLE] Puzzle ${date}: row needs 6 comma-separated items, got ${items.length}`);
    return null;
  }

  const finalWord = items[5].replace(/\*/g, '');
  if (finalWord.length !== 6 || !/^[A-Z]{6}$/.test(finalWord)) {
    console.warn(`[JUGGLE] Puzzle ${date}: final word "${finalWord}" must be 6 alphabetic letters`);
    return null;
  }

  const words           = [];
  const allBonusLetters = [];

  for (let wi = 0; wi < 5; wi++) {
    const raw    = items[wi];
    const answer = raw.replace(/\*/g, '');

    if (answer.length !== 6 || !/^[A-Z]{6}$/.test(answer)) {
      console.warn(`[JUGGLE] Puzzle ${date}: word ${wi + 1} "${answer}" must be 6 alphabetic letters`);
      return null;
    }

    // Derive circled positions by scanning raw string for asterisks.
    // Each * marks the letter immediately preceding it.
    const bonusIndices = [];
    let answerPos = 0;
    for (let ci = 0; ci < raw.length; ci++) {
      if (raw[ci] === '*') {
        bonusIndices.push(answerPos - 1);
      } else {
        answerPos++;
      }
    }

    bonusIndices.forEach(idx => allBonusLetters.push(answer[idx]));

    const scrambled = deterministicScramble(answer, date + wi);
    words.push({ answer, scrambled, bonusIndices });
  }

  const totalAsterisks = items.slice(0, 5)
    .reduce((n, s) => n + (s.match(/\*/g) || []).length, 0);
  if (totalAsterisks !== 6) {
    console.warn(`[JUGGLE] Puzzle ${date}: expected 6 asterisks, found ${totalAsterisks}`);
  }

  if (sortLetters(allBonusLetters.join('')) !== sortLetters(finalWord)) {
    console.warn(
      `[JUGGLE] Puzzle ${date}: bonus letters "${allBonusLetters.join('')}" are not an anagram of "${finalWord}"`
    );
  }

  // ── Word display order ────────────────────────────────────────────────────
  // Deterministically reorder the five words so solving top-to-bottom does
  // not reveal the final answer's letter sequence.
  const wordDisplayPerm  = lcgPermutation(5, date + '\x00wordorder');
  const displayWords     = wordDisplayPerm.map(i => words[i]);

  // Bonus letters re-collected in the new display order.
  const displayBonusLetters = [];
  displayWords.forEach(w => w.bonusIndices.forEach(idx => displayBonusLetters.push(w.answer[idx])));

  // ── Slot assignment ───────────────────────────────────────────────────────
  // Map each bonus letter (in reveal order) to a fixed final-prompt slot such
  // that no 3 consecutive prompt slots spell a consecutive substring of the answer.
  const bonusSlotOrder = computeBonusSlotOrder(displayBonusLetters, finalWord, date);

  return { theme, words: displayWords, finalWord, bonusSlotOrder };
}

// ─── Seeded LCG helpers ───────────────────────────────────────────────────────

function lcgHash(seed) {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (Math.imul(31, h) + seed.charCodeAt(i)) | 0;
  return h;
}

// Returns a deterministic permutation of [0..n-1] via Fisher-Yates + LCG.
function lcgPermutation(n, seed) {
  let h = lcgHash(seed);
  const perm = Array.from({ length: n }, (_, i) => i);
  for (let i = n - 1; i > 0; i--) {
    h = (Math.imul(h, 1664525) + 1013904223) | 0;
    const j = Math.abs(h) % (i + 1);
    [perm[i], perm[j]] = [perm[j], perm[i]];
  }
  return perm;
}

// Assigns each bonus letter (in word-reveal order) to a fixed slot in the
// final-word prompt. Scores 120 seeded candidates and picks the one that best
// avoids consecutive answer substrings, answer-bigram runs, and correct-position
// placements — guaranteeing no 3 consecutive prompt slots spell part of the answer.
function computeBonusSlotOrder(bonusLetters, finalWord, seed) {
  let h = lcgHash(seed + '\x00slots');
  function next() { h = (Math.imul(h, 1664525) + 1013904223) | 0; return Math.abs(h); }

  function buildPrompt(perm) {
    const slots = Array(6);
    perm.forEach((slot, i) => { slots[slot] = bonusLetters[i]; });
    return slots;
  }

  function score(perm) {
    const s = buildPrompt(perm);
    let n = 0;
    for (let j = 0; j <= 3; j++) if (finalWord.includes(s[j] + s[j+1] + s[j+2])) n += 100;
    for (let j = 0; j <= 4; j++) if (finalWord.includes(s[j] + s[j+1]))            n += 8;
    for (let j = 0; j < 6;  j++) if (s[j] === finalWord[j])                        n += 3;
    return n;
  }

  const base = [0, 1, 2, 3, 4, 5];
  let best = base.slice(), bestScore = score(base);

  for (let attempt = 0; attempt < 120; attempt++) {
    const c = base.slice();
    for (let i = 5; i > 0; i--) { const j = next() % (i + 1); [c[i], c[j]] = [c[j], c[i]]; }
    const sc = score(c);
    if (sc < bestScore) { bestScore = sc; best = c.slice(); }
  }

  return best;
}

// ─── Deterministic scramble ───────────────────────────────────────────────────
// Uses a seeded LCG so the same date + word always produces the same scramble.

function deterministicScramble(word, seed) {
  const letters = word.split('');

  let h = 0;
  for (let i = 0; i < seed.length; i++) {
    h = (Math.imul(31, h) + seed.charCodeAt(i)) | 0;
  }

  // Fisher-Yates
  for (let i = letters.length - 1; i > 0; i--) {
    h = (Math.imul(h, 1664525) + 1013904223) | 0;
    const j = Math.abs(h) % (i + 1);
    [letters[i], letters[j]] = [letters[j], letters[i]];
  }

  // If shuffle produced the original, swap the first non-identical adjacent pair
  if (letters.join('') === word) {
    for (let i = 0; i < letters.length - 1; i++) {
      if (letters[i] !== letters[i + 1]) {
        [letters[i], letters[i + 1]] = [letters[i + 1], letters[i]];
        break;
      }
    }
  }

  // Break any consecutive bigrams that appear consecutively in the answer
  // read forwards OR backwards — either direction hints at the word.
  const answerBigrams = new Set();
  for (let i = 0; i < word.length - 1; i++) {
    answerBigrams.add(word[i] + word[i + 1]);   // forward
    answerBigrams.add(word[i + 1] + word[i]);   // reversed
  }

  for (let pass = 0; pass < 30; pass++) {
    let badIdx = -1;
    for (let i = 0; i < letters.length - 1; i++) {
      if (answerBigrams.has(letters[i] + letters[i + 1])) { badIdx = i; break; }
    }
    if (badIdx === -1) break; // no matching bigrams — done

    // Advance LCG and swap letters[badIdx+1] with a position that is neither
    // badIdx nor badIdx+1, guaranteeing the bigram at badIdx is broken.
    h = (Math.imul(h, 1664525) + 1013904223) | 0;
    const n         = letters.length;
    const swapWith  = ((Math.abs(h) % (n - 2)) + badIdx + 2) % n;
    [letters[badIdx + 1], letters[swapWith]] = [letters[swapWith], letters[badIdx + 1]];
  }

  return letters.join('');
}

// ─── Build PUZZLES and PUZZLE_ANSWERS ────────────────────────────────────────

function sortLetters(str) {
  return str.toUpperCase().split('').sort().join('');
}

const PUZZLES = {};
Object.entries(PUZZLE_ROWS).forEach(([date, { theme, row }]) => {
  const parsed = parsePuzzleRow(date, theme, row);
  if (parsed) PUZZLES[date] = parsed;
});

// All puzzle answers auto-accepted by isValidGuess(), even if absent from WORD_LIST.
const PUZZLE_ANSWERS = new Set();
Object.values(PUZZLES).forEach(p => {
  p.words.forEach(w => PUZZLE_ANSWERS.add(w.answer.toLowerCase()));
  PUZZLE_ANSWERS.add(p.finalWord.toLowerCase());
});

// ─── Validation (called from init in main.js) ─────────────────────────────────

function validatePuzzles() {
  Object.entries(PUZZLES).forEach(([date, puzzle]) => {
    const errors       = [];
    const bonusLetters = [];

    if (puzzle.words.length !== 5)
      errors.push(`Expected 5 words, got ${puzzle.words.length}`);

    puzzle.words.forEach((w, i) => {
      const tag = `Word ${i + 1} ("${w.answer}")`;
      if (w.answer.length !== 6)
        errors.push(`${tag}: must be 6 letters`);
      if (sortLetters(w.scrambled) !== sortLetters(w.answer))
        errors.push(`${tag}: scrambled "${w.scrambled}" doesn't match answer letters`);
      w.bonusIndices.forEach(idx => {
        if (idx < 0 || idx > 5) errors.push(`${tag}: bonusIndex ${idx} out of 0–5 range`);
        else bonusLetters.push(w.answer[idx]);
      });
    });

    if (bonusLetters.length !== 6)
      errors.push(`Total bonus letters is ${bonusLetters.length}, expected 6`);
    if (puzzle.finalWord.length !== 6)
      errors.push(`finalWord "${puzzle.finalWord}" must be 6 letters`);
    if (sortLetters(bonusLetters.join('')) !== sortLetters(puzzle.finalWord))
      errors.push(`Bonus letters "${bonusLetters.join('')}" ≠ anagram of finalWord "${puzzle.finalWord}"`);

    // Informational: puzzle answers still accepted even if not in WORD_LIST
    if (typeof WORD_LIST !== 'undefined') {
      const missing = puzzle.words
        .map(w => w.answer)
        .concat([puzzle.finalWord])
        .filter(w => !WORD_LIST.has(w.toLowerCase()));
      if (missing.length) {
        console.info(
          `[JUGGLE] Puzzle ${date}: not in WORD_LIST (auto-accepted anyway): ${missing.join(', ')}`
        );
      }
    }

    if (errors.length) {
      console.warn(`[JUGGLE] Puzzle ${date} errors:\n  · ${errors.join('\n  · ')}`);
    } else {
      console.log(`[JUGGLE] Puzzle ${date} ✓`);
    }
  });
}
