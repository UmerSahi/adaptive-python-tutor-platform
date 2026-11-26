"""Knowledge Tracing Model Comparison (Day 2, Task 1):
Compares 4 models using a strict student-level train/test split:
1. Baseline (per-concept historical mean)
2. BKT (Bayesian Knowledge Tracing fitted via L-BFGS-B MLE per concept)
3. PFA (Performance Factor Analysis: logistic regression on prior successes/failures)
4. DKT (Deep Knowledge Tracing: PyTorch LSTM over interaction sequences)

Metrics: ROC-AUC, Accuracy, RMSE.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from scipy.optimize import minimize
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, accuracy_score, root_mean_squared_error
from sklearn.model_selection import GroupShuffleSplit

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"


def split_by_student(df: pd.DataFrame, test_size: float = 0.2, seed: int = 42):
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(gss.split(df, groups=df["student_id"]))
    return df.iloc[train_idx].copy(), df.iloc[test_idx].copy()


# ---------------------------------------------------------------------------
# 1. Baseline: Per-Concept Historical Mean
# ---------------------------------------------------------------------------
def run_baseline(train_df: pd.DataFrame, test_df: pd.DataFrame) -> np.ndarray:
    global_mean = train_df["correct"].mean()
    concept_means = train_df.groupby("concept_id")["correct"].mean().to_dict()
    return test_df["concept_id"].map(lambda c: concept_means.get(c, global_mean)).to_numpy()


# ---------------------------------------------------------------------------
# 2. BKT: Bayesian Knowledge Tracing (per-concept HMM)
# ---------------------------------------------------------------------------
def _bkt_neg_log_lik(params: np.ndarray, sequences: list[list[int]]) -> float:
    p_l0, p_t, p_g, p_s = params
    eps = 1e-6
    nll = 0.0
    for seq in sequences:
        p_l = p_l0
        for obs in seq:
            p_corr = p_l * (1.0 - p_s) + (1.0 - p_l) * p_g
            p_corr = np.clip(p_corr, eps, 1.0 - eps)
            nll -= obs * np.log(p_corr) + (1 - obs) * np.log(1.0 - p_corr)
            if obs == 1:
                p_l_post = (p_l * (1.0 - p_s)) / p_corr
            else:
                p_l_post = (p_l * p_s) / (1.0 - p_corr)
            p_l = p_l_post + (1.0 - p_l_post) * p_t
    return float(nll)


def fit_and_predict_bkt(train_df: pd.DataFrame, test_df: pd.DataFrame) -> np.ndarray:
    bkt_params: dict[str, tuple[float, float, float, float]] = {}
    bounds = [(0.05, 0.85), (0.01, 0.50), (0.01, 0.35), (0.01, 0.35)]
    init = np.array([0.30, 0.15, 0.15, 0.10])

    for cid, grp in train_df.groupby("concept_id"):
        seqs = [s["correct"].tolist() for _, s in grp.groupby("student_id")]
        res = minimize(_bkt_neg_log_lik, init, args=(seqs,), method="L-BFGS-B", bounds=bounds)
        bkt_params[cid] = tuple(res.x)

    preds = np.zeros(len(test_df))
    test_sorted = test_df.sort_values(["student_id", "week", "attempt_num"])
    pred_map = {}

    for (sid, cid), grp in test_sorted.groupby(["student_id", "concept_id"], sort=False):
        p_l0, p_t, p_g, p_s = bkt_params.get(cid, (0.30, 0.15, 0.15, 0.10))
        p_l = p_l0
        for idx, row in grp.iterrows():
            p_corr = p_l * (1.0 - p_s) + (1.0 - p_l) * p_g
            pred_map[idx] = float(np.clip(p_corr, 1e-4, 1.0 - 1e-4))
            obs = int(row["correct"])
            if obs == 1:
                p_l_post = (p_l * (1.0 - p_s)) / max(1e-6, p_corr)
            else:
                p_l_post = (p_l * p_s) / max(1e-6, 1.0 - p_corr)
            p_l = p_l_post + (1.0 - p_l_post) * p_t

    for pos, idx in enumerate(test_df.index):
        preds[pos] = pred_map[idx]
    return preds


# ---------------------------------------------------------------------------
# 3. PFA: Performance Factor Analysis
# ---------------------------------------------------------------------------
def _add_pfa_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["student_id", "week", "attempt_num"]).copy()
    df["prior_succ"] = df.groupby(["student_id", "concept_id"])["correct"].cumsum() - df["correct"]
    df["prior_fail"] = (
        df.groupby(["student_id", "concept_id"]).cumcount() - df["prior_succ"]
    )
    return df


def fit_and_predict_pfa(train_df: pd.DataFrame, test_df: pd.DataFrame) -> np.ndarray:
    tr = _add_pfa_features(train_df)
    te = _add_pfa_features(test_df)

    concepts = sorted(train_df["concept_id"].unique())
    c_to_idx = {c: i for i, c in enumerate(concepts)}

    def make_X(d: pd.DataFrame) -> np.ndarray:
        X = np.zeros((len(d), len(concepts) + 2), dtype=np.float32)
        for row_i, (_, r) in enumerate(d.iterrows()):
            ci = c_to_idx.get(r["concept_id"])
            if ci is not None:
                X[row_i, ci] = 1.0
            X[row_i, -2] = r["prior_succ"]
            X[row_i, -1] = r["prior_fail"]
        return X

    clf = LogisticRegression(max_iter=500, C=1.0)
    clf.fit(make_X(tr), tr["correct"].to_numpy())
    probs = clf.predict_proba(make_X(te))[:, 1]
    prob_series = pd.Series(probs, index=te.index)
    return prob_series.loc[test_df.index].to_numpy()


# ---------------------------------------------------------------------------
# 4. DKT: Deep Knowledge Tracing (PyTorch LSTM)
# ---------------------------------------------------------------------------
class _SeqDataset(Dataset):
    def __init__(self, sequences):
        self.sequences = sequences

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        return self.sequences[idx]


class DKTModel(nn.Module):
    def __init__(self, num_concepts: int, hidden_dim: int = 64):
        super().__init__()
        self.num_concepts = num_concepts
        self.emb = nn.Embedding(num_concepts * 2 + 1, 32, padding_idx=0)
        self.lstm = nn.LSTM(32, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, num_concepts)

    def forward(self, x):
        h, _ = self.lstm(self.emb(x))
        return torch.sigmoid(self.fc(h))


def fit_and_predict_dkt(
    train_df: pd.DataFrame, test_df: pd.DataFrame, epochs: int = 6, seed: int = 42
) -> np.ndarray:
    torch.manual_seed(seed)
    concepts = sorted(train_df["concept_id"].unique())
    c_to_idx = {c: i for i, c in enumerate(concepts)}
    n_c = len(concepts)

    def build_seqs(df: pd.DataFrame):
        seqs = []
        for _, grp in df.sort_values(["student_id", "week", "attempt_num"]).groupby("student_id"):
            c_ids = [c_to_idx[c] for c in grp["concept_id"]]
            corr = grp["correct"].tolist()
            idxs = grp.index.tolist()
            # Input token at t uses interaction at t-1 (0 = start token)
            in_tokens = [0] + [c_ids[t] + 1 + (n_c if corr[t] == 1 else 0) for t in range(len(c_ids) - 1)]
            seqs.append((in_tokens, c_ids, corr, idxs))
        return seqs

    train_seqs = build_seqs(train_df)
    test_seqs = build_seqs(test_df)

    model = DKTModel(n_c, hidden_dim=64)
    opt = torch.optim.Adam(model.parameters(), lr=3e-3)
    bce = nn.BCELoss()

    model.train()
    for _ in range(epochs):
        np.random.shuffle(train_seqs)
        for i in range(0, len(train_seqs), 32):
            batch = train_seqs[i : i + 32]
            max_len = max(len(s[0]) for s in batch)
            x_pad = torch.zeros((len(batch), max_len), dtype=torch.long)
            y_c = torch.zeros((len(batch), max_len), dtype=torch.long)
            y_v = torch.zeros((len(batch), max_len), dtype=torch.float32)
            mask = torch.zeros((len(batch), max_len), dtype=torch.bool)
            for b, (inp, cid, cor, _) in enumerate(batch):
                L = len(inp)
                x_pad[b, :L] = torch.tensor(inp, dtype=torch.long)
                y_c[b, :L] = torch.tensor(cid, dtype=torch.long)
                y_v[b, :L] = torch.tensor(cor, dtype=torch.float32)
                mask[b, :L] = True

            out = model(x_pad)
            pred_c = out.gather(2, y_c.unsqueeze(-1)).squeeze(-1)
            loss = bce(pred_c[mask], y_v[mask])
            opt.zero_grad()
            loss.backward()
            opt.step()

    model.eval()
    pred_map = {}
    with torch.no_grad():
        for inp, cid, _, idxs in test_seqs:
            x = torch.tensor([inp], dtype=torch.long)
            out = model(x)[0]
            for t, orig_idx in enumerate(idxs):
                pred_map[orig_idx] = float(out[t, cid[t]].item())

    return np.array([pred_map[i] for i in test_df.index])


def run_kt_comparison() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "learner_interactions.csv")
    train_df, test_df = split_by_student(df, test_size=0.2, seed=42)
    y_true = test_df["correct"].to_numpy()

    models = {
        "Baseline (Concept Mean)": run_baseline(train_df, test_df),
        "BKT (EM/MLE)": fit_and_predict_bkt(train_df, test_df),
        "PFA (Logistic)": fit_and_predict_pfa(train_df, test_df),
        "DKT (PyTorch LSTM)": fit_and_predict_dkt(train_df, test_df),
    }

    rows = []
    for name, y_prob in models.items():
        y_pred = (y_prob >= 0.5).astype(int)
        rows.append(
            {
                "Model": name,
                "AUC": round(float(roc_auc_score(y_true, y_prob)), 4),
                "Accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
                "RMSE": round(float(root_mean_squared_error(y_true, y_prob)), 4),
            }
        )

    res_df = pd.DataFrame(rows).sort_values("AUC", ascending=False)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    res_df.to_csv(OUTPUTS_DIR / "kt_model_comparison.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = np.arange(len(res_df))
    w = 0.25
    ax.bar(x - w, res_df["AUC"], w, label="AUC", color="#3b82f6")
    ax.bar(x, res_df["Accuracy"], w, label="Accuracy", color="#10b981")
    ax.bar(x + w, res_df["RMSE"], w, label="RMSE", color="#f59e0b")
    ax.set_xticks(x)
    ax.set_xticklabels(res_df["Model"], rotation=15, ha="right")
    ax.set_ylim(0, 1.0)
    ax.set_title("Knowledge Tracing Model Comparison (Student-Level Split)", fontweight="bold")
    ax.legend()
    plt.tight_layout()
    fig.savefig(OUTPUTS_DIR / "kt_model_comparison.png", dpi=150)
    plt.close(fig)

    print(res_df.to_string(index=False))
    return res_df


if __name__ == "__main__":
    run_kt_comparison()
