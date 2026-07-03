# Stataskills Call Matrix

- Total cases: 55
- Passed: 55
- Failed: 0
- Public tools with primary PASS: 38 / 38

## Cases

| Status | Kind | Tool | Case | Seconds | Summary / Error |
|---|---|---|---|---:|---|
| PASS | primary | `read_csv` | `read_csv.primary` | 0.001 | DataFrame shape=(800, 4) |
| PASS | primary | `describe` | `describe.primary` | 0.003 | dict keys=['Length_of_Stay_days'] |
| PASS | primary | `calculate_statistic` | `calculate_statistic.primary` | 0.002 | 15.130500000000001 |
| PASS | primary | `check_missing_values` | `check_missing_values.primary` | 0.002 | dict keys=['Age', 'Cholesterol'] |
| PASS | primary | `detect_outliers` | `detect_outliers.primary` | 0.002 | dict keys=['Length_of_Stay_days'] |
| PASS | primary | `check_column_type_is` | `check_column_type_is.primary` | 0.001 | dict keys=['Sex'] |
| PASS | primary | `show_csv_info_en` | `show_csv_info_en.primary` | 0.002 | "\n        Dataset name\n    hospital_stay.csv\n        Dataset first 5 rows:\n     Length_of_Stay_days  Patient_Age  Severity_Score  Is_Surgical\n            7 |
| PASS | primary | `read_file` | `read_file.primary.txt` | 0.0 | 'stataskills verification text file\n' |
| PASS | branch | `read_file` | `read_file.branch.csv` | 0.0 | list len=3 |
| PASS | branch | `read_file` | `read_file.branch.md` | 0.0 | '# stataskills verification\n' |
| PASS | primary | `correlation_analysis` | `correlation_analysis.primary.pearson` | 0.001 | dict keys=['type', 'shape', 'columns', 'head'] |
| PASS | branch | `correlation_analysis` | `correlation_analysis.branch.partial` | 0.005 | dict keys=['type', 'shape', 'columns', 'head'] |
| PASS | primary | `ci_normal` | `ci_normal.primary.mean` | 0.0 | list len=2 |
| PASS | branch | `ci_normal` | `ci_normal.branch.variance` | 0.0 | list len=2 |
| PASS | primary | `ci_two_normal` | `ci_two_normal.primary.mean_diff` | 0.0 | list len=2 |
| PASS | branch | `ci_two_normal` | `ci_two_normal.branch.var_ratio` | 0.0 | list len=2 |
| PASS | primary | `contingency_test` | `contingency_test.primary.chisquare` | 0.005 | dict keys=['method', 'statistic', 'p_value', 'dof'] |
| PASS | branch | `contingency_test` | `contingency_test.branch.fisher` | 0.003 | dict keys=['method', 'odds_ratio', 'p_value'] |
| PASS | branch | `contingency_test` | `contingency_test.branch.mantel` | 0.006 | dict keys=['method', 'common_odds_ratio', 'ci95', 'p_value'] |
| PASS | primary | `ks_test` | `ks_test.primary.one_sample` | 0.003 | dict keys=['test', 'column', 'distribution', 'statistic', 'p_value'] |
| PASS | branch | `ks_test` | `ks_test.branch.two_sample` | 0.002 | dict keys=['test', 'columns', 'statistic', 'p_value'] |
| PASS | primary | `mood_variance_test` | `mood_variance_test.primary` | 0.001 | dict keys=['method', 'statistic', 'p_value'] |
| PASS | primary | `nonparametric_test` | `nonparametric_test.primary.mannwhitney` | 0.002 | dict keys=['method', 'statistic', 'p_value'] |
| PASS | branch | `nonparametric_test` | `nonparametric_test.branch.wilcoxon` | 0.001 | dict keys=['method', 'statistic', 'p_value'] |
| PASS | branch | `nonparametric_test` | `nonparametric_test.branch.kruskal` | 0.002 | dict keys=['method', 'statistic', 'p_value'] |
| PASS | primary | `fdr_control_df` | `fdr_control_df.primary.bh` | 0.003 | dict keys=['type', 'shape', 'columns', 'head'] |
| PASS | branch | `fdr_control_df` | `fdr_control_df.branch.by` | 0.002 | dict keys=['type', 'shape', 'columns', 'head'] |
| PASS | primary | `fwer_control_df` | `fwer_control_df.primary.bonferroni` | 0.002 | dict keys=['type', 'shape', 'columns', 'head'] |
| PASS | branch | `fwer_control_df` | `fwer_control_df.branch.holm` | 0.008 | dict keys=['type', 'shape', 'columns', 'head'] |
| PASS | primary | `simple_linear_regression` | `simple_linear_regression.primary` | 0.01 | dict keys=['model', 'intercept', 'coefficient', 'r_squared', 'p_value', 'summary'] |
| PASS | primary | `multivariable_linear_regression` | `multivariable_linear_regression.primary` | 0.007 | dict keys=['model', 'coefficients', 'pvalues', 'r_squared', 'adj_r_squared', 'vif'] |
| PASS | primary | `run_glm` | `run_glm.primary.gaussian` | 0.006 | dict keys=['method', 'model', 'coefficients', 'std_errors', 'pvalues', 'aic', 'bic', 'pseudo_r2'] |
| PASS | branch | `run_glm` | `run_glm.branch.logistic` | 0.009 | dict keys=['method', 'model', 'coefficients', 'std_errors', 'pvalues', 'aic', 'bic', 'pseudo_r2'] |
| PASS | branch | `run_glm` | `run_glm.branch.poisson` | 0.028 | dict keys=['method', 'model', 'coefficients', 'std_errors', 'pvalues', 'aic', 'bic', 'pseudo_r2'] |
| PASS | primary | `huber_regression` | `huber_regression.primary` | 0.006 | dict keys=['method', 'model', 'coefficients', 'std_errors', 'pvalues', 'scale', 'converged'] |
| PASS | primary | `advanced_regression` | `advanced_regression.primary` | 0.035 | dict keys=['method', 'model', 'best_alpha', 'coefficients', 'r2', 'rmse', 'y_test', 'y_pred'] |
| PASS | primary | `sparse_pca_analysis` | `sparse_pca_analysis.primary` | 0.104 | dict keys=['component_matrix', 'reduced_data', 'top_features_per_component'] |
| PASS | primary | `test_stationarity` | `test_stationarity.primary.adf` | 0.005 | dict keys=['method', 'statistic', 'p_value', 'stationary'] |
| PASS | branch | `test_stationarity` | `test_stationarity.branch.kpss` | 0.001 | dict keys=['method', 'statistic', 'p_value', 'stationary'] |
| PASS | primary | `decompose_stl` | `decompose_stl.primary` | 0.002 | dict keys=['method', 'model', 'trend_mean', 'trend_std', 'seasonal_mean', 'resid_var'] |
| PASS | primary | `auto_arima_modeling` | `auto_arima_modeling.primary` | 1.728 | dict keys=['method', 'model', 'order', 'seasonal_order', 'aic', 'bic', 'aicc', 'coefficients'] |
| PASS | primary | `kaplan_meier_plot` | `kaplan_meier_plot.primary` | 0.012 | dict keys=['A', 'B'] |
| PASS | primary | `logrank_test_compare` | `logrank_test_compare.primary` | 0.011 | dict keys=['type', 'shape', 'columns', 'head'] |
| PASS | primary | `fit_cox_model` | `fit_cox_model.primary` | 0.043 | dict keys=['method', 'model', 'coefficients', 'hazard_ratios', 'pvalues', 'ci95_lower', 'ci95_upper', 'model_info'] |
| PASS | primary | `ab_ttest` | `ab_ttest.primary` | 0.003 | dict keys=['method', 'group_A_mean', 'group_B_mean', 't_statistic', 'p_value', 'conclusion'] |
| PASS | primary | `bootstrap_abtest` | `bootstrap_abtest.primary` | 0.118 | dict keys=['method', 'observed_difference', 'ci_lower', 'ci_upper', 'significant', 'conclusion'] |
| PASS | primary | `ab_power_analysis` | `ab_power_analysis.primary.proportion` | 0.002 | 10 |
| PASS | branch | `ab_power_analysis` | `ab_power_analysis.branch.mean` | 0.001 | 199 |
| PASS | primary | `bayesian_inference` | `bayesian_inference.primary.binomial` | 0.0 | dict keys=['posterior_mean', 'credible_interval', 'posterior_dist'] |
| PASS | branch | `bayesian_inference` | `bayesian_inference.branch.normal` | 0.0 | dict keys=['posterior_mean', 'credible_interval', 'posterior_dist'] |
| PASS | primary | `bayesian_linear_regression` | `bayesian_linear_regression.primary` | 0.004 | dict keys=['method', 'model', 'posterior_mean', 'posterior_std', 'credible_interval', 'P(coef < 0)'] |
| PASS | primary | `fit_hierarchical_model` | `fit_hierarchical_model.primary` | 1.374 | dict keys=['model', 'trace', 'summary'] |
| PASS | primary | `estimate_ATT_with_psm` | `estimate_ATT_with_psm.primary` | 0.014 | dict keys=['ATT', 'n_matched', 'matched_data'] |
| PASS | primary | `estimate_did_effect` | `estimate_did_effect.primary` | 0.016 | dict keys=['DID_coefficient', 'p_value', 'conf_int', 'model', 'placebo'] |
| PASS | primary | `synthetic_control` | `synthetic_control.primary` | 0.013 | dict keys=['time', 'treated', 'synthetic', 'treatment_effect', 'weights'] |
