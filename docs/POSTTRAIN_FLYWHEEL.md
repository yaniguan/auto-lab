# The Auto-Lab Post-Training & Data Flywheel (`L3` ↔ `L0`–`L6`)

Autonomous wet-lab agents fail when trained solely on static next-token prediction over literature text: free-form text models hallucinate reagent volumes, swap wash and read steps, ignore pipette capacity limits, and exploit naive scalar RL rewards via verbose `<think>` padding or answer-format gaming.

The Auto-Lab stack closes this gap with a four-stage **Execution-to-RLVR Flywheel**:

## 1. Episodic Logging & Seeded Contrastive Twins (`lab-rehearsal` → `twinstep`)

1. Every dry-run and mock/hardware run in [`lab-rehearsal`](https://github.com/yaniguan/lab-rehearsal) records structured violation traces (`enough_liquid`, `volume_in_range`, `no_overfill`, `no_tip_reuse`) into `runs.jsonl`.
2. [`twinstep`](https://github.com/yaniguan/twinstep) takes valid liquid-handling protocols (`transfer`, `mix`, `incubate`, `wash`, `read`) and deterministically injects six typed failure modes (`swap_order`, `wrong_volume`, `wrong_unit`, `missing_step`, `wrong_temperature`, `wrong_time`), paired with minimal liquid-flow and stage-barrier ordering DAGs.

## 2. Tensorized Filtering, Repair & GPU Packing (`labfill`)

Short, variable-length protocol traces (`8..512` tokens) waste ~70% of compute on pad tokens under naive batching. [`labfill`](https://github.com/yaniguan/labfill) provides five recipes bridging data generation and single-GPU utilization:

- **Recipe 1 & 5**: Tensorized protocol rule validation (`225,851 proto/s` at `B=16,384` on 1 CPU thread) and batched 96-well plate volume rehearsal (`3,823 plates/s`).
- **Recipe 2**: Generate-N / Check / Keep filtering (`163,078 candidates/s`) and intent-preserving single-edit repair (`K=24` parallel edits).
- **Recipe 4**: Sequence packing raises useful-token density from `30.6%` to `92.1%` (`2.60×` real tok/s), and combining sequence packing with `bf16` autocast achieves `5.42×` real tokens/s over padded `fp32` on CPU (`GPU runs pending`).

## 3. Multi-Stage Verified Post-Training (`labbench-posttrain` / `labrl`)

[`labbench-posttrain`](https://github.com/yaniguan/labbench-posttrain) unifies two domain tracks (**Scientist** + **Operator**) and code-checked protocol/electrolyte RL environments (`BioProBench` `PQA`/`ORD`/`ERR`/`GEN` + `CALiSol-23` conductivity) under the installable `labrl` SDK:

```text
SFT (Anchor Policy)
  └──► Offline Preference & Hybrid Alignment: DPO / MPO (DPO + BCO + SFT) / TROPD (On-Policy Distillation)
         └──► Online Verifiable RL (RLVR): PPO (Causal GAE / VAPO) / GRPO / GDPO (Multi-Reward) + DAPO
                └──► Evaluation Harness: LAB-Bench (Strictly Eval-Only Canary Guard) & Prospective Blind Holdout
```

Key post-training safeguards in `labbench-posttrain`:
- **Cryptographic `SplitGuard`**: 49,139 multi-origin records (`40,790` train / `4,189` val / `4,160` test) with **0 cross-split group overlap**, strict separation of `measurement` (`29,399`), `compute` (`13,990`), `ml_prediction` (`5,667`), and `human_annotation` (`83`), and a hard canary block preventing training on `data/labbench/`.
- **Anti-Hack Verified Reward Composers**: 8 verified reward templates gating auxiliary formatting/length bonuses strictly on core scientific/protocol correctness, with `<think>` length penalties and exploit-policy audits (`python -m bioenvs.audit`).
- **Dual Execution Engines**: `TorchLocalEngine` for CPU smoke verification and 1×GPU debugging, plus `NeMoRLEngine` 4-axis recipe generation (`algo × domain × model × hardware`) for `8×A100` / `H100` clusters. *(Full A100/H100 training metrics remain explicitly marked PENDING until executed.)*

## 4. Edge Compression & Bench Deployment (`lab-feet` → `L1`/`L2`)

Once a Scientist or Operator policy is aligned and verified in `labbench-posttrain`, [`lab-feet`](https://github.com/yaniguan/lab-feet) targets distillation and low-bit quantization (`int8` and `4-bit` packed weights, `35×` parameter reduction in the baseline MLP probe) so routine sensory monitoring (`lab-ears`), step checking, and tactile reflex loops (`lab-hands`) execute locally next to the bench without round-trip cloud latency.
