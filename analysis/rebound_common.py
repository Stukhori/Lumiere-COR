"""Shared data loading, validation, and aggregation helpers for paper figures."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
PAPER_DIR = ROOT / "paper"
FIGURE_DIR = PAPER_DIR / "figures"
TABLE_DIR = PAPER_DIR / "tables"

MASTER_FILE = DATA_DIR / "football_rebound_3x3_reconciled_master_data.csv"
AUDIT_FILE = DATA_DIR / "audit_25_videos_blinded.csv"
SESSION2_FILE = DATA_DIR / "matched_pressure_session2_counterbalanced.csv"

BALL_ORDER = ["Ball_A", "Ball_B", "Ball_C"]
TEMP_ORDER = [0, 20, 40]
BALL_LABEL = {"Ball_A": "Ball A", "Ball_B": "Ball B", "Ball_C": "Ball C"}


@dataclass
class ValidationResult:
    critical_errors: list[str]
    warnings: list[str]
    notes: list[str]

    @property
    def ok(self) -> bool:
        return not self.critical_errors


def ensure_output_dirs() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    missing = [str(path) for path in (MASTER_FILE, AUDIT_FILE, SESSION2_FILE) if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required source file(s): " + ", ".join(missing))
    return pd.read_csv(MASTER_FILE), pd.read_csv(AUDIT_FILE), pd.read_csv(SESSION2_FILE)


def recomputed_cor(frame: pd.DataFrame) -> pd.Series:
    return np.sqrt(frame["Rebound_Height_m"] / frame["Release_Height_m"])


def ball_condition_means(
    frame: pd.DataFrame,
    extra_groups: list[str] | None = None,
) -> pd.DataFrame:
    groups = ["Ball_ID", "Target_Temp_C"] + (extra_groups or [])
    numeric = [
        c
        for c in [
            "Calculated_COR_e",
            "Pre_Impact_Press_PSI",
            "Release_Height_m",
            "Rebound_Height_m",
            "Surface_Temp_C",
        ]
        if c in frame.columns
    ]
    return frame.groupby(groups, as_index=False, observed=True)[numeric].mean()


def overall_from_ball_means(ball_means: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    numeric = [
        c
        for c in ["Calculated_COR_e", "Pre_Impact_Press_PSI", "Release_Height_m", "Rebound_Height_m"]
        if c in ball_means.columns
    ]
    return ball_means.groupby(groups, as_index=False, observed=True)[numeric].mean()


def _filename_timestamp(value: str) -> datetime | None:
    match = re.search(r"VID_(\d{8})_(\d{6})", str(value))
    if not match:
        return None
    return datetime.strptime("".join(match.groups()), "%Y%m%d%H%M%S")


def validate_frames(
    master: pd.DataFrame,
    audit: pd.DataFrame,
    session2: pd.DataFrame,
) -> ValidationResult:
    critical: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []
    frames = {
        "Session 1 master": (master, 162),
        "Annotation audit": (audit, 25),
        "Session 2": (session2, 30),
    }
    required_common = [
        "Drop_ID",
        "Protocol",
        "Target_Temp_C",
        "Ball_ID",
        "Pre_Impact_Press_PSI",
        "Release_Height_m",
        "Rebound_Height_m",
        "Calculated_COR_e",
    ]

    for name, (frame, expected) in frames.items():
        if len(frame) != expected:
            critical.append(f"{name}: expected {expected} rows, found {len(frame)}.")
        else:
            notes.append(f"{name}: row count validated ({len(frame)}).")
        absent = [col for col in required_common if col not in frame.columns]
        if absent:
            critical.append(f"{name}: missing required columns: {', '.join(absent)}.")
            continue
        duplicated = frame.loc[frame["Drop_ID"].duplicated(keep=False), "Drop_ID"].tolist()
        if duplicated:
            critical.append(f"{name}: duplicate Drop_ID values: {duplicated}.")
        missing_counts = frame[required_common].isna().sum()
        missing_counts = missing_counts[missing_counts > 0]
        if not missing_counts.empty:
            critical.append(f"{name}: missing required values: {missing_counts.to_dict()}.")
        nonpositive = frame.loc[
            (frame["Release_Height_m"] <= 0) | (frame["Rebound_Height_m"] <= 0), "Drop_ID"
        ].tolist()
        if nonpositive:
            critical.append(f"{name}: non-positive height(s) at Drop_ID {nonpositive}.")
        invalid_order = frame.loc[
            frame["Rebound_Height_m"] >= frame["Release_Height_m"], "Drop_ID"
        ].tolist()
        if invalid_order:
            critical.append(f"{name}: rebound height is not below release height at Drop_ID {invalid_order}.")

        delta = recomputed_cor(frame) - frame["Calculated_COR_e"]
        discrepant = frame.loc[delta.abs() > 0.0001, ["Drop_ID", "Release_Height_m", "Rebound_Height_m", "Calculated_COR_e"]]
        for row in discrepant.itertuples(index=False):
            implied = float(np.sqrt(row.Rebound_Height_m / row.Release_Height_m))
            warnings.append(
                f"{name} Drop {int(row.Drop_ID)}: heights imply COR {implied:.6f}, "
                f"recorded COR is {row.Calculated_COR_e:.4f} (difference {implied-row.Calculated_COR_e:+.6f})."
            )
        if discrepant.empty:
            notes.append(f"{name}: all recorded COR values agree with displayed heights within 0.0001.")

    expected_master_protocols = {"Factorial_3x3_Sealed": 135, "Matched_Pressure_10PSI": 27}
    actual_master_protocols = master.get("Protocol", pd.Series(dtype=str)).value_counts().to_dict()
    if actual_master_protocols != expected_master_protocols:
        critical.append(
            f"Session 1 protocol counts invalid: expected {expected_master_protocols}, found {actual_master_protocols}."
        )
    expected_s2_protocols = {"Matched_Counterbalanced": 27, "Baseline_Control": 3}
    actual_s2_protocols = session2.get("Protocol", pd.Series(dtype=str)).value_counts().to_dict()
    if actual_s2_protocols != expected_s2_protocols:
        critical.append(
            f"Session 2 protocol counts invalid: expected {expected_s2_protocols}, found {actual_s2_protocols}."
        )

    if "Is_Baseline_Control" not in session2.columns:
        critical.append("Session 2: missing Is_Baseline_Control.")
    else:
        control_consistency = session2["Protocol"].eq("Baseline_Control") == session2["Is_Baseline_Control"].astype(bool)
        if not control_consistency.all():
            critical.append("Session 2: Protocol and Is_Baseline_Control disagree.")

    valid_master = {"Factorial_3x3_Sealed", "Matched_Pressure_10PSI"}
    valid_audit = valid_master
    valid_s2 = {"Matched_Counterbalanced", "Baseline_Control"}
    for name, frame, valid in [
        ("Session 1 master", master, valid_master),
        ("Annotation audit", audit, valid_audit),
        ("Session 2", session2, valid_s2),
    ]:
        invalid = sorted(set(frame.get("Protocol", [])) - valid)
        if invalid:
            critical.append(f"{name}: invalid protocol labels: {invalid}.")

    matched = master.loc[master["Protocol"].eq("Matched_Pressure_10PSI")]
    if not matched.empty:
        notes.append(
            "Session 1 matched-pressure pre-impact range: "
            f"{matched['Pre_Impact_Press_PSI'].min():.2f}-{matched['Pre_Impact_Press_PSI'].max():.2f} PSI."
        )

    if {161, 162}.issubset(set(master.get("Drop_ID", []))) and "Video_Filename" in master:
        t161 = _filename_timestamp(master.loc[master["Drop_ID"].eq(161), "Video_Filename"].iloc[0])
        t162 = _filename_timestamp(master.loc[master["Drop_ID"].eq(162), "Video_Filename"].iloc[0])
        if t161 and t162 and t161 > t162:
            warnings.append(
                f"Drop 161 timestamp anomaly: filename time {t161.isoformat(sep=' ')} is later than "
                f"Drop 162 time {t162.isoformat(sep=' ')}."
            )

    audit_required = ["Annotator1_h0_m", "Annotator1_h1_m", "Annotator2_h0_m", "Annotator2_h1_m", "Diff_h0_m", "Diff_h1_m"]
    absent_audit = [col for col in audit_required if col not in audit.columns]
    if absent_audit:
        critical.append(f"Annotation audit: missing audit columns: {', '.join(absent_audit)}.")
    else:
        h0_ok = np.allclose(audit["Diff_h0_m"], audit["Annotator2_h0_m"] - audit["Annotator1_h0_m"], atol=1e-12)
        h1_ok = np.allclose(audit["Diff_h1_m"], audit["Annotator2_h1_m"] - audit["Annotator1_h1_m"], atol=1e-12)
        if not (h0_ok and h1_ok):
            critical.append("Annotation audit: stored differences do not follow Annotator 2 minus Annotator 1.")
        else:
            notes.append("Annotation differences validated as Annotator 2 minus Annotator 1.")

    sealed_means = ball_condition_means(
        master.loc[master["Protocol"].eq("Factorial_3x3_Sealed")], ["Target_Press_PSI"]
    )
    s1_match_means = ball_condition_means(matched)
    s2_exp = session2.loc[session2["Protocol"].eq("Matched_Counterbalanced")]
    s2_match_means = ball_condition_means(s2_exp)
    expected_mean_counts = {
        "Session 1 sealed": (len(sealed_means), 27),
        "Session 1 matched": (len(s1_match_means), 9),
        "Session 2 matched": (len(s2_match_means), 9),
    }
    for name, (actual, expected) in expected_mean_counts.items():
        if actual != expected:
            critical.append(f"{name}: expected {expected} ball-condition means, found {actual}.")
    if len(s2_exp) != 27 or len(session2) - len(s2_exp) != 3:
        critical.append("Session 2 experimental/control separation failed.")
    else:
        notes.append("Session 2 primary means exclude all 3 controls and retain 27 experimental drops.")

    return ValidationResult(critical, warnings, notes)


def write_validation_report(result: ValidationResult) -> Path:
    ensure_output_dirs()
    path = PAPER_DIR / "data_validation_report.txt"
    lines = [
        "Football rebound data validation report",
        "=======================================",
        "",
        f"Status: {'PASS WITH WARNINGS' if result.ok and result.warnings else 'PASS' if result.ok else 'FAIL'}",
        "",
        "CRITICAL ERRORS",
        "---------------",
    ]
    lines.extend([f"- {x}" for x in result.critical_errors] or ["- None."])
    lines.extend(["", "WARNINGS", "--------"])
    lines.extend([f"- {x}" for x in result.warnings] or ["- None."])
    lines.extend(["", "VALIDATED CHECKS / NOTES", "------------------------"])
    lines.extend([f"- {x}" for x in result.notes] or ["- None."])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def matched_contrasts(frame: pd.DataFrame) -> pd.Series:
    means = frame.groupby(["Ball_ID", "Target_Temp_C"], observed=True)["Calculated_COR_e"].mean().unstack()
    return (means[40] - means[0]).reindex(BALL_ORDER)


def audit_stats(audit: pd.DataFrame, height: str) -> dict[str, float]:
    diff_mm = (
        audit[f"Annotator2_{height}_m"] - audit[f"Annotator1_{height}_m"]
    ) * 1000.0
    bias = float(diff_mm.mean())
    sd = float(diff_mm.std(ddof=1))
    return {
        "n": int(diff_mm.size),
        "bias_mm": bias,
        "mad_mm": float(diff_mm.abs().mean()),
        "sd_mm": sd,
        "loa_low_mm": bias - 1.96 * sd,
        "loa_high_mm": bias + 1.96 * sd,
    }
