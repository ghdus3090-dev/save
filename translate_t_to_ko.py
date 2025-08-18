import os, re, time, json
from typing import Tuple, List

# ------------------------------
# 설정
# ------------------------------
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_PATH, "dialog_extracted_copied.txt")
OUTPUT_FILE = os.path.join(BASE_PATH, "dialog_extracted_translated.txt")

# Papago 사용 시 환경변수 설정 필요:
#   PAPAGO_CLIENT_ID, PAPAGO_CLIENT_SECRET
# googletrans 사용 시: pip install googletrans==4.0.0-rc1

# ------------------------------
# 유틸: 토큰 보호/복원 (번역 보호)
# ------------------------------
TOKEN_PATTERNS = [
    r"\[[^\]\n]+\]",           # 대괄호 토큰 [Spice], [!Something], [A_B], [::target::] 등
    r"::[^:\n]+::",            # ::value::, ::percent_value::
    r"<[^>\n]+>",              # <Title>…</Title>, <good>500</good>
    r"\$my\([^)]+\)",          # $my(Elite)
    r"\[[^\]\n]*?-[^\]\n]*?\]",# [Atreides-longname] 등 하이픈 포함
]

TOKEN_REGEX = re.compile("|".join(f"({p})" for p in TOKEN_PATTERNS))

def protect_tokens(text: str) -> Tuple[str, List[str]]:
    placeholders = []
    def repl(m):
        placeholders.append(m.group(0))
        return f"__TAG_{len(placeholders)-1}__"
    protected = TOKEN_REGEX.sub(repl, text)
    return protected, placeholders

def restore_tokens(text: str, placeholders: List[str]) -> str:
    for i, tok in enumerate(placeholders):
        text = text.replace(f"__TAG_{i}__", tok)
    return text

# ------------------------------
# Papago 번역 (있으면 최우선)
# ------------------------------
def translate_papago(text: str) -> str:
    client_id = os.getenv("PAPAGO_CLIENT_ID")
    client_secret = os.getenv("PAPAGO_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError("Papago API 키가 없습니다.")

    import urllib.request, urllib.parse

    url = "https://openapi.naver.com/v1/papago/n2mt"
    data = {
        "source": "en",
        "target": "ko",
        "text": text
    }
    data_encoded = urllib.parse.urlencode(data).encode("utf-8")
