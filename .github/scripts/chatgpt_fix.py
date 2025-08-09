import os, fnmatch, subprocess, sys, pathlib
from typing import List
from openai import OpenAI

# --- Config (env with sane defaults) ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
FILE_GLOBS = [g.strip() for g in (os.getenv("FILE_GLOBS") or "src/**/*.ts,src/**/*.tsx,src/**/*.js,src/**/*.jsx").split(",")]
MAX_FILES = int(os.getenv("MAX_FILES") or "10")
MAX_CHARS_PER_FILE = int(os.getenv("MAX_CHARS_PER_FILE") or "50000")

EXCLUDE_DIRS = {"node_modules", ".next", "dist", "build", ".git", ".venv", ".gradle", "out"}

SYSTEM_PROMPT = (
    "당신은 숙련된 프런트엔드/풀스택 개발자입니다. "
    "작은 리팩토링, 주석 보강, 미세한 가독성 개선, 간단한 ESLint 수준 정리만 수행하십시오. "
    "기능/로직/퍼블릭 API 시그니처는 바꾸지 마십시오. 테스트/빌드가 깨질 변경 금지. "
    "가능하면 변경 이유를 파일 최상단에 한 줄 주석으로 추가하세요."
)

USER_INSTR = (
    "아래 파일 내용을 소폭 개선해 주세요. 주석 보강, 불필요한 코드/주석 정리, 일관성 향상 등.\n"
    "- 로직과 동작 결과는 동일해야 합니다.\n"
    "- 대규모 리팩토링/패턴 교체/라이브러리 변경 금지.\n"
    "- 반드시 전체 파일을 결과로 반환해 주세요."
)

if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY is missing.")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

def get_changed_files() -> List[str]:
    """Get files changed in the last commit; fallback to repo files if needed."""
    # Try to get files in the last commit range
    try:
        out = subprocess.check_output(["bash", "-lc", "git diff --name-only HEAD^ HEAD"], text=True).strip()
        files = [line for line in out.splitlines() if line.strip()]
        if files:
            return files
    except Exception as e:
        print("diff fallback:", e)

    # Fallback: list tracked files
    try:
        out = subprocess.check_output(["bash", "-lc", "git ls-files"], text=True).strip()
        files = [line for line in out.splitlines() if line.strip()]
        return files
    except Exception as e:
        print("ls-files failed:", e)
        return []

def match_globs(path: str) -> bool:
    for g in FILE_GLOBS:
        if fnmatch.fnmatch(path, g):
            return True
    return False

def excluded(path: str) -> bool:
    parts = pathlib.Path(path).parts
    return any(seg in EXCLUDE_DIRS for seg in parts)

def improve_file(path: str) -> bool:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            src = f.read()
        if not src or len(src) > MAX_CHARS_PER_FILE:
            return False

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"{USER_INSTR}\n\n<FILE path='{path}'>\n{src}\n</FILE>"},
        ]

        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.1,
        )
        out = resp.choices[0].message.content or ""
        out = out.strip()
        if out and out != src:
            with open(path, "w", encoding="utf-8") as f:
                f.write(out)
            print("modified:", path)
            return True
    except Exception as e:
        print("skip:", path, e)
    return False

def main():
    all_changed = get_changed_files()

    # Filter by globs + exclude dirs + only existing files
    candidates = []
    for p in all_changed:
        if not os.path.isfile(p):
            continue
        if excluded(p):
            continue
        if match_globs(p):
            candidates.append(p)

    # De-duplicate and cap
    seen = set()
    filtered = []
    for p in candidates:
        if p not in seen:
            filtered.append(p)
            seen.add(p)
        if len(filtered) >= MAX_FILES:
            break

    if not filtered:
        print("No candidate files matched; nothing to do.")
        return

    print("Target files:", filtered)

    any_change = False
    for p in filtered:
        changed = improve_file(p)
        any_change = any_change or changed

    if not any_change:
        print("No effective changes produced.")

if __name__ == "__main__":
    main()
