"""防災モード API (GET /summary, POST /simulate) のテスト（DEMO-2 再設計）。

BE-7 の当初実装（東京駅付近に架空センサーを新規追加）から、実在する20消火栓の
うち無作為に選んだセンサーを Level 3 に変化させる設計へ変更した。
"""

from app.store import get_disaster_sensor_ids, get_hydrants, get_store, initialize_sensors


def _seed_initial_sensors() -> None:
    """アプリ起動時と同じ「20件Lv0」の初期状態を用意する。"""
    initialize_sensors(get_store())


def test_simulate_disaster_changes_selected_hydrants_to_level3(client):
    """POST /simulate で実在消火栓のうち count 件が Level 3 に変化する（新規追加はしない）。"""
    _seed_initial_sensors()
    count = 6
    response = client.post(f"/api/v1/disaster/simulate?count={count}")

    assert response.status_code == 200
    data = response.json()
    assert data["inserted_count"] == count
    assert "Level 3" in data["message"] or "防災" in data["message"]

    store = get_store()
    level3_alerts = store.list_alerts(level=3)
    assert len(level3_alerts) == count
    all_sensor_ids = {h.sensor_id for h in get_hydrants()}
    for alert in level3_alerts:
        # 実在マスタのセンサーであり、架空センサー(SEN-DISASTER-xxx等)は作られない
        assert alert.sensor_id in all_sensor_ids
        assert alert.audio_pcm16 is not None
        assert alert.sample_rate_hz is not None


def test_simulate_disaster_does_not_add_new_sensors(client):
    """防災シミュレーション後も監視センサー数は20のまま増加しない。"""
    from app.services.kpi import calculate_kpi_summary

    _seed_initial_sensors()
    summary_before = calculate_kpi_summary()
    assert summary_before.total_sensors == 20

    response = client.post("/api/v1/disaster/simulate?count=6")
    assert response.status_code == 200

    summary_after = calculate_kpi_summary()
    assert summary_after.total_sensors == 20

    kpi_response = client.get("/api/v1/kpi/summary")
    assert kpi_response.status_code == 200
    assert kpi_response.json()["total_sensors"] == 20


def test_simulate_disaster_keeps_store_at_twenty_records(client):
    """シミュレーション後もストア内は常に20件（重複が発生しない）。"""
    _seed_initial_sensors()
    response = client.post("/api/v1/disaster/simulate?count=6")
    assert response.status_code == 200

    alerts = client.get("/api/v1/alerts").json()
    assert len(alerts) == 20


def test_simulate_disaster_preserves_untouched_sensors(client):
    """選出されなかった14件は現在の状態を保持したまま変化しない。"""
    _seed_initial_sensors()
    before = {item["sensor_id"]: item for item in client.get("/api/v1/alerts").json()}

    response = client.post("/api/v1/disaster/simulate?count=6")
    assert response.status_code == 200

    after = {item["sensor_id"]: item for item in client.get("/api/v1/alerts").json()}
    untouched_sensor_ids = [
        sensor_id for sensor_id, item in after.items() if item["severity_level"] != 3
    ]
    # 選出されなかったセンサーは Level 0 のまま（telemetry_id も変わらない）
    assert len(untouched_sensor_ids) == 14
    for sensor_id in untouched_sensor_ids:
        assert after[sensor_id]["telemetry_id"] == before[sensor_id]["telemetry_id"]
        assert after[sensor_id]["severity_level"] == 0


def test_simulate_disaster_registers_disaster_sensor_ids(client):
    """選出された sensor_id が防災クラスタ判定用に記録される。"""
    _seed_initial_sensors()
    response = client.post("/api/v1/disaster/simulate?count=6")
    assert response.status_code == 200

    disaster_ids = get_disaster_sensor_ids()
    assert len(disaster_ids) == 6
    level3_sensor_ids = {
        alert.sensor_id for alert in get_store().list_alerts(level=3)
    }
    assert disaster_ids == level3_sensor_ids


def test_simulate_disaster_respects_count_parameter(client):
    """count パラメータの値が反映される。"""
    for count in [1, 3, 10, 20]:
        _seed_initial_sensors()
        response = client.post(f"/api/v1/disaster/simulate?count={count}")
        assert response.status_code == 200
        data = response.json()
        assert data["inserted_count"] == count


def test_simulate_disaster_validation(client):
    """count パラメータのバリデーション（1-20）。"""
    response = client.post("/api/v1/disaster/simulate?count=0")
    assert response.status_code == 422  # 0 は範囲外（ge=1）

    response = client.post("/api/v1/disaster/simulate?count=21")
    assert response.status_code == 422  # 21 は範囲外（le=20）


def test_disaster_summary_empty_when_not_simulated(client):
    """シミュレーション未実施の場合、summary は empty（通常検知のLevel3は対象外）。"""
    _seed_initial_sensors()
    response = client.get("/api/v1/disaster/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_clusters"] == 0
    assert data["total_affected_households"] == 0
    assert data["clusters"] == []


def test_disaster_summary_excludes_organic_level3_alerts(client):
    """通常の漏水検知でLevel3になったセンサーは被災エリアクラスタに含まれない。"""
    _seed_initial_sensors()
    # シミュレーションを介さず、通常経路で1件だけ Level 3 を作る
    payload = {
        "count": 3,
    }
    seed_response = client.post("/api/v1/alerts/seed", json=payload)
    assert seed_response.status_code == 200

    response = client.get("/api/v1/disaster/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_clusters"] == 0


def test_simulate_disaster_summary_includes_simulated_alerts(client):
    """POST /simulate 後に GET /summary でクラスタが返される。"""
    _seed_initial_sensors()
    response = client.post("/api/v1/disaster/simulate?count=6")
    assert response.status_code == 200

    response = client.get("/api/v1/disaster/summary")
    assert response.status_code == 200
    data = response.json()

    assert data["total_clusters"] > 0
    assert data["total_affected_households"] > 0
    assert len(data["clusters"]) > 0
    total_affected_sensors = sum(len(c["affected_sensor_ids"]) for c in data["clusters"])
    assert total_affected_sensors == 6

    for cluster in data["clusters"]:
        assert "cluster_id" in cluster
        assert "center_lat" in cluster
        assert "center_lng" in cluster
        assert "affected_sensor_ids" in cluster
        assert "geometry" in cluster
        assert cluster["geometry"]["type"] == "Polygon"


def test_disaster_summary_clustering_by_distance(client):
    """実在消火栓は数km単位で離れているため、距離閾値内のみが同一クラスタになる。"""
    _seed_initial_sensors()
    client.post("/api/v1/disaster/simulate?count=6")

    response = client.get("/api/v1/disaster/summary?threshold_meters=300")
    assert response.status_code == 200
    data = response.json()
    # 実消火栓は互いに300m以上離れているため、6件選出時は基本的に6クラスタ
    assert data["total_clusters"] >= 1
    assert data["total_clusters"] <= 6
