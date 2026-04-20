"""投稿・生成AIツール等の定数（Ver 2.10）。"""

# value → 表示ラベル（プルダウン・「使用したAI」表示用）
AI_TOOL_CHOICES = [
    ('', '（未選択）'),
    ('chatgpt', 'ChatGPT'),
    ('claude', 'Claude'),
    ('gemini', 'Google Gemini'),
    ('copilot', 'Microsoft Copilot'),
    ('midjourney', 'Midjourney'),
    ('dall_e', 'DALL·E'),
    ('stable_diffusion', 'Stable Diffusion'),
    ('adobe_firefly', 'Adobe Firefly'),
    ('leonardo', 'Leonardo.Ai'),
    ('runway', 'Runway'),
    ('pika', 'Pika'),
    ('nijijourney', 'niji・journey'),
    ('canva_ai', 'Canva AI'),
    ('imagefx', 'Google ImageFX'),
    ('bing_image_creator', 'Bing Image Creator'),
    ('other', 'その他'),
]

AI_TOOL_LABELS = {v: lab for v, lab in AI_TOOL_CHOICES if v}


def normalize_ai_tool(value: str) -> str:
    if not value or not isinstance(value, str):
        return ''
    v = value.strip().lower().replace(' ', '_').replace('-', '_')
    if v in AI_TOOL_LABELS:
        return v
    return ''
