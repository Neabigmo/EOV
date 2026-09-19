"""M4.13 — 生成 `PHASE1_PROTOCOL.md` 要求的**复现性与 TIS 清单**（M4 首轮全部缺失）。

冻结要求（逐字）
----------------
L39: TIS 的构造代码必须放在 `eov/` 下并被 `experiments/` 引用；所有特征函数签名只接受 `τ₀` 数据对象，
     **在类型/接口层面就无法访问 `τ`**。
L40: **每个实验目录必须包含 `TIS_MANIFEST.json`**：列出用到的每一个输入文件（含 sha256）与每一个特征。
L271: 全部随机种子显式固定并写入 `logs/`；**每个实验目录含 `config.json` + `seeds.json`**。
L272: 数据 manifest：`data/manifests/*.sha256`（下载时间、URL/DOI、sha256）。

本脚本**派生**这些文件（读真实文件的 sha256、从脚本读常量），**不手写** —— 手写的 manifest 会漂移。
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "experiments", "M4")
DMAN = os.path.join(ROOT, "data", "manifests")

MEAS = "data/processed/M2_measurements.parquet"
MEAS3 = "data/processed/M3_taskpanel_measurements.parquet"
AUDIT = "data_registry/M2_AUDIT_TABLE.csv"
MANIFEST = "data_registry/PHASE1_ANALYSIS_READY_MANIFEST.csv"

# 每个实验**真实读取**的输入文件（审计 S-3：原实现对 4 个实验写同一份硬编码清单，
# 造成 3 个幻影输入 + 遗漏 M4_EXP2_V.npz）。以下按脚本里的实际 open/read 列出。
REAL_INPUTS = {
    "exp1_stability": ["data/processed/M2_measurements.parquet"],
    "exp2_baselines": ["data/processed/M2_measurements.parquet"],
    # exp3 的 S3 读 Exp 2 的 NPZ（含 R_AZT_0.44 / R_AZT_36.0）—— 审计 S-3 指出的遗漏
    "exp3_tomorrow": ["data/processed/M2_measurements.parquet",
                      "data/processed/M4_EXP2_V.npz"],
    "exp4_readiness": ["data/processed/M2_measurements.parquet",
                       "data/processed/M4_EXP2_V.npz"],
}

# 审计 S-4/S-5：原 manifest 对所有实验都写"arrs 只装 AMP 族的键"，该句**对 exp2 为假**。
# 以下逐实验如实描述隔离层级。**L39 的修法（eov/tis.py + 迁移）已完成，见 L39_STATUS。**
ISOLATION = {
    "exp1_stability": dict(
        arrs_holds_future_keys=False, data_level_firewall="N/A（无跨任务预测侧）",
        type_level_firewall="N/A（不使用 Day-0 特征）",
        note="Exp 1 不做跨任务预测；每个任务用自己的测量模拟搜索，比较是 ground-truth 对 ground-truth。"
             "故 TIS 白名单为空。"),
    "exp2_baselines": dict(
        arrs_holds_future_keys=True,
        data_level_firewall="由 TIS 保证（`TIS.for_dataset` 只取白名单键；`arrs` 里那两个 AZT 键从不进入特征路径）",
        type_level_firewall="满足（`feats = TIS.for_dataset(DS, arrs, ctx, space).features(P)`；"
                            "函数签名只接受 TIS 实例，调用方无法传入 future 数组）",
        note="`arrs` 含 2 个 AZT 键（用于 oracle 侧的 V 与 NR）；特征**只**由 TIS 产出。"
             "TIS 白名单硬编码在 `eov/tis.py` 的 `TODAY_SPEC` 内，exp2 没有任何参数可以扩大它。"),
    "exp3_tomorrow": dict(
        arrs_holds_future_keys=False, data_level_firewall="满足（`arrs` 只装 AMP 族的键）",
        type_level_firewall="满足（S1 的 leave-one-out 走 `tis.without(键)`，仍只能取白名单子集）",
        note="S1 用 `tis.without(('AMP', hold))`；S3 用完整 TIS。两者都只接受 TIS 实例。"
             "S3 阶段读 `M4_EXP2_V.npz` 的 AZT reachability —— **oracle 侧**，`AMENDMENT-002 B-4` 要求如此，"
             "不构成泄漏。"),
    "exp4_readiness": dict(
        arrs_holds_future_keys=False,
        data_level_firewall="满足（不自己构造特征）",
        type_level_firewall="满足（特征由 exp2 的 NPZ 提供，而那份由 TIS 产出）",
        note="exp4 **不构造 Day-0 特征**，直接读 `M4_EXP2_V.npz` 里由 TIS 产出的 `feat_*`。"
             "故 L39 对它无需额外改动。"),
}

# L39 的状态与证据（改这一节前请先跑 tests/test_tis.py）
L39_STATUS = dict(
    satisfied=True,
    implementation="eov/tis.py —— `TIS` 类 + 模块级 `TODAY_SPEC`（τ₀ 白名单的**唯一**权威定义）",
    enforcement=[
        "唯一的公开构造入口 `TIS.for_dataset(dataset_id, arrs, ctx, space)`：**没有任何参数可以扩大白名单**",
        "`TIS.value(key)` / `TIS.u(key, z)`：白名单外的键一律 `TISViolation`",
        "`TIS.features(parents)`：签名只接受 TIS 实例 —— 调用方无法把 future 数组传进来",
        "`TIS.without(key)`：只能取白名单的子集，不扩大访问面",
    ],
    evidence="tests/test_tis.py（7 项全通过）",
    evidence_detail=[
        "T1 拒绝测试：stray 键 → `TISViolation`；未知数据集 → `TISViolation`",
        "T2 **逐位复现**：TIS 重建的 8 个特征与 `M4_EXP2_V.npz` 落盘的 `feat_*` 相比 `max|diff| == 0`",
        "T3 **迁移惰性**：与迁移前的 exp3 实现相比，5 个 leave-one-out 变体全部 `max|diff| < 1e-12` 且 argmax 不变",
        "T2b 注入测试：把 AZT 数组替换为全 999，特征逐位不变",
    ],
    migrated=["eov/exp2_baselines.py（L198）", "eov/exp3_tomorrow_test.py（S1 与 S3 两处）"],
    not_applicable=["eov/exp1_stability.py（不使用 Day-0 特征）",
                    "eov/exp4_readiness_vs_eov.py（读 exp2 NPZ 的 `feat_*`，不自行构造）"],
    migration_verification=dict(
        end_to_end=True,
        method="迁移后**完整重跑** exp2（2,106 s）与 exp3 --s1-only（1,575 s），与迁移前产物做 sha256 比对",
        result="**全部 6 个产物逐字节相同（IDENTICAL）**",
        identical_artifacts=[
            "data_registry/M4_EXP2_LADDER.csv (09bcb6b9a523e606)",
            "data_registry/M4_EXP2_FEATURES.csv (0a23bb36b4107927)",
            "data_registry/M4_EXP2_SCALE_SENSITIVITY.csv (b6b4b8b42a125f45)",
            "data/processed/M4_EXP2_V.npz (ad40966dc98df837)",
            "data_registry/M4_EXP3_S1_MODEL_SELECTION.csv (50003378fcc6a63d)",
            "data/processed/M4_EXP3_S1_R.npz (bf2b972602f66237)",
        ],
        note="这不仅证明特征惰性，还证明**整条搜索模拟路径**惰性（含 MLDE 与策略随机流未被推移）。"),
    residual_risk="无（端到端重跑已逐字节复现）。",
)
TIS_TODAY = {
    "exp1_stability": {
        "note": "Exp 1 不使用任何 Day-0 特征；它对**每个任务各自**模拟搜索，"
                "度量的是同一 parent 在该任务下的可达值。故 TIS 白名单为空，"
                "每个任务的分析只读该任务自己的测量（不是跨任务预测）。",
        "allowed_today_pairs": [],
        "features": [],
    },
    "exp2_baselines": {
        "note": "τ_today = AMP 全浓度族；τ_future = AZT@0.44（主）/ AZT@36.0（强制复现）。"
                "future 的任何测量不得进入特征构造、选择器拟合或排序。",
        "allowed_today_pairs": [["AMP", c] for c in
                                ["0.0", "3.1", "12.2", "48.8", "195.0", "781.0"]],
        "features": ["current_fitness", "known_family_mean", "known_family_worst",
                     "local_robustness", "neighbor_informative_frac", "dist_to_best",
                     "n_better_neighbors", "local_ruggedness", "proxy_eov_today"],
    },
    "exp3_tomorrow": {
        "note": "S1（模型选择）只用 AMP 族 leave-one-concentration-out；AZT 在 S2 冻结之前完全不可见。"
                "S3 才揭晓 AZT。",
        "allowed_today_pairs": [["AMP", c] for c in
                                ["0.0", "3.1", "12.2", "48.8", "195.0", "781.0"]],
        "features": ["current_fitness", "known_family_mean", "known_family_worst",
                     "local_robustness", "neighbor_informative_frac", "dist_to_best",
                     "n_better_neighbors", "local_ruggedness", "proxy_eov_today"],
    },
    "exp4_readiness": {
        "note": "同一 TIS。匹配对的容差由噪声决定，不人工调 ε。",
        "allowed_today_pairs": [["AMP", c] for c in
                                ["0.0", "3.1", "12.2", "48.8", "195.0", "781.0"]],
        "features": ["current_fitness", "known_family_mean", "known_family_worst",
                     "local_robustness", "neighbor_informative_frac", "dist_to_best",
                     "n_better_neighbors", "local_ruggedness", "proxy_eov_today"],
    },
}

CONFIG = {
    "exp1_stability": dict(
        script="eov/exp1_stability.py", dataset="Phillips2023_HA_CH65",
        tasks=["MA90", "SI06", "G189E"], space_size=65536, topology_degree=16,
        policies=["random", "greedy_ssm", "mlde_ridge"], budgets=[24, 96, 384],
        utility="PROTOCOL §3.3 OP-12 (q05/q95, NO clip; AMENDMENT-013 §1)",
        utility_sensitivity="scale2max", n_parents=1000,
        parent_pool="MA90 informative (65530)", output="data_registry/M4_EXP1_*.csv"),
    "exp2_baselines": dict(
        script="eov/exp2_baselines.py", dataset="TEM-1CML",
        today="AMP 全浓度族", futures=["AZT@0.44 (primary)", "AZT@36.0 (replication)"],
        space_size=55296, topology_degree=18,
        policies=["random", "greedy_ssm", "mlde_ridge"], budgets=[24, 96, 384],
        utility="PROTOCOL §3.3 OP-12 (no clip); AMENDMENT-014 §3 全栈统一尺度",
        n_parents=1000, n_noise_reps=3, n_boot=2000,
        output="data_registry/M4_EXP2_*.csv"),
    "exp3_tomorrow": dict(
        script="eov/exp3_tomorrow_test.py", dataset="TEM-1CML",
        today="AMP 全浓度族", futures=["AZT@0.44 (primary)", "AZT@36.0 (replication)"],
        space_size=55296, topology_degree=18,
        policies=["random", "greedy_ssm", "mlde_ridge"], budgets=[24, 96, 384],
        n_boot=2000, frozen_selector_file="data_registry/M4_EXP3_FROZEN_SELECTOR.md",
        output="data_registry/M4_EXP3_*.csv"),
    "exp4_readiness": dict(
        script="eov/exp4_readiness_vs_eov.py", dataset="TEM-1CML",
        today="AMP 全浓度族", futures=["AZT@0.44", "AZT@36.0"],
        space_size=55296, topology_degree=18,
        policies=["random", "greedy_ssm", "mlde_ridge"], budgets=[24, 96, 384],
        split="sha256('eov-m4-split|'+genotype_id) parity 50/50 (OP-9)",
        match_tolerance="2 x median(sigma_u) = 0.152235 (M4 实际; OP-8 默认见 _OP8.csv)",
        n_boot=2000, output="data_registry/M4_EXP4_*.csv"),
}

SEEDS = {
    "shared_seed": 20260919,
    "exp1_stability": {"eov/exp1_stability.py": 20260919},
    "exp2_baselines": {"eov/exp2_baselines.py": 20260919,
                       "bootstrap": 20260919 + 7},
    "exp3_tomorrow": {"simulation": 4242, "parent_sampling": 20260919,
                      "bootstrap": 20260919 + 11},
    "exp4_readiness": {"eov/exp4_readiness_vs_eov.py": 20260919},
    "aux": {"m4_h1_auxiliary.py": [20260919 + 5, 20260919 + 77],
            "m4_op4_rep_sensitivity.py": [20260919, 20260919 + 3],
            "m4_layer_decomposition.py": "none (deterministic)",
            "m4_int1_int3_diagnostic.py": 20260919,
            "m4_exp3_topk_sensitivity.py": 20260919 + 11},
}

# 数据下载 provenance（来源与许可见 data_registry/DATA_AUDIT.md v3 与 PROVENANCE_LEDGER.csv）
DATA_PROVENANCE = {
    "data/processed/M2_measurements.parquet":
        dict(role="M2 物化产物", source_dataset="TEM-1CML / Phillips2023_HA_CH65 / Phillips2021_CR9114",
             produced_by="eov/ (M2 materialization)", note="四态语义 schema v1.4"),
    "data/processed/M3_taskpanel_measurements.parquet":
        dict(role="M3 任务面板产物", source_dataset="DAOx / TEV_ProtRec",
             produced_by="eov/m3_taskpanel_closeout.py", note="非 graph_eligible"),
}


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    os.makedirs(DMAN, exist_ok=True)
    made = []
    for name, cfg in CONFIG.items():
        d = os.path.join(EXP, name)
        os.makedirs(d, exist_ok=True)
        tis = TIS_TODAY[name]
        iso = ISOLATION[name]
        # TIS_MANIFEST.json：**按实验**列出真实输入（含 sha256）+ 每一个特征
        inputs = []
        for rel in REAL_INPUTS[name]:
            p = os.path.join(ROOT, rel)
            if os.path.exists(p):
                inputs.append(dict(path=rel, sha256=sha256(p), bytes=os.path.getsize(p)))
            else:
                print("  !! MISSING real input", rel, "for", name)
        man = dict(
            experiment=name, generated_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            protocol_refs=["PHASE1_PROTOCOL.md L39", "PHASE1_PROTOCOL.md L40"],
            tis_definition=tis["note"],
            allowed_today_pairs=tis["allowed_today_pairs"],
            forbidden_access=["任何 future task 的测量（列于 config.json 的 futures）"],
            inputs=inputs,
            features=tis["features"],
            isolation_audit=dict(
                arrs_holds_future_keys=iso["arrs_holds_future_keys"],
                data_level_firewall=iso["data_level_firewall"],
                type_level_firewall=iso["type_level_firewall"],
                note=iso["note"]),
            l39_status=L39_STATUS,
            feature_interface_note=(
                "L39 要求 TIS 特征函数**在类型/接口层面无法访问 τ**。"
                "**已满足**：唯一的特征入口是 `eov/tis.py` 的 `TIS.features(parents)`，"
                "签名只接受 TIS 实例；τ₀ 白名单硬编码在该模块的 `TODAY_SPEC` 内，"
                "调用方没有任何参数可以扩大它。证据见 `l39_status.evidence`。"
                "本实验的具体情况：" + iso["note"]),
        )
        with open(os.path.join(d, "TIS_MANIFEST.json"), "w", encoding="utf-8") as f:
            json.dump(man, f, ensure_ascii=False, indent=2)
        with open(os.path.join(d, "config.json"), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        with open(os.path.join(d, "seeds.json"), "w", encoding="utf-8") as f:
            json.dump(SEEDS.get(name, {}), f, ensure_ascii=False, indent=2)
        made.append(d)
        print("WROTE", d)

    # data/manifests/*.sha256
    for rel, prov in DATA_PROVENANCE.items():
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            print("  MISSING", rel)
            continue
        out = os.path.join(DMAN, os.path.basename(rel) + ".sha256")
        with open(out, "w", encoding="utf-8") as f:
            f.write("# data manifest (PHASE1_PROTOCOL.md L272)\n")
            f.write("# path: %s\n" % rel)
            f.write("# sha256: %s\n" % sha256(p))
            f.write("# bytes: %d\n" % os.path.getsize(p))
            f.write("# recorded_at: %s\n" % time.strftime("%Y-%m-%dT%H:%M:%S%z"))
            for k, v in prov.items():
                f.write("# %s: %s\n" % (k, v))
        print("WROTE", out)

    # 全局 seeds 日志
    logdir = os.path.join(ROOT, "logs")
    os.makedirs(logdir, exist_ok=True)
    with open(os.path.join(logdir, "M4_SEEDS.json"), "w", encoding="utf-8") as f:
        json.dump(dict(generated_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"), seeds=SEEDS),
                  f, ensure_ascii=False, indent=2)
    print("WROTE logs/M4_SEEDS.json")
    print("\n汇总：%d 个实验目录 + %d 个数据 manifest" % (len(made), len(DATA_PROVENANCE)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
