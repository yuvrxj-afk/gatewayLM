from fastapi import HTTPException, Header

from ..config.loader import Team, load_config


async def get_current_team(x_api_key: str = Header(...)) -> Team:
    config = load_config()
    team = next((t for t in config.teams if t.api_key == x_api_key), None)

    if not team:
        raise HTTPException(status_code=401, detail="invalid API key")

    return team
