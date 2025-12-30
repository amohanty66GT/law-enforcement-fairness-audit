"""
Visualization components for the fairness and bias audit dashboard.
Creates interactive charts and plots using Plotly.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class BiasVisualizer:
    """Creates visualizations for bias analysis results."""
    
    def __init__(self):
        self.color_palette = px.colors.qualitative.Set3
        self.bias_colors = {
            'over_represented': '#ff6b6b',
            'under_represented': '#4ecdc4',
            'normal': '#95a5a6'
        }
    
    def create_category_distribution(self, df: pd.DataFrame) -> go.Figure:
        """Create pie chart of crime category distribution."""
        
        category_counts = df['crime_family'].value_counts()
        
        fig = px.pie(
            values=category_counts.values,
            names=category_counts.index,
            title="Distribution of Crime Categories",
            color_discrete_sequence=self.color_palette
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
        )
        
        fig.update_layout(
            showlegend=True,
            height=400,
            font=dict(size=12)
        )
        
        return fig
    
    def create_geographic_distribution(self, df: pd.DataFrame) -> go.Figure:
        """Create bar chart of geographic distribution."""
        
        state_counts = df['birth_state'].value_counts().head(15)  # Top 15 states
        
        fig = px.bar(
            x=state_counts.index,
            y=state_counts.values,
            title="Cases by State (Top 15)",
            labels={'x': 'State', 'y': 'Number of Cases'},
            color=state_counts.values,
            color_continuous_scale='Blues'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_representation_scatter(self, geo_results: Dict) -> go.Figure:
        """Create scatter plot of representation vs population."""
        
        if 'representation_analysis' not in geo_results:
            return go.Figure().add_annotation(text="No data available", showarrow=False)
        
        rep_data = pd.DataFrame(geo_results['representation_analysis'])
        
        # Color points based on bias
        colors = []
        for _, row in rep_data.iterrows():
            if row['over_represented']:
                colors.append(self.bias_colors['over_represented'])
            elif row['under_represented']:
                colors.append(self.bias_colors['under_represented'])
            else:
                colors.append(self.bias_colors['normal'])
        
        fig = go.Figure()
        
        # Add scatter points
        fig.add_trace(go.Scatter(
            x=rep_data['population_millions'],
            y=rep_data['observed_cases'],
            mode='markers+text',
            text=rep_data['state'],
            textposition='top center',
            marker=dict(
                size=12,
                color=colors,
                line=dict(width=1, color='white')
            ),
            hovertemplate=(
                '<b>%{text}</b><br>'
                'Population: %{x:.1f}M<br>'
                'Observed Cases: %{y}<br>'
                'Representation Ratio: %{customdata:.2f}<br>'
                '<extra></extra>'
            ),
            customdata=rep_data['representation_ratio']
        ))
        
        # Add expected line (perfect representation)
        if len(rep_data) > 0:
            max_pop = rep_data['population_millions'].max()
            total_cases = rep_data['observed_cases'].sum()
            total_pop = rep_data['population_millions'].sum()
            expected_slope = total_cases / total_pop
            
            fig.add_trace(go.Scatter(
                x=[0, max_pop],
                y=[0, max_pop * expected_slope],
                mode='lines',
                name='Expected (proportional)',
                line=dict(dash='dash', color='gray', width=2),
                hoverinfo='skip'
            ))
        
        fig.update_layout(
            title="State Representation vs Population",
            xaxis_title="Population (Millions)",
            yaxis_title="Observed Cases",
            height=500,
            showlegend=True
        )
        
        return fig
    
    def create_category_proportions(self, cat_results: Dict) -> go.Figure:
        """Create comparison of category proportions."""
        
        wanted_props = cat_results['wanted_distribution']['proportions']
        
        categories = list(wanted_props.keys())
        wanted_values = list(wanted_props.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Wanted List',
            x=categories,
            y=wanted_values,
            marker_color='lightblue'
        ))
        
        # Add baseline if available
        if 'baseline_distribution' in cat_results:
            baseline_props = cat_results['baseline_distribution']['proportions']
            baseline_values = [baseline_props.get(cat, 0) for cat in categories]
            
            fig.add_trace(go.Bar(
                name='Baseline Crime Stats',
                x=categories,
                y=baseline_values,
                marker_color='lightcoral'
            ))
        
        fig.update_layout(
            title="Category Proportions: Wanted List vs Baseline",
            xaxis_title="Crime Category",
            yaxis_title="Proportion",
            barmode='group',
            height=400,
            xaxis_tickangle=-45
        )
        
        return fig
    
    def create_persistence_boxplot(self, df: pd.DataFrame) -> go.Figure:
        """Create box plot of case persistence by category."""
        
        fig = px.box(
            df,
            x='crime_family',
            y='case_age_days',
            title="Case Persistence by Category",
            labels={'case_age_days': 'Case Age (Days)', 'crime_family': 'Crime Category'},
            color='crime_family',
            color_discrete_sequence=self.color_palette
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_temporal_trends(self, temporal_results: Dict) -> go.Figure:
        """Create line chart of temporal trends by category."""
        
        if 'yearly_category_counts' not in temporal_results:
            return go.Figure().add_annotation(text="No temporal data available", showarrow=False)
        
        yearly_data = temporal_results['yearly_category_counts']
        
        fig = go.Figure()
        
        # Convert to DataFrame for easier handling
        df_yearly = pd.DataFrame(yearly_data).fillna(0)
        
        for i, category in enumerate(df_yearly.columns):
            fig.add_trace(go.Scatter(
                x=df_yearly.index,
                y=df_yearly[category],
                mode='lines+markers',
                name=category,
                line=dict(color=self.color_palette[i % len(self.color_palette)], width=3),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title="Temporal Trends by Crime Category",
            xaxis_title="Year",
            yaxis_title="Number of Cases",
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    def create_bias_heatmap(self, df: pd.DataFrame) -> go.Figure:
        """Create heatmap showing bias patterns across dimensions."""
        
        # Create cross-tabulation of region vs category
        crosstab = pd.crosstab(df['birth_region'], df['crime_family'], normalize='columns')
        
        fig = px.imshow(
            crosstab.values,
            x=crosstab.columns,
            y=crosstab.index,
            color_continuous_scale='RdBu_r',
            title="Regional Distribution by Crime Category (Normalized)",
            labels=dict(color="Proportion")
        )
        
        fig.update_layout(
            height=400,
            xaxis_title="Crime Category",
            yaxis_title="Region"
        )
        
        return fig
    
    def create_representation_ratio_chart(self, geo_results: Dict) -> go.Figure:
        """Create horizontal bar chart of representation ratios."""
        
        if 'representation_analysis' not in geo_results:
            return go.Figure().add_annotation(text="No data available", showarrow=False)
        
        rep_data = pd.DataFrame(geo_results['representation_analysis'])
        rep_data = rep_data.sort_values('representation_ratio', ascending=True)
        
        # Color bars based on bias
        colors = []
        for _, row in rep_data.iterrows():
            if row['over_represented']:
                colors.append(self.bias_colors['over_represented'])
            elif row['under_represented']:
                colors.append(self.bias_colors['under_represented'])
            else:
                colors.append(self.bias_colors['normal'])
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=rep_data['state'],
            x=rep_data['representation_ratio'],
            orientation='h',
            marker_color=colors,
            hovertemplate=(
                '<b>%{y}</b><br>'
                'Representation Ratio: %{x:.2f}<br>'
                'Observed: %{customdata[0]}<br>'
                'Expected: %{customdata[1]:.1f}<br>'
                '<extra></extra>'
            ),
            customdata=rep_data[['observed_cases', 'expected_cases']].values
        ))
        
        # Add reference line at ratio = 1.0
        fig.add_vline(x=1.0, line_dash="dash", line_color="gray", 
                     annotation_text="Perfect Representation")
        
        # Add bias threshold lines
        fig.add_vline(x=1.2, line_dash="dot", line_color="red", opacity=0.5)
        fig.add_vline(x=0.8, line_dash="dot", line_color="red", opacity=0.5)
        
        fig.update_layout(
            title="State Representation Ratios",
            xaxis_title="Representation Ratio (Observed/Expected)",
            yaxis_title="State",
            height=max(400, len(rep_data) * 25),
            showlegend=False
        )
        
        return fig
    
    def create_summary_dashboard(self, df: pd.DataFrame, all_results: Dict) -> go.Figure:
        """Create comprehensive summary dashboard."""
        
        # Create subplot figure
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Geographic Distribution', 
                'Category Distribution',
                'Temporal Trends', 
                'Case Persistence'
            ),
            specs=[[{"type": "bar"}, {"type": "pie"}],
                   [{"type": "scatter"}, {"type": "box"}]]
        )
        
        # Geographic distribution (top 10 states)
        state_counts = df['birth_state'].value_counts().head(10)
        fig.add_trace(
            go.Bar(x=state_counts.index, y=state_counts.values, name="States"),
            row=1, col=1
        )
        
        # Category distribution
        category_counts = df['crime_family'].value_counts()
        fig.add_trace(
            go.Pie(labels=category_counts.index, values=category_counts.values, name="Categories"),
            row=1, col=2
        )
        
        # Temporal trends (simplified)
        yearly_counts = df.groupby('publication_year').size()
        fig.add_trace(
            go.Scatter(x=yearly_counts.index, y=yearly_counts.values, 
                      mode='lines+markers', name="Yearly Trends"),
            row=2, col=1
        )
        
        # Case persistence by category
        for category in df['crime_family'].unique()[:5]:  # Limit to 5 categories
            cat_data = df[df['crime_family'] == category]['case_age_days']
            fig.add_trace(
                go.Box(y=cat_data, name=category),
                row=2, col=2
            )
        
        fig.update_layout(
            height=800,
            title_text="Fairness Audit Summary Dashboard",
            showlegend=False
        )
        
        return fig
    
    def create_weapons_distribution_chart(self, df: pd.DataFrame, serious_only: bool = True) -> go.Figure:
        """Create bar chart of weapon distribution in serious crimes."""
        
        if serious_only:
            filtered_df = df[df.get('severity_flag', False) == True]
            title = "Weapon Distribution in Serious Crimes"
        else:
            filtered_df = df
            title = "Weapon Distribution in All Crimes"
        
        if len(filtered_df) == 0:
            return go.Figure().add_annotation(text="No data available", showarrow=False)
        
        weapon_counts = filtered_df['weapon_category'].value_counts()
        
        fig = px.bar(
            x=weapon_counts.index,
            y=weapon_counts.values,
            title=title,
            labels={'x': 'Weapon Category', 'y': 'Number of Cases'},
            color=weapon_counts.values,
            color_continuous_scale='Reds'
        )
        
        fig.update_layout(
            xaxis_tickangle=-45,
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_weapons_comparison_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create grouped bar chart comparing weapon distribution in serious vs all crimes."""
        
        serious_df = df[df.get('severity_flag', False) == True]
        
        if len(serious_df) == 0:
            return go.Figure().add_annotation(text="No serious crimes data available", showarrow=False)
        
        # Get weapon distributions
        all_weapons = df['weapon_category'].value_counts(normalize=True) * 100
        serious_weapons = serious_df['weapon_category'].value_counts(normalize=True) * 100
        
        # Get all weapon categories
        all_categories = set(all_weapons.index) | set(serious_weapons.index)
        
        fig = go.Figure()
        
        categories = list(all_categories)
        all_values = [all_weapons.get(cat, 0) for cat in categories]
        serious_values = [serious_weapons.get(cat, 0) for cat in categories]
        
        fig.add_trace(go.Bar(
            name='All Crimes',
            x=categories,
            y=all_values,
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Serious Crimes',
            x=categories,
            y=serious_values,
            marker_color='darkred'
        ))
        
        fig.update_layout(
            title="Weapon Distribution: All Crimes vs Serious Crimes",
            xaxis_title="Weapon Category",
            yaxis_title="Percentage",
            barmode='group',
            height=400,
            xaxis_tickangle=-45
        )
        
        return fig
    
    def create_weapons_temporal_chart(self, df: pd.DataFrame, serious_only: bool = True) -> go.Figure:
        """Create line chart of weapon trends over time."""
        
        if serious_only:
            filtered_df = df[df.get('severity_flag', False) == True]
            title = "Weapon Trends in Serious Crimes Over Time"
        else:
            filtered_df = df
            title = "Weapon Trends in All Crimes Over Time"
        
        if len(filtered_df) == 0 or 'publication_year' not in filtered_df.columns:
            return go.Figure().add_annotation(text="No temporal data available", showarrow=False)
        
        # Calculate yearly percentages
        yearly_data = filtered_df.groupby(['publication_year', 'weapon_category']).size().unstack(fill_value=0)
        yearly_percentages = yearly_data.div(yearly_data.sum(axis=1), axis=0) * 100
        
        fig = go.Figure()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        for i, weapon in enumerate(yearly_percentages.columns):
            fig.add_trace(go.Scatter(
                x=yearly_percentages.index,
                y=yearly_percentages[weapon],
                mode='lines+markers',
                name=weapon.replace('_', ' ').title(),
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Year",
            yaxis_title="Percentage of Cases",
            height=500,
            hovermode='x unified'
        )
        
        return fig
    
    def create_unknown_weapons_trend_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create chart showing percentage of unknown weapons over time."""
        
        serious_df = df[df.get('severity_flag', False) == True]
        
        if len(serious_df) == 0 or 'publication_year' not in serious_df.columns:
            return go.Figure().add_annotation(text="No data available", showarrow=False)
        
        # Calculate unknown weapon percentage by year
        yearly_stats = serious_df.groupby('publication_year').agg({
            'weapon_category': lambda x: (x == 'unknown').sum() / len(x) * 100
        }).round(2)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=yearly_stats.index,
            y=yearly_stats['weapon_category'],
            mode='lines+markers',
            name='Unknown Weapons %',
            line=dict(color='orange', width=4),
            marker=dict(size=10, color='orange'),
            fill='tonexty'
        ))
        
        fig.update_layout(
            title="Percentage of Unknown Weapon Records Over Time",
            xaxis_title="Year",
            yaxis_title="Percentage of Cases with Unknown Weapons",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_weapons_regional_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create heatmap of weapon usage by region."""
        
        serious_df = df[df.get('severity_flag', False) == True]
        
        if len(serious_df) == 0 or 'birth_region' not in serious_df.columns:
            return go.Figure().add_annotation(text="No regional data available", showarrow=False)
        
        # Create cross-tabulation
        crosstab = pd.crosstab(serious_df['birth_region'], serious_df['weapon_category'], normalize='index') * 100
        
        fig = px.imshow(
            crosstab.values,
            x=crosstab.columns,
            y=crosstab.index,
            color_continuous_scale='Reds',
            title="Weapon Usage by Region (% within region)",
            labels=dict(color="Percentage")
        )
        
        fig.update_layout(
            height=400,
            xaxis_title="Weapon Category",
            yaxis_title="Region"
        )
        
        return fig

if __name__ == "__main__":
    # Test visualizations with sample data
    import numpy as np
    
    # Create sample data
    np.random.seed(42)
    sample_df = pd.DataFrame({
        'crime_family': np.random.choice(['Violent', 'White Collar', 'Drug Related'], 100),
        'birth_state': np.random.choice(['CA', 'TX', 'NY', 'FL'], 100),
        'birth_region': np.random.choice(['West', 'South', 'Northeast'], 100),
        'case_age_days': np.random.normal(365, 200, 100),
        'publication_year': np.random.choice([2021, 2022, 2023], 100)
    })
    
    visualizer = BiasVisualizer()
    
    # Test category distribution
    fig1 = visualizer.create_category_distribution(sample_df)
    print("Category distribution chart created")
    
    # Test geographic distribution
    fig2 = visualizer.create_geographic_distribution(sample_df)
    print("Geographic distribution chart created")
    
    # Test persistence boxplot
    fig3 = visualizer.create_persistence_boxplot(sample_df)
    print("Persistence boxplot created")
    
    print("All visualizations tested successfully!")