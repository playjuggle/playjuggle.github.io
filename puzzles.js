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
  "start": "2026-10-02",
  "end": "2026-11-04"
};

const PUZZLE_ENTRIES = [
  { "date": "2026-11-04", "theme": "Savanna Wildlife", "row": "ZEBRAS*, HYEN*AS, I*MP*ALA, JACKAL*, BA*BOON, PLAINS" },
  { "date": "2026-11-03", "theme": "Bistro Dining", "row": "B*OOTHS, WAI*TER*, S*ALADS, ST*EAKS, BO*TTLE, BISTRO" },
  { "date": "2026-11-02", "theme": "Murder Mystery", "row": "ALIBIS, SLEU*TH, M*OTIVE, COR*PSE*, D*AGGER*, MURDER" },
  { "date": "2026-11-01", "theme": "Garage Workshop", "row": "JIG*SA*W, DR*ILLS, SANDE*R, CLA*MPS, G*LOVES, GARAGE" },
  { "date": "2026-10-31", "theme": "Haunted House", "row": "GHOS*TS, ZOM*BIE*, C*A*SKET, SPIDER*, SKULLS, SCREAM" },
  { "date": "2026-10-30", "theme": "Church Service", "row": "C*H*OIRS, H*YMNAL, SER*MON, U*SHERS, C*ANDLE, CHURCH" },
  { "date": "2026-10-29", "theme": "Horse Stable", "row": "SA*DDL*E, B*RIDLE, HALT*ER, HORSE*S, GROOMS*, STABLE" },
  { "date": "2026-10-28", "theme": "Bridge Construction", "row": "G*IRD*ER, AR*CHE*S, RI*VETS, PYLONS, B*RICKS, BRIDGE" },
  { "date": "2026-10-27", "theme": "Cold Spell", "row": "IC*ICL*E, FL*URRY, FROS*TS, H*EATER, SKI*ING, CHILLS" },
  { "date": "2026-10-26", "theme": "Police Patrol", "row": "SI*RENS, BADGE*S, RADIO*S, P*ATROL*, C*RIMES, POLICE" },
  { "date": "2026-10-25", "theme": "Running Stream", "row": "M*INNOW, PE*BBLE, RA*PIDS*, OT*TERS, R*USHES, STREAM" },
  { "date": "2026-10-24", "theme": "Picnic Lunch", "row": "N*AP*KIN, C*HEESE, JUI*C*ES, FRUI*TS, BREADS, PICNIC" },
  { "date": "2026-10-23", "theme": "Autumn Harvest", "row": "ACORN*S, LEA*VES, APPLES, SQU*ASH, NU*T*M*EG, AUTUMN" },
  {
    "date": "2026-10-22",
    "theme": "Toy Box",
    "row": "RAT*TLE, CO*WB*O*Y*, BLOCKS, BOX*CAR, DOMINO, TOYBOX"
  },
  {
    "date": "2026-10-21",
    "theme": "Museum Exhibit",
    "row": "S*TATU*E*, RELICS, PLAQU*E, M*OSAIC, M*URALS, MUSEUM"
  },
  {
    "date": "2026-10-20",
    "theme": "Roadside Repair",
    "row": "WHE*ELS, P*LI*ER*S, BR*A*KES, CABLES, FENDER, REPAIR"
  },
  {
    "date": "2026-10-19",
    "theme": "Urban Rail",
    "row": "TR*ACKS, TRAI*N*S, TUNNEL, SI*G*NAL, D*EPOTS, RIDING"
  },
  {
    "date": "2026-10-18",
    "theme": "Hair Styling",
    "row": "BARBE*R, CURL*ER, CUT*TER, S*HAVER, DRY*ERS*, STYLES"
  },
  {
    "date": "2026-10-17",
    "theme": "Snow Day",
    "row": "MI*TTE*N, S*LEIGH*, PAR*KAS, BEANIE, SHOV*EL, SHIVER"
  },
  {
    "date": "2026-10-16",
    "theme": "Hotel Room",
    "row": "T*O*WE*LS*, SHEETS, MIR*R*OR, REMOTE, HANGER, RESORT"
  },
  {
    "date": "2026-10-15",
    "theme": "Ocean Life",
    "row": "W*HA*LE*S*, SHAR*KS, MANT*AS, MUSSEL, CORALS, WATERS"
  },
  {
    "date": "2026-10-14",
    "theme": "Birthday Party",
    "row": "B*A*NNE*R, PINATA, PRIZES*, GUES*TS, CH*EERS, BASHES"
  },
  {
    "date": "2026-10-13",
    "theme": "Moving Day",
    "row": "C*RA*TES, TRU*CK*S, P*ACKER, MOVERS, TEN*ANT, UNPACK"
  },
  {
    "date": "2026-10-12",
    "theme": "Lawn Care",
    "row": "M*O*W*ERS, WEEDER, EDG*I*N*G, SPRAYS, RAKING, MOWING"
  },
  {
    "date": "2026-10-11",
    "theme": "Dental Visit",
    "row": "MOL*ARS, BRAC*ES, EN*AMEL, C*AVI*TY, CANI*NE, CLINIC"
  },
  {
    "date": "2026-10-10",
    "theme": "Dance Rehearsal",
    "row": "DA*NCE*R, T*IG*HTS*, TUTORS*, TANGOS, RHYTHM, STAGES"
  },
  {
    "date": "2026-10-09",
    "theme": "Backyard Dinner",
    "row": "GR*I*LLS, KE*BABS, ON*ION*S, PLATES, D*RINKS, DINNER"
  },
  {
    "date": "2026-10-08",
    "theme": "Art Studio",
    "row": "IN*KING, PA*S*TEL, EA*SELS, SKETC*H, SILV*ER, CANVAS"
  },
  {
    "date": "2026-10-07",
    "theme": "Sports Tournament",
    "row": "SO*CCER*, T*ENNIS, P*ADDLE, SKATER, H*OCKEY*, TROPHY"
  },
  {
    "date": "2026-10-06",
    "theme": "Diner Brunch",
    "row": "B*U*R*GER, QUIC*H*E, HASHES, PAN*INI, CREPES, BRUNCH"
  },
  {
    "date": "2026-10-05",
    "theme": "Photo Studio",
    "row": "T*RIP*O*D, S*TRO*BE, FILTER, SH*ADOW, FAMILY, PHOTOS"
  },
  {
    "date": "2026-10-04",
    "theme": "Farmers' Market",
    "row": "BA*NANA, MEL*ONS*, T*URNIP, OL*IVES*, GRAPES, STALLS"
  },
  {
    "date": "2026-10-03",
    "theme": "Hand Sewing",
    "row": "NEEDLE, T*H*READ, FABRI*C*, BUT*TON, S*POOLS, STITCH"
  },
  {
    "date": "2026-10-02",
    "theme": "Home Office",
    "row": "LAP*T*O*P, TABLE*T, C*HECK*S, PAPERS, DEVICE, POCKET"
  }
];
