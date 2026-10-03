// ---------------------------------------------------------------------------
// HOW TO ADD A PUZZLE
// ---------------------------------------------------------------------------
// Add one entry to PUZZLE_ENTRIES per date, inserted in chronological
// position so the list stays newest-to-oldest — for a new future date this
// normally means prepending it at the very top, not appending to the end.
// Do not reorder or remove existing entries otherwise. After editing, run
// `python3 scripts/validate_puzzles.py` and resolve every reported error
// (warnings do not block) before publishing.
//
// Each entry needs:
//   date  — "YYYY-MM-DD"
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
//   ?date=YYYY-MM-DD   preview any puzzle date. NOT side-effect-free: it can
//                      still write that date's saved game state, emit
//                      analytics, and affect completion/achievement records.
//   ?reset             clear saved progress for the active date
//
// WORD_LIST (wordlist.js) gates valid wrong guesses.
// Puzzle answers and the final word are always accepted even if absent
// from WORD_LIST — no need to duplicate them there.
//
// PUZZLE_ENTRIES is an ordered list (newest-to-oldest) so duplicate dates
// remain individually inspectable in source and in the validator. game.js
// consumes entries in order to build PUZZLE_ROWS, so — matching plain
// JavaScript object-literal semantics — a later entry for the same date
// overwrites an earlier one at runtime.
//
// Historical note preserved from the prior inline comment on the
// 2026-05-24 "Around the House" entry (marker derivation, not itself
// authored data): CLOSET[4]=E, FRIDGE[3]=D,[4]=G, CARPET[1]=A,
// PANTRY[2]=N, SHOWER[5]=R → GARDEN.
//
// PUZZLE_PUBLISHING_RANGE and PUZZLE_ENTRIES below are written as strict
// JSON values (double-quoted keys/strings, no comments, no trailing
// commas) so scripts/validate_puzzles.py can parse them without
// executing JavaScript.
// ---------------------------------------------------------------------------

const PUZZLE_PUBLISHING_RANGE = {
  "start": "2026-05-24",
  "end": "2026-06-17"
};

const PUZZLE_ENTRIES = [
  { "date": "2026-06-17", "theme": "Garden Path", "row": "BA*MBOO, CACT*U*S, OR*CHID, GARDEN*, FLOWE*R, NATURE" },
  { "date": "2026-06-16", "theme": "Movie Night", "row": "CINEMA*, AC*TIO*N, SCR*EEN, POS*T*ER, CREDIT, ACTORS" },
  { "date": "2026-06-15", "theme": "Road Trip", "row": "T*R*AVEL, DETO*U*R, MOTE*LS, SCENIC, S*NACKS, ROUTES" },
  { "date": "2026-06-14", "theme": "Rainy Day", "row": "C*LOUD*S, PUDDLE*, SPLASH*, PON*CHO, STOR*MY, DRENCH" },
  { "date": "2026-06-13", "theme": "Game Night", "row": "TOKE*NS, BOA*R*D*S, PUZZL*E*, WINNER, SCORES, DEALER" },
  { "date": "2026-06-12", "theme": "Bake Shop", "row": "PASTR*Y*, COOK*IE, BA*TTE*R, MUFFIN, B*UTTER, BAKERY" },
  { "date": "2026-06-11", "theme": "Hard Hat Zone", "row": "HELMET*, HAM*MER, LADDE*R, WORKE*R, WREN*C*H, CEMENT" },
  { "date": "2026-06-10", "theme": "Bird Watching", "row": "FALC*ON, MA*GPIE, PA*R*ROT, PIGEON*, TURKEY*, CANARY" },
  { "date": "2026-06-09", "theme": "Crayon Box", "row": "PUR*PLE, IN*DIG*O, YELLO*W, MA*ROON, VIOLE*T, ORANGE" },
  { "date": "2026-06-08", "theme": "What's for Dessert?", "row": "C*OOKI*E, GE*L*ATO, SUNDA*E, PASTR*Y, MOUSSE, ECLAIR" },
  { "date": "2026-06-07", "theme": "The Veggie Garden", "row": "C*ELERY, GA*R*LIC, TO*MATO, POT*ATO, PEPPER*, CARROT" },
  { "date": "2026-06-06", "theme": "Outer Space", "row": "R*OC*KET, GA*LAXY, METEOR*, PLANE*T*, COSMOS, CRATER" },
  { "date": "2026-06-05", "theme": "Hail Mary", "row": "KIC*K*ER, HELMET*, PLA*YER, JERSE*Y, HUDDL*E, TACKLE" },
  { "date": "2026-06-04", "theme": "X Marks the Spot", "row": "PAR*ROT, CA*NNON, ANCHO*R, IS*L*AND, PI*STOL, SAILOR" },
  { "date": "2026-06-03", "theme": "Once Upon a Time", "row": "KNIG*HT, WIZARD*, THRO*NE, CA*STLE, PR*IN*CE, DRAGON" },
  { "date": "2026-06-02", "theme": "Animal Kingdom", "row": "JAGU*AR, RABBIT*, PAR*ROT*, L*IZARD, MONKE*Y, TURTLE" },
  { "date": "2026-06-01", "theme": "Class is in Session", "row": "CR*AYON, PE*NCIL, LES*SON, MA*RKER*, RE*CESS, ERASER" },
  { "date": "2026-05-31", "theme": "Grocery Store", "row": "BASKET, A*ISLES, CO*UPON*, GROC*ER, MAR*KET*, CARTON" },
  { "date": "2026-05-30", "theme": "Airplane Mode", "row": "WI*N*DOW, RUN*WAY, FLIG*HT, JE*TLAG, TICKE*T, ENGINE" },
  { "date": "2026-05-29", "theme": "Music Class", "row": "GU*IT*AR, VIO*LIN, MELOD*Y, S*INGER, PI*ANOS, STUDIO" },
  { "date": "2026-05-28", "theme": "Beach Day", "row": "SUN*TAN, S*ANDAL, CO*OLE*R, C*A*BANA, TROPIC, OCEANS" },
  { "date": "2026-05-27", "theme": "Camping Trip", "row": "FORE*ST, GR*OUND, SUM*MIT, C*ANOP*Y, TRA*ILS, CAMPER" },
  { "date": "2026-05-26", "theme": "Breakfast", "row": "C*EREAL, YO*GURT, WAF*F*LE, OME*LET, ORANGE*, COFFEE" },
  { "date": "2026-05-25", "theme": "Under the Sea", "row": "TU*RTLE, OYSTER*, ANC*H*OR, SHRI*MP, SALMON*, URCHIN" },
  { "date": "2026-05-24", "theme": "Around the House", "row": "CLOSE*T, FRID*G*E, CA*RPET, PAN*TRY, SHOWER*, GARDEN" }
];
