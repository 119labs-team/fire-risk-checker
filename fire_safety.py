"""체크리스트, 화재 위험도 분석, 위험도 변화 기록 기능."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

fire_safety_bp = Blueprint("fire_safety", __name__)

# answer가 "no"이면 안전 수칙을 지키지 않은 것으로 보고 points만큼 가산합니다.
# 중요한 항목일수록 높은 점수를 배정했습니다. 총점은 정확히 100점입니다.
CHECKLIST_ITEMS = [
    {"id": "extinguisher", "text": "집에 사용 가능한 소화기가 있나요?", "points": 15,
     "advice": "소화기를 눈에 잘 띄고 꺼내기 쉬운 곳에 비치하세요."},
    {"id": "detector", "text": "화재감지기가 정상 작동하나요?", "points": 15,
     "advice": "감지기 배터리와 작동 상태를 정기적으로 확인하세요."},
    {"id": "power_strip", "text": "멀티탭을 문어발식으로 사용하지 않나요?", "points": 15,
     "advice": "고전력 제품은 벽면 콘센트에 직접 연결하세요."},
    {"id": "old_wire", "text": "손상되거나 오래된 전선이 없나요?", "points": 10,
     "advice": "피복이 벗겨지거나 눌린 전선은 즉시 교체하세요."},
    {"id": "gas_valve", "text": "가스 사용 후 중간 밸브를 잠그나요?", "points": 10,
     "advice": "조리가 끝나면 불과 가스 밸브를 함께 확인하세요."},
    {"id": "cooking", "text": "조리 중 자리를 비우지 않나요?", "points": 10,
     "advice": "조리 중에는 자리를 비우지 말고 주변 가연물을 치우세요."},
    {"id": "heater", "text": "난방기 주변 1m 안에 가연물이 없나요?", "points": 10,
     "advice": "난방기와 이불·커튼·종이 사이에 충분한 거리를 두세요."},
    {"id": "exit", "text": "현관과 대피 통로에 장애물이 없나요?", "points": 8,
     "advice": "현관과 복도는 언제나 바로 이동할 수 있게 비워 두세요."},
    {"id": "smoking", "text": "실내에서 담배를 피우지 않나요?", "points": 7,
     "advice": "실내 흡연을 피하고 불씨가 완전히 꺼졌는지 확인하세요."},
]


def get_db() -> sqlite3.Connection:
    """요청 중 하나의 DB 연결을 만들어 재사용합니다."""
    if "db" not in g:
        db_path = Path(current_app.root_path) / current_app.config["DATABASE"]
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db


@fire_safety_bp.teardown_app_request
def close_db(_error=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """처음 실행할 때 위험도 기록 테이블을 생성합니다."""
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS fire_risk_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            score INTEGER NOT NULL CHECK(score BETWEEN 0 AND 100),
            risk_level TEXT NOT NULL,
            unsafe_count INTEGER NOT NULL,
            advice_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    db.commit()


def analyze_answers(answers: dict[str, str]) -> dict:
    """체크 결과를 0~100점 위험 점수와 개선 조언으로 변환합니다."""
    score = 0
    advice = []

    for item in CHECKLIST_ITEMS:
        if answers.get(item["id"]) == "no":
            score += item["points"]
            advice.append(item["advice"])

    if score <= 20:
        level, color = "낮음", "safe"
    elif score <= 50:
        level, color = "보통", "warning"
    else:
        level, color = "높음", "danger"

    return {
        "score": score,
        "level": level,
        "color": color,
        "unsafe_count": len(advice),
        "advice": advice,
    }


def current_user_id() -> int:
    """팀원의 로그인 기능과 연결되는 부분입니다."""
    # 로그인 미구현 상태에서는 데모 사용자 1번을 사용합니다.
    return int(session.get("user_id", 1))


@fire_safety_bp.route("/checklist", methods=["GET", "POST"])
def checklist():
    if request.method == "GET":
        return render_template("checklist.html", items=CHECKLIST_ITEMS)

    # 모든 문항에 답했는지 서버에서도 다시 검사합니다.
    answers = {item["id"]: request.form.get(item["id"], "") for item in CHECKLIST_ITEMS}
    if any(answer not in {"yes", "no"} for answer in answers.values()):
        flash("모든 항목에 답해주세요.")
        return render_template("checklist.html", items=CHECKLIST_ITEMS, answers=answers), 400

    result = analyze_answers(answers)
    db = get_db()
    cursor = db.execute(
        """
        INSERT INTO fire_risk_records
            (user_id, score, risk_level, unsafe_count, advice_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            current_user_id(),
            result["score"],
            result["level"],
            result["unsafe_count"],
            json.dumps(result["advice"], ensure_ascii=False),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    db.commit()
    return redirect(url_for("fire_safety.result", record_id=cursor.lastrowid))


@fire_safety_bp.route("/result/<int:record_id>")
def result(record_id: int):
    record = get_db().execute(
        "SELECT * FROM fire_risk_records WHERE id = ? AND user_id = ?",
        (record_id, current_user_id()),
    ).fetchone()
    if record is None:
        return "분석 결과를 찾을 수 없습니다.", 404

    # 저장된 점수에 맞는 화면 색상을 다시 결정합니다.
    color = "safe" if record["score"] <= 20 else "warning" if record["score"] <= 50 else "danger"
    advice = json.loads(record["advice_json"])
    return render_template("result.html", record=record, color=color, advice=advice)


@fire_safety_bp.route("/history")
def history():
    records = get_db().execute(
        """
        SELECT * FROM fire_risk_records
        WHERE user_id = ? ORDER BY created_at ASC, id ASC
        """,
        (current_user_id(),),
    ).fetchall()
    return render_template("history.html", records=records)


@fire_safety_bp.route("/api/history")
def history_api():
    """차트나 다른 화면에서 기록을 가져갈 수 있는 JSON API입니다."""
    records = get_db().execute(
        "SELECT score, risk_level, created_at FROM fire_risk_records WHERE user_id = ? ORDER BY created_at, id",
        (current_user_id(),),
    ).fetchall()
    return jsonify([dict(row) for row in records])
