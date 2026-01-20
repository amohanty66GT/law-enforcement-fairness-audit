# Law Enforcement Data Fairness & Bias Audit

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A comprehensive data science project analyzing representation patterns in public law enforcement datasets to identify potential biases and skews across categories, geography, and time. **Features advanced weapons analysis and agent-based architecture.**

![Dashboard Preview](docs/dashboard-preview.png)

## 🎯 Project Overview

This system analyzes public law enforcement data to identify patterns in representation across:
- **🗺️ Geographic distribution**: Regional skews in wanted notices vs population
- **📈 Crime categories**: Representation of different offense types over time  
- **⏰ Temporal trends**: How patterns change across years/quarters
- **🔄 Case persistence**: Duration patterns by category
- **🔫 Weapons analysis**: Weapon usage patterns in serious crimes
- **🤖 Agent-based architecture**: Modular, resilient analysis pipeline *(NEW)*

## 🚀 Key Features

### Agent-Based Architecture (NEW)
- **🤖 Modular agents** with single responsibilities
- **🔄 Resilient pipeline** with graceful error handling
- **📊 Transparent execution** with detailed logging and metrics
- **🧪 Comprehensive testing** for each agent and integration
- **🔧 Easy extensibility** for adding new analysis types

### Core Analysis
- **Statistical bias detection** using chi-square tests and trend analysis
- **Automated data ingestion** from multiple public APIs
- **Feature engineering** with geographic, temporal, and categorical analysis
- **Interactive visualizations** with filtering and drill-down capabilities

### Weapons Analysis (Advanced Feature)
- **🔫 Weapon categorization**: firearm, knife, blunt_object, none, unknown, other
- **🚨 Serious crime detection**: Flags violent crimes (homicide, assault, robbery, etc.)
- **📊 Statistical analysis**: Distribution, trends, and data quality metrics
- **🗺️ Regional patterns**: Geographic weapon usage analysis
- **⏰ Temporal trends**: Weapon usage changes over time

### Ethical Framework
- ✅ **Aggregate-only analysis** - No individual tracking or deanonymization
- ✅ **No tactical insights** - Avoids operational intelligence
- ✅ **Privacy protection** - Maintains ethical boundaries with aggregation thresholds
- ✅ **Transparency** - Clear methodology and limitations

## 🤖 Agent Architecture

The system uses 7 specialized agents that communicate via structured data objects:

1. **🔄 Ingestion Agent** - Fetches data from FBI API with pagination and deduplication
2. **✅ Validation & Drift Agent** - Validates data quality and detects distribution changes
3. **🔫 Weapon Classification Agent** - Categorizes weapons using rule-based mapping
4. **🚨 Serious Crime Filter Agent** - Identifies serious crimes consistently
5. **📊 Statistical Analysis Agent** - Performs bias detection using statistical tests
6. **📈 Trend & Anomaly Agent** - Analyzes temporal patterns and detects anomalies
7. **📋 Reporting & Visualization Agent** - Generates privacy-compliant reports and charts

**Benefits:**
- **Resilience**: System continues if individual agents fail
- **Modularity**: Each agent can be tested and modified independently
- **Transparency**: Complete visibility into each processing step
- **Extensibility**: Easy to add new analysis capabilities

## 📊 Data Sources

- **FBI Wanted API**: Public wanted persons data
- **FBI Crime Data Explorer**: Reported crime statistics  
- **City Open Data**: Local police department datasets (LAPD, Pittsburgh, Atlanta)

## 🛠️ Tech Stack

- **Backend**: Python, pandas, requests, scipy, statsmodels
- **Database**: PostgreSQL/DuckDB
- **Visualization**: Plotly, Streamlit, Altair
- **APIs**: FBI Wanted, FBI CDE, city open data portals

## 📈 Sample Results

From analysis of 1,000 sample records:
- **Geographic bias detected**: CA (22.1%), TX (15.8%), FL (11.7%) - Chi-square p=0.0001
- **489 serious crimes identified** (48.9% of dataset)
- **Weapon distribution**: Firearm (55.6%), Knife (23.7%), Unknown (20.7%)
- **Data quality insight**: 20.7% unknown weapon information indicates reporting gaps

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/law-enforcement-fairness-audit.git
cd law-enforcement-fairness-audit

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
```

### Run Analysis

#### Agent-Based Analysis (Recommended)
```bash
# Run modern agent-based analysis
python scripts/run_agent_analysis.py --data-source sample --output-dir output

# Compare traditional vs agent approaches
python scripts/run_analysis_comparison.py --approach both
```

#### Traditional Analysis
```bash
# Run legacy monolithic analysis
python scripts/run_simple_analysis.py --data-source sample

# Results saved to output/ directory
```

### Start Dashboard

```bash
# Launch interactive dashboard
python scripts/start_simple_dashboard.py --port 8502

# Or use Streamlit directly
streamlit run src/dashboard/app.py

# Open browser to http://localhost:8501
```

### Testing

```bash
# Run agent integration tests
python test_agent_integration.py

# Run traditional analysis tests
python test_analysis.py
```

### Using Make (Optional)

```bash
# Quick setup and run
make setup
make run-analysis
make dashboard
```

## 📱 Dashboard Features

- **📊 Overview**: Dataset summary and key metrics
- **🗺️ Geographic Analysis**: State representation vs population with bias detection
- **📈 Category Analysis**: Crime type distribution patterns
- **⏰ Temporal Trends**: Changes over time with correlation analysis
- **🔫 Weapons Analysis**: Weapon patterns in serious crimes *(Featured)*
- **📋 Statistical Results**: Comprehensive hypothesis test results

### Interactive Controls
- Year range filtering
- Region selection
- Serious crimes toggle
- Comparative analysis options
- Data refresh and cache clearing

## 🔬 Research Questions Addressed

1. Are certain crime types overrepresented in public notices vs reported crime stats?
2. Do regional patterns show geographic bias in wanted list visibility?
3. How have category distributions changed over time?
4. What factors influence case persistence on public lists?
5. **What weapon patterns exist in serious crimes?** *(NEW)*
6. **How does weapon information completeness vary over time and region?** *(NEW)*

## 📊 Statistical Methods

- **Geographic Analysis**: Chi-square goodness of fit test
- **Category Analysis**: Chi-square test of independence  
- **Temporal Analysis**: Pearson correlation analysis
- **Persistence Analysis**: One-way ANOVA
- **Weapons Analysis**: Distribution analysis with data quality metrics

## 🔒 Ethical Constraints

### What We DON'T Do
- ❌ Individual-level tracking or predictions
- ❌ Tactical or operational insights
- ❌ Deanonymization of public records
- ❌ Profiling or targeting recommendations

### What We DO
- ✅ Aggregate statistical analysis only
- ✅ Transparency and accountability research
- ✅ Data quality assessment
- ✅ Policy-relevant insights
- ✅ Clear limitation documentation

## 📁 Project Structure

```
law-enforcement-fairness-audit/
├── src/
│   ├── data_ingestion/          # API data collection
│   ├── data_processing/         # Feature engineering
│   ├── analysis/               # Statistical analysis & weapons analysis
│   └── dashboard/              # Streamlit visualizations
├── scripts/                    # Execution scripts
├── config/                     # Configuration files
├── output/                     # Analysis results
├── docs/                       # Documentation
└── tests/                      # Test files
```

## 🧪 Testing

```bash
# Run component tests
python test_analysis.py

# Verify analysis results
python verify_analysis.py

# Run full test suite (if available)
pytest tests/
```

## 📚 Documentation

- [Weapons Analysis Feature](WEAPONS_ANALYSIS_FEATURE.md) - Detailed feature documentation
- [Ethics Framework](ETHICS.md) - Ethical guidelines and constraints
- [Configuration Guide](config/settings.py) - System configuration options

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- FBI for providing public APIs and data transparency
- Open data initiatives from various police departments
- Statistical analysis libraries: scipy, statsmodels, pandas
- Visualization tools: Plotly, Streamlit

## 📞 Contact

- **Project Link**: [https://github.com/yourusername/law-enforcement-fairness-audit](https://github.com/yourusername/law-enforcement-fairness-audit)
- **Issues**: [GitHub Issues](https://github.com/yourusername/law-enforcement-fairness-audit/issues)

---

**⚖️ Built with ethics in mind - Promoting transparency and accountability in law enforcement data**