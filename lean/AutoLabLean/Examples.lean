import AutoLabLean.TrustRegime
/-!
# AutoLabLean.Examples: Machine-Checked Valid & Boundary-Crossing Witnesses for All 14 Repos

Uses compile-time `#guard` assertions so the Lean 4 compiler itself rejects compilation
if any of the 14 repository checkers ever drifts on valid or boundary-violating examples!
-/
namespace AutoLabLean.Examples

/-- Baseline well-formed 4-well deck (`res:buffer = 1`, `res:stock = 2`, `plate:A1 = 3`, `plate:B1 = 4`). -/
def demoDeck : DeckState :=
  { wells :=
      [ { wellId := 1, vol := 2500, cap := 3000, deadVol := 50, soluteAmt := 0,
          hasBuffer := true, hasSample := false, frozen := false, sealed := false },
        { wellId := 2, vol := 1500, cap := 3000, deadVol := 50, soluteAmt := 1500,
          hasBuffer := false, hasSample := true, frozen := false, sealed := false },
        { wellId := 3, vol := 0, cap := 3000, deadVol := 50, soluteAmt := 0,
          hasBuffer := false, hasSample := false, frozen := false, sealed := false },
        { wellId := 4, vol := 0, cap := 3000, deadVol := 50, soluteAmt := 0,
          hasBuffer := false, hasSample := false, frozen := false, sealed := false } ]
    tip := .noTip
    pipMin := 200
    pipMax := 3000
    failedHashes := [9999] }

/-- Clean 2-well serial dilution protocol (`0.1 uL` units: `100.0 uL = 1000`). -/
def validDilutionSteps : List RehearsalStep :=
  [ .pickTip,
    .transfer 1 3 1000,
    .transfer 1 4 1000,
    .dropTip,
    .pickTip,
    .transfer 2 3 1000,
    .mix 3 1000 3,
    .transfer 3 4 1000,
    .mix 4 1000 3,
    .sealWell 3,
    .incubate 3 95 600,
    .dropTip ]

/-- Complete valid `ResearchCycle` passing all 14 repository guardrails! -/
def validCycle : ResearchCycle :=
  { cycleId := 1
    expectedUtility := 850
    askWhy := { topScorePermille := 789, noinfoThreshPermille := 350,
                supportHits := 2, contradictHits := 1, hasDiscriminatingExperiment := true }
    decide := { nCalib := 180, alphaPermille := 100, knnDistPermille := 410,
                tauDistPermille := 758, loMilli := -2410, hiMilli := 630,
                physMinMilli := -15000, physMaxMilli := 1750 }
    procurement := { isDirectBuy := false, steps := 1, maxSteps := 2, bondIsAcyclic := true,
                     targetAtoms := { c := 12, n := 3, o := 1, s := 0, hal := 0 },
                     leavingDelta := { c := 0, n := 0, o := 0, s := 0, hal := 1 },
                     reactantAtoms := [ { c := 4, n := 2, o := 0, s := 0, hal := 1 },
                                        { c := 8, n := 1, o := 1, s := 0, hal := 0 } ],
                     allLeavesInStock := true, costComplete := true, isUsdPerGram := true,
                     priceCents := some 1450, budgetCents := some 2500,
                     sourceLicenses := [.permissive], commercialMode := true }
    scheduleOps := [ { opId := 1, poolId := 0, machineIdx := 0, poolCap := 2,
                       startMin := 0, durMin := 18, releaseMin := 0, deadlineMin := 120 },
                     { opId := 2, poolId := 1, machineIdx := 0, poolCap := 2,
                       startMin := 20, durMin := 30, releaseMin := 0, deadlineMin := 120 },
                     { opId := 3, poolId := 2, machineIdx := 0, poolCap := 1,
                       startMin := 52, durMin := 5, releaseMin := 0, deadlineMin := 120 } ]
    scheduleLinks := [ { predEndMin := 18, succStartMin := 20, minWaitMin := 0, maxWaitMin := 10 },
                       { predEndMin := 50, succStartMin := 52, minWaitMin := 0, maxWaitMin := 15 } ]
    atlasSource := { httpsOnly := true, noPrivateIp := true, spdxKnown := true,
                     licenseClass := .permissive, forTraining := true, commercial := true }
    protocolHash := 1001
    rehearsalSteps := validDilutionSteps
    sqlCheck := { parsedNonEmpty := true, statementCount := 1, astReadOnly := true,
                  authorizerReadOnly := true, usesSystemTables := false, unknownColumnsCount := 0,
                  hasImplicitCrossJoin := false, matchesGoldResult := true,
                  matchesCounterexDBs := true, runtimePropsHold := true }
    leanCheck := { hasSorryOrAdmit := false, hasUnsafeOrAxiom := false,
                   hasVacuousTrueThm := false, kernelVerified := true }
    splitManifest := { trainGroups := [1, 2, 3], valGroups := [4], testGroups := [5], canaryGroups := [99] }
    rolloutReward := { coreScientificVerified := true, oracleFieldStripped := true,
                       thinkTokens := 240, maxThinkTokens := 512,
                       taskRewardPermille := 900, formatBonusPermille := 100 }
    twinNSteps := 4
    twinOrder := [0, 1, 2, 3]
    twinDagEdges := [(0, 1), (1, 2), (2, 3)]
    packBinCap := 512
    packExpected := 472
    packSlices := [ { seqId := 0, offset := 0, len := 180 },
                    { seqId := 1, offset := 180, len := 292 } ]
    acousticEvent := { rawAudioSaved := false, sampleRateHz := 16000,
                       retainedBands := [{ loHz := 50, hiHz := 280 }, { loHz := 3500, hiHz := 7800 }],
                       scoreCalibOK := true }
    stepbotCompile := { occupiedSlots := [1, 2, 4], pipMaxTenthUL := 3000, tipRackMaxTenthUL := 2000,
                        transferVol := 1000, nDistributeWells := 2, disposalVol := 100,
                        sourceWellVol := 2500, tipsRequired := 4, tipsAvailable := 96 }
    armTrajectory := { minClearanceMM := 8, reqSafetyMarginMM := 5, absElbowQ2Mrad := 1850,
                       vesselRimClearZMM := 12, maxLateralAccMMS2 := 450, sloshLimitMMS2 := 800,
                       tactileRadialErrUM := 85 }
    edgeStudent := { bitWidth := 4, scaleMicro := 12500, packedWeightBytes := 1520,
                     maxEdgeSramBytes := 4096, agreementPermille := 996, minAgreePermille := 980 } }

def demoWorld : LabWorld :=
  { deck := demoDeck, executedCycles := [], cumulativeReward := 0, blockedAttempts := 0 }

-- Compile-time machine-checked assertions across all 14 repos!
#guard (verifyCycle demoWorld validCycle).isOk == true

-- 1. `lab-ask-why`: Contested claim without discriminating experiment -> DENIED
#guard checkAskWhy { validCycle.askWhy with hasDiscriminatingExperiment := false }
       == some { repo := .labAskWhy, rule := "contested_requires_experiment",
                 detail := "both support and contradict evidence present without a discriminating experiment" }

-- 2. `lab-decide`: Out-of-domain macrocycle (`knnDist = 1380 > 758`) -> ABSTAIN / DENIED
#guard (checkDecide { validCycle.decide with knnDistPermille := 1380 }).isSome == true

-- 3. `buy-or-make`: Endocyclic lactam ring cleavage (`bondIsAcyclic = false`) -> DENIED
#guard (checkBuyOrMake { validCycle.procurement with bondIsAcyclic := false }).isSome == true

-- 4. `labshift`: Plate waits 40 min after incubation (`maxWait = 15`) -> DENIED
#guard (checkSchedule validCycle.scheduleOps
         [{ predEndMin := 50, succStartMin := 90, minWaitMin := 0, maxWaitMin := 15 }]).isSome == true

-- 5. `lab-automation-atlas`: `LAB-Bench` (`evalOnly`) fed into training -> DENIED
#guard (checkAtlasResource { validCycle.atlasSource with licenseClass := .evalOnly }).isSome == true

private def hasRehearsalErrRule (res : Except RegimeViolation DeckState) (r : String) : Bool :=
  match res with
  | .error v => v.rule == r
  | .ok _    => false

-- 6. `lab-rehearsal`: Dirty sample tip dips back into clean buffer (`well 1 -> well 4`) -> DENIED
#guard hasRehearsalErrRule
         (checkRehearsal demoDeck 2002 [.pickTip, .transfer 2 3 500, .transfer 1 4 500, .dropTip])
         "no_tip_cross_contamination" == true

-- 6b. `lab-rehearsal`: Serial-dilution back-entry up row (`tip at dilute well 4 re-enters concentrated well 3`) -> DENIED
#guard hasRehearsalErrRule
         (checkRehearsal demoDeck 2003
           [.pickTip, .transfer 1 3 600, .transfer 1 4 600, .dropTip,
            .pickTip, .transfer 2 3 600, .transfer 3 4 600, .mix 4 600 2, .transfer 3 4 200, .dropTip])
         "no_tip_cross_contamination" == true

-- 7. `lab-verify`: Semantic `COUNT` vs `COUNT DISTINCT` failure at Layer 4 -> DENIED
#guard (checkSqlGate { validCycle.sqlCheck with matchesGoldResult := false }).isSome == true

-- 8. `labbench-posttrain`: Unverified rollout gets strictly 0 reward (anti-reward-hack)
#guard gatedRewardPermille { validCycle.rolloutReward with coreScientificVerified := false } == 0

-- 9. `twinstep`: Swapped `read` before `incubate` (`[0, 1, 3, 2]`) -> DENIED
#guard (checkTwinStepOrder 4 [0, 1, 3, 2] [(0, 1), (1, 2), (2, 3)]).isSome == true

-- 10. `labfill`: Overlapping packed slices (`[0..180)` and `[170..300)`) -> DENIED
#guard (checkPackedBin 512 310 [{ seqId := 0, offset := 0, len := 180 },
                                { seqId := 1, offset := 170, len := 130 }]).isSome == true

-- 11. `lab-ears`: Retained mel band `[250, 500] Hz` overlaps speech `[300, 3400] Hz` -> DENIED
#guard (checkLabEars { validCycle.acousticEvent with
                       retainedBands := [{ loHz := 250, hiHz := 500 }] }).isSome == true

-- 12. `stepbot`: `distribute` disposal volume underflows reservoir (`2*1000 + 600 > 2500`) -> DENIED
#guard (checkStepbot { validCycle.stepbotCompile with disposalVol := 600 }).isSome == true

-- 13. `lab-hands`: Straight-line arm path grazes bottle (`minClearanceMM = 2 < 5`) -> DENIED
#guard (checkLabHands { validCycle.armTrajectory with minClearanceMM := 2 }).isSome == true

-- 14. `lab-feet`: Zero quantization scale (`scaleMicro = 0`) -> DENIED
#guard (checkLabFeet { validCycle.edgeStudent with scaleMicro := 0 }).isSome == true

end AutoLabLean.Examples
