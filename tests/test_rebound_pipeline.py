"""Lightweight structural and output tests for the rebound figure pipeline."""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from rebound_common import (  # noqa: E402
    FIGURE_DIR,
    PAPER_DIR,
    TABLE_DIR,
    ball_condition_means,
    load_data,
    recomputed_cor,
    validate_frames,
)


def test_expected_rows_protocols_and_unique_ids() -> None:
    master, audit, session2 = load_data()
    assert (len(master), len(audit), len(session2)) == (162, 25, 30)
    assert master["Protocol"].value_counts().to_dict() == {
        "Factorial_3x3_Sealed": 135,
        "Matched_Pressure_10PSI": 27,
    }
    assert session2["Protocol"].value_counts().to_dict() == {
        "Matched_Counterbalanced": 27,
        "Baseline_Control": 3,
    }
    assert not master["Drop_ID"].duplicated().any()
    assert not audit["Drop_ID"].duplicated().any()
    assert not session2["Drop_ID"].duplicated().any()


def test_validation_and_cor_recomputation() -> None:
    master, audit, session2 = load_data()
    result = validate_frames(master, audit, session2)
    assert result.ok
    discrepancy_ids = set(master.loc[(recomputed_cor(master) - master["Calculated_COR_e"]).abs() > 0.0001, "Drop_ID"])
    assert discrepancy_ids == {44, 160}
    assert np.isfinite(recomputed_cor(master)).all()


def test_audit_difference_definitions() -> None:
    _, audit, _ = load_data()
    assert np.allclose(audit["Diff_h0_m"], audit["Annotator2_h0_m"] - audit["Annotator1_h0_m"], atol=1e-12)
    assert np.allclose(audit["Diff_h1_m"], audit["Annotator2_h1_m"] - audit["Annotator1_h1_m"], atol=1e-12)


def test_primary_session2_excludes_controls_and_ball_mean_counts() -> None:
    master, _, session2 = load_data()
    sealed = master.loc[master["Protocol"].eq("Factorial_3x3_Sealed")]
    s1_match = master.loc[master["Protocol"].eq("Matched_Pressure_10PSI")]
    s2_match = session2.loc[session2["Protocol"].eq("Matched_Counterbalanced")]
    assert len(s2_match) == 27
    assert not s2_match["Is_Baseline_Control"].astype(bool).any()
    assert len(ball_condition_means(sealed, ["Target_Press_PSI"])) == 27
    assert len(ball_condition_means(s1_match)) == 9
    assert len(ball_condition_means(s2_match)) == 9


def test_no_provisional_summary_targets_embedded_in_plot_source() -> None:
    source = (ROOT / "analysis" / "make_paper_figures.py").read_text(encoding="utf-8")
    for prohibited in ["0.0351", "0.0304", "0.0284", "0.0366", "0.0308", "0.0301", "0.06776", "0.03646", "53.8"]:
        assert prohibited not in source


def test_all_requested_outputs_exist_and_are_nonempty() -> None:
    figure_stems = [
        "fig1_experimental_design",
        "fig2_sealed_factorial_response",
        "fig2a_sealed_factorial_cor",
        "fig2b_sealed_factorial_pressure",
        "fig3_matched_pressure_replication",
        "fig4_protocol_path_comparison",
        "fig5_annotation_agreement",
        "figS1_release_height_stability",
        "figS2_matched_pressure_control",
        "figS3_run_order_diagnostics",
    ]
    paths = [FIGURE_DIR / f"{stem}.{suffix}" for stem in figure_stems for suffix in ("pdf", "svg", "png")]
    paths += [
        FIGURE_DIR / "figure_includes.tex",
        PAPER_DIR / "figure_captions.md",
        PAPER_DIR / "analysis_summary.md",
        PAPER_DIR / "data_validation_report.txt",
    ]
    for stem in ["table1_design_summary", "table2_condition_summary", "table3_ball_level_contrasts"]:
        paths += [TABLE_DIR / f"{stem}.csv", TABLE_DIR / f"{stem}.tex"]
    missing = [str(path) for path in paths if not path.exists() or path.stat().st_size == 0]
    assert not missing, missing
