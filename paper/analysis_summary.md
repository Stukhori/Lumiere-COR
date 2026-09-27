# Analysis summary

## Results generated from the files

- Validated row counts: Session 1 master = 162; annotation audit = 25; Session 2 = 30.
- Session 1 contains 135 sealed-factorial and 27 matched-pressure drops. Session 2 contains 27 matched counterbalanced experimental drops and 3 operational baseline checks.
- Session 1 matched-pressure observed pre-impact range: 9.90–10.07 PSI.
- All primary Session 2 temperature-condition means exclude the three operational checks.

### Exact condition summaries

The full machine-readable values are in `tables/table2_condition_summary.csv`. Means of COR are calculated from the three ball-condition means; the two SD columns distinguish variation across drops from variation across ball-condition means.

```text
                   Protocol   Session  Target_Temp_C  Nominal_Pressure_PSI  N_balls  N_drops  Mean_Surface_Temp_C  Mean_Pre_Impact_Press_PSI  Mean_Release_Height_m  Mean_Rebound_Height_m  Rebound_Height_SD_across_drops_m  Mean_COR_from_ball_means  COR_SD_across_drops  COR_SD_across_ball_condition_means
    Matched counterbalanced Session 2              0             10.000000        3        9                  NaN                   9.972222               2.499889               1.576556                          0.018941                  0.794122             0.004855                            0.005564
    Matched counterbalanced Session 2             20             10.000000        3        9                  NaN                  10.008889               2.499000               1.639444                          0.017861                  0.809956             0.004246                            0.004874
    Matched counterbalanced Session 2             40             10.000000        3        9                  NaN                  10.000000               2.500000               1.708333                          0.015628                  0.826622             0.003942                            0.004504
           Matched pressure Session 1              0             10.000000        3        9             0.666667                   9.986667               2.499667               1.576333                          0.019736                  0.794089             0.005069                            0.005733
           Matched pressure Session 1             20             10.000000        3        9            20.000000                   9.992222               2.499667               1.639000                          0.018702                  0.809733             0.004796                            0.005531
           Matched pressure Session 1             40             10.000000        3        9            38.822222                  10.026667               2.499444               1.702778                          0.019709                  0.825389             0.004701                            0.005308
Operational baseline checks Session 2             20             10.000000        3        3                  NaN                   9.980000               2.500000               1.644333                          0.015567                  0.811000             0.003816                            0.003816
           Sealed factorial Session 1              0              6.000000        3       15             0.880000                   4.687333               2.498867               1.337800                          0.012480                  0.731660             0.003541                            0.004045
           Sealed factorial Session 1              0             10.000000        3       15             0.593333                   8.428000               2.498267               1.506600                          0.016141                  0.776547             0.004270                            0.005037
           Sealed factorial Session 1              0             14.000000        3       15             0.926667                  12.145333               2.498000               1.663467                          0.018165                  0.815973             0.004533                            0.005337
           Sealed factorial Session 1             20              6.000000        3       15            20.000000                   6.004667               2.498733               1.436333                          0.012494                  0.758173             0.003183                            0.003744
           Sealed factorial Session 1             20             10.000000        3       15            20.000000                  10.013333               2.498867               1.646533                          0.015450                  0.811720             0.003807                            0.004490
           Sealed factorial Session 1             20             14.000000        3       15            20.000000                  14.012667               2.499200               1.815200                          0.017753                  0.852233             0.004071                            0.004813
           Sealed factorial Session 1             40              6.000000        3       15            38.460000                   7.281333               2.499600               1.527600                          0.013114                  0.781747             0.003444                            0.004072
           Sealed factorial Session 1             40             10.000000        3       15            38.440000                  11.617333               2.499600               1.781867                          0.011451                  0.844307             0.002680                            0.003168
           Sealed factorial Session 1             40             14.000000        3       15            38.613333                  15.896667               2.498400               1.943667                          0.019338                  0.882007             0.004358                            0.005154
```

### Ball-level 0–40 °C COR contrasts

- Ball A: Session 1 matched 0.035133; Session 2 matched 0.036600; Session 1 sealed 10-PSI path 0.067120.
- Ball B: Session 1 matched 0.030400; Session 2 matched 0.030833; Session 1 sealed 10-PSI path 0.065840.
- Ball C: Session 1 matched 0.028367; Session 2 matched 0.030067; Session 1 sealed 10-PSI path 0.070320.

Across-ball means were 0.031300 in Session 1 matched and 0.032500 in Session 2 matched, a Session 2 minus Session 1 difference of +0.001200. The replicated direction was positive for every ball in both sessions.

### Sealed-versus-matched path comparison

The across-ball 0–40 °C change was 0.067760 for the Session 1 sealed nominal-10-PSI path and 0.031300 for the Session 1 matched path. Their descriptive difference was 0.036460; expressed relative to the sealed-path change, this is 53.81%. This percentage compares observed experimental paths and must not be interpreted as the fraction caused by gas pressure or as a material-effect decomposition.

### Drop 161 sensitivity

With all Session 1 matched drops, Ball C's contrast was 0.028367 and the across-ball mean contrast was 0.031300. Excluding Drop 161 changes Ball C's contrast to 0.029217 and the across-ball mean to 0.031583 (change +0.000283). The exclusion is a sensitivity check only; the source row remains intact.

### Blinded annotation agreement

- Release height ($h_0$): n = 25, bias = -0.52 mm, mean absolute difference = 0.84 mm, 95% limits of agreement = -2.32 to +1.28 mm.
- Rebound height ($h_1$): n = 25, bias = -0.24 mm, mean absolute difference = 0.80 mm, 95% limits of agreement = -2.52 to +2.04 mm.

## Validation warnings

- Session 1 master Drop 44: heights imply COR 0.810502, recorded COR is 0.8099 (difference +0.000602).
- Session 1 master Drop 160: heights imply COR 0.819756, recorded COR is 0.8200 (difference -0.000244).
- Drop 161 timestamp anomaly: filename time 2026-09-26 22:03:37 is later than Drop 162 time 2026-09-26 17:06:54.

Values affected by recorded-COR versus displayed-height discrepancies remain provisional pending source-data correction. Figures and summaries use the recorded `Calculated_COR_e` values and never overwrite them.

## Interpretive statements

Across all three balls, COR increased from 0 to 40 °C in both matched-pressure sessions, and the magnitudes were closely aligned. The sealed nominal-10-PSI path showed a larger descriptive change while its measured pre-impact pressure rose strongly with temperature. These observations compare experimental paths; they do not identify a casing-hysteresis mechanism or partition causal contributions.

## Limitations and statistical units

The study contains three physical balls. Repeated drops are technical/repeated observations, not independent footballs. Overall plotted condition means therefore average the three ball-condition means, and no confidence intervals or p-values treat individual drops as independent units. Across-ball SDs describe variation among only three ball means and are not population-level uncertainty estimates. Run-order displays are exploratory; a visually small trend cannot establish absence of drift. Session 2 controls used different balls and are not treated as a same-ball time series.
