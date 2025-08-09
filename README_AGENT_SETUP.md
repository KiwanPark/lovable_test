# Lovable → GitHub → ChatGPT 에이전트 후처리 세팅 가이드

이 폴더는 러버블이 GitHub에 푸시한 뒤, ChatGPT API를 통해 **소규모 자동 수정을 적용**하는 최소 구성 예시입니다.

## 1) 준비물
- OpenAI API Key (대시보드에서 발급)
- GitHub 저장소 권한 (Actions 사용 가능)

## 2) GitHub Secrets / Variables
- **Secrets**: `OPENAI_API_KEY` (필수)
- **Variables**(선택): 
  - `OPENAI_MODEL` (기본 `gpt-4o-mini`)
  - `FILE_GLOBS` (예: `src/**/*.ts,src/**/*.tsx`)
  - `MAX_FILES` (기본 10)
  - `MAX_CHARS_PER_FILE` (기본 50000)

## 3) 설치
레포지토리 루트에 다음을 추가합니다.
```
.github/workflows/lovable-agent.yml
.github/scripts/chatgpt_fix.py
```
이 레포 안의 동일 경로 구조를 그대로 복사하면 됩니다.

## 4) 동작 방식
1. `main` 브랜치로 푸시 발생(러버블 푸시 포함) 또는 수동 실행
2. 직전 커밋 기준 변경 파일 목록을 계산
3. `FILE_GLOBS`에 매칭되는 파일만 선별하여 ChatGPT에 소폭 개선 요청
4. 변경 결과를 커밋/푸시

## 5) 안전장치/운영 팁
- 워크플로우는 `github-actions[bot]`이 만든 커밋에는 재실행하지 않음
- 대수술 방지를 위해 시스템 메시지에 “작은 수정만”을 강제
- 필요 시 PR 모드로 변경: `peter-evans/create-pull-request` 액션 사용
- 비용 절감: `FILE_GLOBS`로 범위를 좁히고, `MAX_FILES`/`MAX_CHARS_PER_FILE` 조절

## 6) 트러블슈팅
- 실행 안 됨: Actions 탭에서 로그 확인
- 변경 없음: 모델 응답이 원문과 동일한 경우(규칙이 너무 보수적일 수 있음). 파일 범위/지침을 완화해 보세요.
- 루프 방지: 커밋 메시지 접두어를 체크하거나 현재 설정처럼 actor 체크를 유지하세요.
