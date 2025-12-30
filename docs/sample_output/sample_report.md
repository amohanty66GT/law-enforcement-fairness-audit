# Sample Analysis Report

**Generated:** 2025-12-29 21:48:26

## Dataset Summary

- **Total Records:** 1,000
- **Date Range:** 2020-01-06 to 2023-12-31
- **Crime Categories:** 5
- **States Represented:** 12

## Geographic Bias Analysis

🚨 **SIGNIFICANT GEOGRAPHIC BIAS DETECTED**

- **Chi-square statistic:** 36.874
- **P-value:** 0.0001
- **Interpretation:** Significant geographic bias detected (p=0.0001). Over-represented states: CA, TX, FL. Under-represented states: NY, PA, IL.

## Category Bias Analysis

✅ **No significant category bias detected**

## Temporal Trend Analysis

- **Categories with significant trends:** 0

## Case Persistence Analysis

✅ **No significant differences in case persistence**

## Weapons in Serious Crimes Analysis

- **Total serious crimes analyzed:** 489
- **Serious crime percentage:** 48.9%
- **Weapon distribution in serious crimes:**
  - Firearm: 55.62%
  - Knife: 23.72%
  - Unknown: 20.65%
- **Unknown weapon information:** 20.7% of serious crimes

**Ethical Note:** Analysis is aggregate-only and avoids tactical insights
**Limitations:** Subject to reporting bias and missing data limitations

## Key Findings

- Geographic bias detected in state representation
- Weapon patterns show firearms most common in serious crimes
- Data quality issues with 20.7% unknown weapon information
- No significant temporal trends in current dataset

## Methodology

This analysis uses statistical tests to identify potential biases:

- **Geographic Analysis:** Chi-square goodness of fit test
- **Category Analysis:** Chi-square test of independence
- **Temporal Analysis:** Pearson correlation analysis
- **Persistence Analysis:** One-way ANOVA
- **Weapons Analysis:** Distribution analysis with data quality metrics

## Limitations

- Analysis based on publicly available data only
- Does not account for all potential confounding variables
- Results should be interpreted within context of data collection methods
- No individual-level tracking or prediction performed
- Subject to reporting bias and missing data limitations