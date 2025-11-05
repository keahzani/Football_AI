"""
Football Prediction System - Streamlit Web App
Interactive interface for predictions, updates, and analysis
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config.config import LEAGUES, MODELS_DIR
from utils.database import DatabaseManager
from prediction.predict import FootballPredictor
from scrapers.historical_downloader import HistoricalDataDownloader
from models.train import MatchPredictor

# Page configuration
st.set_page_config(
    page_title="Football Match Predictor",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .prediction-box {
        padding: 20px;
        border-radius: 10px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    .high-confidence {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    .medium-confidence {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .low-confidence {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    .metric-card {
        padding: 15px;
        border-radius: 8px;
        background: #f0f2f6;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'predictor' not in st.session_state:
    st.session_state.predictor = None
if 'db' not in st.session_state:
    st.session_state.db = DatabaseManager()
if 'last_update' not in st.session_state:
    st.session_state.last_update = None

def load_models():
    """Load prediction models"""
    if st.session_state.predictor is None:
        with st.spinner("Loading models..."):
            st.session_state.predictor = FootballPredictor()
            st.session_state.predictor.load_models()
    return st.session_state.predictor

def get_teams_in_league(league_name: str):
    """Get list of teams in a league"""
    db = st.session_state.db
    query = """
        SELECT DISTINCT t.team_name 
        FROM teams t
        JOIN leagues l ON t.league_id = l.league_id
        WHERE l.league_name = ?
        ORDER BY t.team_name
    """
    results = db.execute_query(query, (league_name,))
    return [row[0] for row in results]

def get_database_stats():
    """Get database statistics"""
    db = st.session_state.db
    stats = {
        'total_matches': db.execute_query("SELECT COUNT(*) FROM matches")[0][0],
        'total_teams': db.execute_query("SELECT COUNT(*) FROM teams")[0][0],
        'total_leagues': db.execute_query("SELECT COUNT(*) FROM leagues")[0][0],
    }
    return stats

def update_database():
    """Update database with latest matches"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Download new data
        status_text.text("Downloading latest match data...")
        progress_bar.progress(20)
        
        downloader = HistoricalDataDownloader()
        all_data = downloader.download_all_leagues()
        
        progress_bar.progress(60)
        status_text.text("Saving to database...")
        
        for league_name, df in all_data.items():
            downloader.save_to_database(league_name, df)
        
        progress_bar.progress(80)
        status_text.text("Retraining models...")
        
        # Retrain models
        trainer = MatchPredictor()
        trainer.train_all_leagues(save_models=True)
        
        progress_bar.progress(100)
        status_text.text("✅ Update complete!")
        
        st.session_state.last_update = datetime.now()
        st.session_state.predictor = None  # Force reload of models
        
        return True
    except Exception as e:
        status_text.text(f"❌ Error: {e}")
        return False

def display_prediction(prediction: dict):
    """Display prediction with styling"""
    if 'error' in prediction:
        st.error(f"❌ {prediction['error']}")
        return
    
    # Main prediction box
    pred = prediction['prediction']
    confidence = pred['confidence']
    
    confidence_class = {
        'HIGH': 'high-confidence',
        'MEDIUM': 'medium-confidence',
        'LOW': 'low-confidence'
    }.get(confidence, 'low-confidence')
    
    st.markdown(f"""
    <div class="prediction-box {confidence_class}">
        <h2>{prediction['home_team']} vs {prediction['away_team']}</h2>
        <h3>{prediction['league']}</h3>
        <h1>{pred['outcome']}</h1>
        <p>Confidence: {confidence}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Probabilities
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🏠 Home Win",
            value=f"{pred['home_win_prob']*100:.1f}%",
            delta=None
        )
    
    with col2:
        st.metric(
            label="🤝 Draw",
            value=f"{pred['draw_prob']*100:.1f}%",
            delta=None
        )
    
    with col3:
        st.metric(
            label="✈️ Away Win",
            value=f"{pred['away_win_prob']*100:.1f}%",
            delta=None
        )
    
    # Probability chart
    fig = go.Figure(data=[
        go.Bar(
            x=['Home Win', 'Draw', 'Away Win'],
            y=[pred['home_win_prob']*100, pred['draw_prob']*100, pred['away_win_prob']*100],
            marker_color=['#2ecc71', '#3498db', '#e74c3c'],
            text=[f"{pred['home_win_prob']*100:.1f}%", 
                  f"{pred['draw_prob']*100:.1f}%", 
                  f"{pred['away_win_prob']*100:.1f}%"],
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Prediction Probabilities",
        yaxis_title="Probability (%)",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Explanation
    st.subheader("📊 Key Factors")
    
    for factor in prediction['explanation']:
        if '✓' in factor:
            st.success(factor)
        elif '⚠' in factor:
            st.warning(factor)
        else:
            st.info(factor)

# Main app
def main():
    # Header
    st.markdown('<h1 class="main-header">⚽ Football Match Predictor</h1>', unsafe_allow_html=True)
    st.markdown("### AI-Powered Match Predictions for Top European Leagues")
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/football2--v1.png", width=100)
        st.title("⚙️ Controls")
        
        # Database stats
        st.subheader("📊 System Status")
        stats = get_database_stats()
        st.metric("Total Matches", f"{stats['total_matches']:,}")
        st.metric("Teams", stats['total_teams'])
        st.metric("Leagues", stats['total_leagues'])
        
        if st.session_state.last_update:
            st.info(f"Last update: {st.session_state.last_update.strftime('%Y-%m-%d %H:%M')}")
        
        st.divider()
        
        # Update button
        st.subheader("🔄 Update Data")
        st.write("Download latest matches and retrain models")
        
        if st.button("🔄 Update Database", type="primary", use_container_width=True):
            with st.spinner("Updating... This may take 10-15 minutes"):
                success = update_database()
                if success:
                    st.balloons()
                    st.success("✅ Update complete!")
                    st.rerun()
        
        st.warning("⚠️ Update takes 10-15 minutes. Run weekly for best results.")
        
        st.divider()
        
        # Help section
        with st.expander("ℹ️ How to Use"):
            st.markdown("""
            1. **Select League** from dropdown
            2. **Choose Teams** (Home and Away)
            3. **Click Predict** to get AI prediction
            4. **Update Weekly** for latest data
            
            **Accuracy**: 42-52% overall
            - Clear favorites: 65-72%
            - Even matches: 40-50%
            """)
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["🎯 Predict Match", "📈 Statistics", "ℹ️ About"])
    
    with tab1:
        st.header("Match Prediction")
        
        # League selection
        league_options = {info['name']: key for key, info in LEAGUES.items()}
        selected_league_name = st.selectbox(
            "Select League",
            options=list(league_options.keys()),
            index=0
        )
        
        selected_league_key = league_options[selected_league_name]
        
        # Get teams
        teams = get_teams_in_league(selected_league_name)
        
        if not teams:
            st.error("No teams found in database. Please update the database first.")
            return
        
        # Team selection
        col1, col2 = st.columns(2)
        
        with col1:
            home_team = st.selectbox(
                "🏠 Home Team",
                options=teams,
                index=0
            )
        
        with col2:
            away_team = st.selectbox(
                "✈️ Away Team",
                options=[t for t in teams if t != home_team],
                index=0
            )
        
        # Predict button
        if st.button("🎯 Predict Match", type="primary", use_container_width=True):
            predictor = load_models()
            
            with st.spinner("Analyzing match data..."):
                # Get team IDs
                db = st.session_state.db
                
                league_result = db.execute_query(
                    "SELECT league_id FROM leagues WHERE league_name = ?",
                    (selected_league_name,)
                )
                league_id = league_result[0][0]
                
                home_team_id = db.get_team_id(home_team, league_id)
                away_team_id = db.get_team_id(away_team, league_id)
                
                # Make prediction
                prediction = predictor.predict_match(
                    home_team_id,
                    away_team_id,
                    league_id,
                    datetime.now().strftime('%Y-%m-%d')
                )
                
                # Display
                display_prediction(prediction)
    
    with tab2:
        st.header("📈 League Statistics")
        
        # League selector for stats
        stat_league = st.selectbox(
            "Select League for Statistics",
            options=list(league_options.keys()),
            key="stat_league"
        )
        
        # Get league stats
        db = st.session_state.db
        league_result = db.execute_query(
            "SELECT league_id FROM leagues WHERE league_name = ?",
            (stat_league,)
        )
        
        if league_result:
            league_id = league_result[0][0]
            
            # Get match statistics
            query = """
                SELECT 
                    COUNT(*) as total_matches,
                    SUM(CASE WHEN result = 'H' THEN 1 ELSE 0 END) as home_wins,
                    SUM(CASE WHEN result = 'D' THEN 1 ELSE 0 END) as draws,
                    SUM(CASE WHEN result = 'A' THEN 1 ELSE 0 END) as away_wins,
                    AVG(home_goals + away_goals) as avg_goals
                FROM matches
                WHERE league_id = ?
            """
            
            stats = db.execute_query(query, (league_id,))
            
            if stats and stats[0][0] > 0:
                total, home_wins, draws, away_wins, avg_goals = stats[0]
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Matches", f"{total:,}")
                
                with col2:
                    st.metric("Home Wins", f"{home_wins} ({home_wins/total*100:.1f}%)")
                
                with col3:
                    st.metric("Draws", f"{draws} ({draws/total*100:.1f}%)")
                
                with col4:
                    st.metric("Away Wins", f"{away_wins} ({away_wins/total*100:.1f}%)")
                
                st.metric("Average Goals per Match", f"{avg_goals:.2f}")
                
                # Pie chart
                fig = go.Figure(data=[go.Pie(
                    labels=['Home Wins', 'Draws', 'Away Wins'],
                    values=[home_wins, draws, away_wins],
                    hole=.3,
                    marker_colors=['#2ecc71', '#3498db', '#e74c3c']
                )])
                
                fig.update_layout(
                    title=f"{stat_league} - Match Outcomes Distribution",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Top scorers
                st.subheader("📊 League Table (by points)")
                
                standings_query = """
                    SELECT 
                        t.team_name,
                        COUNT(*) as played,
                        SUM(CASE 
                            WHEN (m.home_team_id = t.team_id AND m.result = 'H') 
                                OR (m.away_team_id = t.team_id AND m.result = 'A') 
                            THEN 3
                            WHEN m.result = 'D' THEN 1
                            ELSE 0
                        END) as points,
                        SUM(CASE 
                            WHEN m.home_team_id = t.team_id THEN m.home_goals 
                            ELSE m.away_goals 
                        END) as goals_for,
                        SUM(CASE 
                            WHEN m.home_team_id = t.team_id THEN m.away_goals 
                            ELSE m.home_goals 
                        END) as goals_against
                    FROM teams t
                    JOIN matches m ON t.team_id = m.home_team_id OR t.team_id = m.away_team_id
                    WHERE t.league_id = ?
                    GROUP BY t.team_id, t.team_name
                    ORDER BY points DESC, (goals_for - goals_against) DESC
                    LIMIT 10
                """
                
                standings_df = db.get_dataframe(standings_query, (league_id,))
                
                if not standings_df.empty:
                    standings_df['GD'] = standings_df['goals_for'] - standings_df['goals_against']
                    standings_df.index = range(1, len(standings_df) + 1)
                    
                    st.dataframe(
                        standings_df[['team_name', 'played', 'points', 'goals_for', 'goals_against', 'GD']],
                        column_config={
                            "team_name": "Team",
                            "played": "P",
                            "points": "Pts",
                            "goals_for": "GF",
                            "goals_against": "GA",
                            "GD": "GD"
                        },
                        use_container_width=True
                    )
    
    with tab3:
        st.header("ℹ️ About This System")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Features")
            st.markdown("""
            - **AI-Powered Predictions** using XGBoost
            - **7,000+ Historical Matches** analyzed
            - **30+ Features** per prediction
            - **5 Major Leagues** supported
            - **42-52% Accuracy** overall
            - **Real-time Updates** via button
            """)
            
            st.subheader("📊 How It Works")
            st.markdown("""
            1. **Data Collection**: 4 seasons of match data
            2. **Feature Engineering**: 30+ calculated metrics
            3. **Machine Learning**: XGBoost models
            4. **Predictions**: Win/Draw/Loss probabilities
            """)
        
        with col2:
            st.subheader("🏆 Supported Leagues")
            for league_info in LEAGUES.values():
                st.markdown(f"- **{league_info['name']}** ({league_info['country']})")
            
            st.subheader("⚠️ Important Notes")
            st.markdown("""
            - **Update weekly** for best results
            - **Check team news** before betting
            - **52% accuracy is excellent** for football
            - **Use as guidance**, not guarantee
            - **Bet responsibly**
            """)
        
        st.divider()
        
        st.info("""
        💡 **Pro Tip**: Combine AI predictions with your own knowledge of:
        - Team injuries and suspensions
        - Manager tactics
        - Team motivation
        - Weather conditions
        """)

if __name__ == "__main__":
    main()
