#!/usr/bin/env python3
"""
Simplified script to run fairness and bias audit without database dependencies.
"""

import sys
import os
import argparse
from datetime import datetime
import logging
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_ingestion.fbi_wanted import FBIWantedIngestion
from data_ingestion.fbi_crime_data import FBICrimeDataIngestion
from data_processing.feature_engineering import FeatureEngineer
from analysis.bias_metrics import BiasAnalyzer
from analysis.weapons_analysis import WeaponsAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main execution function."""
    
    parser = argparse.ArgumentParser(description='Run fairness and bias audit analysis')
    parser.add_argument('--data-source', choices=['fbi', 'sample'], 
                       default='sample', help='Data source to use')
    parser.add_argument('--max-pages', type=int, default=10, 
                       help='Maximum pages to fetch from FBI API')
    parser.add_argument('--confidence-level', type=float, default=0.95,
                       help='Confidence level for statistical tests')
    parser.add_argument('--output-dir', default='output',
                       help='Directory for output files')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    logger.info("Starting fairness and bias audit analysis")
    logger.info(f"Configuration: {vars(args)}")
    
    try:
        # Step 1: Data Ingestion
        logger.info("Step 1: Data Ingestion")
        wanted_df = ingest_data(args.data_source, args.max_pages)
        
        if wanted_df.empty:
            logger.error("No data ingested. Exiting.")
            return
        
        logger.info(f"Ingested {len(wanted_df)} wanted persons records")
        
        # Step 2: Feature Engineering
        logger.info("Step 2: Feature Engineering")
        engineer = FeatureEngineer()
        
        # Also ingest crime data for baseline comparison
        crime_ingestion = FBICrimeDataIngestion()
        crime_df = crime_ingestion.fetch_offense_data([2020, 2021, 2022, 2023])
        
        processed_df = engineer.engineer_features(wanted_df, crime_df)
        logger.info(f"Feature engineering complete. Shape: {processed_df.shape}")
        
        # Save processed data to CSV
        processed_df.to_csv(os.path.join(args.output_dir, 'processed_data.csv'), index=False)
        crime_df.to_csv(os.path.join(args.output_dir, 'crime_baseline.csv'), index=False)
        
        # Step 3: Bias Analysis
        logger.info("Step 3: Bias Analysis")
        analyzer = BiasAnalyzer(confidence_level=args.confidence_level)
        
        # Geographic bias analysis
        geo_results = analyzer.analyze_geographic_bias(processed_df)
        logger.info(f"Geographic analysis complete. Significant bias: {geo_results.get('significant_bias', 'N/A')}")
        
        # Category bias analysis
        cat_results = analyzer.analyze_categorical_bias(processed_df, crime_df)
        logger.info(f"Category analysis complete. Significant bias: {cat_results.get('significant_bias', 'N/A')}")
        
        # Temporal trend analysis
        temporal_results = analyzer.analyze_temporal_trends(processed_df)
        significant_trends = sum(
            1 for stats in temporal_results.get('trend_analysis', {}).values() 
            if stats.get('significant_trend', False)
        )
        logger.info(f"Temporal analysis complete. Significant trends: {significant_trends}")
        
        # Case persistence analysis
        persistence_results = analyzer.analyze_case_persistence(processed_df)
        logger.info(f"Persistence analysis complete. Significant differences: {persistence_results.get('significant_differences', 'N/A')}")
        
        # Weapons analysis
        logger.info("Step 3b: Weapons in Serious Crimes Analysis")
        weapons_analyzer = WeaponsAnalyzer()
        weapons_results = weapons_analyzer.analyze_weapon_patterns(processed_df)
        logger.info(f"Weapons analysis complete. Serious crimes analyzed: {weapons_results.get('total_serious_crimes', 'N/A')}")
        
        # Generate weapons summary
        weapons_summary = weapons_analyzer.generate_weapons_summary(weapons_results)
        logger.info(f"Weapons summary: {weapons_summary}")
        
        # Step 4: Save Results
        logger.info("Step 4: Saving Results")
        
        results = {
            'geographic': geo_results,
            'categorical': cat_results,
            'temporal': temporal_results,
            'persistence': persistence_results,
            'weapons': weapons_results
        }
        
        save_results(results, args.output_dir)
        
        # Step 5: Generate Summary Report
        logger.info("Step 5: Generating Summary Report")
        generate_summary_report(results, processed_df, args.output_dir)
        
        logger.info("Analysis complete!")
        logger.info(f"Results saved to: {args.output_dir}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

def ingest_data(data_source, max_pages):
    """Ingest data based on source configuration."""
    
    if data_source == 'fbi':
        logger.info("Ingesting data from FBI Wanted API")
        ingestion = FBIWantedIngestion()
        return ingestion.fetch_wanted_data(max_pages=max_pages)
    else:  # sample data
        logger.info("Generating sample data for demonstration")
        return generate_sample_data()

def generate_sample_data():
    """Generate sample data for testing and demonstration."""
    
    import pandas as pd
    import numpy as np
    
    np.random.seed(42)
    
    states = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI', 'WA', 'AZ']
    
    # More realistic crime scenarios with varied descriptions
    crime_scenarios = [
        # Serious crimes with weapon indicators
        {'type': 'Armed Bank Robbery', 'desc': 'Suspect entered bank with handgun and demanded money from teller'},
        {'type': 'Aggravated Assault', 'desc': 'Victim attacked with knife during altercation outside bar'},
        {'type': 'Murder Investigation', 'desc': 'Homicide victim found with gunshot wounds, suspect fled scene'},
        {'type': 'Shooting Incident', 'desc': 'Multiple shots fired during robbery, firearm recovered at scene'},
        {'type': 'Assault with Weapon', 'desc': 'Suspect struck victim with baseball bat causing serious injuries'},
        {'type': 'Armed Robbery', 'desc': 'Convenience store robbed at gunpoint by masked suspect'},
        {'type': 'Kidnapping Case', 'desc': 'Victim abducted at gunpoint from parking lot'},
        {'type': 'Domestic Violence', 'desc': 'Suspect threatened victim with knife during domestic dispute'},
        
        # Non-serious crimes without weapons
        {'type': 'Drug Trafficking', 'desc': 'Large quantity of narcotics seized during traffic stop'},
        {'type': 'Cyber Crime', 'desc': 'Computer fraud scheme targeting elderly victims online'},
        {'type': 'Money Laundering', 'desc': 'Financial investigation into suspicious banking transactions'},
        {'type': 'Tax Evasion', 'desc': 'Failure to report income and pay federal taxes over multiple years'},
        {'type': 'Wire Fraud', 'desc': 'Fraudulent investment scheme conducted via electronic communications'},
        {'type': 'Identity Theft', 'desc': 'Suspect used stolen personal information to open credit accounts'},
        {'type': 'Embezzlement', 'desc': 'Employee stole funds from company accounts over two year period'},
        
        # Mixed cases with some ambiguity
        {'type': 'Robbery Investigation', 'desc': 'Store clerk reported theft by unknown suspect'},
        {'type': 'Assault Case', 'desc': 'Victim injured during fight at local establishment'},
        {'type': 'Burglary', 'desc': 'Residence broken into while owners were away on vacation'},
        {'type': 'Vehicle Theft', 'desc': 'Car stolen from shopping mall parking lot'},
        {'type': 'Vandalism', 'desc': 'Property damage reported at commercial building'}
    ]
    
    n_records = 1000
    
    # Create more realistic sample data
    sample_data = []
    
    for i in range(n_records):
        # Introduce geographic bias - overrepresent certain states
        if i < n_records * 0.35:  # 35% from CA, TX, FL (reduced from 40%)
            state = np.random.choice(['CA', 'TX', 'FL'], p=[0.5, 0.3, 0.2])  # CA most common
        else:
            state = np.random.choice(states)
        
        # Select crime scenario - mix of serious and non-serious
        scenario = np.random.choice(crime_scenarios)
        
        # More realistic publication date distribution
        # Recent bias but not as extreme
        if np.random.random() < 0.55:  # 55% recent cases (reduced from 60%)
            pub_date = pd.Timestamp('2023-01-01') + pd.Timedelta(days=np.random.randint(0, 365))
        elif np.random.random() < 0.3:  # 30% from 2022
            pub_date = pd.Timestamp('2022-01-01') + pd.Timedelta(days=np.random.randint(0, 365))
        else:  # 15% from 2020-2021
            pub_date = pd.Timestamp('2020-01-01') + pd.Timedelta(days=np.random.randint(0, 730))
        
        sample_data.append({
            'uid': f'sample_{i:04d}',
            'title': f'{scenario["type"]} Case {i}',
            'description': scenario['desc'],
            'place_of_birth': f'City, {state}',
            'publication_date': pub_date,
            'modified_date': pub_date + pd.Timedelta(days=np.random.randint(0, 30)),
            'ingestion_date': pd.Timestamp.now(),
            'reward_text': f'${np.random.choice([5000, 10000, 25000])}' if np.random.random() > 0.4 else None,
            'images': [f'image_{i}.jpg'] if np.random.random() > 0.6 else []
        })
    
    df = pd.DataFrame(sample_data)
    df['case_age_days'] = (df['ingestion_date'] - df['publication_date']).dt.days
    
    return df

def save_results(results, output_dir):
    """Save analysis results to files."""
    
    # Save to JSON files
    for analysis_type, result in results.items():
        output_file = os.path.join(output_dir, f'{analysis_type}_analysis.json')
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_types(obj):
            if hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif hasattr(obj, 'tolist'):  # numpy array
                return obj.tolist()
            elif hasattr(obj, 'isoformat'):  # datetime
                return obj.isoformat()
            return obj
        
        # Recursively convert types
        def recursive_convert(data):
            if isinstance(data, dict):
                return {k: recursive_convert(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [recursive_convert(item) for item in data]
            else:
                return convert_types(data)
        
        converted_result = recursive_convert(result)
        
        with open(output_file, 'w') as f:
            json.dump(converted_result, f, indent=2, default=str)
        
        logger.info(f"Saved {analysis_type} results to {output_file}")

def generate_summary_report(results, df, output_dir):
    """Generate a summary report of the analysis."""
    
    report_file = os.path.join(output_dir, 'fairness_audit_report.md')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Law Enforcement Data Fairness & Bias Audit Report\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Dataset summary
        f.write("## Dataset Summary\n\n")
        f.write(f"- **Total Records:** {len(df):,}\n")
        f.write(f"- **Date Range:** {df['publication_date'].min().strftime('%Y-%m-%d')} to {df['publication_date'].max().strftime('%Y-%m-%d')}\n")
        f.write(f"- **Crime Categories:** {df['crime_family'].nunique()}\n")
        f.write(f"- **States Represented:** {df['birth_state'].nunique()}\n\n")
        
        # Geographic analysis
        geo_results = results['geographic']
        f.write("## Geographic Bias Analysis\n\n")
        
        if 'significant_bias' in geo_results:
            if geo_results['significant_bias']:
                f.write("🚨 **SIGNIFICANT GEOGRAPHIC BIAS DETECTED**\n\n")
            else:
                f.write("✅ **No significant geographic bias detected**\n\n")
            
            f.write(f"- **Chi-square statistic:** {geo_results.get('chi_square_statistic', 'N/A'):.3f}\n")
            f.write(f"- **P-value:** {geo_results.get('p_value', 'N/A'):.4f}\n")
            f.write(f"- **Interpretation:** {geo_results.get('interpretation', 'N/A')}\n\n")
        
        # Category analysis
        cat_results = results['categorical']
        f.write("## Category Bias Analysis\n\n")
        
        if 'significant_bias' in cat_results:
            if cat_results['significant_bias']:
                f.write("🚨 **SIGNIFICANT CATEGORY BIAS DETECTED**\n\n")
            else:
                f.write("✅ **No significant category bias detected**\n\n")
        
        # Temporal trends
        temporal_results = results['temporal']
        f.write("## Temporal Trend Analysis\n\n")
        
        if 'trend_analysis' in temporal_results:
            significant_trends = [
                cat for cat, stats in temporal_results['trend_analysis'].items()
                if stats.get('significant_trend', False)
            ]
            
            f.write(f"- **Categories with significant trends:** {len(significant_trends)}\n")
            
            if significant_trends:
                f.write("- **Trending categories:**\n")
                for cat in significant_trends:
                    stats = temporal_results['trend_analysis'][cat]
                    direction = stats['trend_direction']
                    f.write(f"  - {cat}: {direction} trend (p={stats['trend_p_value']:.4f})\n")
            f.write("\n")
        
        # Case persistence
        persistence_results = results['persistence']
        f.write("## Case Persistence Analysis\n\n")
        
        if 'significant_differences' in persistence_results:
            if persistence_results['significant_differences']:
                f.write("🚨 **SIGNIFICANT DIFFERENCES IN CASE PERSISTENCE DETECTED**\n\n")
                f.write(f"- **Interpretation:** {persistence_results.get('interpretation', 'N/A')}\n\n")
            else:
                f.write("✅ **No significant differences in case persistence**\n\n")
        
        # Weapons analysis
        weapons_results = results['weapons']
        f.write("## Weapons in Serious Crimes Analysis\n\n")
        
        if 'error' not in weapons_results:
            f.write(f"- **Total serious crimes analyzed:** {weapons_results.get('total_serious_crimes', 'N/A')}\n")
            f.write(f"- **Serious crime percentage:** {weapons_results.get('serious_crime_percentage', 'N/A'):.1f}%\n")
            
            if 'weapon_distribution' in weapons_results:
                weapon_dist = weapons_results['weapon_distribution']['percentages']
                f.write("- **Weapon distribution in serious crimes:**\n")
                for weapon, pct in weapon_dist.items():
                    f.write(f"  - {weapon.replace('_', ' ').title()}: {pct}%\n")
            
            if 'data_quality' in weapons_results:
                data_quality = weapons_results['data_quality']
                unknown_pct = data_quality['unknown_weapon_percentage']
                f.write(f"- **Unknown weapon information:** {unknown_pct:.1f}% of serious crimes\n")
            
            f.write(f"\n**Ethical Note:** {weapons_results.get('ethical_note', 'N/A')}\n")
            f.write(f"**Limitations:** {weapons_results.get('limitations', 'N/A')}\n\n")
        else:
            f.write(f"Analysis could not be completed: {weapons_results['error']}\n\n")
        
        # Key findings
        f.write("## Key Findings\n\n")
        
        findings = []
        if geo_results.get('significant_bias'):
            findings.append("Geographic bias detected in state representation")
        if cat_results.get('significant_bias'):
            findings.append("Category bias detected in crime type distribution")
        if len([cat for cat, stats in temporal_results.get('trend_analysis', {}).items() 
                if stats.get('significant_trend', False)]) > 0:
            findings.append("Significant temporal trends identified")
        if persistence_results.get('significant_differences'):
            findings.append("Differences in case persistence across categories")
        
        if findings:
            for finding in findings:
                f.write(f"- {finding}\n")
        else:
            f.write("- No significant biases detected in this analysis\n")
        
        f.write("\n")
        
        # Methodology
        f.write("## Methodology\n\n")
        f.write("This analysis uses statistical tests to identify potential biases:\n\n")
        f.write("- **Geographic Analysis:** Chi-square goodness of fit test\n")
        f.write("- **Category Analysis:** Chi-square test of independence\n")
        f.write("- **Temporal Analysis:** Pearson correlation analysis\n")
        f.write("- **Persistence Analysis:** One-way ANOVA\n\n")
        
        # Limitations
        f.write("## Limitations\n\n")
        f.write("- Analysis based on publicly available data only\n")
        f.write("- Does not account for all potential confounding variables\n")
        f.write("- Results should be interpreted within context of data collection methods\n")
        f.write("- No individual-level tracking or prediction performed\n\n")
    
    logger.info(f"Summary report saved to {report_file}")

if __name__ == "__main__":
    main()