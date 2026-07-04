from flask import Flask, render_template, send_from_directory, jsonify, request
from pathlib import Path
import json
import csv
import math

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
IMG_DIR = STATIC_DIR / "img"

DATA_DIR_CANDIDATES = [
    BASE_DIR / "data",
    BASE_DIR / "data" / "processed",
    BASE_DIR / "data" / "raw",
    BASE_DIR / "static" / "data",
    BASE_DIR
]


# =========================================================
# 기본 요약값
# summary.json이 없거나 일부 값이 비어 있어도 웹이 깨지지 않게 함
# =========================================================

DEFAULT_SUMMARY = {
    "dataset": {
        "city": "서울특별시",
        "date_start": "2010-06-01",
        "date_end": "2025-08-31",
        "months": "6월, 7월, 8월",
        "rows": 1354453,
        "features": 65,
        "station_count": 46
    },
    "metrics": {
        "mean_O3": 0.0290,
        "max_O3": 0.2274,
        "mean_temp": 25.6,
        "mean_humidity": 70.8,
        "mean_NO2": 0.0260,
        "mean_PM25": 17.0,
        "mean_PM10": 31.7
    },
    "modeling": {
        "best_model": "HistGradientBoosting Regression",
        "best_R2": 0.721,
        "best_MAE": 0.0085,
        "best_RMSE": 0.0113
    },
    "findings": [
        {
            "title": "오후 시간대 오존 증가",
            "value": "15~16시",
            "body": "시간대 평균 그래프에서 오후 15~16시 부근의 오존 농도가 가장 높게 나타났습니다."
        },
        {
            "title": "기온과 오존의 양의 관계",
            "value": "+",
            "body": "기온이 높을수록 오존 농도가 증가하는 경향이 나타났습니다."
        },
        {
            "title": "습도와 오존의 음의 관계",
            "value": "-",
            "body": "습도가 높을수록 오존 농도가 낮아지는 경향이 확인되었습니다."
        },
        {
            "title": "비선형 모델의 우수성",
            "value": "R² 0.721",
            "body": "HistGradientBoosting Regression이 가장 높은 설명력을 보였습니다."
        }
    ]
}


DEFAULT_MODELS = [
    {
        "Model": "HistGradientBoosting Regression",
        "R2": 0.721,
        "MAE": 0.0085,
        "RMSE": 0.0113,
        "sample_rows": 50000,
        "features_used": 13
    },
    {
        "Model": "Polynomial Ridge degree=2",
        "R2": 0.653,
        "MAE": 0.0096,
        "RMSE": 0.0126,
        "sample_rows": 50000,
        "features_used": 10
    },
    {
        "Model": "Ridge Regression",
        "R2": 0.578,
        "MAE": 0.0107,
        "RMSE": 0.0139,
        "sample_rows": 50000,
        "features_used": 59
    },
    {
        "Model": "Multiple Linear Regression",
        "R2": 0.578,
        "MAE": 0.0107,
        "RMSE": 0.0139,
        "sample_rows": 50000,
        "features_used": 59
    },
    {
        "Model": "SGD ElasticNet Regression",
        "R2": 0.572,
        "MAE": 0.0108,
        "RMSE": 0.0140,
        "sample_rows": 50000,
        "features_used": 59
    }
]


# =========================================================
# 유틸 함수
# =========================================================

def deep_merge(base, incoming):
    result = dict(base)

    for key, value in incoming.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def find_data_file(filename):
    for folder in DATA_DIR_CANDIDATES:
        candidate = folder / filename
        if candidate.exists():
            return candidate

    for candidate in BASE_DIR.rglob(filename):
        if ".venv" not in candidate.parts and "__pycache__" not in candidate.parts:
            return candidate

    return None


def load_summary():
    summary_path = find_data_file("summary.json")

    if not summary_path:
        return DEFAULT_SUMMARY

    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        if not isinstance(loaded, dict):
            return DEFAULT_SUMMARY

        return deep_merge(DEFAULT_SUMMARY, loaded)

    except Exception:
        return DEFAULT_SUMMARY


def to_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def to_int(value, default=0):
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def normalize_model_row(row):
    model_name = (
        row.get("Model")
        or row.get("model")
        or row.get("모델")
        or row.get("name")
        or row.get("Name")
        or "모델명 없음"
    )

    r2_value = (
        row.get("R2")
        or row.get("R²")
        or row.get("r2")
        or row.get("r_squared")
        or row.get("R_squared")
        or 0
    )

    return {
        "Model": model_name,
        "R2": to_float(r2_value),
        "MAE": to_float(row.get("MAE") or row.get("mae")),
        "RMSE": to_float(row.get("RMSE") or row.get("rmse")),
        "sample_rows": to_int(row.get("sample_rows") or row.get("Sample Rows") or row.get("표본 수"), 50000),
        "features_used": to_int(row.get("features_used") or row.get("Features Used") or row.get("사용 변수 수"), 0)
    }


def load_models():
    model_path = find_data_file("model_performance.csv")

    if not model_path:
        return DEFAULT_MODELS

    try:
        rows = []

        with open(model_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                rows.append(normalize_model_row(row))

        if not rows:
            return DEFAULT_MODELS

        rows.sort(key=lambda x: x["R2"], reverse=True)
        return rows

    except Exception:
        return DEFAULT_MODELS


def normalize_filename_text(text):
    return (
        str(text)
        .lower()
        .replace("₂", "2")
        .replace("₃", "3")
        .replace("-", "_")
        .replace(" ", "_")
    )


def find_img_by_keywords(*keywords):
    """
    static/img 폴더에서 파일명에 keywords가 모두 들어간 이미지를 자동 탐색.
    Render는 대소문자를 구분하므로 서버에서 직접 파일명을 찾아 넘긴다.
    """
    if not IMG_DIR.exists():
        return None

    image_files = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        image_files.extend(IMG_DIR.glob(ext))

    normalized_keywords = [normalize_filename_text(k) for k in keywords]

    for file in sorted(image_files):
        name = normalize_filename_text(file.name)

        if all(keyword in name for keyword in normalized_keywords):
            return f"img/{file.name}"

    return None


def find_img_by_any_keyword_sets(keyword_sets):
    for keywords in keyword_sets:
        found = find_img_by_keywords(*keywords)
        if found:
            return found
    return None


def get_variable_images():
    temp_img = find_img_by_any_keyword_sets([
        ("02", "temp", "o3"),
        ("02", "temperature", "o3"),
        ("temp", "o3"),
        ("temperature", "o3"),
        ("temp", "ozone"),
        ("temperature", "ozone"),
        ("기온", "오존"),
    ])

    no2_img = find_img_by_any_keyword_sets([
        ("03", "no2", "o3"),
        ("03", "no2", "ozone"),
        ("no2", "o3"),
        ("no2", "ozone"),
        ("NO2", "O3"),
        ("NO2", "ozone"),
        ("이산화질소", "오존"),
    ])

    return {
        "temp_o3": temp_img,
        "no2_o3": no2_img
    }


def get_standard_images():
    return {
        "correlation": find_img_by_any_keyword_sets([
            ("01", "correlation"),
            ("correlation", "heatmap"),
            ("상관", "히트맵")
        ]),
        "hourly": find_img_by_any_keyword_sets([
            ("04", "hourly"),
            ("hour", "mean", "o3"),
            ("hourly", "o3")
        ]),
        "monthly": find_img_by_any_keyword_sets([
            ("05", "monthly"),
            ("month", "mean", "o3"),
            ("monthly", "o3")
        ]),
        "yearly": find_img_by_any_keyword_sets([
            ("06", "yearly"),
            ("year", "mean", "o3"),
            ("yearly", "o3")
        ]),
        "hour_month": find_img_by_any_keyword_sets([
            ("07", "hour", "month"),
            ("hour", "month", "heatmap"),
            ("hour_month", "o3")
        ]),
        "r2": find_img_by_any_keyword_sets([
            ("08", "r2"),
            ("model", "r2"),
            ("comparison", "r2")
        ]),
        "rmse": find_img_by_any_keyword_sets([
            ("09", "rmse"),
            ("model", "rmse"),
            ("comparison", "rmse")
        ]),
        "actual_predicted": find_img_by_any_keyword_sets([
            ("actual", "predicted"),
            ("prediction", "actual"),
            ("10", "actual")
        ]),
        "residual_plot": find_img_by_any_keyword_sets([
            ("residual", "plot"),
            ("11", "residual")
        ]),
        "residual_distribution": find_img_by_any_keyword_sets([
            ("residual", "distribution"),
            ("12", "residual")
        ])
    }


summary = load_summary()
models = load_models()


# =========================================================
# Jinja 필터
# =========================================================

@app.template_filter("ppm")
def ppm_filter(value):
    try:
        return f"{float(value):.4f} ppm"
    except Exception:
        return "0.0000 ppm"


@app.template_filter("num")
def num_filter(value):
    try:
        return f"{int(float(value)):,}"
    except Exception:
        return str(value)


# =========================================================
# 페이지 라우트
# =========================================================

@app.route("/")
@app.route("/overview")
def overview():
    return render_template(
        "overview.html",
        page_title="대시보드",
        active_page="overview",
        summary=summary,
        images=get_standard_images()
    )


@app.route("/correlation")
def correlation():
    return render_template(
        "correlation.html",
        page_title="상관관계 분석",
        active_page="correlation",
        summary=summary,
        images=get_standard_images()
    )


@app.route("/variables")
def variables():
    return render_template(
        "variables.html",
        page_title="변수별 분석",
        active_page="variables",
        summary=summary,
        variable_images=get_variable_images()
    )


@app.route("/time")
def time_analysis():
    return render_template(
        "time.html",
        page_title="시간대 분석",
        active_page="time",
        summary=summary,
        images=get_standard_images()
    )


@app.route("/models")
def model_page():
    return render_template(
        "models.html",
        page_title="모델링 결과",
        active_page="models",
        summary=summary,
        models=models,
        images=get_standard_images()
    )


@app.route("/prediction")
def prediction():
    return render_template(
        "prediction.html",
        page_title="예측 및 평가",
        active_page="prediction",
        summary=summary,
        images=get_standard_images()
    )


@app.route("/data")
def data_page():
    return render_template(
        "data.html",
        page_title="데이터 정보",
        active_page="data",
        summary=summary
    )


@app.route("/about")
def about():
    return render_template(
        "about.html",
        page_title="소개",
        active_page="about",
        summary=summary
    )


# =========================================================
# 간단 예측 API
# prediction.html에서 필요할 경우 사용 가능
# =========================================================

@app.route("/api/predict", methods=["GET", "POST"])
def api_predict():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
    else:
        payload = request.args

    temp = to_float(payload.get("temp"), 30.0)
    humidity = to_float(payload.get("humidity"), 65.0)
    no2 = to_float(payload.get("NO2") or payload.get("no2"), 0.025)
    pm25 = to_float(payload.get("PM25") or payload.get("pm25"), 17.0)
    pm10 = to_float(payload.get("PM10") or payload.get("pm10"), 32.0)
    wind = to_float(payload.get("wind"), 2.1)
    solar = to_float(payload.get("solar"), 1.2)
    sunshine = to_float(payload.get("sunshine"), 0.55)
    pressure = to_float(payload.get("pressure"), 1010.0)
    hour = to_float(payload.get("hour"), 16.0)

    hour_effect = max(0, 1 - abs(hour - 16) / 9) * 0.018

    predicted = (
        0.011
        + (temp - 25) * 0.0012
        - (humidity - 70) * 0.00016
        + no2 * 0.04
        + (solar * 0.004)
        + (sunshine * 0.004)
        - (wind - 2.1) * 0.001
        + hour_effect
        + (pm25 - 17) * 0.00003
        + (pm10 - 32) * 0.00002
        + (pressure - 1010) * 0.00001
    )

    predicted = max(0, min(predicted, 0.22))

    if predicted < 0.04:
        level = "낮음"
    elif predicted < 0.08:
        level = "보통"
    elif predicted < 0.12:
        level = "높음"
    else:
        level = "매우 높음"

    return jsonify({
        "predicted_o3": round(predicted, 4),
        "predicted_o3_x100": round(predicted * 100, 3),
        "level": level
    })


# =========================================================
# Render health check
# =========================================================

@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


# =========================================================
# 파일 다운로드
# =========================================================

@app.route("/download/<path:filename>")
def download_file(filename):
    file_path = find_data_file(filename)

    if not file_path:
        return jsonify({
            "error": "file not found",
            "filename": filename
        }), 404

    return send_from_directory(file_path.parent, file_path.name, as_attachment=True)


# =========================================================
# Render 실행
# =========================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)