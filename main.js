// ---------------------------------------------------------------------------
// FEEDBACK_ENDPOINT
// Create a free account at formspree.io → New Project "Juggle" → New Form
// "Feedback" → copy the endpoint from the Integration tab.
// Looks like: https://formspree.io/f/xabcdefg
// Leave blank to disable feedback without breaking anything.
// ---------------------------------------------------------------------------
const FEEDBACK_ENDPOINT = 'https://formspree.io/f/xjgzagya';

// ---------------------------------------------------------------------------
// PUBLIC_GAME_URL
// Set this to your live URL once the game is deployed (e.g. GitHub Pages).
// Looks like: https://username.github.io/juggle
// Leave blank to use the current page origin + path automatically.
// ---------------------------------------------------------------------------
const PUBLIC_GAME_URL = 'https://playjuggle.github.io';

// ─── Daily color palette ──────────────────────────────────────────────────────
// Order maps to J U G G L E: pink, blue, orange, purple, yellow, green.
// E (index 5) = green = accent on day 0 (2026-05-25).
const PALETTE      = ['#F4A0BC','#A4C0E8','#F7B090','#C4B0E8','#F0DC8C','#A8D4B4'];
const PALETTE_DARK = ['#C84B70','#3A74C0','#D05A1A','#7B45C0','#B08000','#3A8C5A'];

// ─── Achievements ─────────────────────────────────────────────────────────────
// hidden: true means the unlock condition is not shown to the player when locked.
const ACHIEVEMENTS = [
  { id: 'flawless',   label: 'Flawless',   icon: '★',   color1: '#F47B55', color2: '#E06040', desc: 'No wrong guesses',  hidden: false },
  { id: 'lightning',  label: 'Lightning',  icon: '⚡',  color1: '#A08FD4', color2: '#8070B8', desc: 'Under 90 seconds',  hidden: false },
  { id: 'unbroken',   label: 'Unbroken',   icon: '📅',  color1: '#F4A0BC', color2: '#E080A0', desc: '5-day streak',      hidden: true  },
  { id: 'wordsmith',  label: 'Wordsmith',  icon: '✏️',  color1: '#A8C8B8', color2: '#80A898', desc: '2 bonus words',     hidden: true  },
  { id: 'hardboiled', label: 'Hardboiled', icon: '🥚',  color1: '#F7B090', color2: '#E0805A', desc: 'Hard mode finish',  hidden: true  },
  { id: 'nightowl',   label: 'Night Owl',  icon: '🌙',  color1: '#7090C0', color2: '#506490', desc: 'After midnight',    hidden: true  },
  { id: 'earlybird',  label: 'Early Bird', icon: '🌅',  color1: '#F0C060', color2: '#C89830', desc: 'Before 8am',        hidden: true  },
  { id: 'ironwill',   label: 'Iron Will',  icon: '💪',  color1: '#90A8B8', color2: '#607888', desc: '5+ wrong guesses',  hidden: true  },
  { id: 'veteran',    label: 'Veteran',    icon: '🏆',  color1: '#D4A840', color2: '#A87820', desc: '10 puzzles done',   hidden: true  },
];

function hexToRgb(hex) {
  return [parseInt(hex.slice(1,3),16), parseInt(hex.slice(3,5),16), parseInt(hex.slice(5,7),16)];
}

// ─── Date helpers ─────────────────────────────────────────────────────────────

// Actual browser-local calendar date — never overridden by URL params.
// Used for streak / visit tracking.
function realTodayKey() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

// Active puzzle date — respects ?date=YYYY-MM-DD for previewing future puzzles.
function todayKey() {
  const p = new URLSearchParams(window.location.search).get('date');
  if (p && /^\d{4}-\d{2}-\d{2}$/.test(p)) return p;
  return realTodayKey();
}

// Human-readable display of the active puzzle date (local calendar).
function todayDisplayDate() {
  const [y, m, d] = todayKey().split('-').map(Number);
  return new Date(y, m - 1, d).toLocaleDateString('en-US', {
    month: 'long', day: 'numeric', year: 'numeric',
  });
}

// ─── Color theme ──────────────────────────────────────────────────────────────

// Calibrated so 2026-05-25 → offset 1 (E = pink accent).
function getDayOffset() {
  return (Math.floor(Date.parse(todayKey()) / 86400000) + 6) % 6;
}

function getDailyColors() {
  const o = getDayOffset();
  return PALETTE.map((_, i) => PALETTE[(o + i) % 6]);
}

function getDailyDarkColors() {
  const o = getDayOffset();
  return PALETTE_DARK.map((_, i) => PALETTE_DARK[(o + i) % 6]);
}

function applyDailyTheme() {
  const colors     = getDailyColors();
  const darkColors = getDailyDarkColors();
  const accent     = colors[5];
  const accentDark = darkColors[5];
  const [r, g, b]  = hexToRgb(accent);

  const root = document.documentElement;
  root.style.setProperty('--accent',       accent);
  root.style.setProperty('--accent-dark',  accentDark);
  root.style.setProperty('--accent-alpha',  `rgba(${r},${g},${b},0.28)`);
  root.style.setProperty('--accent-solved', `rgba(${r},${g},${b},0.52)`);

  document.querySelectorAll('.logo-l').forEach(el => {
    el.style.color = colors[parseInt(el.dataset.li)];
  });

  applyFavicon(accent);
}

function applyFavicon(color) {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><circle cx="16" cy="13" r="9" fill="none" stroke="${color}" stroke-width="3.5"/><rect x="4" y="27" width="24" height="3" rx="1.5" fill="#111"/></svg>`;
  const url  = 'data:image/svg+xml,' + encodeURIComponent(svg);
  const link = document.getElementById('favicon') || document.querySelector("link[rel~='icon']");
  if (link) link.href = url;
}

// ─── Timer ────────────────────────────────────────────────────────────────────

const Timer = {
  elapsed:   0,
  startTime: null,
  active:    false,
  hidden:    false,
  _iv:       null,

  start() {
    this.elapsed   = 0;
    this.startTime = Date.now();
    this.active    = true;
    this._iv = setInterval(() => this._render(), 250);
    this._render();
  },

  pause() {
    if (!this.active) return;
    this.elapsed += Date.now() - this.startTime;
    clearInterval(this._iv);
    this.active = false;
    this._render();
  },

  resume() {
    if (this.active) return;
    this.startTime = Date.now();
    this.active    = true;
    this._iv = setInterval(() => this._render(), 250);
    this._render();
  },

  resumeFrom(ms) {
    this.elapsed = ms;
    this.resume();
  },

  _current() {
    return this.elapsed + (this.active ? Date.now() - this.startTime : 0);
  },

  format() {
    const s = Math.floor(this._current() / 1000);
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  },

  _render() {
    const el = document.getElementById('timer-display');
    if (!el) return;
    el.textContent       = this.hidden ? '—:—' : this.format();
    el.style.opacity     = this.hidden ? '0.4' : '';
    el.dataset.tooltip   = this.hidden ? 'Show timer' : 'Hide timer';
  },
};

// ─── How-to-play animation ────────────────────────────────────────────────────
// Animates the PURPLE example in the How to Play modal.
// Cycle: 5 s initial delay → letters appear 480 ms apart → 8 s hold → fade out
// → 2 s pause → repeat (no initial delay on subsequent cycles).

const HOW_ANIMATION = {
  _timers:  [],
  _running: false,

  start() {
    this.clear();
    this._running = true;
    this._timers.push(setTimeout(() => this._cycle(), 5000));
  },

  _cycle() {
    if (!this._running) return;
    const slots   = document.querySelectorAll('.how-example-slots .how-slot');
    const letters = ['P', 'U', 'R', 'P', 'L', 'E'];

    slots.forEach(s => { s.textContent = ''; s.style.color = ''; s.style.transition = ''; });

    letters.forEach((ch, i) => {
      this._timers.push(setTimeout(() => {
        if (!this._running) return;
        slots[i].textContent = ch;
      }, i * 480));
    });

    // fade out letter color only — borders (border-bottom) stay visible
    this._timers.push(setTimeout(() => {
      if (!this._running) return;
      slots.forEach(s => { s.style.transition = 'color 0.6s'; s.style.color = 'transparent'; });

      this._timers.push(setTimeout(() => {
        if (!this._running) return;
        slots.forEach(s => { s.style.transition = ''; s.textContent = ''; s.style.color = ''; });
        this._cycle();
      }, 600 + 2000));
    }, (letters.length - 1) * 480 + 8000));
  },

  clear() {
    this._running = false;
    this._timers.forEach(t => clearTimeout(t));
    this._timers = [];
    document.querySelectorAll('.how-example-slots .how-slot').forEach(s => {
      s.textContent = ''; s.style.color = ''; s.style.transition = '';
    });
  },
};

// ─── State ────────────────────────────────────────────────────────────────────

const S = {
  puzzle:          null,
  words:           [],
  final:           null,
  activeWord:      0,
  cursor:          0,
  hardMode:        false,
  gameStarted:     false,
  wrongGuesses:    0,
  invalidAttempts: 0,
  hintsUsed:       0,
};

let confettiFired   = false;
let completionCache = null;

// ─── Persistence ──────────────────────────────────────────────────────────────

function puzzleStorageKey() {
  return `juggle_puzzle_${todayKey()}`;
}

function saveSettings() {
  localStorage.setItem('juggle_settings', JSON.stringify({
    hardMode:    S.hardMode,
    timerHidden: Timer.hidden,
  }));
}

function loadSettings() {
  try {
    return JSON.parse(localStorage.getItem('juggle_settings') || '{}');
  } catch { return {}; }
}

function saveState() {
  const data = {
    words: S.words.map(w => ({
      confirmed: w.confirmed,
      guess:     w.guess,
      solved:    w.solved,
    })),
    final: {
      bonusLetters: S.final.bonusLetters,
      confirmed:    S.final.confirmed,
      guess:        S.final.guess,
      solved:       S.final.solved,
    },
    activeWord: S.activeWord,
    cursor:     S.cursor,
    hardMode:        S.hardMode,
    wrongGuesses:    S.wrongGuesses,
    invalidAttempts: S.invalidAttempts,
    hintsUsed:       S.hintsUsed,
    gameStarted:     S.gameStarted,
    timerMs:        Timer._current(),
  };
  try {
    localStorage.setItem(puzzleStorageKey(), JSON.stringify(data));
  } catch (_) {}
}

function loadState() {
  try {
    const raw = localStorage.getItem(puzzleStorageKey());
    if (!raw) return false;
    const d = JSON.parse(raw);

    d.words.forEach((w, i) => {
      S.words[i].confirmed = w.confirmed;
      S.words[i].guess     = w.guess;
      S.words[i].solved    = w.solved;
    });
    S.final.bonusLetters = d.final.bonusLetters;
    S.final.confirmed    = d.final.confirmed;
    S.final.guess        = d.final.guess;
    S.final.solved       = d.final.solved;
    S.activeWord = d.activeWord;
    S.cursor     = d.cursor;
    S.hardMode           = d.hardMode          ?? false;
    S.wrongGuesses       = d.wrongGuesses       ?? 0;
    S.invalidAttempts    = d.invalidAttempts    ?? 0;
    S.hintsUsed          = d.hintsUsed          ?? 0;
    S.gameStarted        = d.gameStarted        ?? false;
    Timer.elapsed        = d.timerMs      ?? 0;
    return true;
  } catch (e) {
    console.warn('[JUGGLE] Could not load saved state:', e);
    return false;
  }
}

// ─── Streak / visits ──────────────────────────────────────────────────────────
// Always use real local date (not ?date= override) for streaks.

function recordVisit() {
  try {
    const visits = JSON.parse(localStorage.getItem('juggle_visits') || '[]');
    const today  = realTodayKey();
    if (!visits.includes(today)) visits.push(today);
    localStorage.setItem('juggle_visits', JSON.stringify(visits));
    return visits.length;
  } catch { return 1; }
}

function getStreak() {
  try {
    const visits  = JSON.parse(localStorage.getItem('juggle_visits') || '[]').sort();
    let streak    = 0;
    const check   = new Date();
    check.setHours(12, 0, 0, 0);
    for (let i = visits.length - 1; i >= 0; i--) {
      const y = check.getFullYear();
      const m = String(check.getMonth() + 1).padStart(2, '0');
      const d = String(check.getDate()).padStart(2, '0');
      if (visits[i] === `${y}-${m}-${d}`) {
        streak++;
        check.setDate(check.getDate() - 1);
      } else {
        break;
      }
    }
    return streak;
  } catch { return 0; }
}

function updateStreakBadge() {
  const streak = getStreak();
  const badge  = document.getElementById('streak-badge');
  if (!badge) return;

  if (streak < 1) {
    badge.innerHTML = '';
    badge.classList.add('hidden');
    return;
  }

  const accent = getComputedStyle(document.documentElement).getPropertyValue('--accent').trim() || '#F4A0BC';
  const r      = 6;
  const circ   = (2 * Math.PI * r).toFixed(1);
  const fill   = Math.min(streak / 7, 1);
  const offset = (parseFloat(circ) * (1 - fill)).toFixed(1);

  badge.innerHTML = `
    <div style="display:flex;align-items:center;gap:3px;color:${accent};">
      <svg width="16" height="16" viewBox="0 0 16 16" style="flex-shrink:0">
        <circle cx="8" cy="8" r="${r}" fill="none" stroke="${accent}" stroke-width="2" opacity="0.18"/>
        <circle cx="8" cy="8" r="${r}" fill="none" stroke="${accent}" stroke-width="2"
          stroke-dasharray="${circ}" stroke-dashoffset="${offset}"
          stroke-linecap="round" transform="rotate(-90 8 8)"/>
      </svg>
      <span style="font-size:0.78rem;font-weight:800;line-height:1;">${streak}</span>
    </div>`;
  badge.classList.remove('hidden');
}

// ─── Achievement persistence ──────────────────────────────────────────────────

function loadAchievements() {
  try { return new Set(JSON.parse(localStorage.getItem('juggle_achievements') || '[]')); }
  catch { return new Set(); }
}

function saveAchievements(unlocked) {
  try { localStorage.setItem('juggle_achievements', JSON.stringify([...unlocked])); }
  catch {}
}

function incrementCompletions() {
  try {
    const completions = JSON.parse(localStorage.getItem('juggle_completions') || '[]');
    const date = todayKey();
    if (!completions.includes(date)) completions.push(date);
    localStorage.setItem('juggle_completions', JSON.stringify(completions));
    return completions.length;
  } catch { return 1; }
}

function checkAndUnlockAchievements() {
  if (completionCache) return completionCache;

  const unlocked          = loadAchievements();
  const newlyUnlocked     = [];
  const earnedThisSession = [];
  const completions       = incrementCompletions();
  const streak            = getStreak();
  const hours             = new Date().getHours();

  const check = (id, condition) => {
    if (!condition) return;
    earnedThisSession.push(id);
    if (!unlocked.has(id)) { unlocked.add(id); newlyUnlocked.push(id); }
  };

  check('flawless',   S.wrongGuesses === 0 && S.invalidAttempts === 0 && S.hintsUsed === 0);
  check('lightning',  Timer.elapsed <= 90000);
  check('unbroken',   streak >= 5);
  check('wordsmith',  S.wrongGuesses >= 2);
  check('hardboiled', S.hardMode);
  check('nightowl',   hours < 5);
  check('earlybird',  hours >= 5 && hours < 8);
  check('ironwill',   S.wrongGuesses >= 5);
  check('veteran',    completions >= 10);

  saveAchievements(unlocked);
  completionCache = { earnedThisSession, newlyUnlocked };
  return completionCache;
}

// ─── Bootstrap ────────────────────────────────────────────────────────────────

function getActivePuzzle() {
  const today = todayKey();
  if (PUZZLES[today]) return PUZZLES[today];
  // Fall back to most recent puzzle on or before today — never a future puzzle.
  const past = Object.keys(PUZZLES).filter(d => d <= today).sort();
  if (past.length > 0) return PUZZLES[past.at(-1)];
  return null;
}

function getShareUrl() {
  if (PUBLIC_GAME_URL) return PUBLIC_GAME_URL;
  if (window.location.protocol === 'file:') return '';
  return window.location.origin + window.location.pathname;
}

function init() {
  validatePuzzles();

  if (new URLSearchParams(window.location.search).has('reset')) {
    localStorage.removeItem(puzzleStorageKey());
  }

  S.puzzle = getActivePuzzle();

  if (!S.puzzle) {
    document.body.innerHTML = `
      <div style="display:flex;height:100vh;align-items:center;justify-content:center;
                  font-family:'Figtree',sans-serif;text-align:center;padding:24px;">
        <p style="color:#777;font-size:1rem;line-height:1.6;">
          No puzzle available yet.<br>Check back soon!
        </p>
      </div>`;
    return;
  }

  S.words = S.puzzle.words.map(w => ({
    answer:       w.answer,
    scrambled:    w.scrambled,
    bonusIndices: w.bonusIndices,
    confirmed:    Array(6).fill(false),
    guess:        Array(6).fill(null),
    solved:       false,
  }));

  S.final = {
    answer:       S.puzzle.finalWord,
    bonusLetters: Array(6).fill(null),
    confirmed:    Array(6).fill(false),
    guess:        Array(6).fill(null),
    solved:       false,
  };

  applyDailyTheme();

  const settings = loadSettings();
  Timer.hidden = settings.timerHidden ?? false;

  document.getElementById('theme-label').textContent = S.puzzle.theme;
  document.getElementById('date-label').textContent  = todayDisplayDate();

  buildBoard();
  recordVisit();       // must happen before updateStreakBadge so today counts
  updateStreakBadge();

  const hasSave = loadState();

  if (hasSave && S.gameStarted) {
    hidePregame();
    restoreBoard();
    Timer._render();
    if (S.final.solved) {
      renderBank();
      showAlreadySolvedScreen();
    } else {
      Timer.resumeFrom(Timer.elapsed);
    }
  } else {
    showPregame(hasSave);
  }

  bindGlobalEvents();
}

// ─── Pre-game screen ──────────────────────────────────────────────────────────

function showPregame(hasSave) {
  document.getElementById('pregame').classList.remove('hidden');
  document.getElementById('theme-title').textContent = S.puzzle.theme;
  document.getElementById('pregame-date').textContent = todayDisplayDate();

  const check      = document.getElementById('hard-check');
  check.checked    = S.hardMode;
  const timerCheck = document.getElementById('timer-hide-check');
  timerCheck.checked = Timer.hidden;

  try {
    const visits = JSON.parse(localStorage.getItem('juggle_visits') || '[]');
    if (visits.length <= 3) setTimeout(() => openHowModal(), 300);
  } catch {}

  document.getElementById('ready-btn').addEventListener('click', onReady);
  document.getElementById('how-btn-pre').addEventListener('click', () => openHowModal());

  check.addEventListener('change', e => {
    S.hardMode = e.target.checked;
    saveSettings();
  });
  timerCheck.addEventListener('change', e => {
    Timer.hidden = e.target.checked;
    Timer._render();
    saveSettings();
  });
}

function hidePregame() {
  document.getElementById('pregame').classList.add('hidden');
}

function onReady() {
  S.gameStarted = true;
  S.hardMode    = document.getElementById('hard-check').checked;
  Timer.hidden  = document.getElementById('timer-hide-check').checked;
  saveSettings();
  hidePregame();
  applyHardMode();
  setActive(0);
  Timer.start();
  saveState();
}

// ─── Already-solved screen ───────────────────────────────────────────────────

function showAlreadySolvedScreen() {
  const overlay = document.createElement('div');
  overlay.id = 'already-solved';
  overlay.style.cssText = 'position:fixed;inset:0;background:var(--bg);display:flex;align-items:center;justify-content:center;z-index:200;';

  const colors   = getDailyColors();
  const logoHTML = 'JUGGLE'.split('').map((ch, i) =>
    `<span class="logo-l${i === 5 ? ' logo-circle' : ''}" data-li="${i}" style="color:${colors[i]}">${ch}</span>`
  ).join('');

  overlay.innerHTML = `
    <div style="text-align:center;padding:40px 24px;max-width:360px;width:100%;">
      <div style="font-size:2.4rem;font-weight:800;letter-spacing:0.16em;display:inline-flex;align-items:center;margin-bottom:28px;">${logoHTML}</div>
      <p style="font-size:1.05rem;font-weight:700;color:var(--black);margin-bottom:6px;">Today's puzzle has been solved.</p>
      <p style="font-size:0.85rem;color:var(--grey-dk);margin-bottom:32px;">Check back tomorrow!</p>
      <button id="as-results-btn" style="display:block;width:100%;padding:14px;background:var(--accent);color:var(--black);font-family:inherit;font-size:0.95rem;font-weight:800;letter-spacing:0.18em;border:none;border-radius:4px;cursor:pointer;margin-bottom:12px;">See Results</button>
      <button id="as-dismiss-btn" style="background:none;border:none;font-family:inherit;font-size:0.78rem;color:var(--grey-dk);text-decoration:underline;cursor:pointer;">View Puzzle</button>
    </div>
  `;
  document.body.appendChild(overlay);

  overlay.querySelector('#as-results-btn').addEventListener('click', () => {
    overlay.remove();
    showCompletion();
  });
  overlay.querySelector('#as-dismiss-btn').addEventListener('click', () => overlay.remove());
}

// ─── Hard mode ────────────────────────────────────────────────────────────────

function applyHardMode() {
  if (!S.hardMode) return;
  for (let i = 0; i < 5; i++) {
    const row = document.getElementById(`row-${i}`);
    if (!S.words[i].solved && i !== S.activeWord) row.classList.add('hard-locked');
  }
}

function unlockHardRow(idx) {
  document.getElementById(`row-${idx}`)?.classList.remove('hard-locked');
}

function isHardLocked(idx) {
  if (!S.hardMode || idx === 5) return false;
  return !S.words[idx].solved && idx !== S.activeWord;
}

// ─── Board construction ───────────────────────────────────────────────────────

function buildBoard() {
  const board = document.getElementById('board');
  board.innerHTML = '';
  for (let i = 0; i < 5; i++) board.appendChild(makePrimaryRow(i));
  board.appendChild(makeFinalRow());
}

function makePrimaryRow(idx) {
  const w = S.words[idx];

  const row = document.createElement('div');
  row.className = 'word-row';
  row.id = `row-${idx}`;

  const prompt = document.createElement('div');
  prompt.className = 'prompt';
  prompt.textContent = w.scrambled.split('').join(' · ');

  const slots = document.createElement('div');
  slots.className = 'slots';
  slots.id = `slots-${idx}`;
  for (let p = 0; p < 6; p++) {
    const slot = document.createElement('div');
    slot.className = 'slot' + (w.bonusIndices.includes(p) ? ' circled' : '');
    slot.dataset.word = idx;
    slot.dataset.pos  = p;
    slot.addEventListener('click', () => onSlotClick(idx, p));
    slots.appendChild(slot);
  }

  row.appendChild(prompt);
  row.appendChild(slots);
  row.addEventListener('click', e => {
    if (!e.target.closest('.slot')) selectWord(idx);
  });
  return row;
}

function makeFinalRow() {
  const row = document.createElement('div');
  row.className = 'word-row final-row';
  row.id = 'row-5';

  const prompt = document.createElement('div');
  prompt.className = 'prompt';
  prompt.id = 'final-prompt';
  prompt.innerHTML = finalPromptHTML(Array(6).fill(null));

  const slots = document.createElement('div');
  slots.className = 'slots';
  slots.id = 'slots-5';
  for (let p = 0; p < 6; p++) {
    const slot = document.createElement('div');
    slot.className = 'slot locked';
    slot.dataset.word = 5;
    slot.dataset.pos  = p;
    slot.addEventListener('click', () => {
      if (!slot.classList.contains('locked')) onSlotClick(5, p);
    });
    slots.appendChild(slot);
  }

  row.appendChild(prompt);
  row.appendChild(slots);
  row.addEventListener('click', e => {
    if (!e.target.closest('.slot') && allPrimaryDone()) selectWord(5);
  });
  return row;
}

// ─── Board restore ────────────────────────────────────────────────────────────

function restoreBoard() {
  S.words.forEach((w, i) => {
    if (w.solved) document.getElementById(`row-${i}`).classList.add('solved');
  });

  renderFinalPrompt();

  if (allPrimaryDone()) {
    document.querySelectorAll('#slots-5 .slot').forEach(s => s.classList.remove('locked'));
  }

  if (S.final.solved) {
    document.getElementById('row-5').classList.add('solved');
  }

  if (S.hardMode) {
    for (let i = 0; i < 5; i++) {
      if (!S.words[i].solved && i !== S.activeWord) {
        document.getElementById(`row-${i}`).classList.add('hard-locked');
      }
    }
  }

  document.querySelectorAll('.word-row').forEach(r => r.classList.remove('active'));
  const activeWs = S.activeWord === 5 ? S.final : S.words[S.activeWord];
  if (!activeWs.solved) {
    document.getElementById(`row-${S.activeWord}`)?.classList.add('active');
  }

  renderAllSlots();
  renderBank();
}

// ─── Final word prompt ────────────────────────────────────────────────────────
// Uses spans so unrevealed ? can be styled differently from revealed letters.

function finalPromptHTML(bonusLetters) {
  return bonusLetters
    .map(l => l
      ? `<span class="fp-letter">${l}</span>`
      : `<span class="fp-unknown">?</span>`)
    .join('<span class="fp-sep"> · </span>');
}

function renderFinalPrompt() {
  const el = document.getElementById('final-prompt');
  if (!el) return;
  el.innerHTML = finalPromptHTML(S.final.bonusLetters);
}

// ─── Slot rendering ───────────────────────────────────────────────────────────

function renderSlots(wordIdx) {
  const ws       = wordIdx === 5 ? S.final : S.words[wordIdx];
  const isActive = S.activeWord === wordIdx;
  document.getElementById(`slots-${wordIdx}`).querySelectorAll('.slot').forEach((slot, p) => {
    slot.textContent = ws.guess[p] ?? '';
    slot.classList.toggle('filled',      ws.guess[p] !== null);
    slot.classList.toggle('confirmed',   ws.confirmed[p]);
    slot.classList.toggle('cursor-here', isActive && S.cursor === p);
  });
}

function renderAllSlots() {
  for (let i = 0; i < 6; i++) renderSlots(i);
}

// ─── Hint ─────────────────────────────────────────────────────────────────────

let _hintTimer = null;

function resetHintTimer() {
  clearTimeout(_hintTimer);
  _hintTimer = null;
  const btn = document.getElementById('hint-btn');
  if (btn) btn.classList.add('hidden');
  if (!S.gameStarted || S.final.solved) return;
  const ws = S.activeWord === 5 ? S.final : S.words[S.activeWord];
  if (!ws || ws.solved) return;
  _hintTimer = setTimeout(() => {
    const b = document.getElementById('hint-btn');
    if (b) b.classList.remove('hidden');
  }, 5000);
}

function giveHint() {
  const ws = S.activeWord === 5 ? S.final : S.words[S.activeWord];
  if (!ws || ws.solved) return;
  let idx = ws.guess.findIndex((g, i) => !ws.confirmed[i] && g === null);
  if (idx === -1) idx = ws.guess.findIndex((g, i) => !ws.confirmed[i] && g !== ws.answer[i]);
  if (idx === -1) return;
  ws.guess[idx]     = ws.answer[idx];
  ws.confirmed[idx] = true;
  S.cursor = firstOpenSlot(ws);
  S.hintsUsed++;
  renderSlots(S.activeWord);
  renderBank();
  saveState();
}

// ─── Letter bank ──────────────────────────────────────────────────────────────
// Duplicate-letter safe: tracks placement counts per letter rather than
// assuming each letter appears only once.

function renderBank() {
  if (S.final.solved) { renderJuggleTiles(); return; }
  resetHintTimer();

  const bank    = document.getElementById('bank');
  bank.innerHTML = '';

  const isFinal = S.activeWord === 5;
  const ws      = isFinal ? S.final : S.words[S.activeWord];

  // Build the full letter list in fixed display order, tagging each as
  // confirmed (hint-placed) or available. Confirmed tiles stay in place
  // greyed-out so the bank never shifts.
  const confirmedRem = ws.answer.split('').filter((_, i) => ws.confirmed[i]);
  const allLetters   = isFinal
    ? S.final.bonusLetters.filter(Boolean)
    : ws.scrambled.split('');

  const letterStates = allLetters.map(ch => {
    const ci = confirmedRem.indexOf(ch);
    if (ci !== -1) { confirmedRem.splice(ci, 1); return { ch, confirmed: true }; }
    return { ch, confirmed: false };
  });

  // Count letters placed at non-cursor, non-confirmed positions.
  const placedElsewhere = {};
  ws.guess.forEach((g, i) => {
    if (g !== null && !ws.confirmed[i] && i !== S.cursor) {
      placedElsewhere[g] = (placedElsewhere[g] || 0) + 1;
    }
  });

  const cursorLetter   = ws.guess[S.cursor];
  const renderedPlaced = {};
  let   cursorShown    = false;

  letterStates.forEach(({ ch, confirmed }) => {
    renderedPlaced[ch] = renderedPlaced[ch] || 0;

    const tile = document.createElement('div');
    tile.className   = 'tile';
    tile.textContent = ch;

    if (confirmed) {
      tile.classList.add('tile-confirmed');
    } else if (!cursorShown && ch === cursorLetter) {
      tile.classList.add('tile-at-cursor');
      cursorShown = true;
    } else if (renderedPlaced[ch] < (placedElsewhere[ch] || 0)) {
      tile.classList.add('tile-placed');
      tile.addEventListener('click', () => placeTile(ch));
      renderedPlaced[ch]++;
    } else {
      tile.classList.add('tile-active');
      tile.addEventListener('click', () => placeTile(ch));
    }

    bank.appendChild(tile);
  });

  // Shuffle button — only when there are 2+ unconfirmed letters available.
  const availCount = letterStates.filter(s => !s.confirmed).length;
  if (availCount > 1) {
    const shuffleBtn = document.createElement('button');
    shuffleBtn.className = 'shuffle-btn';
    shuffleBtn.setAttribute('aria-label', 'Shuffle letters');
    shuffleBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 3 21 3 21 8"/><line x1="4" y1="20" x2="21" y2="3"/><polyline points="21 16 21 21 16 21"/><line x1="4" y1="4" x2="21" y2="21"/></svg>`;
    shuffleBtn.addEventListener('click', shuffleBank);
    bank.appendChild(shuffleBtn);
  }

  // Backspace button — always visible; faded when nothing to delete.
  const hasPlaced = ws.guess.some((g, i) => g !== null && !ws.confirmed[i]);
  const bkspBtn = document.createElement('button');
  bkspBtn.className = 'backspace-btn' + (hasPlaced ? '' : ' backspace-btn--empty');
  bkspBtn.setAttribute('aria-label', 'Backspace');
  bkspBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 4H8l-7 8 7 8h13a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z"/><line x1="18" y1="9" x2="12" y2="15"/><line x1="12" y1="9" x2="18" y2="15"/></svg>`;
  if (hasPlaced) bkspBtn.addEventListener('click', doBackspace);
  bank.appendChild(bkspBtn);

  updateSubmit();
}

function shuffleBank() {
  const isFinal = S.activeWord === 5;
  const ws      = isFinal ? S.final : S.words[S.activeWord];
  if (ws.solved) return;

  if (isFinal) {
    const arr = S.final.bonusLetters.slice();
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    if (arr.join('') === S.final.bonusLetters.join('')) {
      for (let i = 0; i < arr.length - 1; i++) {
        if (arr[i] !== arr[i + 1]) { [arr[i], arr[i + 1]] = [arr[i + 1], arr[i]]; break; }
      }
    }
    S.final.bonusLetters = arr;
    renderFinalPrompt();
  } else {
    const letters = ws.scrambled.split('');
    for (let i = letters.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [letters[i], letters[j]] = [letters[j], letters[i]];
    }
    if (letters.join('') === ws.scrambled) {
      for (let i = 0; i < letters.length - 1; i++) {
        if (letters[i] !== letters[i + 1]) { [letters[i], letters[i + 1]] = [letters[i + 1], letters[i]]; break; }
      }
    }
    ws.scrambled = letters.join('');
    const promptEl = document.querySelector(`#row-${S.activeWord} .prompt`);
    if (promptEl) promptEl.textContent = ws.scrambled.split('').join(' · ');
  }

  renderBank();
  saveState();
}

function doBackspace() {
  const ws = S.activeWord === 5 ? S.final : S.words[S.activeWord];
  if (ws.solved) return;
  if (ws.guess[S.cursor] !== null && !ws.confirmed[S.cursor]) {
    ws.guess[S.cursor] = null;
  } else {
    let prev = S.cursor - 1;
    while (prev >= 0 && ws.confirmed[prev]) prev--;
    if (prev >= 0) { ws.guess[prev] = null; S.cursor = prev; }
  }
  renderSlots(S.activeWord);
  renderBank();
  saveState();
}

function renderJuggleTiles() {
  clearTimeout(_hintTimer);
  _hintTimer = null;
  const hintBtn = document.getElementById('hint-btn');
  if (hintBtn) hintBtn.classList.add('hidden');

  const bank = document.getElementById('bank');
  bank.innerHTML = '';
  const colors = getDailyColors();
  'JUGGLE'.split('').forEach((ch, i) => {
    const tile = document.createElement('div');
    tile.className  = 'tile tile-juggle';
    if (i === 5) tile.classList.add('tile-juggle-e');
    tile.textContent = ch;
    tile.style.color = colors[i];
    bank.appendChild(tile);
  });
  const btn = document.getElementById('submit-btn');
  if (btn) btn.classList.add('hidden');
  const vr = document.getElementById('view-results-btn');
  if (vr) vr.classList.remove('hidden');
}

// ─── Tile placement ───────────────────────────────────────────────────────────
// Handles duplicate letters: only displaces an existing placement if all
// available copies of the letter are already on the board.

function availableCount(letter) {
  if (S.activeWord === 5) {
    const total     = S.final.bonusLetters.filter(ch => ch === letter).length;
    const confirmed = S.final.answer.split('').filter((ch, i) => ch === letter && S.final.confirmed[i]).length;
    return total - confirmed;
  }
  const ws = S.words[S.activeWord];
  return ws.answer.split('').filter((ch, i) => ch === letter && !ws.confirmed[i]).length;
}

function placeTile(letter) {
  const ws = S.activeWord === 5 ? S.final : S.words[S.activeWord];
  if (ws.solved) return;

  if (letter === null) {
    ws.guess[S.cursor] = null;
  } else {
    const avail          = availableCount(letter);
    const placedElsewhere = ws.guess.filter(
      (g, idx) => g === letter && idx !== S.cursor && !ws.confirmed[idx]
    ).length;

    if (placedElsewhere >= avail) {
      // All copies already on board — move one to make room at cursor.
      const clearAt = ws.guess.findIndex(
        (g, idx) => g === letter && idx !== S.cursor && !ws.confirmed[idx]
      );
      if (clearAt !== -1) ws.guess[clearAt] = null;
    }

    ws.guess[S.cursor] = letter;
  }

  advanceCursor();
  renderSlots(S.activeWord);
  renderBank();
  saveState();
}

// ─── Cursor ───────────────────────────────────────────────────────────────────

function firstOpenSlot(ws) {
  const i = ws.confirmed.findIndex(c => !c);
  return i === -1 ? 0 : i;
}

function firstBlankSlot(ws) {
  const i = ws.guess.findIndex((g, j) => g === null && !ws.confirmed[j]);
  return i === -1 ? firstOpenSlot(ws) : i;
}

function advanceCursor() {
  const ws = S.activeWord === 5 ? S.final : S.words[S.activeWord];
  let next = S.cursor + 1;
  while (next < 6 && (ws.confirmed[next] || ws.guess[next] !== null)) next++;
  if (next < 6) S.cursor = next;
}

function moveCursorLR(dir) {
  const ws = S.activeWord === 5 ? S.final : S.words[S.activeWord];
  let pos  = S.cursor + dir;
  while (pos >= 0 && pos < 6 && ws.confirmed[pos]) pos += dir;
  if (pos >= 0 && pos < 6) {
    S.cursor = pos;
    renderSlots(S.activeWord);
    renderBank();
  }
}

// ─── Word selection ───────────────────────────────────────────────────────────

function selectWordAt(idx, preferredCursor) {
  if (idx === 5 && !allPrimaryDone()) return;
  if (isHardLocked(idx)) return;
  const ws = idx === 5 ? S.final : S.words[idx];
  if (ws.solved) return;

  S.cursor = (preferredCursor !== undefined && !ws.confirmed[preferredCursor])
    ? preferredCursor
    : firstOpenSlot(ws);

  document.querySelectorAll('.word-row').forEach(r => r.classList.remove('active'));
  S.activeWord = idx;
  document.getElementById(`row-${idx}`).classList.add('active');
  renderAllSlots();
  renderBank();
}

function selectWord(idx)  { selectWordAt(idx); }
function setActive(idx)   { selectWord(idx); }

function allPrimaryDone() { return S.words.every(w => w.solved); }
function nextUnsolved()   { return S.words.findIndex(w => !w.solved); }

// ─── Slot click ───────────────────────────────────────────────────────────────

function onSlotClick(wordIdx, pos) {
  if (!S.gameStarted) return;
  const ws = wordIdx === 5 ? S.final : S.words[wordIdx];
  if (ws.solved || ws.confirmed[pos]) return;
  if (wordIdx === 5 && !allPrimaryDone()) return;
  if (isHardLocked(wordIdx)) return;

  if (S.activeWord === wordIdx) {
    if (S.cursor === pos && ws.guess[pos] !== null && !ws.confirmed[pos]) {
      ws.guess[pos] = null;
      renderSlots(wordIdx);
      renderBank();
      saveState();
    } else {
      S.cursor = pos;
      renderSlots(wordIdx);
      renderBank();
    }
  } else {
    selectWordAt(wordIdx, pos);
  }
}

// ─── Keyboard ─────────────────────────────────────────────────────────────────

function bindGlobalEvents() {
  document.addEventListener('keydown', onKey);

  document.addEventListener('visibilitychange', () => {
    if (!S.gameStarted || S.final.solved) return;
    document.hidden ? Timer.pause() : Timer.resume();
  });

  document.getElementById('how-btn-game').addEventListener('click', () => openHowModal());
  document.getElementById('how-close').addEventListener('click', closeHowModal);
  document.getElementById('how-backdrop').addEventListener('click', closeHowModal);
  document.getElementById('how-continue').addEventListener('click', closeHowModal);

  document.getElementById('achievements-btn').addEventListener('click', () => openAchievementsModal());
  document.getElementById('ach-close').addEventListener('click', closeAchievementsModal);
  document.getElementById('ach-backdrop').addEventListener('click', closeAchievementsModal);

  document.getElementById('submit-btn').addEventListener('click', handleSubmit);
  document.getElementById('hint-btn').addEventListener('click', giveHint);
  document.getElementById('view-results-btn').addEventListener('click', () => showCompletion());

  document.getElementById('timer-display').addEventListener('click', () => {
    Timer.hidden = !Timer.hidden;
    Timer._render();
    saveSettings();
  });

}

function onKey(e) {
  if (!S.gameStarted) return;
  const k = e.key;

  if (k === 'ArrowLeft')  { e.preventDefault(); moveCursorLR(-1);                return; }
  if (k === 'ArrowRight') { e.preventDefault(); moveCursorLR(+1);                return; }
  if (k === 'ArrowUp')    { e.preventDefault(); shiftWord(-1);                   return; }
  if (k === 'ArrowDown')  { e.preventDefault(); shiftWord(+1);                   return; }
  if (k === 'Tab')        { e.preventDefault(); shiftWord(e.shiftKey ? -1 : +1); return; }

  if (k === 'Backspace') { e.preventDefault(); doBackspace(); return; }

  if (k === 'Enter') { e.preventDefault(); handleSubmit();  return; }

  if (/^[a-zA-Z]$/.test(k)) {
    const letter    = k.toUpperCase();
    const isFinal   = S.activeWord === 5;
    const available = isFinal
      ? S.final.bonusLetters.filter(Boolean)
      : S.words[S.activeWord].answer.split('').filter((_, i) => !S.words[S.activeWord].confirmed[i]);
    if (available.includes(letter)) placeTile(letter);
  }
}

function shiftWord(dir) {
  let idx = S.activeWord + dir;
  while (idx >= 0 && idx <= 4 && (S.words[idx]?.solved || isHardLocked(idx))) idx += dir;
  if (idx < 0 || idx > 5) return;
  if (idx === 5 && !allPrimaryDone()) return;
  const ws = idx === 5 ? S.final : S.words[idx];
  const cursor = ws.guess.some(g => g !== null) ? firstBlankSlot(ws) : undefined;
  selectWordAt(idx, cursor);
}

// ─── Submit ───────────────────────────────────────────────────────────────────

function isValidGuess(word) {
  const lower = word.toLowerCase();
  if (typeof PUZZLE_ANSWERS !== 'undefined' && PUZZLE_ANSWERS.has(lower)) return true;
  if (typeof WORD_LIST === 'undefined') return true;
  return WORD_LIST.has(lower);
}

function updateSubmit() {
  const ws    = S.activeWord === 5 ? S.final : S.words[S.activeWord];
  const ready = ws.guess.every(g => g !== null) && isValidGuess(ws.guess.join(''));
  document.getElementById('submit-btn').classList.toggle('btn-ready', ready);
}

function shakeSubmit() {
  const btn = document.getElementById('submit-btn');
  btn.classList.remove('shake');
  void btn.offsetWidth;
  btn.classList.add('shake');
  setTimeout(() => btn.classList.remove('shake'), 400);
}

function handleSubmit() {
  if (!S.gameStarted) return;
  const isFinal = S.activeWord === 5;
  const ws      = isFinal ? S.final : S.words[S.activeWord];

  if (!ws.guess.every(g => g !== null)) { shakeSubmit(); return; }
  if (!isValidGuess(ws.guess.join(''))) {
    S.invalidAttempts++;
    shakeSubmit();
    saveState();
    return;
  }

  ws.guess.join('') === ws.answer ? solveWord(isFinal) : wrongGuess(isFinal, ws.guess.join(''));
}

function solveWord(isFinal) {
  const justSolvedIdx = S.activeWord;
  const ws            = isFinal ? S.final : S.words[justSolvedIdx];
  ws.solved    = true;
  ws.confirmed = Array(6).fill(true);

  document.getElementById(`row-${justSolvedIdx}`).classList.add('solved');

  if (!isFinal) {
    revealBonusLetters(justSolvedIdx);
    renderAllSlots();

    if (allPrimaryDone()) {
      unlockFinalWord();
    } else {
      let next = justSolvedIdx + 1;
      while (next < 5 && S.words[next].solved) next++;
      if (next >= 5) next = S.words.findIndex(w => !w.solved);
      if (next >= 0 && next < 5) {
        if (S.hardMode) {
          unlockHardRow(next);
          S.activeWord = next;
        }
        setActive(next);
      }
    }
  } else {
    renderSlots(5);
    renderBank();
    Timer.hidden = false;
    Timer._render();
    saveSettings();
    Timer.pause();
    saveState();
    setTimeout(showCompletion, 350);
    return;
  }

  saveState();
}

function wrongGuess(isFinal, guess) {
  S.wrongGuesses++;
  const ws     = isFinal ? S.final : S.words[S.activeWord];
  const answer = ws.answer;

  document.getElementById(`slots-${S.activeWord}`).classList.add('shake');
  setTimeout(() => document.getElementById(`slots-${S.activeWord}`)?.classList.remove('shake'), 400);

  // Confirm any correct-position letters (positional check handles duplicates correctly).
  for (let i = 0; i < 6; i++) {
    if (!ws.confirmed[i] && guess[i] === answer[i]) {
      ws.confirmed[i] = true;
      if (!isFinal && S.words[S.activeWord].bonusIndices.includes(i)) {
        revealOneLetter(guess[i]);
      }
    }
  }

  S.cursor = firstOpenSlot(ws);
  renderSlots(S.activeWord);
  renderBank();
  saveState();
}

// ─── Bonus letters ────────────────────────────────────────────────────────────

function revealBonusLetters(wordIdx) {
  S.words[wordIdx].bonusIndices.forEach(pos => revealOneLetter(S.words[wordIdx].answer[pos]));
}

function revealOneLetter(letter) {
  const slot = S.final.bonusLetters.findIndex(b => b === null);
  if (slot === -1) return;
  S.final.bonusLetters[slot] = letter;
  renderFinalPrompt();
}

// ─── Final word activation ────────────────────────────────────────────────────

function unlockFinalWord() {
  document.querySelectorAll('#slots-5 .slot').forEach(s => s.classList.remove('locked'));
  setActive(5);
}

// ─── How to play modal ────────────────────────────────────────────────────────

function openHowModal() {
  if (S.gameStarted && !S.final.solved) Timer.pause();
  document.getElementById('how-modal').classList.add('modal-open');
  HOW_ANIMATION.start();
}

function closeHowModal() {
  document.getElementById('how-modal').classList.remove('modal-open');
  HOW_ANIMATION.clear();
  if (S.gameStarted && !S.final.solved) Timer.resume();
}

// ─── Achievements modal ───────────────────────────────────────────────────────

let _achFromCompletion = false;

function openAchievementsModal(fromCompletion = false) {
  _achFromCompletion = fromCompletion;
  if (S.gameStarted && !S.final.solved) Timer.pause();
  renderAchievementsGrid();
  document.getElementById('achievements-modal').classList.add('modal-open');
}

function closeAchievementsModal() {
  document.getElementById('achievements-modal').classList.remove('modal-open');
  if (S.gameStarted && !S.final.solved) Timer.resume();
  if (_achFromCompletion) {
    _achFromCompletion = false;
    showCompletion();
  }
}

function renderAchievementsGrid() {
  const grid = document.getElementById('achievements-grid');
  if (!grid) return;
  const unlocked = loadAchievements();
  const earned   = ACHIEVEMENTS.filter(a => unlocked.has(a.id)).length;

  document.getElementById('ach-count').textContent = `${earned} / ${ACHIEVEMENTS.length} earned`;

  grid.innerHTML = ACHIEVEMENTS.map(a => {
    if (unlocked.has(a.id)) {
      return `
        <div class="ach-item">
          <div class="medal-drop">
            <div class="medal-ribbons">
              <div class="medal-strip" style="background:${a.color1}"></div>
              <div class="medal-strip" style="background:${a.color2}"></div>
            </div>
            <div class="medal-face" style="border-color:${a.color1};color:${a.color1};">
              <div class="medal-icon">${a.icon}</div>
            </div>
          </div>
          <div class="ach-label">${a.label}</div>
          <div class="ach-desc">${a.desc}</div>
        </div>`;
    } else {
      const lockedDesc = a.hidden ? '???' : a.desc;
      return `
        <div class="ach-item">
          <div class="medal-drop ach-locked-medal">
            <div class="medal-ribbons">
              <div class="medal-strip" style="background:#4A4440"></div>
              <div class="medal-strip" style="background:#3A3430"></div>
            </div>
            <div class="medal-face" style="background:#3A3430;border-color:#5A5450;color:#5A5450;">
              <div class="medal-icon" style="font-size:0.7rem">?</div>
            </div>
          </div>
          <div class="ach-label ach-label-locked">${a.label}</div>
          <div class="ach-desc ach-desc-locked">${lockedDesc}</div>
        </div>`;
    }
  }).join('');
}

// ─── Completion card ──────────────────────────────────────────────────────────

function showCompletion() {
  if (document.getElementById('completion')) return;

  const { earnedThisSession } = checkAndUnlockAchievements();
  const time      = Timer.format();
  const cleanPlay = S.wrongGuesses === 0;

  const tags = [];
  if (S.hardMode) tags.push('Hard');

  // Build share text with URL embedded so iMessage shows the full message
  const url        = getShareUrl();
  const timeStr    = time + (S.hardMode ? '*' : '');
  const shareLines = [S.puzzle.theme, timeStr];
  if (url) shareLines.push(url);
  const shareText  = shareLines.join('\n');

  const achSection = earnedThisSession.length ? `
    <div id="completion-achievements">
      <div class="completion-ach-eyebrow">${earnedThisSession.length === 1 ? 'Achievement Unlocked' : 'Achievements Unlocked'}</div>
      ${earnedThisSession.map(id => {
        const a = ACHIEVEMENTS.find(x => x.id === id);
        return `<div class="completion-ach-row">
          <span class="completion-ach-icon" style="color:${a.color1}">${a.icon}</span>
          <span class="completion-ach-name">${a.label}</span>
        </div>`;
      }).join('')}
    </div>` : '';

  const overlay = document.createElement('div');
  overlay.id = 'completion';
  overlay.innerHTML = `
    <div id="completion-card">
      <button class="modal-close" id="completion-close">✕</button>
      <div id="completion-theme">${S.puzzle.theme}</div>
      <div id="completion-time">${time}${S.hardMode ? '<sup>*</sup>' : ''}</div>
      <div id="completion-tags">
        ${tags.map(t => `<span class="ctag">${t}</span>`).join('')}
      </div>
      ${achSection}
      <button class="ghost-btn" id="ach-from-card" style="font-size:0.72rem;">View achievements →</button>
      <button id="share-btn">Share</button>
      <div id="share-confirm" class="hidden"></div>
      <div id="feedback-wrap">
        <button id="feedback-toggle" class="ghost-btn">Give feedback</button>
        <div id="feedback-box" class="hidden">
          <textarea id="feedback-text" placeholder="Bugs, suggestions, thoughts…" rows="4"></textarea>
          <button id="feedback-send">Send</button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  let stopConfetti = null;
  if (!confettiFired && typeof confetti === 'function') {
    confettiFired = true;
    setTimeout(() => {
      const card = overlay.querySelector('#completion-card');
      if (!card) return;
      const cnv = document.createElement('canvas');
      cnv.width  = window.innerWidth;
      cnv.height = window.innerHeight;
      cnv.style.cssText = 'position:fixed;top:0;left:0;pointer-events:none;';
      overlay.insertBefore(cnv, card);
      const myConfetti = confetti.create(cnv, { resize: false });
      const rect = card.getBoundingClientRect();
      const ox = (rect.left + rect.width / 2) / window.innerWidth;
      const oy = (rect.top + rect.height / 2) / window.innerHeight;
      const cc = ['#F4A0BC','#C4B0E8','#A4C0E8','#A8D4B4','#F0DC8C','#F7B090'];
      myConfetti({ particleCount: 160, spread: 80, origin: { x: ox, y: oy }, colors: cc });
      stopConfetti = () => { myConfetti.reset(); cnv.remove(); };
    }, 80);
  }

  const dismissOverlay = () => {
    if (stopConfetti) { stopConfetti(); stopConfetti = null; }
    overlay.remove();
  };
  overlay.addEventListener('click', e => { if (e.target === overlay) dismissOverlay(); });
  overlay.querySelector('#completion-close').addEventListener('click', dismissOverlay);
  overlay.querySelector('#ach-from-card').addEventListener('click', () => { dismissOverlay(); openAchievementsModal(true); });

  // Share — URL embedded in text so iMessage shows full message, not just a link preview
  overlay.querySelector('#share-btn').addEventListener('click', () => {
    const shareConfirm = overlay.querySelector('#share-confirm');
    const showMsg = (msg) => {
      shareConfirm.textContent = msg;
      shareConfirm.classList.remove('hidden');
      setTimeout(() => shareConfirm.classList.add('hidden'), 2500);
    };

    if (navigator.share) {
      navigator.share({ title: 'JUGGLE', text: shareText })
        .then(() => showMsg('Shared!'))
        .catch(err => { if (err.name !== 'AbortError') copyToClipboard(shareText, showMsg); });
    } else {
      copyToClipboard(shareText, showMsg);
    }
  });

  overlay.querySelector('#feedback-toggle').addEventListener('click', () => {
    overlay.querySelector('#feedback-box').classList.toggle('hidden');
  });

  overlay.querySelector('#feedback-send').addEventListener('click', async () => {
    const msg = overlay.querySelector('#feedback-text').value.trim();
    if (!msg) return;

    const btn = overlay.querySelector('#feedback-send');
    if (btn.disabled) return;

    if (!FEEDBACK_ENDPOINT) {
      btn.textContent = 'Feedback not configured yet';
      btn.disabled = true;
      setTimeout(() => { btn.textContent = 'Send'; btn.disabled = false; }, 2500);
      return;
    }

    btn.disabled    = true;
    btn.textContent = 'Sending…';

    const payload = {
      message:       msg,
      date:          todayKey(),
      displayedDate: todayDisplayDate(),
      theme:         S.puzzle.theme,
      mode:          S.hardMode ? 'Hard' : 'Easy',
      time:          Timer.format(),
      wrongGuesses:  S.wrongGuesses,
      noMistakes:    S.wrongGuesses === 0,
      url:           getShareUrl(),
      timestamp:     new Date().toISOString(),
      userAgent:     navigator.userAgent,
    };

    try {
      const res = await fetch(FEEDBACK_ENDPOINT, {
        method:  'POST',
        headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      });
      if (res.ok) {
        btn.textContent = 'Thank you!';
        overlay.querySelector('#feedback-text').value = '';
      } else {
        btn.textContent = 'Error — try again';
        btn.disabled    = false;
      }
    } catch {
      btn.textContent = 'Error — try again';
      btn.disabled    = false;
    }
  });
}

// ─── Share helpers ────────────────────────────────────────────────────────────

function copyToClipboard(text, callback) {
  navigator.clipboard.writeText(text)
    .then(() => callback && callback('Copied to clipboard!'))
    .catch(() => callback && callback('Could not copy — try long-pressing'));
}

// ─── Start ────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', init);
