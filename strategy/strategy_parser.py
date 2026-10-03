import json

from core.gemini import clean_llm_output, get_model

SYSTEM_PROMPT = """
You are a quantitative trading strategy parser.
Convert plain-English strategy into JSON spec.
Return ONLY valid JSON. No markdown.

{
  "ticker": "^NSEI",
  "start": "2019-01-01",
  "end": "2024-01-01",
  "entry_indicator": "SMA",
  "entry_fast": 50,
  "entry_slow": 200,
  "entry_signal": "crossover_above",
  "exit_indicator": "RSI",
  "exit_period": 14,
  "exit_above": 70,
  "exit_below": 30,
  "stop_loss_pct": 0.05,
  "position_size": 0.95
}

Defaults: stop_loss 0.05, position_size 0.95, ticker ^NSEI, dates 2019-2024.
"""


def parse_strategy(description: str) -> dict:
    model = get_model()
    response = model.generate_content(SYSTEM_PROMPT + "\n\nStrategy:\n" + description)
    return json.loads(clean_llm_output(response.text))
