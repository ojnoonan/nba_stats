async def update_team_players(self, team_id: int) -> None:
    """Update players for a specific team"""
    try:
        # Get team
        stmt = sa_select(Team).filter_by(team_id=team_id)
        result = await self.db.execute(stmt)
        team = result.scalar_one_or_none()
        if not team:
            raise ValueError(f"Team {team_id} not found")

        try:
            # Get status and initialize if needed
            status = await self._get_status()
            if status:
                # Only set initial status if not already updating
                if not status.is_updating:
                    status.is_updating = True
                    status.current_phase = "players"
                    status.players_percent_complete = 0
                    status.players_updated = False

                # Initialize components dict if needed
                if not hasattr(status, "components") or status.components is None:
                    status.components = {}
                if not isinstance(status.components, dict):
                    status.components = {}
                if "players" not in status.components:
                    status.components["players"] = {}

                # Keep existing percentage if already updating
                current_percent = status.components.get("players", {}).get(
                    "percent_complete", 0
                )
                if isinstance(status.components, dict):
                    status.components["players"] = {
                        "updated": False,
                        "last_update": None,
                        "percent_complete": current_percent,
                        "last_error": None,
                    }
                await self.db.commit()

            try:
                # Main player update logic would go here
                pass

                # Final status update
                status = await self._get_status()
                if status:
                    now = datetime.now(timezone.utc)

                    # Reset updating state
                    status.is_updating = False
                    status.current_phase = None
                    status.current_detail = f"Completed processing team: {team.name}"

                    # Initialize/update components
                    if not hasattr(status, "components") or status.components is None:
                        status.components = {}
                    if not isinstance(status.components, dict):
                        status.components = {}
                    if "players" not in status.components:
                        status.components["players"] = {}

                    # Update all status fields atomically
                    status.players_updated = True
                    status.players_last_update = now
                    status.players_percent_complete = 100
                    if isinstance(status.components, dict):
                        status.components["players"] = {
                            "updated": True,
                            "last_update": now,
                            "percent_complete": 100,
                            "last_error": None,
                        }
                    await self.db.commit()
            except Exception as update_e:
                logger.error(
                    f"Failed to update final status for team {team.name}: {str(update_e)}"
                )
                await self._safe_rollback()
                # Don't re-raise, as the player data was updated successfully

        except Exception as status_e:
            logger.error(f"Error handling update status: {str(status_e)}")
            await self._safe_rollback()
            raise

    except Exception as e:
        logger.error(f"Error in update_team_players: {str(e)}")
        try:
            status = await self._get_status()
            if status:
                if not hasattr(status, "components") or status.components is None:
                    status.components = {}
                if isinstance(status.components, dict):
                    if "players" not in status.components:
                        status.components["players"] = {}
                    status.components["players"]["last_error"] = str(e)
                status.current_detail = (
                    f"Error processing team {team.name if team else team_id}: {str(e)}"
                )
                status.last_error = str(e)
                status.last_error_time = datetime.now(timezone.utc)
                await self.db.commit()
        except Exception as inner_e:
            logger.error(f"Failed to update error status: {str(inner_e)}")
            await self._safe_rollback()
        raise
