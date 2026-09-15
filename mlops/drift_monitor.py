from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DriftMetric:
    feature: str
    psi: float
    mean_shift_std: float
    missing_rate_reference: float
    missing_rate_current: float
    severity: str


@dataclass(frozen=True)
class DriftReport:
    metrics: tuple[DriftMetric, ...]
    max_psi: float
    severe_feature_count: int
    warning_feature_count: int
    deployment_gate: str

    def to_dict(self) -> dict:
        return {
            "metrics": [asdict(x) for x in self.metrics],
            "max_psi": self.max_psi,
            "severe_feature_count": self.severe_feature_count,
            "warning_feature_count": self.warning_feature_count,
            "deployment_gate": self.deployment_gate,
        }


def _edges(reference: pd.Series, bins: int) -> np.ndarray:
    clean = reference.dropna().astype(float).to_numpy()
    if not len(clean):
        return np.array([-np.inf, np.inf])
    quantiles = np.unique(np.quantile(clean, np.linspace(0, 1, bins + 1)))
    if len(quantiles) < 3:
        lo, hi = float(np.min(clean)), float(np.max(clean))
        pad = max(1e-9, abs(hi - lo) * .01 + 1e-9)
        quantiles = np.array([lo - pad, (lo + hi) / 2, hi + pad])
    quantiles[0] = -np.inf
    quantiles[-1] = np.inf
    return quantiles


def population_stability_index(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    edges = _edges(reference, bins)
    ref = pd.cut(reference.astype(float), bins=edges, include_lowest=True).value_counts(normalize=True, sort=False)
    cur = pd.cut(current.astype(float), bins=edges, include_lowest=True).value_counts(normalize=True, sort=False)
    ref_arr = np.clip(ref.to_numpy(dtype=float), 1e-6, 1)
    cur_arr = np.clip(cur.to_numpy(dtype=float), 1e-6, 1)
    return float(np.sum((cur_arr - ref_arr) * np.log(cur_arr / ref_arr)))


def monitor(reference: pd.DataFrame, current: pd.DataFrame, features: Iterable[str]) -> DriftReport:
    metrics: list[DriftMetric] = []
    for feature in features:
        if feature not in reference or feature not in current:
            raise KeyError(f"feature missing from monitoring frame: {feature}")
        ref = reference[feature]
        cur = current[feature]
        psi = population_stability_index(ref, cur)
        ref_std = float(ref.std(skipna=True) or 0.0)
        mean_shift = abs(float(cur.mean(skipna=True) - ref.mean(skipna=True))) / max(1e-9, ref_std)
        ref_missing = float(ref.isna().mean())
        cur_missing = float(cur.isna().mean())
        if psi >= .25 or mean_shift >= 1.0 or abs(cur_missing - ref_missing) >= .10:
            severity = "SEVERE"
        elif psi >= .10 or mean_shift >= .5 or abs(cur_missing - ref_missing) >= .04:
            severity = "WARNING"
        else:
            severity = "NORMAL"
        metrics.append(DriftMetric(feature, psi, mean_shift, ref_missing, cur_missing, severity))

    severe = sum(m.severity == "SEVERE" for m in metrics)
    warning = sum(m.severity == "WARNING" for m in metrics)
    gate = "BLOCK" if severe >= 2 else "REVIEW" if severe or warning >= 2 else "PASS"
    return DriftReport(tuple(metrics), max((m.psi for m in metrics), default=0.0), severe, warning, gate)


def save_report(report: DriftReport, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
