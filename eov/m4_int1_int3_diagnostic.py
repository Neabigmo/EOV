"""M4.8 — 评估 `PHASE1_DECISION.md` §4.3 **第 1、3 条 NO-GO 形态**所需的两个登记诊断。

§4.3 说出现下列任一即 NO-GO：
    1. `EOV ≃ stability`（或 ≃ promiscuity）
    2. `EOV ≃ promiscuity`
    3. 换掉未来任务后 parent ordering 基本随机、且不存在可预测结构

但操作化它们的 `INT-1`（第 1/2 条）与 `INT-3`（第 3 条）**都是 ⏳ 未签字的登记默认**。
和 `INT-5` / `OP-8` 一样，本脚本**按登记默认口径算出数字**，供用户签字时直接取用——
**不新增判据、不新增模型族、不新增数据集**。

  INT-1  登记默认：proxy-only 模型对该 proxy 的 held-out `CV-R² >= 0.80`，
         **且**加入全部其他 today-available 信息后 `ΔCV-R² < 0.02`
  INT-3  登记默认：跨任务 parent 排序的 Kendall τ 的 95% CI **覆盖 0**

CV 方案按 `OP-13` 登记默认的精神：**外层 5-fold 固定 split（按 sequence hash）**。
估计量用固定 λ 的 ridge（与 `eov/search_sim.py` 的 MLDE 同族），**不做内层调参**
（内层调参是 OP-13 的完整要求，此处只给最小诊断；这一点必须标注）。
"""
from __future__ import annotations

import csv
import hashlib
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from landscape import MixedAlphabetSpace  # noqa: E402
from search_sim import BUDGETS, POLICIES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEAS = os.path.join(ROOT, "data", "processed", "M2_measurements.parquet")
NPZ2 = os.path.join(ROOT, "data", "processed", "M4_EXP2_V.npz")
OUT_CV = os.path.join(ROOT, "data_registry", "M4_INT1_CV_DIAGNOSTIC.csv")
OUT_TAU = os.path.join(ROOT, "data_registry", "M4_INT3_KENDALL_TAU.csv")

DS = "TEM-1CML"
TODAY_PRIMARY = ("AMP", "781.0")
FUTURES = [("AZT", "0.44"), ("AZT", "36.0")]
PROXIES = ["current_fitness", "known_family_mean", "known_family_worst", "local_robustness",
           "neighbor_informative_frac", "dist_to_best", "n_better_neighbors", "local_ruggedness"]
SALT = "eov-m4-split"          # OP-9 登记默认所要求的 salt；M4 实际用的就是这个
N_FOLD = 5
N_BOOT = 2000


def fold_of(gid: str, salt: str = SALT) -> int:
    return int(hashlib.sha256((salt + "|" + gid).encode("utf-8")).hexdigest()[:8], 16) % N_FOLD


def cv_r2(X: np.ndarray, y: np.ndarray, folds: np.ndarray, lam: float = 1.0) -> float:
    """外层 5-fold 的 CV-R²。估计量 = 固定 λ 的 ridge（y 标准化），**不做内层调参**。"""
    pred = np.full(len(y), np.nan)
    for k in range(N_FOLD):
        te = folds == k
        tr = ~te
        if tr.sum() < 20 or te.sum() < 5:
            continue
        Xtr, ytr = X[tr], y[tr]
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        Ztr = (Xtr - mu) / sd
        Zte = (X[te] - mu) / sd
        ym, ys = ytr.mean(), ytr.std()
        ys = ys if ys > 0 else 1.0
        yz = (ytr - ym) / ys
        A = Ztr.T @ Ztr + lam * np.eye(Ztr.shape[1])
        w = np.linalg.solve(A, Ztr.T @ yz)
        pred[te] = Zte @ w * ys + ym
    m = ~np.isnan(pred)
    if m.sum() < 20:
        return float("nan")
    ss_res = float(((y[m] - pred[m]) ** 2).sum())
    ss_tot = float(((y[m] - y[m].mean()) ** 2).sum())
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


def main() -> int:
    d2 = np.load(NPZ2)
    parents = d2["parents"]
    feats = {k[5:]: d2[k] for k in d2.files if k.startswith("feat_")}
    df = pd.read_parquet(MEAS)
    t = df[df.dataset_id == DS]
    ids = sorted(set(t.genotype_id.astype(str).unique()))
    space = MixedAlphabetSpace.from_masked_profiles([s for s in ids if "X" not in s])
    n = space.space_size()

    def load(tid, cid):
        s = t[(t.task_id == tid) & (t.condition_id == cid)]
        s = s[~s.genotype_id.astype(str).str.contains("X", regex=False)]
        s = s.drop_duplicates("genotype_id")
        v = np.full(n, np.nan)
        idx = np.array([space.index_of(tuple(x)) for x in s.genotype_id.astype(str)], dtype=np.int64)
        ok = s.informative.astype(bool).values
        v[idx[ok]] = pd.to_numeric(s.value_group, errors="coerce").values[ok]
        vv = v[~np.isnan(v)]
        q05, q95 = float(np.percentile(vv, 5)), float(np.percentile(vv, 95))
        return v, (lambda z: (z - q05) / (q95 - q05))

    _, u_today = load(*TODAY_PRIMARY)
    gids = [space.node_id(space.node_from_index(int(x))) for x in parents]
    folds = np.array([fold_of(g) for g in gids])
    print("fold 分布:", np.bincount(folds).tolist(), flush=True)

    # ======================================================== INT-1 / OP-13
    cv_rows = []
    for key in FUTURES:
        _, u_f = load(*key)
        name = "%s@%s" % key
        for si, pol in enumerate(POLICIES):
            for bi, B in enumerate(BUDGETS):
                y = np.array([np.nan if np.isnan(z) else u_f(z)
                              for z in np.nanmean(d2["R_%s_%s" % key][si, bi], axis=1)])
                proxy_today = np.array([np.nan if np.isnan(z) else u_today(z)
                                        for z in np.nanmean(d2["R_AMP_781.0"][si, bi], axis=1)])
                base_cols = {p: feats[p] for p in PROXIES}
                ok = ~np.isnan(y)
                for p in PROXIES:
                    ok &= np.isfinite(base_cols[p])
                ok &= np.isfinite(proxy_today)
                if ok.sum() < 100:
                    continue
                # (a) 单 proxy
                per_proxy = {}
                for p in PROXIES:
                    per_proxy[p] = cv_r2(base_cols[p][ok][:, None], y[ok], folds[ok])
                # (b) 全部 proxy
                Xp = np.column_stack([base_cols[p][ok] for p in PROXIES])
                r2_proxy = cv_r2(Xp, y[ok], folds[ok])
                # (c) 全部 proxy + 今天的 option value
                Xe = np.column_stack([Xp, proxy_today[ok]])
                r2_plus = cv_r2(Xe, y[ok], folds[ok])
                row = dict(future=name, policy=pol, budget=B, n=int(ok.sum()),
                           r2_proxy_only=round(r2_proxy, 4),
                           r2_proxy_plus_today_eov=round(r2_plus, 4),
                           delta_cv_r2=round(r2_plus - r2_proxy, 4))
                for p in PROXIES:
                    row["r2_" + p] = round(per_proxy[p], 4)
                # INT-1：是否"proxy-only 已 ≥0.80 且增量 <0.02"
                row["INT1_proxy_ge_080"] = bool(r2_proxy >= 0.80)
                row["INT1_delta_lt_002"] = bool((r2_plus - r2_proxy) < 0.02)
                row["INT1_EOV_reducible"] = bool(r2_proxy >= 0.80 and (r2_plus - r2_proxy) < 0.02)
                cv_rows.append(row)
        print("  CV 完成 %s (%.0f s)" % (name, 0), flush=True)
    with open(OUT_CV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(cv_rows[0].keys()))
        w.writeheader()
        for r in cv_rows:
            w.writerow(r)
    C = pd.DataFrame(cv_rows)
    print("\nWROTE", OUT_CV, len(cv_rows), "rows")
    print("\n=== INT-1 / OP-13 诊断（greedy_ssm）===")
    g = C[C.policy == "greedy_ssm"]
    print(g[["future", "budget", "r2_proxy_only", "r2_proxy_plus_today_eov",
             "delta_cv_r2", "INT1_EOV_reducible"]].to_string(index=False))
    print("\nproxy-only 的 CV-R² 区间：%.4f ~ %.4f（全部 %d 格）" % (
        C.r2_proxy_only.min(), C.r2_proxy_only.max(), len(C)))
    print("触发 INT-1 'EOV 可归约'（proxy>=0.80 且 Δ<0.02）的格数：%d / %d" % (
        int(C.INT1_EOV_reducible.sum()), len(C)))

    # ======================================================== INT-3
    tau_rows = []
    for si, pol in enumerate(POLICIES):
        for bi, B in enumerate(BUDGETS):
            Vs = {}
            for key in FUTURES:
                _, u_f = load(*key)
                Vs[key] = np.array([np.nan if np.isnan(z) else u_f(z)
                                    for z in np.nanmean(d2["R_%s_%s" % key][si, bi], axis=1)])
            a, b = Vs[FUTURES[0]], Vs[FUTURES[1]]
            m = ~np.isnan(a) & ~np.isnan(b)
            if m.sum() < 50:
                continue
            tau = float(stats.kendalltau(a[m], b[m]).statistic)
            rng = np.random.default_rng(20260919)
            bs = []
            idx = np.flatnonzero(m)
            for _ in range(N_BOOT):
                pick = rng.choice(idx, size=len(idx), replace=True)
                if len(np.unique(a[pick])) < 3 or len(np.unique(b[pick])) < 3:
                    continue
                bs.append(float(stats.kendalltau(a[pick], b[pick]).statistic))
            lo, hi = (np.percentile(bs, [2.5, 97.5]) if len(bs) >= 100
                      else (float("nan"), float("nan")))
            tau_rows.append(dict(
                task_pair="AZT@0.44 ~ AZT@36.0", policy=pol, budget=B, n=int(m.sum()),
                kendall_tau=round(tau, 4), CI_lo=round(float(lo), 4), CI_hi=round(float(hi), 4),
                CI_covers_0=bool(lo == lo and lo <= 0 <= hi),
                INT3_ordering_random=bool(lo == lo and lo <= 0 <= hi),
                spearman=round(float(stats.spearmanr(a[m], b[m]).statistic), 4)))
    with open(OUT_TAU, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(tau_rows[0].keys()))
        w.writeheader()
        for r in tau_rows:
            w.writerow(r)
    T = pd.DataFrame(tau_rows)
    print("\nWROTE", OUT_TAU, len(tau_rows), "rows")
    print("\n=== INT-3 诊断：跨未来任务的 parent 排序 Kendall τ ===")
    print(T[["policy", "budget", "n", "kendall_tau", "CI_lo", "CI_hi", "CI_covers_0",
             "INT3_ordering_random"]].to_string(index=False))
    print("\n'CI 覆盖 0'（= ordering 基本随机）的格数：%d / %d" % (
        int(T.CI_covers_0.sum()), len(T)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
