# 집콕세이프 화재 안전 기능

담당 범위인 **체크리스트 → 화재 위험도 분석 → 위험도 변화 기록**만 독립적으로 구현한 Flask 모듈입니다.

## 실행 방법

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

브라우저에서 `http://127.0.0.1:5000`을 열면 됩니다. 체크 결과는 실행 폴더의 `home_safe.db`에 자동 저장됩니다.

## 계산 방식

- 각 문항에서 안전한 답은 0점, 안전하지 않은 답은 항목별 7~15점을 더합니다.
- 합계 0~20점: 위험도 낮음
- 합계 21~50점: 위험도 보통
- 합계 51~100점: 위험도 높음
- 점수가 높을수록 화재 위험 요인이 많다는 뜻입니다.

이 점수는 교육용 자가 점검 지표이며 전문 소방 안전 진단을 대신하지 않습니다.

## 팀 프로젝트에 합치는 방법

1. `fire_safety.py`, `templates`, `static`을 팀 Flask 프로젝트에 복사합니다.
2. 팀의 앱 생성 코드에서 다음 두 줄을 연결합니다.

```python
from fire_safety import fire_safety_bp, init_db
app.register_blueprint(fire_safety_bp, url_prefix="/fire")
```

3. 앱 컨텍스트 안에서 최초 한 번 `init_db()`를 호출합니다.
4. 로그인 담당 코드가 로그인 성공 시 `session["user_id"] = 회원번호`를 저장하도록 맞춥니다.

화면 주소는 `/fire/checklist`, `/fire/history`이며, 다른 팀원이 차트 데이터를 쓰고 싶다면 `/fire/api/history`에서 JSON으로 가져갈 수 있습니다.

## 파일 역할

- `app.py`: 기능을 혼자 실행해 보는 예제
- `fire_safety.py`: 점수 계산, DB 저장, 화면/API 주소
- `templates/`: 체크리스트·결과·기록 화면
- `static/style.css`: 화면 디자인
