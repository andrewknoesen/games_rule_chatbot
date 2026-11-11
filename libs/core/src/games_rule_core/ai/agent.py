"""Rules judge: one ADK agent with two tools over the ingested rulebooks.

Tools open their own DB sessions because ADK calls them outside FastAPI's
request cycle. Each question runs in a fresh in-memory session (no chat
memory between questions)."""

from typing import Any

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

from games_rule_core.ai.config import settings
from games_rule_core.ai.rag import search_chunks
from games_rule_core.postgres.models.models import Game
from games_rule_core.postgres.session import async_session_maker

APP_NAME = "games_rule"

INSTRUCTION = """You are a friendly but precise tabletop game rules judge.
Each message gives you a game id and a player's question about that game.

1. ALWAYS call search_rules with the game id (more than once with different
   wording if the first results do not answer it). Call get_game_overview when
   you need the setup, turn order, components or winning conditions.
2. Answer ONLY from what the tools return. If the rulebook does not cover the
   question, say so plainly and suggest the closest rule that does apply.
3. Cite rulebook pages like (p. 7) after each claim.
4. Be concise: answer first, then a short explanation. Use Markdown.
5. Only answer questions about this game's rules."""


async def search_rules(game_id: int, query: str) -> list[dict[str, Any]]:
    """Search the game's rulebook for passages relevant to the query.

    Args:
        game_id: The id of the game whose rulebook to search.
        query: What to look for, phrased like a rulebook would phrase it.

    Returns:
        Passages with the rulebook page number they come from.
    """
    return await search_chunks(game_id, query)


async def get_game_overview(game_id: int) -> dict[str, Any]:
    """Get the game's summary: players, objective, components, setup, turn
    structure, win conditions and glossary.

    Args:
        game_id: The id of the game.
    """
    async with async_session_maker() as session:
        game = await session.get(Game, game_id)
    if game is None:
        return {"error": f"no game with id {game_id}"}
    return game.model_dump(
        include={
            "name",
            "objective",
            "min_players",
            "max_players",
            "components",
            "setup",
            "turn_structure",
            "win_conditions",
            "glossary",
        }
    )


rules_agent = Agent(
    name="rules_judge",
    model=settings.chat_model,
    description="Answers questions about a board game using its rulebook.",
    instruction=INSTRUCTION,
    tools=[search_rules, get_game_overview],
)


async def ask(game_id: int, question: str) -> str:
    runner = InMemoryRunner(agent=rules_agent, app_name=APP_NAME)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id="web"
    )
    message = types.Content(
        role="user",
        parts=[types.Part(text=f"Game id: {game_id}\nQuestion: {question}")],
    )
    answer = ""
    async for event in runner.run_async(
        user_id="web", session_id=session.id, new_message=message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            answer = "".join(p.text or "" for p in event.content.parts)
    return answer.strip() or "Sorry, I couldn't find an answer to that."
