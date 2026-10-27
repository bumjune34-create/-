# 산지 개발 AI 시뮬레이터 — 웹 배포용

학교 컴퓨터는 설치 없이 배포된 URL에 접속합니다. **이 ZIP 자체가 공개 URL은 아니며**, 인터넷 서버에 배포해야 합니다.

## Render에 배포
1. [GitHub](https://github.com)에 새 비공개 저장소를 만들고 이 폴더의 파일과 `static` 폴더를 함께 업로드합니다. (압축파일 자체를 올리는 것이 아니라 압축을 푼 내용입니다.)
2. [Render](https://dashboard.render.com/)에 로그인 → New → Web Service → GitHub 저장소 연결.
3. Python 런타임, Build Command `pip install -r requirements.txt`, Start Command `uvicorn server:app --host 0.0.0.0 --port $PORT`.
4. Render의 Environment에 `OPENAI_API_KEY`를 추가합니다. **키를 HTML이나 GitHub에 넣지 마세요.** 이전에 채팅에 노출된 키는 폐기하고 새로 발급받으세요.
5. 배포 완료 후 Render가 제공하는 `https://...onrender.com` 주소를 학교에서 엽니다.

## 주의
- Render 및 OpenAI API 사용 요금이 발생할 수 있습니다. 무료/유료 플랜 제공 조건은 Render에서 확인하세요.
- 학교 네트워크가 외부 접속을 차단하면 열리지 않을 수 있습니다.
- **학급 공개 전 접근 제한과 지출 한도를 구성하세요.** 공개 URL로 배포 시 누구나 AI 생성 요청을 보낼 수 있으므로, Render의 인증/방화벽 또는 별도 로그인·속도 제한을 추가하는 것이 좋습니다.
- AI 자유 개발은 실험 기능으로, 생성 결과의 경계나 지형의 일관성이 완벽하지 않을 수 있습니다.
- 기존 6개 시설은 버튼과 드래그로 즉시 실행 가능하며 별도 API 요청은 하지 않습니다.
- 실행 시 사진/효과음 교사용 등록은 브라우저의 로컬 데이터로 처리되며, 현재 배포판은 등록 데이터를 서버에 영구 저장하지 않습니다. 수업용 HTML 저장 기능은 그대로 있습니다.

## 로컬 테스트
`pip install -r requirements.txt`
`OPENAI_API_KEY` 환경변수를 설정한 후 `uvicorn server:app --host 127.0.0.1 --port 8765`
`http://127.0.0.1:8765` 열기
