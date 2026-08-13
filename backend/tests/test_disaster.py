"""防災モード API (GET /summary, POST /simulate) のテスト。"""

from app.services.kpi import calculate_kpi_summary
from app.store import clear_runtime_sensors, get_store, reset_store


def test_simulate_disaster_creates_level3_alerts(client):
    """POST /simulate で指定件数の Level 3 アラートがストアに追加される。"""
    count = 6
    response = client.post(f"/api/v1/disaster/simulate?count={count}")

    # レスポンス確認
    assert response.status_code == 200
    data = response.json()
    assert data["inserted_count"] == count
    assert "シミュレーション" in data["message"]

    # ストア確認: Level 3 アラートが count 件以上追加されたか
    store = get_store()
    level3_alerts = store.list_alerts(level=3)
    actual_count = len(level3_alerts)
    assert actual_count >= count, f"Expected at least {count} Level 3 alerts, got {actual_count}"


def test_simulate_disaster_summary_includes_simulated_alerts(client):
    """POST /simulate 後に GET /summary でクラスタが返される。"""
    # 6 件のシミュレーションアラートを投入
    response = client.post("/api/v1/disaster/simulate?count=6")
    assert response.status_code == 200

    # サマリーを取得
    response = client.get("/api/v1/disaster/summary")
    assert response.status_code == 200
    data = response.json()

    # クラスタが0でないことを確認（シミュレーション成功の証）
    assert data["total_clusters"] > 0, "Expected clusters but got total_clusters=0"
    assert data["total_affected_households"] > 0
    assert len(data["clusters"]) > 0


def test_simulate_disaster_respects_count_parameter(client):
    """count パラメータの値が反映される。"""
    for count in [1, 3, 10, 20]:
        reset_store()  # 各テストで初期化
        response = client.post(f"/api/v1/disaster/simulate?count={count}")
        assert response.status_code == 200
        data = response.json()
        assert data["inserted_count"] == count


def test_simulate_disaster_validation(client):
    """count パラメータのバリデーション（1-20）。"""
    # 0 は範囲外（ge=1）
    response = client.post("/api/v1/disaster/simulate?count=0")
    assert response.status_code == 422  # Validation Error

    # 21 は範囲外（le=20）
    response = client.post("/api/v1/disaster/simulate?count=21")
    assert response.status_code == 422


def test_disaster_summary_empty(client):
    """アラートなしの場合、summary は empty。"""
    response = client.get("/api/v1/disaster/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_clusters"] == 0
    assert data["total_affected_households"] == 0
    assert data["clusters"] == []


def test_disaster_summary_clustering(client):
    """複数アラートが距離でクラスタリングされる。"""
    # 3 件投入して、クラスタ件数を確認
    response = client.post("/api/v1/disaster/simulate?count=3")
    assert response.status_code == 200

    response = client.get("/api/v1/disaster/summary")
    assert response.status_code == 200
    data = response.json()

    # クラスタは 1 以上（クラスタリング処理が機能している）
    assert data["total_clusters"] >= 1

    # 各クラスタに必須フィールドがある
    for cluster in data["clusters"]:
        assert "cluster_id" in cluster
        assert "center_lat" in cluster
        assert "center_lng" in cluster
        assert "affected_sensor_ids" in cluster
        assert "geometry" in cluster
        assert cluster["geometry"]["type"] == "Polygon"


def test_disaster_simulate_increases_total_sensors(client):
    """防災シミュレーション実行後、KPI の監視センサ数が増加する。"""
    # 初期状態: 監視センサ数は 10（hydrants.json の実件数）
    summary_before = calculate_kpi_summary()
    assert summary_before.total_sensors == 10

    # シミュレーションを 6 件実行
    response = client.post("/api/v1/disaster/simulate?count=6")
    assert response.status_code == 200

    # シミュレーション後: 監視センサ数は 16（10 + 6）に増加
    summary_after = calculate_kpi_summary()
    assert summary_after.total_sensors == 16

    # KPI エンドポイントでも 16 を返す
    kpi_response = client.get("/api/v1/kpi/summary")
    assert kpi_response.status_code == 200
    kpi_data = kpi_response.json()
    assert kpi_data["total_sensors"] == 16

    # テスト隔離: クリア後は元に戻る
    clear_runtime_sensors()
    summary_cleared = calculate_kpi_summary()
    assert summary_cleared.total_sensors == 10
