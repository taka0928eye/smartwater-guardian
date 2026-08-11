import pytest
from app.schemas.work_order import WorkOrder
from app.services.prompts import (
    build_system_prompt,
    build_user_prompt,
    extract_json_from_response,
    get_clean_work_order_schema,
)


@pytest.fixture
def dummy_telemetry():
    return {
        "hydrant_id": "HYD-001",
        "leak_level": 2,
        "confidence": 0.85,
        "dominant_freq": 1250.0,
        "energy_ratio": 0.45,
        "spectrum": [0.1] * 128,  # コスト削減のためプロンプトからは除外されるべきデータ
    }


@pytest.fixture
def dummy_pipe_info():
    return {
        "address": "東京都千代田区1-1",
        "lat": 35.6812,
        "lng": 139.7671,
        "material": "DIP",
        "diameter_mm": 150,
        "install_year": 1985,
        "age_years": 41,
        "depth_m": 1.5,
    }


def test_build_user_prompt_contains_all_fields_except_spectrum(dummy_telemetry, dummy_pipe_info):
    prompt = build_user_prompt(dummy_telemetry, dummy_pipe_info)
    assert "HYD-001" in prompt
    assert "DIP" in prompt
    assert "35.6812" in prompt
    assert "spectrum" not in prompt  # 128点スペクトル除外確認
    assert "概算" in prompt


def test_schema_excludes_cost_fields():
    schema = get_clean_work_order_schema()
    props = schema["properties"]
    assert "prompt_tokens" not in props
    assert "completion_tokens" not in props
    assert "cost_yen" not in props
    assert "model" not in props
    assert "latency_ms" not in props


def test_build_system_prompt_schema_integration():
    sys_prompt = build_system_prompt()
    assert "概算" in sys_prompt
    assert "properties" in sys_prompt
    assert "prompt_tokens" not in sys_prompt


def test_extract_json_with_code_fence():
    raw_response = '```json\n{"parts": [], "total_estimate_yen": 50000, "work_steps": [], "required_workers": 2, "estimated_duration_hours": 3.0, "urgency": "medium", "notification_text": "テスト", "source": "llm"}\n```'
    data = extract_json_from_response(raw_response)
    assert data["total_estimate_yen"] == 50000


def test_extract_json_without_code_fence():
    raw_response = '{"parts": [], "total_estimate_yen": 30000, "work_steps": [], "required_workers": 1, "estimated_duration_hours": 1.5, "urgency": "low", "notification_text": "テスト", "source": "llm"}'
    data = extract_json_from_response(raw_response)
    assert data["total_estimate_yen"] == 30000


def test_extract_json_invalid_raises_error():
    with pytest.raises(ValueError):
        extract_json_from_response("This is not JSON")


def test_work_order_fallback_support():
    order = WorkOrder(
        parts=[],
        total_estimate_yen=0,
        work_steps=["確認"],
        required_workers=1,
        estimated_duration_hours=1.0,
        urgency="low",
        notification_text="フォールバック文面",
        source="fallback"
    )
    assert order.source == "fallback"
    assert order.prompt_tokens == 0  # 既定値
