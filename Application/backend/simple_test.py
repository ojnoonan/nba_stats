#!/usr/bin/env python3
import requests

game_id = "0042400306"
box_score_url = f"https://stats.nba.com/stats/boxscoretraditionalv2?GameID={game_id}&RangeType=0&StartPeriod=1&EndPeriod=10&StartRange=0&EndRange=28800"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://www.nba.com/'
}

print(f"Testing game {game_id}")
print(f"URL: {box_score_url}")

try:
    response = requests.get(box_score_url, headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Keys: {list(data.keys())}")
        
        if 'resultSets' in data:
            for i, result_set in enumerate(data['resultSets']):
                name = result_set.get('name', 'Unknown')
                rows = len(result_set.get('rowSet', []))
                print(f"Set {i}: {name} - {rows} rows")
                
                if name == 'PlayerStats' and rows > 0:
                    print(f"Sample: {result_set['rowSet'][0][:5]}")  # First 5 columns
        else:
            print("No resultSets")
    else:
        print(f"Failed: {response.text[:200]}")
        
except Exception as e:
    print(f"Error: {e}")
