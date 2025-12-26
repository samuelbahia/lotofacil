"""
Streamlit Dashboard for Lottery Analysis System

Interactive web dashboard for visualizing lottery statistics and generating games.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime

from data_collector import DataCollector
from statistical_analysis import StatisticalAnalysis
from game_generator import GameGenerator
from ml_models import LotteryMLModels

# Page config
st.set_page_config(
    page_title="Lottery Analysis System",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'collector' not in st.session_state:
    st.session_state.collector = DataCollector()
    st.session_state.analyzer = StatisticalAnalysis()
    st.session_state.generator = GameGenerator()
    st.session_state.ml = LotteryMLModels()


def main():
    """Main dashboard function"""
    
    st.title("🎲 Lottery Analysis System")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.header("Settings")
        
        lottery_type = st.selectbox(
            "Select Lottery",
            ["lotofacil", "megasena", "quina"],
            index=0
        )
        
        st.markdown("---")
        
        page = st.radio(
            "Navigate",
            ["📊 Statistics", "🎯 Generate Games", "🤖 ML Insights", "ℹ️ About"]
        )
        
        st.markdown("---")
        st.caption("Version 1.0.0")
    
    # Load data
    df = st.session_state.collector.get_lottery_data(lottery_type)
    
    if df.empty:
        st.error(f"No data found for {lottery_type}. Please run data migration first.")
        st.code("python migrate_data.py")
        return
    
    # Route to selected page
    if page == "📊 Statistics":
        show_statistics(df, lottery_type)
    elif page == "🎯 Generate Games":
        show_game_generator(df, lottery_type)
    elif page == "🤖 ML Insights":
        show_ml_insights(df, lottery_type)
    else:
        show_about()


def show_statistics(df: pd.DataFrame, lottery_type: str):
    """Display statistics page"""
    
    st.header(f"📊 {lottery_type.upper()} Statistics")
    
    # Database stats
    stats = st.session_state.collector.get_statistics(lottery_type)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Draws", stats['total_draws'])
    with col2:
        st.metric("Latest Draw", f"#{stats['latest_draw_number']}")
    with col3:
        st.metric("Latest Date", stats['latest_draw_date'])
    
    st.markdown("---")
    
    # Frequency analysis
    st.subheader("Number Frequency Analysis")
    
    freq_df = st.session_state.analyzer.calculate_frequency(df, lottery_type)
    
    # Frequency bar chart
    fig = px.bar(
        freq_df.head(25),
        x='number',
        y='absolute_frequency',
        title='Number Frequency Distribution',
        labels={'number': 'Number', 'absolute_frequency': 'Times Drawn'},
        color='absolute_frequency',
        color_continuous_scale='viridis'
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Hot and Cold numbers
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 Hot Numbers (Last 100 draws)")
        hot_cold = st.session_state.analyzer.identify_hot_cold_numbers(df, lottery_type, 100)
        hot_numbers = hot_cold['hot_numbers'][:10]
        st.write(" • ".join([f"**{n}**" for n in hot_numbers]))
    
    with col2:
        st.subheader("❄️ Cold Numbers (Last 100 draws)")
        cold_numbers = hot_cold['cold_numbers'][:10]
        st.write(" • ".join([f"**{n}**" for n in cold_numbers]))
    
    st.markdown("---")
    
    # Even/Odd distribution
    st.subheader("Even/Odd Distribution")
    even_odd = st.session_state.analyzer.analyze_even_odd_distribution(df)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Average Even", f"{even_odd['average_even']:.1f}")
    with col2:
        st.metric("Average Odd", f"{even_odd['average_odd']:.1f}")
    
    # Most common distributions
    most_common = even_odd['most_common'][:5]
    dist_df = pd.DataFrame([
        {'Even': e, 'Odd': o, 'Count': c}
        for (e, o), c in most_common
    ])
    
    fig = px.bar(
        dist_df,
        x=['Even', 'Odd'],
        y='Count',
        title='Most Common Even/Odd Distributions',
        barmode='group'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Correlation heatmap
    st.subheader("Number Correlation Matrix (Top 15 Numbers)")
    
    corr_matrix = st.session_state.analyzer.analyze_correlation(df, lottery_type)
    
    # Show only top 15 numbers for readability
    top_15 = freq_df.head(15)['number'].tolist()
    corr_subset = corr_matrix.loc[top_15, top_15]
    
    fig = px.imshow(
        corr_subset,
        title='Co-occurrence Heat Map',
        labels=dict(color="Co-occurrences"),
        color_continuous_scale='RdBu_r'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Top pairs
    st.subheader("Most Frequent Number Pairs")
    top_pairs = st.session_state.analyzer.find_frequent_pairs(df, 10)
    
    pairs_df = pd.DataFrame([
        {'Pair': f"{p[0]}-{p[1]}", 'Count': c}
        for p, c in top_pairs
    ])
    
    fig = px.bar(
        pairs_df,
        x='Pair',
        y='Count',
        title='Top 10 Number Pairs'
    )
    st.plotly_chart(fig, use_container_width=True)


def show_game_generator(df: pd.DataFrame, lottery_type: str):
    """Display game generator page"""
    
    st.header(f"🎯 Generate Games for {lottery_type.upper()}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        n_games = st.slider("Number of games", 1, 20, 6)
    
    with col2:
        strategy = st.selectbox(
            "Strategy",
            ["all", "conservative", "balanced", "aggressive", "intermediate"]
        )
    
    if st.button("🎲 Generate Games", type="primary"):
        with st.spinner("Generating games..."):
            # Determine strategies
            if strategy == 'all':
                strategies = ['conservative', 'balanced', 'aggressive', 'intermediate']
            else:
                strategies = [strategy]
            
            # Generate games
            games = st.session_state.generator.generate_multiple_games(
                lottery_type,
                count=n_games,
                strategies=strategies
            )
            
            # Display games
            st.success(f"Generated {len(games)} games!")
            
            # Show games in a nice table
            games_data = []
            for game in games:
                games_data.append({
                    'Game #': game['game_id'],
                    'Strategy': game['strategy'].upper(),
                    'Numbers': ' - '.join([str(n).zfill(2) for n in game['numbers']]),
                    'Cost (R$)': f"{game['cost']:.2f}"
                })
            
            games_df = pd.DataFrame(games_data)
            st.dataframe(games_df, use_container_width=True, hide_index=True)
            
            # Investment summary
            investment = st.session_state.generator.calculate_total_investment(games)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Games", investment['total_games'])
            with col2:
                st.metric("Total Investment", f"R$ {investment['total_cost']:.2f}")
            with col3:
                st.metric("Avg Cost/Game", f"R$ {investment['average_cost_per_game']:.2f}")
            
            # Download options
            st.markdown("---")
            st.subheader("📥 Download Games")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # JSON download
                json_str = json.dumps(games, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"{lottery_type}_games_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col2:
                # Text download
                text_output = st.session_state.generator.format_games_output(games, lottery_type)
                st.download_button(
                    label="Download Text",
                    data=text_output,
                    file_name=f"{lottery_type}_games_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )


def show_ml_insights(df: pd.DataFrame, lottery_type: str):
    """Display ML insights page"""
    
    st.header(f"🤖 Machine Learning Insights for {lottery_type.upper()}")
    
    tab1, tab2 = st.tabs(["Clustering Analysis", "Random Forest"])
    
    with tab1:
        st.subheader("Game Clustering")
        st.write("Identify similar patterns in historical games using K-means clustering.")
        
        n_clusters = st.slider("Number of clusters", 3, 10, 5)
        
        if st.button("Run Clustering", key="cluster_btn"):
            with st.spinner("Clustering games..."):
                results = st.session_state.ml.cluster_games(df, lottery_type, n_clusters)
                
                # Display results
                st.success(f"Identified {results['n_clusters']} clusters")
                
                # Cluster sizes pie chart
                fig = px.pie(
                    values=results['cluster_sizes'],
                    names=[f"Cluster {i}" for i in range(n_clusters)],
                    title="Cluster Size Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Show sample games from each cluster
                st.subheader("Sample Games from Each Cluster")
                for cluster_name, stats in results['cluster_stats'].items():
                    with st.expander(f"{cluster_name.replace('_', ' ').title()} ({stats['size']} games, {stats['percentage']:.1f}%)"):
                        for i, game in enumerate(stats['sample_games'], 1):
                            st.write(f"{i}. {game}")
    
    with tab2:
        st.subheader("Random Forest Model")
        st.write("Train a Random Forest model to analyze number patterns.")
        
        if st.button("Train Model", key="train_btn"):
            with st.spinner("Training Random Forest..."):
                results = st.session_state.ml.train_random_forest(df, lottery_type)
                
                if results:
                    st.success("Model trained successfully!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Train Score", f"{results['train_score']:.3f}")
                    with col2:
                        st.metric("Test Score", f"{results['test_score']:.3f}")
                    with col3:
                        st.metric("CV Score", f"{results['cv_mean_score']:.3f}")
                    
                    st.info(f"Model trained on {results['n_samples_train']} samples, tested on {results['n_samples_test']} samples")
                else:
                    st.warning("Machine learning is disabled in configuration")


def show_about():
    """Display about page"""
    
    st.header("ℹ️ About Lottery Analysis System")
    
    st.markdown("""
    ## Complete Lottery Analysis System
    
    A comprehensive Python-based system for statistical analysis and intelligent 
    game generation for Brazilian lottery games.
    
    ### 🎯 Features
    
    - **Data Management**: SQLite database with automated collection and validation
    - **Statistical Analysis**: Comprehensive analysis including frequency, patterns, and correlations
    - **Intelligent Game Generation**: Multiple strategies to maximize winning chances
    - **Machine Learning**: Random Forest and K-means clustering for pattern recognition
    - **Interactive Dashboard**: Web-based visualization and game generation
    
    ### 📊 Supported Lotteries
    
    - ✅ Lotofácil (fully tested)
    - ✅ Mega-Sena (configured)
    - ✅ Quina (configured)
    - ⚠️ Lotomania (configured, needs testing)
    
    ### 🔧 Strategies
    
    1. **Conservative**: Focus on most frequent numbers with balanced distribution
    2. **Aggressive**: Mix of hot and cold numbers for maximum coverage
    3. **Balanced**: Optimal distribution across all statistical factors (recommended)
    4. **Intermediate**: Focus on secondary prizes (14/15 points in Lotofácil)
    
    ### ⚠️ Important Disclaimer
    
    This system is for **educational and entertainment purposes only**. 
    Lottery games are games of chance, and no system can guarantee wins. 
    Play responsibly and within your means.
    
    ### 📝 Version
    
    - **Version**: 1.0.0
    - **Last Updated**: December 2024
    - **Python**: 3.11+
    
    ### 👨‍💻 Usage
    
    For command-line usage and advanced features, refer to the README documentation.
    
    ```bash
    python main.py --help
    ```
    """)


if __name__ == '__main__':
    main()
