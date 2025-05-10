PRD: NBA Stats Website (for Code Generation Agent)
Document Purpose: This Product Requirements Document (PRD) outlines the specifications for building an NBA statistics website. It is intended for use by a code generation agent (e.g., VS Code Copilot Agent) to guide the development process. It includes functional requirements (often framed as user stories for context), technical specifications, design guidelines, and testing requirements.
Project Goal: To create a personal-use website displaying current NBA season stats for players and teams, featuring search, schedules, game details, various stat views, and strength of schedule, using data fetched periodically from nba_api and stored locally.
User Roles:
User: A general visitor interacting with the website.
Developer/Admin: The person overseeing the agent's work and potentially maintaining the application.
1. Core Architecture & Data Handling
Objective: Establish a robust backend and frontend structure with a local database to manage data fetched from an external, unofficial API.
Requirement: Set up a backend service using Python (Flask or FastAPI recommended for simplicity) responsible for:
Scheduled data fetching from nba_api.
Interaction with the SQLite database (CRUD operations).
Serving data to the frontend via a well-defined internal RESTful API.
Requirement: Create and manage a local SQLite database. The schema should logically store data for:
Teams (ID, name, abbreviation, conference, division, win/loss record, logo path/URL, etc.)
Players (ID, name, current team ID, position, number, headshot path/URL, active status, etc.)
Games (ID, date/time UTC, home team ID, away team ID, scores, status - upcoming/completed, etc.)
PlayerGameStats (linking Player ID and Game ID to specific stats for that game: MIN, PTS, REB, AST, STL, BLK, FGM/A, 3PM/A, FTM/A, etc.)
Consider tables/fields for storing calculated SoS, seasonal averages, etc.
Requirement: Build a web frontend (using a modern framework like React, Vue, or Svelte is acceptable; ensure compatibility with Tailwind CSS for styling) that:
Communicates with the backend API to fetch and display data.
Implements all UI/UX requirements defined in this document.
Requirement: Integrate the nba_api Python library (pip install nba-api) into the backend service for fetching data.
Critical Note: nba_api uses unofficial NBA.com endpoints. The agent must implement robust error handling for API calls (e.g., try-except blocks) to manage potential 4xx/5xx errors, unexpected data formats, or missing data.
Requirement: Implement strict rate-limiting logic in the backend data fetching module when calling nba_api. Use time.sleep() (e.g., 0.6 to 1 second delays recommended between consecutive calls) and consider exponential backoff strategies if 429 (Too Many Requests) errors occur. Log rate limit events.
Requirement: Implement the chosen strategy for acquiring and storing URLs/paths for NBA team logos and player headshots. Assume these paths/URLs will be populated into the database. The frontend should gracefully handle cases where an image path is missing (e.g., display a default placeholder).
Requirement: Create a scheduled task mechanism within the backend (e.g., using libraries like APScheduler, schedule, or a simple loop with sleep in a background thread/process; system cron is also an option) to automatically trigger data fetching routines (e.g., daily or twice-daily) to update game results and stats for completed games.
2. Global Features & User Experience
Objective: Define the overall look, feel, and common interactive elements of the website.
Requirement: Implement a dark theme as the primary visual style for the entire website.
Requirement: Apply rounded corners consistently to UI elements like buttons, cards, modals, input fields, etc. (Tailwind CSS utilities like rounded-md, rounded-lg should be used).
Requirement: Style interactive elements (buttons, clickable list items/cards) with a subtle gloss/shine effect (CSS gradients/shadows can achieve this).
Requirement: Implement a hover effect for all clickable elements: they should slightly enlarge (transform: scale(1.03)) and optionally "lift" (box-shadow, slight translateY) with a smooth transition (transition-transform, transition-shadow).
Requirement: Display two timestamps prominently in the main navigation bar:
"Last Updated: [Timestamp]"
"Next Update: [Timestamp]"
The backend API must provide these timestamps. The "Next Update" timestamp should reflect the next scheduled run time of the data fetching task.
Requirement: Ensure all displayed timestamps (game times, update times) are converted from UTC (stored in backend/DB) to the user's local timezone using frontend JavaScript (e.g., Intl.DateTimeFormat or a library like date-fns).
Requirement: Implement a clear main navigation bar containing links/elements for: Search, Upcoming Games, Teams, Players, and the Data Timestamps.
Requirement: Implement the primary interaction model using popup modals for displaying Team, Player, Game Detail, and Game Preview information upon clicking relevant links/items. Use a suitable modal component/library compatible with the chosen frontend framework.
Requirement: Within each modal, include an "Open in New Page" icon/button (e.g., an external link icon) that navigates the user to a dedicated page displaying the same content. This requires distinct routable pages for individual teams, players, and games in addition to the modal views.
3. Search Functionality
Objective: Allow users to easily find teams and players using a unified search interface.
Requirement: Implement a single search input field in the navigation bar.
Requirement: The search input should trigger a call to a backend API endpoint as the user types (with debounce logic to limit requests).
Requirement: The backend search endpoint should query the local SQLite database for both team names and player names matching the search term (case-insensitive, partial matches allowed).
Requirement: The search results returned by the backend API should be structured to allow grouping by team on the frontend. Example structure: [{ team: { id, name, logo }, players: [{ id, name, is_traded_flag }, ...] }, ...].
Requirement: The frontend should display search results dynamically below the search bar, grouped by team. Display the team name/logo as a header for each group, followed by a list of matching players belonging to that team.
Requirement: If a player exists under multiple teams in the results (due to trades within the season scope), clearly indicate this (e.g., add "(Traded)" or similar text next to their name). The backend query needs to handle finding players across multiple team affiliations within the season.
Requirement: Clicking a team name/logo in the results opens the Team Modal. Clicking a player name opens the Player Modal.
4. Upcoming Games Page
Objective: Display a clear, styled list of future NBA games.
Requirement: Create an "Upcoming Games" page accessible from the main navigation.
Requirement: Fetch upcoming game data (future dates, times in UTC, teams involved) from the backend API (which queries the local DB).
Requirement: Group games chronologically under date headings formatted as "MMM D" (e.g., "Aug 12").
Requirement: Style each game listing as a rounded rectangle container.
Requirement: Inside each game container, display:
Home Team Logo & Name
Away Team Logo & Name
Scheduled Start Time (converted to user's local time).
Requirement: Clicking a team's name/logo within a game listing opens the Team Modal.
Requirement: Clicking the general area of the game listing (e.g., between the teams) opens the Game Preview Modal.
5. Game Preview (Upcoming Game Detail)
Objective: Provide pre-game context including lineups and head-to-head history.
Requirement: Implement the Game Preview Modal and corresponding Page.
Requirement: Fetch data from the backend API for the specific game ID, including team info, scheduled time (UTC), and any previous head-to-head results from the current season stored in the DB.
Requirement: Display team names/logos, scheduled start time (local timezone), and a list/summary of previous current-season matchups.
Requirement: Attempt to display projected starting lineups.
Agent Task: Check if nba_api has any reliable endpoint for this (unlikely, but check documentation/examples).
Fallback Implementation: If no official projected lineup is available, query the local DB for the top 5 players for each team based on average minutes played (descending) in the current season and display these as the "Likely Lineup".
Requirement: Include the "Open in New Page" functionality.
6. Teams List & Team Detail
Objective: Allow users to browse teams and view detailed team information.
Requirement: Create a "Teams" page accessible from the main navigation. Display a list/grid of all teams with their logos and names, fetched from the backend. Consider adding filtering/sorting options (e.g., by conference/division).
Requirement: Clicking a team on the Teams page opens the Team Modal.
Requirement: Implement the Team Modal and corresponding Page.
Requirement: Fetch detailed data for the specific team ID from the backend API, including logo path, name, record, stats, roster, full schedule, and calculated SoS values.
Requirement: Display team logo, name, record, and key team season stats.
Requirement: Display the current roster list. Player names must be clickable, opening the Player Modal.
Requirement: Display the team's full current-season schedule (past and upcoming). Past games must be clickable, opening the Game Detail Modal. Upcoming games should open the Game Preview Modal.
Requirement: Calculate and display Strength of Schedule (SoS) metrics:
Backend logic is required to calculate this (e.g., upon data update). A common method is averaging the winning percentages of opponents.
Display both "SoS Played" (based on past opponents) and "SoS Remaining" (based on future opponents).
Requirement: Include the "Open in New Page" functionality.
7. Players List & Player Detail
Objective: Allow users to browse players and view detailed player statistics and game logs.
Requirement: Create a "Players" page accessible from the main navigation. Display a list of all players for the current season, fetched from the backend. Implement searching/filtering capabilities (e.g., by name, team, position).
Requirement: Clicking a player on the Players page opens the Player Modal.
Requirement: Implement the Player Modal and corresponding Page.
Requirement: Fetch detailed data for the specific player ID from the backend API, including headshot path, bio info, season averages, and game log data.
Requirement: Display player headshot, name, team, bio info, and season average stats.
Requirement: Implement distinct views (e.g., using tabs or buttons within the modal/page) to show aggregated stats for the player's Last 5, Last 10, and Last 20 games played. The backend API needs endpoints to provide this calculated data.
Requirement: Implement distinct views/sections to show the player's Top 5 scoring games and Bottom 5 scoring games for the current season. The backend API needs endpoints for this.
Requirement: Display a detailed Game Log table showing the player's stats for each game played in the current season.
Requirement: Each row in the Game Log table must be clickable, opening the Game Detail Modal for that specific game.
Requirement: Include the "Open in New Page" functionality.
8. Game Detail (Past Game)
Objective: Display the final results and detailed box score for a completed game.
Requirement: Implement the Game Detail Modal and corresponding Page.
Requirement: Fetch detailed data for the specific completed game ID from the backend API, including final score, date, teams, and all player stats for that game.
Requirement: Display the final score, date, and team names/logos.
Requirement: Display a detailed box score table.
Include columns for: Player Name, MIN, PTS, REB, AST, STL, BLK, FG% (FGM/A), 3P% (3PM/A), FT% (FTM/A).
Include players from both teams.
Requirement: Implement client-side sorting for the box score table. Clicking any stat column header should sort the table rows based on that column's value (ascending/descending toggle). Default sort should be Points (PTS) descending.
Requirement: Include a checkbox/toggle labeled "Hide DNP" which, when checked, filters out players with 0 minutes played from the box score table.
Requirement: Include the "Open in New Page" functionality.
9. Technical Specifications & Constraints Summary
Backend: Python (Flask/FastAPI preferred)
Database: SQLite
Frontend: Modern JS Framework (React/Vue/Svelte preferred) or HTML/CSS/JS. Must support component-based structure and API interaction.
Styling: Tailwind CSS is preferred. Adhere to Dark Theme, rounded corners, gloss/shine, hover effects.
External API: nba_api Python library (unofficial, requires rate limiting and robust error handling).
Images: Requires a separate mechanism for sourcing/storing Team Logos and Player Headshots. Implement graceful fallbacks (placeholders).
Timezones: Store all dates/times in UTC in the backend/DB. Convert to user's local time on the frontend for display.
Deployment: (Not specified, but assume standard web deployment practices).
10. Testing Requirements
Requirement: Before relying on any nba_api endpoint in the backend logic, the agent must perform exploratory calls to:
Verify the endpoint exists and returns data for the current season.
Analyze the exact structure and data types of the response JSON/dictionary.
Confirm that the necessary data points (e.g., specific stats, player IDs, team IDs) are present and accessible.
Document findings (e.g., in code comments) regarding endpoint reliability and data structure.
Requirement: Implement unit tests for backend utility functions (e.g., SoS calculation, date manipulation).
Requirement: Implement integration tests for the backend API endpoints to ensure they correctly interact with the database and return data in the expected format.
Requirement: Implement basic frontend tests (e.g., component rendering tests, basic interaction tests) if using a framework that supports them easily.
Requirement: Manually test all user flows described in the stories, paying close attention to:
Search functionality with various inputs.
Modal opening/closing and "Open in New Page" navigation.
Correct data display for players, teams, games.
Stat calculations (Last X, High/Low 5, SoS).
Timezone conversions.
Hover effects and styling consistency.
Handling of missing images.
Box score sorting and filtering.
Responsiveness on different screen sizes (implied standard web requirement).
Requirement: Specifically test the rate-limiting implementation by observing backend logs during data fetching to ensure delays are occurring and 429 errors are handled if they arise.
