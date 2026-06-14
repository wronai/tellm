# tellm v4 - STT+TTS+LLM+SQLite+HTML


## AI Cost Tracking

![PyPI](https://img.shields.io/badge/pypi-costs-blue) ![Version](https://img.shields.io/badge/version-4.0.5-blue) ![Python](https://img.shields.io/badge/python-3.9+-blue) ![License](https://img.shields.io/badge/license-Apache--2.0-green)
![AI Cost](https://img.shields.io/badge/AI%20Cost-$0.60-orange) ![Human Time](https://img.shields.io/badge/Human%20Time-3.1h-blue) ![Model](https://img.shields.io/badge/Model-openrouter%2Fqwen%2Fqwen3--coder--next-lightgrey)

- 🤖 **LLM usage:** $0.6006 (4 commits)
- 👤 **Human dev:** ~$313 (3.1h @ $100/h, 30min dedup)

Generated on 2026-06-14 using [openrouter/qwen/qwen3-coder-next](https://openrouter.ai/qwen/qwen3-coder-next)

---

## Instalacja
```bash
tar -xzf tellm-4.0.2.tar.gz
cd tellm-4.0.2
pip install -e .
```

## Uruchomienie
```bash
cp .env.example .env
# ustaw OPENROUTER_API_KEY w .env
tellm-bot --host localhost --port 8008
```

## Użycie
```python
from tellm import create_bot
bot = create_bot(db_path="tellm.db")
view = bot.generate_view("trans", task, result)
html = view.to_html()
```


## License

Licensed under Apache-2.0.
