# 🎵 English Practice Player - Streamlit

영어 학습을 위한 TTS(Text-to-Speech) 플레이어입니다. (Streamlit 버전)

## ✨ 주요 기능

### 📂 플레이리스트 생성
- **CSV 파일 업로드**: `english`, `korean` 컬럼이 포함된 CSV 파일 지원
- **텍스트 붙여넣기**:
  - CSV 형식: `english,korean`
  - 줄바꿈 형식: 영어와 한국어를 번갈아 입력
- **샘플 데이터**: 즉시 테스트 가능한 샘플 제공

### 🔊 Google Cloud TTS 음성 재생
- **고품질 TTS**: Google Cloud Text-to-Speech API 사용
- **다양한 음성**: en-US/GB/AU Standard, WaveNet, Neural2 음성 지원
- **재생 모드**:
  - 일반 재생 (None)
  - 한곡 반복 (Repeat One)
  - 전체 반복 (Repeat All)
- **네비게이션**: 처음/이전/재생/다음/마지막 트랙

### 💾 플레이리스트 관리
- **SQLite 저장**: 서버 측 데이터베이스에 저장
- **여러 플레이리스트**: 무제한 플레이리스트 관리
- **CSV 내보내기**: 플레이리스트를 CSV 파일로 내보내기

### ⬇️ MP3 다운로드 (NEW!)
- **개별 다운로드**: 현재 재생 중인 트랙을 MP3로 다운로드
- **일괄 다운로드**: 전체 플레이리스트를 ZIP으로 다운로드
- **오프라인 청취**: 다운받은 MP3로 언제든지 학습 가능

### 💰 비용 효율적
- **무료 티어**: Google Cloud TTS 월 400만 글자 무료
- **유료**: 100만 글자당 $4 (매우 저렴)
- **캐싱**: 한 번 생성한 음성은 캐시되어 재사용 (비용 절감)

## 🚀 설치 및 실행

### 1. 사전 준비

#### Google Cloud TTS API 키 발급
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 프로젝트 생성 또는 선택
3. Cloud Text-to-Speech API 활성화
4. API 키 생성 (Credentials → Create credentials → API key)
5. API 키 복사 (AIzaSy로 시작)

자세한 내용은 `SETUP.md` 파일 참고

### 2. 로컬 실행

```bash
# 저장소 클론
git clone https://github.com/yourusername/english-practice-streamlit.git
cd english-practice-streamlit

# 가상환경 생성 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# Streamlit 실행
streamlit run app.py
```

브라우저에서 자동으로 http://localhost:8501 이 열립니다.

### 3. API 키 입력
- 앱 실행 후 사이드바에서 API 키 입력
- 세션에만 저장되며 브라우저 종료 시 삭제됨
- 영구 사용을 원하면 `.streamlit/secrets.toml` 파일 생성 (아래 참고)

### 4. Streamlit Cloud 배포 (무료)

1. **GitHub에 코드 업로드**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/username/english-practice-streamlit.git
git push -u origin main
```

2. **Streamlit Cloud 배포**
- https://share.streamlit.io 접속
- "New app" 클릭
- GitHub 레포지토리 연결
- Main file: `app.py`
- Deploy 클릭

3. **API 키 설정 (중요!)**
- Streamlit Cloud 대시보드 → 앱 선택
- Settings → Secrets 클릭
- 다음 내용 입력:
```toml
[google_cloud]
api_key = "AIzaSy...실제_발급받은_키"
```
- Save 클릭

**완료!** 이제 전 세계 어디서든 접속 가능합니다.

## 📂 프로젝트 구조

```
streamlit-english-practice/
├── app.py                      # 메인 애플리케이션
├── requirements.txt            # Python 패키지 목록
├── packages.txt                # 시스템 패키지 (libsndfile1)
├── .streamlit/
│   ├── config.toml            # 테마 설정
│   └── secrets.toml           # API 키 (gitignore됨)
├── modules/
│   ├── __init__.py
│   ├── tts_engine.py          # Google Cloud TTS 엔진
│   ├── audio_player.py        # 오디오 재생 및 다운로드
│   ├── storage.py             # SQLite 플레이리스트 관리
│   ├── csv_parser.py          # CSV/텍스트 파싱
│   └── ui_components.py       # UI 컴포넌트
├── utils/
│   ├── __init__.py
│   ├── cache_manager.py       # LRU 캐시 (100MB, 30일 TTL)
│   ├── audio_utils.py         # 오디오 유틸리티
│   └── security.py            # API 키 검증
└── data/
    ├── sample_data.json       # 샘플 데이터
    ├── playlists.db           # SQLite 데이터베이스 (자동 생성)
    └── cache/                 # 오디오 캐시 (자동 생성)
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

**형식 1: CSV**
```
english,korean
Hello, how are you?,안녕하세요, 어떻게 지내세요?
Nice to meet you.,만나서 반갑습니다.
```

**형식 2: 줄바꿈**
```
Hello, how are you?
안녕하세요, 어떻게 지내세요?
Nice to meet you.
만나서 반갑습니다.
```

## 🎤 지원 음성

| 지역 | 음성 타입 | 예시 |
|-----|----------|------|
| **미국 (en-US)** | Standard, WaveNet, Neural2 | A, B, C, D, E, F, G, H, I, J |
| **영국 (en-GB)** | Standard, WaveNet, Neural2 | A, B, C, D, F |
| **호주 (en-AU)** | Standard, WaveNet, Neural2 | A, B, C, D |

- **Standard**: 기본 품질, 저렴
- **WaveNet**: 고품질, 자연스러움
- **Neural2**: 최신, 가장 자연스러움

## 💡 팁

1. **비용 절감**: 캐시 시스템이 자동으로 생성된 음성을 저장합니다. 같은 문장을 여러 번 재생해도 한 번만 요금이 부과됩니다.

2. **오프라인 청취**: MP3 다운로드 기능으로 언제든지 오프라인으로 학습할 수 있습니다.

3. **데이터 백업**: 정기적으로 플레이리스트를 CSV로 내보내 백업하세요.

4. **음성 테스트**: 여러 음성을 테스트해보고 가장 좋은 음성을 선택하세요.

5. **ZIP 다운로드**: 전체 플레이리스트를 ZIP으로 다운받아 모바일 기기로 전송하세요.

## 🐛 문제 해결

### API 키 오류
- API 키가 'AIzaSy'로 시작하는지 확인
- Google Cloud Console에서 Text-to-Speech API가 활성화되었는지 확인
- Billing이 활성화되었는지 확인 (무료 티어 사용 가능)

### 오디오 생성 실패
- API 키가 올바른지 확인
- Google Cloud 무료 티어 한도(월 400만 글자)를 초과하지 않았는지 확인
- 인터넷 연결 확인

### 캐시가 작동하지 않음
- `data/cache/` 디렉토리가 생성되었는지 확인
- 쓰기 권한이 있는지 확인

### 플레이리스트가 사라짐
- `data/playlists.db` 파일이 삭제되었을 수 있습니다
- 정기적으로 CSV로 백업하세요

## 🆚 PWA 버전과 비교

| 기능 | PWA 버전 | Streamlit 버전 |
|------|----------|----------------|
| **TTS 엔진** | 브라우저 내장 (Web Speech API) | Google Cloud TTS ✅ |
| **음질** | 보통 | 고품질 ✅ |
| **오프라인** | 완전 지원 | 미지원 |
| **속도 조절** | 0.5x~2x | 미지원 (단순화) |
| **MP3 다운로드** | 미지원 | 지원 ✅ |
| **ZIP 다운로드** | 미지원 | 지원 ✅ |
| **비용** | 무료 | 무료 티어 or 저렴 |
| **배포** | Vercel/Netlify | Streamlit Cloud ✅ |
| **유지보수** | HTML/CSS/JS (2,954줄) | Python (1,480줄) ✅ |

## 📊 비용 예상

**무료 티어 (월)**:
- 4,000,000 글자 무료
- 약 200~400개 문장 (평균 50~100자/문장)
- 대부분의 개인 사용자는 무료 범위

**유료 (초과 시)**:
- $4 / 1,000,000 글자
- 예: 10,000 문장 (50자) = 500,000 글자 = $2

**캐싱 효과**:
- 한 번 생성한 음성은 30일간 재사용
- 실제 비용은 훨씬 낮음

## 📝 라이선스

MIT License

## 🙋 문의

문제가 있거나 기능 제안이 있으시면 이슈를 등록해주세요!

---

**즐거운 영어 학습 되세요! 🎉**
