# Lumiere football rebound figures

This repository contains the trial-level data, reproducible analysis scripts, and paper figures for the football coefficient-of-restitution study.

## View the results

- Open `paper/analysis_summary.md` for the numerical results and interpretation.
- Open `paper/data_validation_report.txt` for the data checks and warnings.
- Open `paper/figure_captions.md` for manuscript-ready captions.
- Open any `paper/figures/*.png` for a quick preview. The corresponding PDF and SVG files are vector versions for publication.
- Open `paper/tables/*.csv` in Excel, Google Sheets, or a text editor. The `.tex` versions can be inserted into LaTeX.

## Import into Overleaf

Upload the `paper/figures` folder to an Overleaf project, keeping its name `figures` relative to the paper's main `.tex` file. Then use, for example:

```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=\linewidth]{figures/fig3_matched_pressure_replication.pdf}
  \caption{Insert the Figure 3 caption from figure_captions.md.}
  \label{fig:matched-replication}
\end{figure}
```

`paper/figures/figure_includes.tex` contains commented examples for all five main figures. The LaTeX tables are in `paper/tables/`.

## Reproduce the figures and tables

From the repository root, install the packages in `requirements.txt` in a Python environment, then run:

```bash
python analysis/validate_rebound_data.py
python analysis/make_paper_figures.py
python -m pytest -q
```

The scripts read the three CSVs in `data/` and regenerate all figures, tables, captions, and summaries. The source CSVs are preserved unchanged.
