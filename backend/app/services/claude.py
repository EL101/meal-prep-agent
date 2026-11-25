"""All Claude API calls live here so prompts, model choice, and validation stay in one place.

Claude drafts; code decides. Every response is parsed into a Pydantic schema, then the
exclusion filter and the optimizer enforce hard constraints (allergens, budget, macros).
"""

import base64
import json
from typing import Any, Literal

import anthropic
from anthropic.types.beta.parsed_beta_message import ParsedBetaMessage

from app.config import get_settings
from app.schemas.llm import InventoryExtraction, RecipeCandidates

ImageMediaType = Literal["image/jpeg", "image/png", "image/gif", "image/webp"]

# Server-side fallback: if the primary model declines on policy grounds, the API re-runs the
# request on a default fallback model inside the same call.
_FALLBACK_BETA = "server-side-fallback-2026-07-01"


class ClaudeRefusalError(RuntimeError):
    pass


_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        key = get_settings().anthropic_api_key or None  # None → SDK resolves credentials itself
        _client = anthropic.AsyncAnthropic(api_key=key)
    return _client


INVENTORY_SYSTEM = """You read photos of fridges, pantries, and grocery receipts and list the \
food items present. Use generic grocery names. Give a confidence for each item; anything you \
cannot clearly identify should get confidence below 0.7 so the app asks the user to confirm. \
For receipts, include the line-item price and use the receipt date to estimate expiry."""

RECIPES_SYSTEM = """You are a meal-prep planner. Propose batch-cookable recipes that use the \
user's existing inventory first (especially items expiring soon), fit their equipment and \
cooking-session time, and move them toward their daily calorie and protein goals. Never use \
excluded foods. Give accurate per-serving calories and protein. Propose more candidates than \
there are meal slots; a separate optimizer chooses the final plan."""


async def extract_inventory(
    image: bytes,
    media_type: ImageMediaType,
    kind: Literal["fridge", "pantry", "receipt"],
) -> InventoryExtraction:
    response = await get_client().beta.messages.parse(
        model=get_settings().claude_model,
        max_tokens=16000,
        betas=[_FALLBACK_BETA],
        fallbacks="default",
        output_config={"effort": get_settings().claude_effort},
        system=INVENTORY_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64.standard_b64encode(image).decode(),
                        },
                    },
                    {"type": "text", "text": f"This is a photo of my {kind}. List the items."},
                ],
            }
        ],
        output_format=InventoryExtraction,
    )
    return _parsed(response)


async def propose_recipes(context: dict[str, Any]) -> RecipeCandidates:
    """`context` holds profile, inventory, exclusions, past ratings, and slots to fill."""
    response = await get_client().beta.messages.parse(
        model=get_settings().claude_model,
        max_tokens=16000,
        betas=[_FALLBACK_BETA],
        fallbacks="default",
        output_config={"effort": get_settings().claude_effort},
        system=RECIPES_SYSTEM,
        messages=[{"role": "user", "content": json.dumps(context, default=str)}],
        output_format=RecipeCandidates,
    )
    return _parsed(response)


def _parsed[T](response: ParsedBetaMessage[T]) -> T:
    if response.stop_reason == "refusal":
        details = response.stop_details
        raise ClaudeRefusalError(details.explanation if details else "Claude declined the request")
    if response.parsed_output is None:
        raise ValueError(
            f"Claude returned no structured output (stop_reason={response.stop_reason})"
        )
    return response.parsed_output
