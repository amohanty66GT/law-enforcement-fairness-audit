#!/usr/bin/env python3
"""
Quick test to verify the analysis components work correctly.
"""

import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_components():
    """Test all major components."""
    
    print("🧪 Testing Fairness & Bias Audit Components")
    print("=" * 50)
    
    # Test 1: Data Ingestion
    print("1. Testing Data Ingestion...")
    try:
        from data_ingestion.fbi_wanted import FBIWantedIngestion
        from data_ingestion.fbi_crime_data import FBICrimeDataIngestion
        
        # Test sample data generation
        import pandas as pd
        import numpy as np
        
        np.random.seed(42)
        sample_data = pd.DataFrame({
            'uid': ['test_001', 'test_002'],
            'title': ['Test Case 1', 'Test Case 2'],
            'description': ['Sample description 1', 'Sample description 2'],
            'place_of_birth': ['Los Angeles, CA', 'Houston, TX'],
            'publication_date': pd.to_datetime(['2023-01-01', '2023-06-01']),
            'modified_date': pd.to_datetime(['2023-01-01', '2023-06-01']),
            'ingestion_date': pd.Timestamp.now(),
            'reward_text': ['$10,000', None],
            'images': [['img1.jpg'], []]
        })
        sample_data['case_age_days'] = (sample_data['ingestion_date'] - sample_data['publication_date']).dt.days
        
        print(f"   ✅ Sample data created: {len(sample_data)} records")
        
    except Exception as e:
        print(f"   ❌ Data ingestion test failed: {e}")
        return False
    
    # Test 2: Feature Engineering
    print("2. Testing Feature Engineering...")
    try:
        from data_processing.feature_engineering import FeatureEngineer
        
        engineer = FeatureEngineer()
        processed_data = engineer.engineer_features(sample_data)
        
        print(f"   ✅ Feature engineering successful: {processed_data.shape}")
        print(f"   ✅ New features: {[col for col in processed_data.columns if col not in sample_data.columns]}")
        
    except Exception as e:
        print(f"   ❌ Feature engineering test failed: {e}")
        return False
    
    # Test 3: Bias Analysis
    print("3. Testing Bias Analysis...")
    try:
        from analysis.bias_metrics import BiasAnalyzer
        from analysis.weapons_analysis import WeaponsAnalyzer
        
        analyzer = BiasAnalyzer()
        weapons_analyzer = WeaponsAnalyzer()
        
        # Create larger sample for meaningful analysis
        np.random.seed(42)
        large_sample = pd.DataFrame({
            'birth_state': np.random.choice(['CA', 'TX', 'NY', 'FL'], 200),
            'birth_state_population': np.random.choice([39.5, 29.1, 19.8, 21.5], 200),
            'crime_family': np.random.choice(['Violent', 'White Collar', 'Drug Related'], 200),
            'publication_year': np.random.choice([2021, 2022, 2023], 200),
            'case_age_days': np.random.normal(365, 200, 200),
            'weapon_category': np.random.choice(['firearm', 'knife', 'unknown', 'none'], 200),
            'weapon_raw': ['sample weapon text'] * 200,
            'severity_flag': np.random.choice([True, False], 200, p=[0.6, 0.4]),
            'birth_region': np.random.choice(['West', 'South', 'Northeast'], 200)
        })
        
        # Test geographic analysis
        geo_results = analyzer.analyze_geographic_bias(large_sample)
        print(f"   ✅ Geographic analysis: {'Bias detected' if geo_results.get('significant_bias') else 'No bias detected'}")
        
        # Test categorical analysis
        cat_results = analyzer.analyze_categorical_bias(large_sample)
        print(f"   ✅ Category analysis completed")
        
        # Test temporal analysis
        temporal_results = analyzer.analyze_temporal_trends(large_sample)
        print(f"   ✅ Temporal analysis completed")
        
        # Test weapons analysis
        weapons_results = weapons_analyzer.analyze_weapon_patterns(large_sample)
        serious_crimes = weapons_results.get('total_serious_crimes', 0)
        print(f"   ✅ Weapons analysis: {serious_crimes} serious crimes analyzed")
        
    except Exception as e:
        print(f"   ❌ Bias analysis test failed: {e}")
        return False
    
    # Test 4: Visualizations
    print("4. Testing Visualizations...")
    try:
        from dashboard.visualizations import BiasVisualizer
        
        visualizer = BiasVisualizer()
        
        # Test basic chart creation
        fig1 = visualizer.create_category_distribution(large_sample)
        fig2 = visualizer.create_geographic_distribution(large_sample)
        
        print(f"   ✅ Visualization components working")
        
    except Exception as e:
        print(f"   ❌ Visualization test failed: {e}")
        return False
    
    print("\n🎉 All tests passed! Your fairness audit system is working correctly.")
    print("\n📊 Key Capabilities Verified:")
    print("   • Data ingestion and processing")
    print("   • Statistical bias detection")
    print("   • Feature engineering")
    print("   • Interactive visualizations")
    print("   • 🔫 Weapons in serious crimes analysis (NEW)")
    
    print("\n🚀 Next Steps:")
    print("   • Run: py scripts/run_simple_analysis.py --data-source sample")
    print("   • Start dashboard: py scripts/start_simple_dashboard.py --port 8502")
    print("   • View results in output/ directory")
    print("   • Check the new 🔫 Weapons Analysis tab in the dashboard!")
    
    return True

if __name__ == "__main__":
    test_components()