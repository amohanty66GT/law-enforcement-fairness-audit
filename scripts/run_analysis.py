#!/usr/bin/env python3
"""
Main script to run the complete fairness and bias audit pipeline.
Orchestrates data ingestion, processing, analysis, and reporting.
"""

import sys
import os
import argparse
from datetime import datetime
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_ingestion.fbi_wanted import FBIWantedIngestion
from data_ingestion.fbi_crime_data import FBICrimeDataIngestion
from data_processing.feature_engineering import FeatureEngineer
from analysis.bias_metrics import BiasAnalyzer
from database.connection import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main execution function."""
    
    parser = argparse.ArgumentParser(description='Run fairness and bias audit analysis')
    parser.add_argument('--data-source', choices=['fbi', 'sample', 'database'], 
                       default='sample', help='Data source to use')
    parser.add_argument('--max-pages', type=int, default=10, 
                       help='Maximum pages to fetch from FBI API')
    parser.add_argument('--confidence-level', type=float, default=0.95,
                       help='Confidence level for statistical tests')
    parser.add_argument('--save-to-db', action='store_true',
                       help='Save results to database')
    parser.add_argument('--db-type', choices=['postgresql', 'duckdb'], 
                       default='duckdb', help='Database type')
    parser.add_argument('--output-dir', default='output',
                       help='Directory for output files')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    logger.info("Starting fairness and bias audit analysis")
    logger.info(f"Configuration: {vars(args)}")
    
    # Initialize components
    db_manager = None
    if args.save_to_db:
        db_manager = DatabaseManager(db_type=args.db_type)
        db_manager.create_tables()
    
    try:
        # Step 1: Data Ingestion
        logger.info("Step 1: Data Ingestion")
        wanted_df = ingest_data(args.data_source, args.max_pages, db_manager)
        
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
        
        if args.save_to_db:
            db_manager.save_wanted_data(processed_df, if_exists='replace')
            db_manager.save_crime_data(crime_df, if_exists='replace')
        
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
        
        # Step 4: Save Results
        logger.info("Step 4: Saving Results")
        
        results = {
            'geographic': geo_results,
            'categorical': cat_results,
            'temporal': temporal_results,
            'persistence': persistence_results
        }
        
        save_results(results, args.output_dir, db_manager)
        
        # Step 5: Generate Summary Report
        logger.info("Step 5: Generating Summary Report")
        generate_summary_report(results, processed_df, args.output_dir)
        
        logger.info("Analysis complete!")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise
        
    finally:
        if db_manager:
            db_manager.close()

def ingest_data(data_source, max_pages, db_manager):
    """Ingest data based on source configuration."""
    
    if data_source == 'fbi':
        logger.info("Ingesting data from FBI Wanted API")
        ingestion = FBIWantedIngestion()
        return ingestion.fetch_wanted_data(max_pages=max_pages)
        
    elif data_source == 'database':
        if not db_manager:
            raise ValueError("Database manager required for database data source")
        logger.info("Loading data from database")
        return db_manager.load_wanted_data()
        
    else:  # sample data
        logger.info("Generating sample data for demonstration")
        return generate_sample_data()

def generate_sample_data():
    """Generate sample data for testing and demonstration."""
    
    import pandas as pd
    import numpy as np
    
    np.random.seed(42)
    
    states = ['CA', 'TX', 'FL', 'NY', 'PA', 'IL', 'OH', 'GA', 'NC', 'MI', 'WA', 'AZ']
    crime_types = ['Bank Fraud', 'Armed Robbery', 'Drug Trafficking', 'Cyber Crime', 
                   'Money Laundering', 'Kidnapping', 'Murder', 'Racketeering']
    
    n_records = 1000
    
    # Create biased sample data to demonstrate detection capabilities
    sample_data = []
    
    for i in range(n_records):
        # Introduce geographic bias - overrepresent certain states
        if i < n_records * 0.4:  # 40% from CA, TX, FL
            state = np.random.choice(['CA', 'TX', 'FL'])
        else:
            state = np.random.choice(states)
        
        # Introduce category bias - overrepresent white collar crimes
        if i < n_records * 0.3:  # 30% white collar
            crime_type = np.random.choice(['Bank Fraud', 'Money Laundering', 'Cyber Crime'])
        else:
            crime_type = np.random.choice(crime_types)
        
        # Random publication date with temporal bias
        if i < n_records * 0.6:  # More recent cases
            pub_date = pd.Timestamp('2023-01-01') + pd.Timedelta(days=np.random.randint(0, 365))
        else:
            pub_date = pd.Timestamp('2020-01-01') + pd.Timedelta(days=np.random.randint(0, 1095))
        
        sample_data.append({
            'uid': f'sample_{i:04d}',
            'title': f'{crime_type} Case {i}',
            'description': f'Sample {crime_type.lower()} case description',
            'place_of_birth': f'City, {state}',
            'publication_date': pub_date,
            'modified_date': pub_date + pd.Timedelta(days=np.random.randint(0, 30)),
            'ingestion_date': pd.Timestamp.now(),
            'reward_text': f'${np.random.choice([5000, 10000, 25000])}' if np.random.random() > 0.3 else None,
            'images': [f'image_{i}.jpg'] if np.random.random() > 0.5 else []
        })
    
    df = pd.DataFrame(sample_data)
    df['case_age_days'] = (df['ingestion_date'] - df['publication_date']).dt.days
    
    return df

def save_results(results, output_dir, db_manager):
    """Save analysis results to files and database."""
    
    import json
    
    # Save to JSON files
    for analysis_type, result in results.items():
        output_file = os.path.join(output_dir, f'{analysis_type}_analysis.json')
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_types(obj):
            if hasattr(obj, 'item'):  # numpy scalar
                return obj.item()
            elif hasattr(obj, 'tolist'):  # numpy array
                return obj.tolist()
            elif isinstance(obj, pd.Timestamp):
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
        
        # Save to database if available
        if db_manager:
            try:
                db_manager.save_analysis_results(result, analysis_type)
            except Exception as e:
                logger.warning(f"Could not save {analysis_type} results to database: {e}")

def generate_summary_report(results, df, output_dir):
    """Generate a summary report of the analysis."""
    
    report_file = os.path.join(output_dir, 'fairness_audit_report.md')
    
    with open(report_file, 'w') as f:
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
        
        # Recommendations
        f.write("## Recommendations\n\n")
        f.write("1. **Regular Monitoring:** Implement ongoing bias monitoring\n")
        f.write("2. **Data Quality:** Improve data collection standardization\n")
        f.write("3. **Transparency:** Publish methodology and limitations\n")
        f.write("4. **Stakeholder Engagement:** Include community input in analysis\n")
    
    logger.info(f"Summary report saved to {report_file}")

if __name__ == "__main__":
    main()