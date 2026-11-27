import AutoLabLean
open AutoLabLean
open AutoLabLean.Examples

private def fmtOptViolation : Option RegimeViolation → String
  | none   => "ALLOW (certified inside Trust Regime)"
  | some v => s!"DENY  {v.format}"

private def fmtExceptWorld : Except RegimeViolation LabWorld → String
  | .ok w    => s!"ALLOW (executed={w.executedCycles.length}, totalVol={totalWellsVol w.deck.wells}, reward={w.cumulativeReward})"
  | .error v => s!"DENY  {v.format}"

/-! `--batch-tsv` parsing is strict, so bad input is denied instead of being read as a default:
Nat fields are ASCII digits only, Int fields may also start with `-`, and flags are exactly
`0` or `1`. An unknown command or step name, a wrong field count or a bad well spec gives
`ERR <repo> malformed_input <detail>`. -/

/-- Remove only the line ending. Tabs separate fields, so an empty last field is kept. -/
private def stripEol (s : String) : String :=
  String.ofList (s.toList.reverse.dropWhile (fun c => c == '\n' || c == '\r')).reverse

/-- Quote a field for an error detail, as printable ASCII so the reply stays on one line. -/
private def quote (s : String) : String :=
  "'" ++ s.map (fun c => if ' ' ≤ c && c ≤ '~' then c else '?') ++ "'"

private def parseNat (s : String) : Except String Nat :=
  match (if s.all Char.isDigit then s.toNat? else none) with
  | some n => pure n
  | none   => throw s!"expected a natural number, got {quote s}"

private def parseInt (s : String) : Except String Int :=
  match (if s.all (fun c => c.isDigit || c == '-') then s.toInt? else none) with
  | some n => pure n
  | none   => throw s!"expected an integer, got {quote s}"

private def parseBool : String → Except String Bool
  | "0" => pure false
  | "1" => pure true
  | s   => throw s!"expected 0 or 1, got {quote s}"

/-- Parse a semicolon-separated list of rehearsal steps:
    `pick;xfer:1:3:1000;mix:3:1000:3;seal:3;inc:3:95:600;thaw:2;drop` -/
private def parseSteps (spec : String) : Except String (List RehearsalStep) :=
  if spec.isEmpty then pure []
  else
    (spec.splitOn ";").mapM fun (tok : String) => do
      match tok.splitOn ":" with
      | ["pick"] => pure .pickTip
      | ["drop"] => pure .dropTip
      | ["seal", w] => pure (.sealWell (← parseNat w))
      | ["thaw", w] => pure (.thawWell (← parseNat w))
      | ["xfer", s, d, v] => pure (.transfer (← parseNat s) (← parseNat d) (← parseNat v))
      | ["mix", w, v, r] => pure (.mix (← parseNat w) (← parseNat v) (← parseNat r))
      | ["inc", w, t, d] => pure (.incubate (← parseNat w) (← parseNat t) (← parseNat d))
      | _ => throw s!"unknown step or wrong field count: {quote tok}"

/-- Parse semicolon-separated deck wells:
    `id:vol:cap:dead:solute:buf:samp:frozen:sealed` -/
private def parseWells (spec : String) : Except String (List DeckWell) :=
  if spec.isEmpty then pure []
  else
    (spec.splitOn ";").mapM fun (tok : String) => do
      match tok.splitOn ":" with
      | [wid, vol, cap, dead, sol, buf, samp, frz, sld] =>
        pure { wellId := (← parseNat wid)
               vol := (← parseNat vol)
               cap := (← parseNat cap)
               deadVol := (← parseNat dead)
               soluteAmt := (← parseNat sol)
               hasBuffer := (← parseBool buf)
               hasSample := (← parseBool samp)
               frozen := (← parseBool frz)
               sealed := (← parseBool sld) }
      | _ => throw s!"bad well spec: {quote tok}"

/-- Evaluate a single TSV command line, split into columns, through the verified Lean 4 checkers.
    Returns `.error detail` if any field fails to parse. -/
private def evalBatchCols (cols : List String) : Except String String :=
  match cols with
  | ["CONFORMAL", n, alpha, dist, tau, lo, hi, pmin, pmax] => do
    let q : ConformalQuery :=
      { nCalib := (← parseNat n), alphaPermille := (← parseNat alpha),
        knnDistPermille := (← parseNat dist), tauDistPermille := (← parseNat tau),
        loMilli := (← parseInt lo), hiMilli := (← parseInt hi),
        physMinMilli := (← parseInt pmin), physMaxMilli := (← parseInt pmax) }
    return match checkDecide q with
    | none => "OK\tlab-decide\tvalid"
    | some v => s!"ERR\t{v.repo.name}\t{v.rule}\t{v.detail}"
  | ["BUYMAKE", isBuy, steps, maxS, acyc, tC, tN, tO, dC, dN, dO, rC, rN, rO, inStock, comp, usdg, hasPrice, price, hasBud, bud, comm, allPerm] => do
    -- Price and budget must parse even when their flag is 0.
    let price ← parseNat price
    let bud ← parseNat bud
    let prop : MakeOrBuyProposal :=
      { isDirectBuy := (← parseBool isBuy), steps := (← parseNat steps), maxSteps := (← parseNat maxS),
        bondIsAcyclic := (← parseBool acyc),
        targetAtoms := { c := (← parseNat tC), n := (← parseNat tN), o := (← parseNat tO), s := 0, hal := 0 },
        leavingDelta := { c := (← parseNat dC), n := (← parseNat dN), o := (← parseNat dO), s := 0, hal := 0 },
        reactantAtoms := [{ c := (← parseNat rC), n := (← parseNat rN), o := (← parseNat rO), s := 0, hal := 0 }],
        allLeavesInStock := (← parseBool inStock), costComplete := (← parseBool comp),
        isUsdPerGram := (← parseBool usdg),
        priceCents := if (← parseBool hasPrice) then some price else none,
        budgetCents := if (← parseBool hasBud) then some bud else none,
        sourceLicenses := if (← parseBool allPerm) then [.permissive] else [.shareAlike],
        commercialMode := (← parseBool comm) }
    return match checkBuyOrMake prop with
    | none => "OK\tbuy-or-make\tvalid"
    | some v => s!"ERR\t{v.repo.name}\t{v.rule}\t{v.detail}"
  | ["REHEARSAL", pipMin, pipMax, pHash, failedCsv, wellsSpec, stepsSpec] => do
    let failed ← if failedCsv.isEmpty then pure [] else (failedCsv.splitOn ",").mapM parseNat
    let deck : DeckState :=
      { wells := (← parseWells wellsSpec), tip := .noTip,
        pipMin := (← parseNat pipMin), pipMax := (← parseNat pipMax), failedHashes := failed }
    let steps ← parseSteps stepsSpec
    return match checkRehearsal deck (← parseNat pHash) steps with
    | .ok sEnd => s!"OK\tlab-rehearsal\tvalid\t{totalWellsVol sEnd.wells}"
    | .error v => s!"ERR\t{v.repo.name}\t{v.rule}\t{v.detail}"
  | ["SQL", nonEmpty, stmts, astRO, authRO, sysTbl, unkCols, xJoin, goldOK, ceOK, propsOK] => do
    let sq : SqlCandidateCheck :=
      { parsedNonEmpty := (← parseBool nonEmpty), statementCount := (← parseNat stmts),
        astReadOnly := (← parseBool astRO), authorizerReadOnly := (← parseBool authRO),
        usesSystemTables := (← parseBool sysTbl), unknownColumnsCount := (← parseNat unkCols),
        hasImplicitCrossJoin := (← parseBool xJoin), matchesGoldResult := (← parseBool goldOK),
        matchesCounterexDBs := (← parseBool ceOK), runtimePropsHold := (← parseBool propsOK) }
    return match checkSqlGate sq with
    | none => "OK\tlab-verify\tvalid"
    | some v => s!"ERR\t{v.repo.name}\t{v.rule}\t{v.detail}"
  | ["REWARD", coreOK, noLeak, thinkTok, maxThink, taskR, fmtB] => do
    let rw : RolloutRewardSpec :=
      { coreScientificVerified := (← parseBool coreOK), oracleFieldStripped := (← parseBool noLeak),
        thinkTokens := (← parseNat thinkTok), maxThinkTokens := (← parseNat maxThink),
        taskRewardPermille := (← parseNat taskR), formatBonusPermille := (← parseNat fmtB) }
    let val := gatedRewardPermille rw
    return match checkRolloutGate rw with
    | none => s!"OK\tlabbench-posttrain\t{val}"
    | some v => s!"ERR\t{v.repo.name}\t{v.rule}\t{val}"
  | ["ATTRIB", preOK, acOK, winOK, tacOK, posOK, negOK, resP, maxRes, ovlP, maxOvl, sigHi] => do
    let t : AssayTelemetry :=
      { preGateCertified := (← parseBool preOK), acousticNormal := (← parseBool acOK),
        scheduleWindowsRespected := (← parseBool winOK), tactileSeatedCleanly := (← parseBool tacOK),
        posControlPassed := (← parseBool posOK), negControlBlankClean := (← parseBool negOK),
        spectralResidualPermille := (← parseNat resP), maxResidualPermille := (← parseNat maxRes),
        precursorOverlapPermille := (← parseNat ovlP), maxOverlapPermille := (← parseNat maxOvl),
        signalAboveActivityThresh := (← parseBool sigHi) }
    let out := attributeAssayOutcome t
    let tag := match out with
      | .executionArtifact         => "EXECUTION_ARTIFACT"
      | .ambiguousCharacterization => "AMBIGUOUS_CHARACTERIZATION"
      | .certifiedPositive         => "CERTIFIED_POSITIVE"
      | .certifiedNegative         => "CERTIFIED_NEGATIVE"
    return s!"OK\tattribution\t{tag}\t{if admitToScientificMemory out then 1 else 0}"
  | ["FRONTIER", isProbe, dist, tau, eta, maxEta, vol, microCap, isBuy, usedPred] => do
    let p : FrontierProbeSpec :=
      { mode := if (← parseBool isProbe) then .frontierCalibration else .exploitation,
        knnDistPermille := (← parseNat dist), tauPermille := (← parseNat tau),
        etaStepPermille := (← parseNat eta), maxEtaPermille := (← parseNat maxEta),
        assayVolTenthUL := (← parseNat vol), microVolCapTenthUL := (← parseNat microCap),
        isDirectBuy := (← parseBool isBuy), usedAsPointPrediction := (← parseBool usedPred) }
    return match checkFrontierAction p with
    | none => "OK\tfrontier\tvalid"
    | some v => s!"ERR\t{v.repo.name}\t{v.rule}\t{v.detail}"
  | ["MCP", tokEp, curEp, leanOK, isExc, humSign] => do
    let e : McpHardwareEnvelope :=
      { tokenEpoch := (← parseNat tokEp), currentDeckEpoch := (← parseNat curEp),
        leanProofValid := (← parseBool leanOK), isFrontierException := (← parseBool isExc),
        humanSupervisorSign := (← parseBool humSign) }
    return match checkMcpHardwareCall e with
    | none => "OK\tmcp\tvalid"
    | some v => s!"ERR\t{v.repo.name}\t{v.rule}\t{v.detail}"
  | ["MEM_SKILL", days, thresh, calEp, curEp, traceRev, microOK] => do
    let s : SkillInvocationCheck :=
      { daysSinceLastUse := (← parseNat days), staleThresholdDays := (← parseNat thresh),
        calibratedDeckEpoch := (← parseNat calEp), currentDeckEpoch := (← parseNat curEp),
        bottomTraceReviewed := (← parseBool traceRev), microRehearsalPass := (← parseBool microOK) }
    return match checkSkillReadiness s with
    | none => "OK\tmemory_skill\tvalid"
    | some v => s!"ERR\t{v.repo.name}\t{v.rule}\t{v.detail}"
  | ["MEM_NOVEL", seen, simP, minSimP, traceOK, toolOK, twinOK] => do
    let n : NovelOnboardingCheck :=
      { seenBefore := (← parseBool seen), analogySimPermille := (← parseNat simP),
        minAnalogyPermille := (← parseNat minSimP), analogBottomTraceLoaded := (← parseBool traceOK),
        toolSpecsQueried := (← parseBool toolOK), twinDryRunCertified := (← parseBool twinOK) }
    return match checkNovelOnboarding n with
    | none => "OK\tmemory_novel\tvalid"
    | some v => s!"ERR\t{v.repo.name}\t{v.rule}\t{v.detail}"
  | _ => throw s!"unknown command or wrong number of fields ({cols.length - 1}) for {quote (cols.headD "")}"

/-- Repo label of each command's `OK` line, also used for its `malformed_input` errors. -/
private def commandRepo : String → String
  | "CONFORMAL" => "lab-decide"
  | "BUYMAKE"   => "buy-or-make"
  | "REHEARSAL" => "lab-rehearsal"
  | "SQL"       => "lab-verify"
  | "REWARD"    => "labbench-posttrain"
  | "ATTRIB"    => "attribution"
  | "FRONTIER"  => "frontier"
  | "MCP"       => "mcp"
  | "MEM_SKILL" => "memory_skill"
  | "MEM_NOVEL" => "memory_novel"
  | _           => "unknown"

/-- Evaluate a single TSV command line. Input that does not parse is denied as `malformed_input`. -/
private def evalBatchLine (line : String) : String :=
  let cols := line.splitOn "\t"
  match evalBatchCols cols with
  | .ok out => out
  | .error detail => s!"ERR\t{commandRepo (cols.headD "")}\tmalformed_input\t{detail}"

private partial def runBatchLoop (stdin : IO.FS.Stream) (stdout : IO.FS.Stream) : IO Unit := do
  let line ← stdin.getLine
  if line.isEmpty then
    pure ()
  else
    let body := stripEol line
    if !body.isEmpty then
      stdout.putStrLn (evalBatchLine body)
      stdout.flush
    runBatchLoop stdin stdout

def runShowcase : IO Unit := do
  IO.println "=== AutoLabLean: 7-Layer, 14-Repo Formal Trust Regime Verifier ==="
  IO.println s!"00. Full 14-Repo ResearchCycle         : {fmtExceptWorld (verifyCycle demoWorld validCycle)}"
  IO.println s!"01. lab-ask-why (missing experiment)   : {fmtOptViolation (checkAskWhy { validCycle.askWhy with hasDiscriminatingExperiment := false })}"
  IO.println s!"02. lab-decide (out-of-domain kNN)     : {fmtOptViolation (checkDecide { validCycle.decide with knnDistPermille := 1380 })}"
  IO.println s!"03. buy-or-make (ring-cleaving SMARTS) : {fmtOptViolation (checkBuyOrMake { validCycle.procurement with bondIsAcyclic := false })}"
  IO.println s!"04. labshift (missed max_wait window)  : {fmtOptViolation (checkSchedule validCycle.scheduleOps [{ predEndMin := 50, succStartMin := 90, minWaitMin := 0, maxWaitMin := 15 }])}"
  IO.println s!"05. lab-automation-atlas (evalOnly)    : {fmtOptViolation (checkAtlasResource { validCycle.atlasSource with licenseClass := .evalOnly })}"
  let badReh := checkRehearsal demoDeck 2002 [.pickTip, .transfer 2 3 500, .transfer 1 4 500, .dropTip]
  let badRehMsg := match badReh with
    | .ok _ => "ALLOW"
    | .error v => "DENY  " ++ v.format
  IO.println s!"06. lab-rehearsal (dirty tip in stock) : {badRehMsg}"
  IO.println s!"07. lab-verify (Layer 4 exec mismatch) : {fmtOptViolation (checkSqlGate { validCycle.sqlCheck with matchesGoldResult := false })}"
  IO.println s!"08. labbench-posttrain (exploit bonus) : {fmtOptViolation (checkRolloutGate { validCycle.rolloutReward with coreScientificVerified := false })} (reward={gatedRewardPermille { validCycle.rolloutReward with coreScientificVerified := false }})"
  IO.println s!"09. twinstep (read before incubate)    : {fmtOptViolation (checkTwinStepOrder 4 [0, 1, 3, 2] [(0, 1), (1, 2), (2, 3)])}"
  IO.println s!"10. labfill (overlapping packed slice) : {fmtOptViolation (checkPackedBin 512 310 [{ seqId := 0, offset := 0, len := 180 }, { seqId := 1, offset := 170, len := 130 }])}"
  IO.println s!"11. lab-ears (speech band overlap)     : {fmtOptViolation (checkLabEars { validCycle.acousticEvent with retainedBands := [{ loHz := 250, hiHz := 500 }] })}"
  IO.println s!"12. stepbot (disposal underflow)       : {fmtOptViolation (checkStepbot { validCycle.stepbotCompile with disposalVol := 600 })}"
  IO.println s!"13. lab-hands (< 5 mm obstacle clear)  : {fmtOptViolation (checkLabHands { validCycle.armTrajectory with minClearanceMM := 2 })}"
  IO.println s!"14. lab-feet (zero quant scale)        : {fmtOptViolation (checkLabFeet { validCycle.edgeStudent with scaleMicro := 0 })}"

  let brokenOOD := { validCycle with cycleId := 2, expectedUtility := 9999,
                                     decide := { validCycle.decide with knnDistPermille := 1500 } }
  let brokenRing := { validCycle with cycleId := 3, expectedUtility := 8888,
                                      procurement := { validCycle.procurement with bondIsAcyclic := false } }
  let wFinal := runShieldedTrajectory demoWorld [brokenOOD, brokenRing, validCycle]
  IO.println s!"Shielded 3-Step Trajectory             : executed={wFinal.executedCycles}, blocked={wFinal.blockedAttempts}, conservedVol={totalWellsVol wFinal.deck.wells} (init={totalWellsVol demoDeck.wells})"

def main (args : List String) : IO UInt32 := do
  match args with
  | ["--batch-tsv"] =>
    let stdin ← IO.getStdin
    let stdout ← IO.getStdout
    runBatchLoop stdin stdout
    return 0
  | _ =>
    runShowcase
    return 0
