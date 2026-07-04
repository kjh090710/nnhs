# Seoul Ozone Dashboard

서울 여름철 오존 농도 분석 결과를 보여주는 Flask 기반 대시보드입니다. Render 배포를 바로 할 수 있도록 `requirements.txt`, `Procfile`, `render.yaml`을 포함했습니다.

## 구성

```text
seoul_ozone_dashboard/
├─ app.py
├─ requirements.txt
├─ Procfile
├─ render.yaml
├─ data/
│  ├─ summary.json
│  ├─ model_performance.csv
│  ├─ predictions.csv
│  └─ predictions_sample.csv
├─ static/
│  ├─ css/style.css
│  ├─ js/main.js
│  └─ img/*.png
├─ templates/*.html
└─ scripts/build_summary.py
```

## 로컬 실행

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows PowerShell은 .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

브라우저에서 `http://127.0.0.1:5000`으로 접속하면 됩니다.

## Render 배포

1. 이 폴더를 GitHub 저장소에 업로드합니다.
2. Render에서 New > Web Service를 선택하고 저장소를 연결합니다.
3. 설정값은 아래처럼 입력합니다.

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

`render.yaml`을 사용하는 경우 Blueprint로 배포할 수도 있습니다.

## 원본 CSV에 대한 안내

`cache_based_clean_dataset.csv`는 용량이 커서 배포 패키지에 넣지 않았습니다. Render 배포에는 요약 파일과 그래프 이미지만 있어도 웹이 정상 작동합니다. 원본 데이터로 요약을 다시 만들고 싶다면 `data/raw/cache_based_clean_dataset.csv`로 넣은 뒤 아래 명령을 실행하면 됩니다.

```bash
python scripts/build_summary.py
```
