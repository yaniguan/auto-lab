import AutoLabLean
open AutoLabLean
open AutoLabLean.Examples

private def fmtOptViolation : Option RegimeViolation → String
  | none   => "ALLOW (certified inside Trust Regime)"
  | some v => s!"DENY  {v.format}"

private def fmtExceptWorld : Except RegimeViolation LabWorld → String
  | .ok w    => s!"ALLOW (executed={w.executedCycles.length}, totalVol={totalWellsVol w.deck.wells}, reward={w.cumulativeReward})"
  | .error v => s!"DENY  {v.format}"

private def trimStr (s : String) : String :=
  String.ofList ((s.toList.dropWhile Char.isWhitespace).reverse.dropWhile Char.isWhitespace).reverse

private def parseNatD (s : String) (d : Nat := 0) : Nat :=
  ((trimStr s).toNat?).getD d

private def parseIntD (s : String) (d : Int := 0) : Int :=
  ((trimStr s).toInt?).getD d

private def parseBoolD (s : String) : Bool :=
  let t := (trimStr s).toLower
  t == "1" || t == "true"

/-- Parse a semicolon-separated list of rehearsal steps:
    `pick;xfer:1:3:1000;mix:3:1000:3;seal:3;inc:3:95:600;thaw:2;drop` -/
private def parseSteps (spec : String) : List RehearsalStep :=
  if (trimStr spec).isEmpty then []
  else
    (spec.splitOn ";").filterMap fun (tok : String) =>
      let parts := (trimStr tok).splitOn ":"
      match parts with
      | ["pick"] => some .pickTip
      | ["drop"] => some .dropTip
      | ["seal", w] => some (.sealWell (parseNatD w))
      | ["thaw", w] => some (.thawWell (parseNatD w))
      | ["xfer", s, d, v] => some (.transfer (parseNatD s) (parseNatD d) (parseNatD v))
      | ["mix", w, v, r] => some (.mix (parseNatD w) (parseNatD v) (parseNatD r))
      | ["inc", w, t, d] => some (.incubate (parseNatD w) (parseNatD t) (parseNatD d))
      | _ => none

/-- Parse semicolon-separated deck wells:
    `id:vol:cap:dead:solute:buf:samp:frozen:sealed` -/
private def parseWells (spec : String) : List DeckWell :=
  if (trimStr spec).isEmpty then []
  else
    (spec.splitOn ";").filterMap fun (tok : String) =>
      match (trimStr tok).splitOn ":" with
      | [wid, vol, cap, dead, sol, buf, samp, frz, sld] =>
        some { wellId := parseNatD wid
               vol := parseNatD vol
               cap := parseNatD cap
               deadVol := parseNatD dead
               soluteAmt := parseNatD sol
               hasBuffer := parseBoolD buf
               hasSample := parseBoolD samp
               frozen := parseBoolD frz
               sealed := parseBoolD sld }
      | _ => none

/-- Evaluate a single TSV command line through the verified Lean 4 checkers. -/
private def evalBatchLine (line : String) : String :=
  let cols := (trimStr line).splitOn "\t"
  match cols with
  | ["CONFORMAL", n, alpha, dist, tau, lo, hi, pmin, pmax] =>
    let q : ConformalQuery :=
      { nCalib := parseNatD n, alphaPermille := parseNatD alpha,
        knnDistPermille := parseNatD dist, tauDistPermille := parseNatD tau,
        loMilli := parseIntD lo, hiMilli := parseIntD hi,
        physMinMilli := parseIntD pmin, physMaxMilli := parseIntD pmax }
    match checkDecide q with
    | none => "OK\tlab-decide\tvalid"
    | some v => s!"ERR\t{v.repo.name}\t{v.rule}\t{v.detail}"
  | ["BUYMAKE", isBuy, steps, maxS, acyc, tC, tN, tO, dC, dN, dO, rC, rN, rO, inStock, comp, usdg, hasPrice, price, hasBud, bud, comm, allPerm] =>
    let prop : MakeOrBuyProposal :=
      { isDirectBuy := parseBoolD isBuy, steps := parseNatD steps, maxSteps := parseNatD maxS,
        bondIsAcyclic := parseBoolD acyc,
        targetAtoms := { c := parseNatD tC, n := parseNatD tN, o := parseNatD tO, s := 0, hal := 0 },
        leavingDelta := { c := parseNatD dC, n := parseNatD dN, o := parseNatD dO, s := 0, hal := 0 },
        reactantAtoms := [{ c := parseNatD rC, n := parseNatD rN, o := parseNatD rO, s := 0, hal := 0 }],
        allLeavesInStock := parseBoolD inStock, costComplete := parseBoolD comp,
        isUsdPerGram := parseBoolD usdg,
        priceCents := if parseBoolD hasPrice then some (parseNatD price) else none,
        budgetCents := if parseBoolD hasBud then some (parseNatD bud) else none,
        sourceLicenses := if parseBoolD allPerm then [.permissive] else [.shareAlike],
        commercialMode := parseBoolD comm }
    match checkBuyOrMake prop with
    | none => "OK\tbuy-or-make\tvalid"
    | some v => s!"ERR\t{v.repo.name}\t{v.rule}\t{v.detail}"
  | ["REHEARSAL", pipMin, pipMax, pHash, failedCsv, wellsSpec, stepsSpec] =>
    let failed := if (trimStr failedCsv).isEmpty then [] else (failedCsv.splitOn ",").map parseNatD
    let deck : DeckState :=
      { wells := parseWells wellsSpec, tip := .noTip,
        pipMin := parseNatD pipMin, pipMax := parseNatD pipMax, failedHashes := failed }
    let steps := parseSteps stepsSpec
    match checkRehearsal deck (parseNatD pHash) steps with
    | .ok sEnd => s!"OK\tlab-rehearsal\tvalid\t{totalWellsVol sEnd.wells}"
    | .error v => s!"ERR\t{v.repo.name}\t{v.rule}\t{v.detail}"
  | ["SQL", nonEmpty, stmts, astRO, authRO, sysTbl, unkCols, xJoin, goldOK, ceOK, propsOK] =>
    let sq : SqlCandidateCheck :=
      { parsedNonEmpty := parseBoolD nonEmpty, statementCount := parseNatD stmts,
        astReadOnly := parseBoolD astRO, authorizerReadOnly := parseBoolD authRO,
        usesSystemTables := parseBoolD sysTbl, unknownColumnsCount := parseNatD unkCols,
        hasImplicitCrossJoin := parseBoolD xJoin, matchesGoldResult := parseBoolD goldOK,
        matchesCounterexDBs := parseBoolD ceOK, runtimePropsHold := parseBoolD propsOK }
    match checkSqlGate sq with
    | none => "OK\tlab-verify\tvalid"
    | some v => s!"ERR\t{v.repo.name}\t{v.rule}\t{v.detail}"
  | ["REWARD", coreOK, noLeak, thinkTok, maxThink, taskR, fmtB] =>
    let rw : RolloutRewardSpec :=
      { coreScientificVerified := parseBoolD coreOK, oracleFieldStripped := parseBoolD noLeak,
        thinkTokens := parseNatD thinkTok, maxThinkTokens := parseNatD maxThink,
        taskRewardPermille := parseNatD taskR, formatBonusPermille := parseNatD fmtB }
    let val := gatedRewardPermille rw
    match checkRolloutGate rw with
    | none => s!"OK\tlabbench-posttrain\t{val}"
    | some v => s!"ERR\t{v.repo.name}\t{v.rule}\t{val}"
  | ["ATTRIB", preOK, acOK, winOK, tacOK, posOK, negOK, resP, maxRes, ovlP, maxOvl, sigHi] =>
    let t : AssayTelemetry :=
      { preGateCertified := parseBoolD preOK, acousticNormal := parseBoolD acOK,
        scheduleWindowsRespected := parseBoolD winOK, tactileSeatedCleanly := parseBoolD tacOK,
        posControlPassed := parseBoolD posOK, negControlBlankClean := parseBoolD negOK,
        spectralResidualPermille := parseNatD resP, maxResidualPermille := parseNatD maxRes,
        precursorOverlapPermille := parseNatD ovlP, maxOverlapPermille := parseNatD maxOvl,
        signalAboveActivityThresh := parseBoolD sigHi }
    let out := attributeAssayOutcome t
    let tag := match out with
      | .executionArtifact         => "EXECUTION_ARTIFACT"
      | .ambiguousCharacterization => "AMBIGUOUS_CHARACTERIZATION"
      | .certifiedPositive         => "CERTIFIED_POSITIVE"
      | .certifiedNegative         => "CERTIFIED_NEGATIVE"
    s!"OK\tattribution\t{tag}\t{if admitToScientificMemory out then 1 else 0}"
  | ["FRONTIER", isProbe, dist, tau, eta, maxEta, vol, microCap, isBuy, usedPred] =>
    let p : FrontierProbeSpec :=
      { mode := if parseBoolD isProbe then .frontierCalibration else .exploitation,
        knnDistPermille := parseNatD dist, tauPermille := parseNatD tau,
        etaStepPermille := parseNatD eta, maxEtaPermille := parseNatD maxEta,
        assayVolTenthUL := parseNatD vol, microVolCapTenthUL := parseNatD microCap,
        isDirectBuy := parseBoolD isBuy, usedAsPointPrediction := parseBoolD usedPred }
    match checkFrontierAction p with
    | none => "OK\tfrontier\tvalid"
    | some v => s!"ERR\t{v.repo.name}\t{v.rule}\t{v.detail}"
  | ["MCP", tokEp, curEp, leanOK, isExc, humSign] =>
    let e : McpHardwareEnvelope :=
      { tokenEpoch := parseNatD tokEp, currentDeckEpoch := parseNatD curEp,
        leanProofValid := parseBoolD leanOK, isFrontierException := parseBoolD isExc,
        humanSupervisorSign := parseBoolD humSign }
    match checkMcpHardwareCall e with
    | none => "OK\tmcp\tvalid"
    | some v => s!"ERR\t{v.repo.name}\t{v.rule}\t{v.detail}"
  | _ => "ERR\tunknown\tmalformed_command\tunrecognized TSV batch command"

private partial def runBatchLoop (stdin : IO.FS.Stream) (stdout : IO.FS.Stream) : IO Unit := do
  let line ← stdin.getLine
  if line.isEmpty then
    pure ()
  else
    let trimmed := trimStr line
    if !trimmed.isEmpty then
      stdout.putStrLn (evalBatchLine trimmed)
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
