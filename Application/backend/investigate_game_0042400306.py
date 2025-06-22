#!/usr/bin/env python3
"""
Script to investigate why game 0042400306 is not working properly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db_connection
from app.services.nba_data_service import NBADataService
import requests
import logging

logging.basicConfig(level=logging.DEBUG)

def investigate_game_0042400306():
    """Investigate why this specific game isn't working"""
    game_id = "0042400306"
    
    print(f"Investigating game {game_id}...")
    
    # Test direct NBA API call
    box_score_url = f"https://stats.nba.com/stats/boxscoretraditionalv2?GameID={game_id}&RangeType=0&StartPeriod=1&EndPeriod=10&StartRange=0&EndRange=28800"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.nba.com/'
    }
    
    print(f"Making direct API call to: {box_score_url}")
    
    try:
        response = requests.get(box_score_url, headers=headers, timeout=30)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            if 'resultSets' in data:
                print(f"Number of result sets: {len(data['resultSets'])}")
                for i, result_set in enumerate(data['resultSets']):
                    print(f"Result set {i}: {result_set.get('name', 'Unknown')} - {len(result_set.get('rowSet', []))} rows")
                    
                    # Check player stats specifically
                    if result_set.get('name') == 'PlayerStats':
                        rows = result_set.get('rowSet', [])
                        print(f"Player stats rows: {len(rows)}")
                        if len(rows) > 0:
                            print(f"Sample player row: {rows[0]}")
                        else:
                            print("No player stats found in API response!")
            else:
                print("No 'resultSets' in response")
                print(f"Response data: {data}")
        else:
            print(f"API call failed with status {response.status_code}")
            print(f"Response text: {response.text}")
            
    except Exception as e:
        print(f"Error making API call: {e}")
    
    # Also check database state
    print("\nChecking database state...")
    db = get_db_connection()
    cursor = db.cursor()
    
    cursor.execute("SELECT * FROM games WHERE game_id = ?", (game_id,))
    game = cursor.fetchone()
    
    if game:
        print(f"Game in database: {dict(game)}")
    else:
        print(f"Game {game_id} not found in database")
    
    cursor.execute("SELECT COUNT(*) FROM player_stats WHERE game_id = ?", (game_id,))
    player_count = cursor.fetchone()[0]
    print(f"Player stats count in database: {player_count}")
    
    db.close()

if __name__ == "__main__":
    investigate_game_0042400306()
