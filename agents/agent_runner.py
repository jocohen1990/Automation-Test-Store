import json
import re
from pathlib import Path

from integrations.openai_client import ask_openai

AGENTS_DIR = Path(__file__).parent


def load_instructions(agent_name: str) -> str:
    """Read agents/<agent_name>.md and strip the --- settings block at the top."""
    text = (AGENTS_DIR / f"{agent_name}.md").read_text(encoding="utf-8")
    # Remove everything up to and including the closing --- of the frontmatter
    return re.sub(r"\A.*?^---\s*$.*?^---\s*$", "", text, count=1, flags=re.S | re.M).strip()


def run_agent(agent_name: str, input_text: str) -> str:
    """Send the agent's .md instructions plus the input to OpenAI and return the answer."""
    return ask_openai(input_text, instructions=load_instructions(agent_name))


def extract_json(text: str):
    """Return the last ```json block in an agent's answer as Python data, or None."""
    blocks = re.findall(r"```json\s*(.*?)```", text, flags=re.S)
    for block in reversed(blocks):
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            continue
    return None
