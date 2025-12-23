# Google Cloud TTS Setup Guide

## 1. Google Cloud API 키 받기

### 1단계: Google Cloud Console 접속
https://console.cloud.google.com/

### 2단계: 프로젝트 생성 (또는 기존 프로젝트 선택)
- 상단 프로젝트 선택 드롭다운 클릭
- "새 프로젝트" 클릭
- 프로젝트 이름 입력 (예: "English Practice PWA")

### 3단계: Text-to-Speech API 활성화
1. 좌측 메뉴 → "API 및 서비스" → "라이브러리"
2. "Cloud Text-to-Speech API" 검색
3. "사용 설정" 클릭

### 4단계: API 키 생성
1. 좌측 메뉴 → "API 및 서비스" → "사용자 인증 정보"
2. "+ 사용자 인증 정보 만들기" → "API 키" 클릭
3. API 키가 생성됨 (복사해두기)

### 5단계: API 키 제한 (보안을 위해 권장)
1. 생성된 API 키 옆 편집 아이콘 클릭
2. "API 제한사항" → "키 제한"
3. "Cloud Text-to-Speech API"만 선택
4. 저장

## 2. 로컬 환경 설정

### .env.local 파일 수정
프로젝트 루트의 `.env.local` 파일을 열고 API 키 입력:

```bash
GOOGLE_CLOUD_TTS_API_KEY=AIzaSy...실제_발급받은_키
```

### 의존성 설치
```bash
npm install
```

## 3. 로컬 테스트

### Vercel Dev 서버 실행
```bash
npx vercel dev
```

또는

```bash
npm run dev
```

### 브라우저에서 접속
```
http://localhost:3000
```

## 4. 기능 테스트

### 테스트 체크리스트
- [ ] 샘플 데이터 로드
- [ ] Google Cloud TTS 모드 선택
- [ ] 재생 버튼 클릭
- [ ] 로딩 스피너 확인
- [ ] 고품질 음성 재생 확인
- [ ] 정확한 시간 표시 확인 (MM:SS / MM:SS)
- [ ] 일시정지/재개 테스트
- [ ] 속도 변경 (즉시 적용 확인)
- [ ] 다음 트랙 자동 재생
- [ ] 사용량 통계 확인

### TTS 모드별 동작
1. **Auto (Recommended)**: 온라인 시 Google TTS, 오프라인/쿼터 초과 시 Browser TTS
2. **Google Cloud**: 항상 Google TTS 사용 (오프라인 시 에러)
3. **Browser TTS**: 항상 Web Speech API 사용 (오프라인 지원)

## 5. Vercel 배포

### 환경 변수 설정
1. Vercel 대시보드 → 프로젝트 선택
2. Settings → Environment Variables
3. 추가:
   - Name: `GOOGLE_CLOUD_TTS_API_KEY`
   - Value: `실제_API_키`
   - Environment: Production, Preview, Development 모두 선택

### 배포
```bash
vercel --prod
```

또는 GitHub에 push하면 자동 배포

## 6. 무료 티어 한도

- **월 1,000,000 characters** (WaveNet voices)
- **캐시 활용**: 90% 절감 효과
- **예상 사용량**:
  - 일일 30트랙 × 50자 = 1,500자/일
  - 월간: ~45,000자 (4.5% 사용)

## 7. 문제 해결

### API 키가 작동하지 않을 때
- API 활성화 확인
- 키 제한 설정 확인
- `.env.local` 파일 저장 확인
- Vercel Dev 서버 재시작

### 음성이 재생되지 않을 때
- 브라우저 콘솔 확인 (F12)
- Network 탭에서 /api/tts 요청 확인
- TTS 모드를 "Browser TTS"로 변경해보기

### 캐시 문제
- 브라우저 DevTools → Application → IndexedDB
- "EnglishPlayerTTS" 데이터베이스 확인/삭제

## 8. 주요 개선 사항

### 이전 (Web Speech API)
- ❌ 브라우저 의존적 음성 품질
- ❌ 추정된 duration
- ❌ 문자 기반 진행률 (부정확)
- ❌ 일시정지 지원 제한적
- ❌ 속도 변경 시 재시작 필요

### 현재 (Google Cloud TTS)
- ✅ 네이티브 수준의 Neural2 음성
- ✅ 정확한 duration (HTML5 Audio)
- ✅ 시간 기반 진행률 (부드러움)
- ✅ 완벽한 일시정지/재개
- ✅ 즉시 속도 변경 (재시작 불필요)

## 9. 다음 단계

- [ ] 음성 프리셋 추가 (미국, 영국, 호주 억양)
- [ ] 플레이리스트별 사용량 통계
- [ ] 오프라인 캐시 용량 설정
- [ ] 백그라운드 프리로딩 최적화
