"""
Streamlit dashboard for fairness and bias audit visualization.
Interactive interface for exploring bias patterns in law enforcement data.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data_ingestion.fbi_wanted import FBIWantedIngestion
from src.data_processing.feature_engineering import FeatureEngineer
from src.analysis.bias_metrics import BiasAnalyzer
from src.dashboard.visualizations import BiasVisualizer

# Page configuration
st.set_page_config(
    page_title="Law Enforcement Data Fairness Audit",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def load_sample_data():
    """Load sample data for demonstration."""
    
    # Try to load processed data from analysis first
    try:
        df = pd.read_csv('output/processed_data.csv')
        # Convert date columns
        df['publication_date'] = pd.to_datetime(df['publication_date'])
        df['modified_date'] = pd.to_datetime(df['modified_date'])
        df['ingestion_date'] = pd.to_datetime(df['ingestion_date'])
        
        # Convert boolean columns
        bool_columns = ['severity_flag', 'public_notice_flag', 'recently_updated', 'has_reward', 'has_images']
        for col in bool_columns:
            if col in df.columns:
                df[col] = df[col].astype(bool)
        
        st.sidebar.success(f"Loaded processed data: {len(df)} records")
        return df
        
    except FileNotFoundError:
        st.sidebar.warning("No processed data found. Run analysis first or using fallback sample data.")
        
        # Fallback to simple sample data
        import numpy as np
        np.random.seed(42)
        
        states = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI']
        
        n_records = 500
        
        sample_data = {
            'uid': [f'wanted_{i:04d}' for i in range(n_records)],
            'title': [f'Case {i}' for i in range(n_records)],
            'description': ['Sample case description'] * n_records,
            'place_of_birth': [f'City, {np.random.choice(states)}' for _ in range(n_records)],
            'publication_date': pd.date_range('2020-01-01', '2023-12-31', periods=n_records),
            'modified_date': pd.date_range('2020-01-01', '2023-12-31', periods=n_records),
            'ingestion_date': pd.Timestamp.now(),
            'reward_text': [f'${np.random.choice([5000, 10000, 25000, None])}' for _ in range(n_records)],
            'images': [[] for _ in range(n_records)],
            'weapon_category': np.random.choice(['firearm', 'knife', 'unknown', 'none'], n_records),
            'severity_flag': np.random.choice([True, False], n_records, p=[0.5, 0.5]),
            'crime_family': np.random.choice(['Violent', 'White Collar', 'Drug Related'], n_records)
        }
        
        df = pd.DataFrame(sample_data)
        df['case_age_days'] = (df['ingestion_date'] - df['publication_date']).dt.days
        
        return df

def main():
    """Main dashboard application."""
    
    # Header
    st.markdown('<div class="main-header">⚖️ Law Enforcement Data Fairness Audit</div>', 
                unsafe_allow_html=True)
    
    # Ethical disclaimer
    st.markdown("""
    <div class="warning-box">
    <strong>⚠️ Ethical Framework:</strong> This analysis examines patterns in public law enforcement data 
    to identify potential biases. We do not track individuals, make predictions about criminality, 
    or deanonymize data. All analysis focuses on aggregate patterns and statistical trends.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar controls
    st.sidebar.header("Analysis Controls")
    
    # Cache clearing button
    if st.sidebar.button("🔄 Refresh Data & Clear Cache"):
        st.cache_data.clear()
        st.rerun()
    
    # Data source selection
    data_source = st.sidebar.selectbox(
        "Data Source",
        ["Sample Data (Demo)", "FBI Wanted API", "Upload CSV"]
    )
    
    # Load data based on selection
    if data_source == "Sample Data (Demo)":
        df = load_sample_data()
        st.sidebar.success(f"Loaded {len(df)} sample records")
    else:
        st.sidebar.info("Live data ingestion not implemented in demo")
        df = load_sample_data()
    
    # Feature engineering
    with st.spinner("Processing data and engineering features..."):
        engineer = FeatureEngineer()
        df_processed = engineer.engineer_features(df)
    
    # Analysis controls
    st.sidebar.subheader("Analysis Parameters")
    
    confidence_level = st.sidebar.slider(
        "Confidence Level", 
        min_value=0.90, 
        max_value=0.99, 
        value=0.95, 
        step=0.01
    )
    
    min_sample_size = st.sidebar.number_input(
        "Minimum Sample Size", 
        min_value=10, 
        max_value=100, 
        value=30
    )
    
    # Year filter
    years = sorted(df_processed['publication_year'].dropna().unique())
    selected_years = st.sidebar.multiselect(
        "Years to Analyze",
        years,
        default=years
    )
    
    # Filter data
    if selected_years:
        df_filtered = df_processed[df_processed['publication_year'].isin(selected_years)]
    else:
        df_filtered = df_processed
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Overview", 
        "🗺️ Geographic Analysis", 
        "📈 Category Analysis", 
        "⏰ Temporal Trends", 
        "🔫 Weapons Analysis",
        "📋 Statistical Results"
    ])
    
    # Initialize analyzer and visualizer
    analyzer = BiasAnalyzer(confidence_level=confidence_level)
    visualizer = BiasVisualizer()
    
    with tab1:
        show_overview(df_filtered, visualizer)
    
    with tab2:
        show_geographic_analysis(df_filtered, analyzer, visualizer, min_sample_size)
    
    with tab3:
        show_category_analysis(df_filtered, analyzer, visualizer)
    
    with tab4:
        show_temporal_analysis(df_filtered, analyzer, visualizer)
    
    with tab5:
        show_weapons_analysis(df_filtered, visualizer)
    
    with tab6:
        show_statistical_results(df_filtered, analyzer, confidence_level)

def show_overview(df, visualizer):
    """Display overview dashboard."""
    
    st.header("Dataset Overview")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Cases", len(df))
    
    with col2:
        st.metric("Crime Categories", df['crime_family'].nunique())
    
    with col3:
        st.metric("States Represented", df['birth_state'].nunique())
    
    with col4:
        avg_age = df['case_age_days'].mean()
        st.metric("Avg Case Age (days)", f"{avg_age:.0f}")
    
    # Distribution charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Crime Category Distribution")
        fig = visualizer.create_category_distribution(df)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Geographic Distribution")
        fig = visualizer.create_geographic_distribution(df)
        st.plotly_chart(fig, use_container_width=True)

def show_geographic_analysis(df, analyzer, visualizer, min_sample_size):
    """Display geographic bias analysis."""
    
    st.header("Geographic Representation Analysis")
    
    if len(df) < min_sample_size:
        st.warning(f"Insufficient data for analysis (need ≥{min_sample_size} records)")
        return
    
    # Run analysis
    with st.spinner("Analyzing geographic patterns..."):
        geo_results = analyzer.analyze_geographic_bias(df)
    
    if 'error' in geo_results:
        st.error(geo_results['error'])
        return
    
    # Display results
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("State Representation vs Population")
        fig = visualizer.create_representation_scatter(geo_results)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Statistical Test Results")
        
        if 'p_value' in geo_results:
            p_val = geo_results['p_value']
            is_significant = geo_results['significant_bias']
            
            st.metric("Chi-Square p-value", f"{p_val:.4f}")
            
            if is_significant:
                st.error("🚨 Significant bias detected")
            else:
                st.success("✅ No significant bias")
            
            st.write("**Interpretation:**")
            st.write(geo_results.get('interpretation', 'No interpretation available'))
    
    # Detailed breakdown
    st.subheader("Detailed State Analysis")
    
    if 'representation_analysis' in geo_results:
        rep_df = pd.DataFrame(geo_results['representation_analysis'])
        
        # Highlight over/under represented states
        def highlight_bias(row):
            if row['over_represented']:
                return ['background-color: #ffcccc'] * len(row)
            elif row['under_represented']:
                return ['background-color: #ccffcc'] * len(row)
            else:
                return [''] * len(row)
        
        styled_df = rep_df.style.apply(highlight_bias, axis=1)
        st.dataframe(styled_df, use_container_width=True)
        
        st.caption("🔴 Red: Over-represented states | 🟢 Green: Under-represented states")

def show_category_analysis(df, analyzer, visualizer):
    """Display category bias analysis."""
    
    st.header("Crime Category Analysis")
    
    # Run analysis
    with st.spinner("Analyzing category patterns..."):
        cat_results = analyzer.analyze_categorical_bias(df)
    
    # Category distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Category Proportions")
        fig = visualizer.create_category_proportions(cat_results)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Case Persistence by Category")
        fig = visualizer.create_persistence_boxplot(df)
        st.plotly_chart(fig, use_container_width=True)
    
    # Statistical results
    if 'p_value' in cat_results:
        st.subheader("Statistical Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Chi-Square p-value", f"{cat_results['p_value']:.4f}")
        
        with col2:
            if cat_results['significant_bias']:
                st.error("🚨 Significant category bias detected")
            else:
                st.success("✅ No significant category bias")

def show_weapons_analysis(df, visualizer):
    """Display weapons in serious crimes analysis."""
    
    st.header("Weapons in Serious Crimes Analysis")
    
    # Ethical disclaimer
    st.markdown("""
    <div class="warning-box">
    <strong>⚠️ Ethical Framework:</strong> This analysis examines weapon patterns in serious crimes 
    at an aggregate level only. No individual-level predictions or tactical insights are provided. 
    Results are subject to reporting bias and missing data limitations.
    </div>
    """, unsafe_allow_html=True)
    
    # Check if we have the required columns
    required_cols = ['severity_flag', 'weapon_category']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        st.error(f"Missing required columns for weapons analysis: {missing_cols}")
        return
    
    # Analysis controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        serious_only = st.checkbox("Serious Crimes Only", value=True)
    
    with col2:
        compare_all = st.checkbox("Compare to All Crimes", value=True)
    
    with col3:
        show_regional = st.checkbox("Show Regional Patterns", value=False)
    
    # Filter data
    if serious_only:
        analysis_df = df[df['severity_flag'] == True]
        if len(analysis_df) == 0:
            st.warning("No serious crimes found in the dataset")
            return
    else:
        analysis_df = df
    
    # Key metrics
    st.subheader("Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_serious = len(df[df['severity_flag'] == True])
        st.metric("Serious Crimes", total_serious)
    
    with col2:
        serious_pct = (total_serious / len(df) * 100) if len(df) > 0 else 0
        st.metric("Serious Crime %", f"{serious_pct:.1f}%")
    
    with col3:
        unknown_weapons = len(analysis_df[analysis_df['weapon_category'] == 'unknown'])
        st.metric("Unknown Weapons", unknown_weapons)
    
    with col4:
        unknown_pct = (unknown_weapons / len(analysis_df) * 100) if len(analysis_df) > 0 else 0
        st.metric("Unknown Weapon %", f"{unknown_pct:.1f}%")
    
    # Weapon distribution charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Weapon Distribution")
        fig1 = visualizer.create_weapons_distribution_chart(df, serious_only=serious_only)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        if compare_all:
            st.subheader("Serious vs All Crimes Comparison")
            fig2 = visualizer.create_weapons_comparison_chart(df)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.subheader("Data Quality: Unknown Weapons Over Time")
            fig2 = visualizer.create_unknown_weapons_trend_chart(df)
            st.plotly_chart(fig2, use_container_width=True)
    
    # Temporal trends
    st.subheader("Weapon Trends Over Time")
    fig3 = visualizer.create_weapons_temporal_chart(df, serious_only=serious_only)
    st.plotly_chart(fig3, use_container_width=True)
    
    # Regional patterns (if requested)
    if show_regional:
        st.subheader("Regional Weapon Patterns")
        fig4 = visualizer.create_weapons_regional_chart(df)
        st.plotly_chart(fig4, use_container_width=True)
    
    # Detailed breakdown
    st.subheader("Detailed Weapon Analysis")
    
    if len(analysis_df) > 0:
        # Weapon category breakdown
        weapon_summary = analysis_df['weapon_category'].value_counts()
        weapon_pct = (weapon_summary / len(analysis_df) * 100).round(2)
        
        summary_df = pd.DataFrame({
            'Weapon Category': weapon_summary.index,
            'Count': weapon_summary.values,
            'Percentage': weapon_pct.values
        })
        
        st.dataframe(summary_df, use_container_width=True)
        
        # Data quality insights
        st.subheader("Data Quality Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Weapon Information Completeness:**")
            completeness_data = {
                'Category': ['Known Weapons', 'Unknown Weapons', 'No Weapon'],
                'Count': [
                    len(analysis_df[~analysis_df['weapon_category'].isin(['unknown', 'none'])]),
                    len(analysis_df[analysis_df['weapon_category'] == 'unknown']),
                    len(analysis_df[analysis_df['weapon_category'] == 'none'])
                ]
            }
            completeness_df = pd.DataFrame(completeness_data)
            st.dataframe(completeness_df)
        
        with col2:
            st.write("**Reporting Limitations:**")
            st.write("• Weapon information may be incomplete in public records")
            st.write("• 'Unknown' category includes cases with missing weapon data")
            st.write("• Reporting practices may vary by jurisdiction and time period")
            st.write("• Analysis excludes individual-level details for privacy")
    
    # Ethical and methodological notes
    st.subheader("Methodology & Limitations")
    
    st.markdown("""
    **Analysis Approach:**
    - Weapon categories extracted from case titles and descriptions using rule-based mapping
    - Serious crimes defined as: homicide, aggravated assault, robbery, kidnapping, rape, terrorism
    - All analysis performed at aggregate level only
    
    **Key Limitations:**
    - **Reporting Bias:** Public records may not reflect complete weapon information
    - **Missing Data:** High percentage of 'unknown' weapons indicates data quality issues
    - **Jurisdictional Variation:** Different agencies may have different reporting standards
    - **Temporal Changes:** Reporting practices may have evolved over time
    
    **Ethical Constraints:**
    - No individual-level predictions or profiling
    - No tactical or operational insights provided
    - Focus on systemic patterns and data quality issues
    - Results intended for policy and transparency purposes only
    """)

def show_temporal_analysis(df, analyzer, visualizer):
    """Display temporal trend analysis."""
    
    st.header("Temporal Trend Analysis")
    
    # Run analysis
    with st.spinner("Analyzing temporal patterns..."):
        temporal_results = analyzer.analyze_temporal_trends(df)
    
    # Yearly trends
    st.subheader("Cases by Year and Category")
    fig = visualizer.create_temporal_trends(temporal_results)
    st.plotly_chart(fig, use_container_width=True)
    
    # Trend statistics
    if 'trend_analysis' in temporal_results:
        st.subheader("Trend Analysis Results")
        
        trend_data = []
        for category, stats in temporal_results['trend_analysis'].items():
            trend_data.append({
                'Category': category,
                'Trend Direction': stats['trend_direction'],
                'Correlation': f"{stats['correlation_with_time']:.3f}",
                'P-value': f"{stats['trend_p_value']:.4f}",
                'Significant': '✅' if stats['significant_trend'] else '❌',
                'Percent Change': f"{stats['percent_change']:.1f}%",
                'Total Cases': stats['total_cases']
            })
        
        trend_df = pd.DataFrame(trend_data)
        st.dataframe(trend_df, use_container_width=True)

def show_statistical_results(df, analyzer, confidence_level):
    """Display comprehensive statistical results."""
    
    st.header("Statistical Analysis Summary")
    
    # Run all analyses
    with st.spinner("Running comprehensive analysis..."):
        geo_results = analyzer.analyze_geographic_bias(df)
        cat_results = analyzer.analyze_categorical_bias(df)
        temporal_results = analyzer.analyze_temporal_trends(df)
        persistence_results = analyzer.analyze_case_persistence(df)
    
    # Summary metrics
    st.subheader("Analysis Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Geographic Bias", 
            "Detected" if geo_results.get('significant_bias') else "Not Detected"
        )
    
    with col2:
        st.metric(
            "Category Bias", 
            "Detected" if cat_results.get('significant_bias') else "Not Detected"
        )
    
    with col3:
        significant_trends = sum(
            1 for stats in temporal_results.get('trend_analysis', {}).values() 
            if stats.get('significant_trend', False)
        )
        st.metric("Significant Trends", significant_trends)
    
    # Detailed results
    st.subheader("Detailed Statistical Results")
    
    results_data = {
        'Analysis Type': [],
        'Test Statistic': [],
        'P-value': [],
        'Significant': [],
        'Interpretation': []
    }
    
    # Geographic results
    if 'p_value' in geo_results:
        results_data['Analysis Type'].append('Geographic Representation')
        results_data['Test Statistic'].append(f"χ² = {geo_results.get('chi_square_statistic', 'N/A'):.3f}")
        results_data['P-value'].append(f"{geo_results['p_value']:.4f}")
        results_data['Significant'].append('Yes' if geo_results['significant_bias'] else 'No')
        results_data['Interpretation'].append(geo_results.get('interpretation', 'N/A'))
    
    # Category results
    if 'p_value' in cat_results:
        results_data['Analysis Type'].append('Category Distribution')
        results_data['Test Statistic'].append(f"χ² = {cat_results.get('chi_square_statistic', 'N/A'):.3f}")
        results_data['P-value'].append(f"{cat_results['p_value']:.4f}")
        results_data['Significant'].append('Yes' if cat_results['significant_bias'] else 'No')
        results_data['Interpretation'].append('Category distribution differs from baseline')
    
    # Persistence results
    if 'anova_p_value' in persistence_results:
        results_data['Analysis Type'].append('Case Persistence')
        results_data['Test Statistic'].append(f"F = {persistence_results.get('anova_f_statistic', 'N/A'):.3f}")
        results_data['P-value'].append(f"{persistence_results['anova_p_value']:.4f}")
        results_data['Significant'].append('Yes' if persistence_results['significant_differences'] else 'No')
        results_data['Interpretation'].append(persistence_results.get('interpretation', 'N/A'))
    
    if results_data['Analysis Type']:
        results_df = pd.DataFrame(results_data)
        st.dataframe(results_df, use_container_width=True)
    
    # Methodology note
    st.subheader("Methodology Notes")
    st.markdown(f"""
    - **Confidence Level**: {confidence_level:.0%}
    - **Geographic Analysis**: Chi-square goodness of fit test comparing state representation to population
    - **Category Analysis**: Chi-square test of independence comparing wanted list to baseline crime statistics
    - **Temporal Analysis**: Pearson correlation analysis for trend detection
    - **Persistence Analysis**: One-way ANOVA comparing case duration across categories
    
    **Limitations**: This analysis is based on publicly available data and may not reflect complete law enforcement activities.
    Results should be interpreted within the context of data availability and collection methods.
    """)

if __name__ == "__main__":
    main()