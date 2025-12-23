# 🎵 English Practice Player - PWA

영어 학습을 위한 TTS(Text-to-Speech) 플레이어입니다.

## ✨ 주요 기능

### 📂 플레이리스트 생성
- **CSV 파일 업로드**: `english`, `korean` 컬럼이 포함된 CSV 파일 지원
- **텍스트 붙여넣기**: 영어-한국어 번역 쌍을 줄바꿈으로 구분하여 입력
- **클립보드에서 가져오기**: 복사한 텍스트를 바로 불러오기
- **샘플 데이터**: 즉시 테스트 가능한 샘플 제공

### 🔊 TTS 음성 재생
- **네이티브 브라우저 TTS**: Web Speech API 사용
- **5단계 속도 조절**: 0.5x ~ 1.5x
- **재생 모드**:
  - 일반 재생
  - 한곡 반복 (🔂)
  - 전체 반복 (🔁)
- **자동 다음 곡**: 트랙 종료 시 자동 진행

### 💾 플레이리스트 관리
- **로컬 저장**: 브라우저 localStorage에 저장
- **여러 플레이리스트**: 무제한 플레이리스트 관리
- **CSV 내보내기**: 플레이리스트를 CSV 파일로 내보내기

### 📱 PWA 기능
- **오프라인 지원**: Service Worker로 오프라인 사용 가능
- **홈 화면 추가**: 앱처럼 사용 가능
- **반응형 디자인**: 모바일/데스크톱 최적화
- **빠른 로딩**: 캐싱으로 빠른 실행

## 🚀 배포 방법

### 방법 1: Vercel (추천 - 가장 쉬움)

1. **GitHub에 코드 업로드**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/username/english-player.git
git push -u origin main
```

2. **Vercel에 배포**
- https://vercel.com 접속
- "New Project" 클릭
- GitHub 레포지토리 연결
- Deploy 클릭

3. **API 키 설정 (중요!)**
- Vercel 대시보드 → 프로젝트 선택
- Settings → Environment Variables 클릭
- 다음 환경 변수 추가:
  - **Name**: `GOOGLE_CLOUD_TTS_API_KEY`
  - **Value**: Google Cloud에서 발급받은 API 키
  - **Environment**: Production, Preview, Development 모두 선택
- 저장 후 프로젝트를 다시 배포 (Redeploy)

**Google Cloud API 키 받는 방법**: `SETUP.md` 파일 참고

**자동 배포**: 이후 `git push`만 하면 자동으로 재배포됩니다!

### 방법 2: Netlify

1. **Netlify에 배포**
```bash
# Netlify CLI 설치
npm install -g netlify-cli

# 배포
netlify deploy --prod
```

2. **또는 드래그 앤 드롭**
- https://app.netlify.com/drop 접속
- 폴더를 드래그 앤 드롭
- 완료!

### 방법 3: GitHub Pages

1. **GitHub Pages 활성화**
- GitHub 레포지토리 → Settings → Pages
- Source: main branch 선택
- Save

2. **접속**
```
https://username.github.io/english-player/
```

## 📂 파일 구조

```
english-player-pwa/
├── index.html          # 메인 HTML
├── styles.css          # 스타일시트
├── app.js             # 메인 JavaScript
├── manifest.json      # PWA 매니페스트
├── sw.js             # Service Worker
├── icon-192.png      # 앱 아이콘 (192x192)
├── icon-512.png      # 앱 아이콘 (512x512)
└── README.md         # 이 파일
```

## 🎨 아이콘 생성

192x192, 512x512 크기의 PNG 아이콘이 필요합니다.

간단한 아이콘 생성 방법:
1. https://favicon.io/favicon-generator/ 접속
2. 아이콘 디자인
3. 다운로드 후 `icon-192.png`, `icon-512.png`로 이름 변경

## 📱 모바일 설치 방법

### iOS (Safari)
1. Safari에서 앱 열기
2. 공유 버튼 탭
3. "홈 화면에 추가" 선택
4. 추가 완료!

### Android (Chrome)
1. Chrome에서 앱 열기
2. 메뉴(⋮) → "홈 화면에 추가"
3. 추가 완료!

## 🔧 로컬 개발

### 환경 변수 설정
프로젝트 루트에 `.env.local` 파일을 생성하고 API 키를 추가하세요:

```bash
GOOGLE_CLOUD_TTS_API_KEY=AIzaSy...실제_발급받은_키
```

**API 키 발급 방법**: `SETUP.md` 파일 참고

### 서버 실행
```bash
# Vercel Dev (추천 - API 엔드포인트 지원)
npx vercel dev

# 또는 간단한 HTTP 서버
python -m http.server 8000
# 또는
npx serve

# 브라우저에서 접속
http://localhost:3000  # Vercel Dev
# 또는
http://localhost:8000  # HTTP 서버
```

## 📋 CSV 파일 형식

```csv
english,korean
"Hello, how are you?","안녕하세요, 어떻게 지내세요?"
"Nice to meet you.","만나서 반갑습니다."
"Thank you very much.","정말 감사합니다."
```

## 🎯 사용 예시

### 텍스트 붙여넣기 형식
```
Hello, how are you?
안녕하세요, 어떻게 지내세요?
Nice to meet you.
만나서 반갑습니다.
Thank you very much.
정말 감사합니다.
```

## 🌐 브라우저 지원

| 브라우저 | TTS | PWA | 오프라인 |
|---------|-----|-----|---------|
| Chrome (Android) | ✅ | ✅ | ✅ |
| Safari (iOS) | ✅ | ✅ | ✅ |
| Firefox | ✅ | ✅ | ✅ |
| Edge | ✅ | ✅ | ✅ |

## 💡 팁

1. **최상의 TTS 품질을 위해**: 시스템 언어를 영어로 설정하면 더 나은 음성을 사용할 수 있습니다.

2. **백그라운드 재생**: 홈 화면에 추가한 후 실행하면 백그라운드 재생이 더 안정적입니다.

3. **데이터 백업**: 정기적으로 플레이리스트를 CSV로 내보내 백업하세요.

4. **여러 플레이리스트**: 주제별로 여러 플레이리스트를 만들어 관리하세요.

## 🐛 문제 해결

### TTS가 작동하지 않을 때
- 브라우저 언어 설정 확인
- 시스템 볼륨 확인
- 페이지 새로고침

### 오프라인에서 작동하지 않을 때
- 한 번 온라인에서 접속하여 캐시 생성 필요
- Service Worker 등록 확인 (개발자 도구 → Application → Service Workers)

### 플레이리스트가 사라졌을 때
- 브라우저 데이터를 삭제하면 localStorage도 삭제됩니다
- 정기적으로 CSV로 백업하세요

## 📝 라이선스

MIT License

## 🙋 문의

문제가 있거나 기능 제안이 있으시면 이슈를 등록해주세요!

---

**즐거운 영어 학습 되세요! 🎉**
