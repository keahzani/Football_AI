"""
Advanced Fixtures Scraper
Fetches upcoming fixtures with injuries, cards, and team news
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import time

from utils.database import DatabaseManager
from config.config import LEAGUES, API_FOOTBALL_KEY, API_FOOTBALL_BASE_URL

class AdvancedFixturesScraper:
    """Scrapes upcoming fixtures with comprehensive team data"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.api_key = API_FOOTBALL_KEY
        self.base_url = API_FOOTBALL_BASE_URL
        self.use_api = bool(self.api_key)
        
    def fetch_upcoming_fixtures(self, days_ahead: int = 7) -> List[Dict]:
        """
        Fetch upcoming fixtures for the next N days
        
        Args:
            days_ahead: Number of days to look ahead
        
        Returns:
            List of fixture dictionaries
        """
        if self.use_api:
            return self._fetch_from_api(days_ahead)
        else:
            return self._scrape_from_web(days_ahead)
    
    def _fetch_from_api(self, days_ahead: int) -> List[Dict]:
        """Fetch fixtures from API-Football"""
        fixtures = []
        
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)
        
        headers = {
            'x-apisports-key': self.api_key
        }
        
        for league_key, league_info in LEAGUES.items():
            league_id = league_info.get('api_id')
            if not league_id:
                continue
            
            print(f"\nFetching {league_info['name']} fixtures...")
            
            # Get fixtures for this league
            url = f"{self.base_url}/fixtures"
            params = {
                'league': league_id,
                'season': today.year,
                'from': today.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d')
            }
            
            try:
                response = requests.get(url, headers=headers, params=params)
                data = response.json()
                
                if data.get('response'):
                    for fixture in data['response']:
                        fixture_data = self._parse_api_fixture(fixture, league_key)
                        if fixture_data:
                            fixtures.append(fixture_data)
                    
                    print(f"✓ Found {len(data['response'])} fixtures")
                
                time.sleep(1)  # Respect API rate limits
                
            except Exception as e:
                print(f"✗ Error fetching {league_info['name']}: {e}")
        
        return fixtures
    
    def _parse_api_fixture(self, fixture: Dict, league_key: str) -> Optional[Dict]:
        """Parse fixture data from API response"""
        try:
            return {
                'league_key': league_key,
                'fixture_id': fixture['fixture']['id'],
                'date': fixture['fixture']['date'],
                'home_team': fixture['teams']['home']['name'],
                'away_team': fixture['teams']['away']['name'],
                'venue': fixture['fixture']['venue']['name'],
                'status': fixture['fixture']['status']['short']
            }
        except Exception as e:
            print(f"Error parsing fixture: {e}")
            return None
    
    def _scrape_from_web(self, days_ahead: int) -> List[Dict]:
        """
        Scrape fixtures from free sources (ESPN, BBC Sport, etc.)
        Fallback when API is not available
        """
        fixtures = []
        
        print("\n📅 Scraping upcoming fixtures from web sources...")
        print("(Using ESPN as free source)")
        
        # ESPN fixtures URLs for each league
        espn_leagues = {
            'premier_league': 'eng.1',
            'la_liga': 'esp.1',
            'bundesliga': 'ger.1',
            'serie_a': 'ita.1',
            'ligue_1': 'fra.1'
        }
        
        for league_key, espn_code in espn_leagues.items():
            league_name = LEAGUES[league_key]['name']
            print(f"\nFetching {league_name}...")
            
            url = f"https://www.espn.com/soccer/fixtures/_/league/{espn_code}"
            
            try:
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Parse fixtures (ESPN structure)
                    fixture_items = soup.find_all('div', class_='competitors')
                    
                    for item in fixture_items[:10]:  # Limit to next 10 matches
                        try:
                            teams = item.find_all('div', class_='team-name')
                            if len(teams) >= 2:
                                fixture_data = {
                                    'league_key': league_key,
                                    'home_team': teams[0].text.strip(),
                                    'away_team': teams[1].text.strip(),
                                    'date': datetime.now().strftime('%Y-%m-%d'),
                                    'status': 'scheduled'
                                }
                                fixtures.append(fixture_data)
                        except:
                            continue
                    
                    print(f"✓ Found {len(fixture_items)} upcoming matches")
                
                time.sleep(2)  # Be nice to the server
                
            except Exception as e:
                print(f"✗ Error scraping {league_name}: {e}")
        
        return fixtures
    
    def fetch_team_news(self, team_name: str, league_key: str) -> Dict:
        """
        Fetch team news: injuries, suspensions, form
        
        Args:
            team_name: Team name
            league_key: League key
        
        Returns:
            Dictionary with team news
        """
        if self.use_api:
            return self._fetch_team_news_api(team_name, league_key)
        else:
            return self._scrape_team_news_web(team_name, league_key)
    
    def _fetch_team_news_api(self, team_name: str, league_key: str) -> Dict:
        """Fetch team news from API-Football"""
        team_news = {
            'injuries': [],
            'suspensions': [],
            'form': None,
            'last_updated': datetime.now().isoformat()
        }
        
        headers = {'x-apisports-key': self.api_key}
        
        try:
            # Get team ID first
            league_id = LEAGUES[league_key].get('api_id')
            url = f"{self.base_url}/teams"
            params = {
                'league': league_id,
                'season': datetime.now().year,
                'search': team_name
            }
            
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            if data.get('response'):
                team_id = data['response'][0]['team']['id']
                
                # Fetch injuries
                injuries_url = f"{self.base_url}/injuries"
                injuries_params = {
                    'team': team_id,
                    'league': league_id,
                    'season': datetime.now().year
                }
                
                injuries_response = requests.get(injuries_url, headers=headers, params=injuries_params)
                injuries_data = injuries_response.json()
                
                if injuries_data.get('response'):
                    for injury in injuries_data['response']:
                        team_news['injuries'].append({
                            'player': injury['player']['name'],
                            'type': injury['player']['type'],
                            'reason': injury['player']['reason']
                        })
                
                print(f"✓ Found {len(team_news['injuries'])} injuries for {team_name}")
        
        except Exception as e:
            print(f"✗ Error fetching team news: {e}")
        
        return team_news
    
    def _scrape_team_news_web(self, team_name: str, league_key: str) -> Dict:
        """Scrape team news from free sources"""
        team_news = {
            'injuries': [],
            'suspensions': [],
            'form': None,
            'last_updated': datetime.now().isoformat()
        }
        
        # Try scraping from physioroom.com (free injury database)
        try:
            league_name = LEAGUES[league_key]['name']
            # Physioroom URLs
            physio_leagues = {
                'premier_league': 'english-premier-league',
                'la_liga': 'spanish-la-liga',
                'bundesliga': 'german-bundesliga',
                'serie_a': 'italian-serie-a',
                'ligue_1': 'french-ligue-1'
            }
            
            if league_key in physio_leagues:
                url = f"https://www.physioroom.com/news/{physio_leagues[league_key]}-injury-table.php"
                
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find team section
                    team_sections = soup.find_all('div', class_='injury-table')
                    
                    for section in team_sections:
                        if team_name.lower() in section.text.lower():
                            injuries = section.find_all('tr', class_='injury-row')
                            for injury in injuries:
                                try:
                                    cols = injury.find_all('td')
                                    if len(cols) >= 3:
                                        team_news['injuries'].append({
                                            'player': cols[0].text.strip(),
                                            'type': cols[1].text.strip(),
                                            'status': cols[2].text.strip()
                                        })
                                except:
                                    continue
                    
                    if team_news['injuries']:
                        print(f"✓ Found {len(team_news['injuries'])} injuries for {team_name}")
        
        except Exception as e:
            print(f"Note: Could not fetch injury data ({e})")
        
        return team_news
    
    def save_fixtures_to_db(self, fixtures: List[Dict]):
        """Save fetched fixtures to database"""
        saved_count = 0
        
        for fixture in fixtures:
            try:
                # Get league ID
                league_key = fixture['league_key']
                league_name = LEAGUES[league_key]['name']
                
                league_result = self.db.execute_query(
                    "SELECT league_id FROM leagues WHERE league_name = ?",
                    (league_name,)
                )
                
                if not league_result:
                    continue
                
                league_id = league_result[0][0]
                
                # Get or create team IDs
                home_team_id = self.db.insert_team(fixture['home_team'], league_id)
                away_team_id = self.db.insert_team(fixture['away_team'], league_id)
                
                # Insert fixture
                query = """
                    INSERT OR REPLACE INTO fixtures 
                    (league_id, date, home_team_id, away_team_id, status, venue, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                
                self.db.execute_update(query, (
                    league_id,
                    fixture['date'],
                    home_team_id,
                    away_team_id,
                    fixture.get('status', 'scheduled'),
                    fixture.get('venue', ''),
                    datetime.now().isoformat()
                ))
                
                saved_count += 1
                
            except Exception as e:
                print(f"Error saving fixture: {e}")
        
        print(f"\n✓ Saved {saved_count} fixtures to database")
        return saved_count
    
    def update_all_fixtures(self, days_ahead: int = 7) -> Dict:
        """
        Complete update: fetch fixtures and team news
        
        Args:
            days_ahead: Days to look ahead
        
        Returns:
            Summary dictionary
        """
        print("="*70)
        print("UPDATING UPCOMING FIXTURES & TEAM NEWS")
        print("="*70)
        
        # Fetch fixtures
        fixtures = self.fetch_upcoming_fixtures(days_ahead)
        
        if not fixtures:
            print("\n⚠ No fixtures found. Using web scraping fallback...")
            print("💡 Tip: Add API-Football key for better data:")
            print("   1. Sign up at https://www.api-football.com/")
            print("   2. Get free API key (100 calls/day)")
            print("   3. Set environment variable: API_FOOTBALL_KEY=your_key")
            return {'fixtures': 0, 'team_news': 0}
        
        # Save to database
        saved_count = self.save_fixtures_to_db(fixtures)
        
        # Fetch team news for unique teams
        print("\n" + "="*70)
        print("FETCHING TEAM NEWS (Injuries & Suspensions)")
        print("="*70)
        
        unique_teams = set()
        for fixture in fixtures:
            unique_teams.add((fixture['home_team'], fixture['league_key']))
            unique_teams.add((fixture['away_team'], fixture['league_key']))
        
        team_news_count = 0
        for team_name, league_key in list(unique_teams)[:10]:  # Limit to avoid rate limits
            print(f"\nFetching news for {team_name}...")
            news = self.fetch_team_news(team_name, league_key)
            if news['injuries'] or news['suspensions']:
                team_news_count += 1
            time.sleep(1)
        
        print("\n" + "="*70)
        print("UPDATE COMPLETE")
        print("="*70)
        print(f"✓ Fixtures saved: {saved_count}")
        print(f"✓ Teams with news: {team_news_count}")
        
        return {
            'fixtures': saved_count,
            'team_news': team_news_count
        }

def main():
    """Update fixtures from command line"""
    scraper = AdvancedFixturesScraper()
    scraper.update_all_fixtures(days_ahead=7)

if __name__ == "__main__":
    main()
