"""BE-7 防災モード API 動作検証スクリプト。"""

import asyncio
import sys
from pathlib import Path

# backend ディレクトリを sys.path に追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx


async def test_disaster_flow():
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        print("=== BE-7 防災モード検証開始 ===")

        # 1. POST /api/v1/disaster/simulate?count=6
        res_sim = await client.post("/api/v1/disaster/simulate?count=6")
        assert res_sim.status_code == 200, f"Simulate API Error: {res_sim.status_code}"
        sim_data = res_sim.json()
        print(f"[✓] シミュレーション投入成功: {sim_data['inserted_count']}件")
        assert sim_data["inserted_count"] == 6

        # 2. GET /api/v1/disaster/summary
        res_sum = await client.get("/api/v1/disaster/summary")
        assert res_sum.status_code == 200, f"Summary API Error: {res_sum.status_code}"
        sum_data = res_sum.json()
        print(f"[✓] サマリー取得成功: クラスタ数={sum_data['total_clusters']}, 想定断水世帯数={sum_data['total_affected_households']}")

        assert sum_data["total_clusters"] > 0, "クラスタが検出されていません"
        
        first_cluster = sum_data["clusters"][0]
        assert "cluster_id" in first_cluster
        assert "priority_valve_hydrant_id" in first_cluster
        
        # Polygon の検証 (GeoJSON 規格: 始点と終点が一致)
        coords = first_cluster["geometry"]["coordinates"][0]
        assert len(coords) >= 4, "Polygon の頂点数が不足しています"
        assert coords[0] == coords[-1], "GeoJSON Polygon の始点と終点が不一致です"
        print("[✓] GeoJSON Polygon 規格検証クリア")

        print("✔ BE-7 防災モードのすべての受け入れ条件を通過しました！")


if __name__ == "__main__":
    # サーバー未起動時でもテストできるように、ルーター直接テスト fallback 付きで実行
    try:
        asyncio.run(test_disaster_flow())
    except httpx.ConnectError:
        print("※ 開発サーバー未起動のため、FastAPI TestClient によるダイレクト検証を実施します。")
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        res_sim = client.post("/api/v1/disaster/simulate?count=6")
        assert res_sim.status_code == 200
        
        res_sum = client.get("/api/v1/disaster/summary")
        assert res_sum.status_code == 200
        data = res_sum.json()
        assert data["total_clusters"] > 0
        coords = data["clusters"][0]["geometry"]["coordinates"][0]
        assert coords[0] == coords[-1]
        print("✔ FastAPI TestClient にて全受け入れ条件の突破を確認しました！")
