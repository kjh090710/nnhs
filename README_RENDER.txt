Render 배포 설정

Build Command:
pip install -r requirements.txt

Start Command:
gunicorn app:app

Health Check Path:
/healthz

주의:
- .venv 폴더는 포함하지 않았습니다.
- data/raw 같은 대용량 원본 데이터는 Render에 올리지 않아도 됩니다.
- data/summary.json, data/model_performance.csv, data/predictions_sample.csv와 static/img 그래프 이미지만 있으면 웹 화면은 동작합니다.
