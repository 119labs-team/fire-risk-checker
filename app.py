"""집콕세이프 화재 안전 기능을 단독으로 실행해 보는 예제 앱입니다."""

from flask import Flask, redirect, session, url_for

from fire_safety import fire_safety_bp, init_db


def create_app() -> Flask:
    app = Flask(__name__)

    # 실제 팀 프로젝트에서는 팀 공용 비밀키를 환경 변수로 관리하세요.
    app.config["SECRET_KEY"] = "dev-only-change-this-key"
    app.config["DATABASE"] = "home_safe.db"

    # 내가 만든 화재 안전 기능을 /fire 주소 아래에 연결합니다.
    app.register_blueprint(fire_safety_bp, url_prefix="/fire")

    with app.app_context():
        init_db()

    @app.route("/")
    def index():
        # 로그인 기능이 합쳐지기 전 테스트를 위한 임시 사용자입니다.
        session.setdefault("user_id", 1)
        return redirect(url_for("fire_safety.checklist"))

    return app


if __name__ == "__main__":
    create_app().run(debug=True)

