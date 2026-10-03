import json

from core.gemini import clean_llm_output, get_model

CODEGEN_PROMPT = """You are an expert backtrader developer.
Write a complete Backtrader Strategy class from the JSON spec.
Return ONLY Python code. Class name must be: GeneratedStrategy

Requirements:
- bt.indicators.SMA and bt.indicators.RSI
- Implement entry_signal from spec (crossover_above uses [0] vs [-1])
- stop_loss_pct and position_size as params
- self.buy(size=...) using position_size fraction of cash
- Track entry_price for stop loss
- self.log() on every buy/sell
- Only buy if not self.position; only sell if self.position"""


def generate_code(spec: dict, error: str = None, prev_code: str = None) -> str:
    model = get_model()
    if error and prev_code:
        prompt = f"Fix this code.\nSpec: {json.dumps(spec)}\nCode:\n{prev_code}\nError: {error}\nReturn ONLY Python."
    else:
        prompt = CODEGEN_PROMPT + f"\n\nSpec:\n{json.dumps(spec, indent=2)}"
    response = model.generate_content(prompt)
    return clean_llm_output(response.text)


def generate_with_retry(spec: dict, max_retries: int = 3, run_fn=None) -> str:
    code = None
    error = None
    for _ in range(max_retries):
        code = generate_code(spec, error, code)
        try:
            compile(code, "<string>", "exec")
            if run_fn:
                run_fn(code)
            return code
        except Exception as e:
            error = str(e)
    raise RuntimeError(f"Code generation failed: {error}")
