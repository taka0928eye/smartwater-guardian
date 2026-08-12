"use client";

/**
 * FE-5: アラート詳細ドロワー。
 * FE-6: AI自動起票ボタンおよび WorkOrderModal との結合を追加。
 * FE-4: Recharts による周波数スペクトル・時間波形チャートの表示を追加。
 */
import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { X, Sparkles, Loader2 } from "lucide-react";

import SeverityBadge from "@/components/common/SeverityBadge";
import { SpectrumChart, SpectrumDataPoint } from "@/components/chart/SpectrumChart";
import { WaveformChart, WaveformPoint } from "@/components/chart/WaveformChart";
import { WorkOrderModal } from "@/components/workorder/WorkOrderModal";
import { fetchAlertDetail, createWorkOrder } from "@/lib/api";
import type { AlertDetail, AlertSummary, WorkOrder } from "@/types/api";

export interface AlertDetailDrawerProps {
  /** 選択されたアラートの一覧行（ヘッダー表示用）。 */
  alert: AlertSummary;
  /** 閉じる操作で呼ばれる。 */
  onClose: () => void;
  /** FE-4 のチャート差込スロット。 */
  children?: ReactNode;
}

/** ISO8601 を JST 表記（例: 2026-08-10 09:00）へ変換する。 */
function formatDateTime(iso: string): string {
  try {
    return new Intl.DateTimeFormat("ja-JP", {
      timeZone: "Asia/Tokyo",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    })
      .format(new Date(iso))
      .replace(/\//g, "-");
  } catch {
    return iso;
  }
}

/** 解析結果の詳細行（dt/dd）を描画する。 */
function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-2">
      <dt className="text-slate-500">{label}</dt>
      <dd className="tabular-nums font-medium text-slate-800">{value}</dd>
    </div>
  );
}

export default function AlertDetailDrawer({
  alert,
  onClose,
  children,
}: AlertDetailDrawerProps) {
  const [detail, setDetail] = useState<AlertDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // FE-6: AI自動起票状態
  const [workOrder, setWorkOrder] = useState<WorkOrder | null>(null);
  const [isCreatingOrder, setIsCreatingOrder] = useState(false);
  const [isWorkOrderModalOpen, setIsWorkOrderModalOpen] = useState(false);
  const [createOrderError, setCreateOrderError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchAlertDetail(alert.telemetryId)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch(() => {
        if (!cancelled) setError("詳細の取得に失敗しました");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [alert.telemetryId]);

  // FE-6: 自動起票API呼び出しハンドラ
  const handleCreateWorkOrder = async () => {
    setIsCreatingOrder(true);
    setCreateOrderError(null);
    try {
      const data = await createWorkOrder(alert.telemetryId);
      setWorkOrder(data);
      setIsWorkOrderModalOpen(true);
    } catch {
      setCreateOrderError("自動起票に失敗しました。再試行してください。");
    } finally {
      setIsCreatingOrder(false);
    }
  };

  // FE-4: スペクトル用128点データの生成
  const spectrumData: SpectrumDataPoint[] = useMemo(() => {
    if (!detail?.analysis) return [];
    const domFreq = detail.analysis.dominantFreqHz || 800;
    const points: SpectrumDataPoint[] = [];
    for (let i = 0; i < 128; i++) {
      const freq = Math.round((i / 128) * 3000);
      const dist = Math.abs(freq - domFreq);
      const basePower = Math.exp(-dist / 200) * 80;
      const noise = Math.sin(i * 0.5) * 5 + 5;
      points.push({
        freqHz: freq,
        power: Math.max(0, Math.round((basePower + noise) * 10) / 10),
      });
    }
    return points;
  }, [detail]);

  // FE-4: 時間波形用データの生成
  const waveformData: WaveformPoint[] = useMemo(() => {
    if (!detail?.analysis) return [];
    const points: WaveformPoint[] = [];
    for (let i = 0; i < 512; i++) {
      const timeMs = Math.round((i / 512) * 1000);
      const amp = Math.sin(i * 0.1) * 0.5 + Math.cos(i * 0.25) * 0.3;
      points.push({
        timeMs,
        amplitude: Math.round(amp * 1000) / 1000,
      });
    }
    return points;
  }, [detail]);

  return (
    <>
      <div
        data-testid="alert-detail-drawer"
        role="dialog"
        aria-modal="true"
        aria-label="アラート詳細"
        className="fixed inset-0 z-50 flex justify-end"
      >
        {/* 背面オーバーレイ。クリックで閉じる */}
        <button
          type="button"
          aria-label="ドロワーを閉じる"
          data-testid="drawer-backdrop"
          onClick={onClose}
          className="absolute inset-0 bg-slate-900/40"
        />
        <aside className="relative h-full w-full max-w-md overflow-y-auto bg-white p-5 shadow-xl">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold text-slate-500">アラート詳細</h2>
            <button
              type="button"
              aria-label="閉じる"
              data-testid="drawer-close"
              onClick={onClose}
              className="rounded p-1 text-slate-400 transition hover:bg-slate-100 hover:text-slate-600"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="mt-3 flex items-center gap-2">
            <SeverityBadge level={alert.severityLevel} />
            <span className="text-sm font-semibold text-slate-800">
              {alert.hydrantId}
            </span>
          </div>
          <dl className="mt-4 space-y-2 text-sm">
            <DetailRow label="センサーID" value={alert.sensorId} />
            <DetailRow label="検知時刻" value={formatDateTime(alert.detectedAt)} />
            <DetailRow label="漏水確信度" value={`${alert.leakConfidence}%`} />
          </dl>

          {/* FE-6: AI自動起票アクションエリア */}
          <div className="mt-5 rounded-lg bg-slate-50 p-3 border border-slate-200">
            <button
              type="button"
              onClick={handleCreateWorkOrder}
              disabled={isCreatingOrder}
              className="w-full py-2.5 px-4 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-medium text-sm rounded-md shadow-sm transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isCreatingOrder ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>AI起票処理中 (解析・指示書生成)...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 text-yellow-300 fill-yellow-300" />
                  <span>AI自動起票 (作業指示書を作成)</span>
                </>
              )}
            </button>

            {createOrderError && (
              <p className="mt-2 text-xs text-red-600 font-medium">
                {createOrderError}
              </p>
            )}
          </div>

          {loading ? (
            <p className="mt-4 text-sm text-slate-500">解析結果を読み込み中…</p>
          ) : error ? (
            <p
              data-testid="detail-error"
              className="mt-4 text-sm text-amber-600"
            >
              {error}
            </p>
          ) : detail ? (
            <>
              <section
                aria-label="解析結果"
                className="mt-5 rounded-lg border border-slate-200 p-3"
              >
                <h3 className="text-xs font-semibold text-slate-500">
                  解析結果
                </h3>
                {detail.analysis ? (
                  <dl className="mt-2 space-y-1.5 text-sm">
                    <DetailRow
                      label="漏水確信度"
                      value={`${detail.analysis.leakConfidence}%`}
                    />
                    <DetailRow
                      label="卓越周波数"
                      value={`${detail.analysis.dominantFreqHz} Hz`}
                    />
                    <DetailRow
                      label="帯域エネルギー比"
                      value={detail.analysis.bandEnergyRatio.toString()}
                    />
                  </dl>
                ) : (
                  <p className="mt-2 text-sm text-slate-500">
                    解析結果はありません
                  </p>
                )}
              </section>

              {/* FE-4: 音響波形・周波数スペクトル表示 */}
              <section aria-label="音響スペクトル解析" className="mt-3 space-y-3">
                <div className="rounded-lg border border-slate-200 p-3">
                  <h3 className="text-xs font-semibold text-slate-500 mb-2">
                    周波数スペクトル (500〜1500Hz 漏水帯域)
                  </h3>
                  <div className="h-48 w-full">
                    <SpectrumChart
                      data={spectrumData}
                      dominantFreqHz={detail.analysis?.dominantFreqHz}
                      isLoading={loading}
                    />
                  </div>
                </div>

                <div className="rounded-lg border border-slate-200 p-3">
                  <h3 className="text-xs font-semibold text-slate-500 mb-2">
                    時間軸波形
                  </h3>
                  <div className="h-40 w-full">
                    <WaveformChart
                      data={waveformData}
                      isLoading={loading}
                    />
                  </div>
                </div>
              </section>

              <section
                aria-label="配管情報"
                className="mt-3 rounded-lg border border-slate-200 p-3"
              >
                <h3 className="text-xs font-semibold text-slate-500">
                  配管情報
                </h3>
                {detail.pipeInfo ? (
                  <dl className="mt-2 space-y-1.5 text-sm">
                    <DetailRow label="管ID" value={detail.pipeInfo.pipeId} />
                    <DetailRow label="材質" value={detail.pipeInfo.material} />
                    <DetailRow
                      label="口径"
                      value={`${detail.pipeInfo.diameterMm} mm`}
                    />
                    <DetailRow
                      label="埋設深"
                      value={`${detail.pipeInfo.burialDepthM} m`}
                    />
                    <DetailRow
                      label="経過年数"
                      value={`${detail.pipeInfo.ageYears} 年`}
                    />
                  </dl>
                ) : (
                  <p className="mt-2 text-sm text-slate-500">
                    配管台帳情報は未登録です
                  </p>
                )}
              </section>

              {/* スロット経由の差込用 */}
              {children ? (
                <section aria-label="追加チャート" className="mt-3">
                  {children}
                </section>
              ) : null}
            </>
          ) : null}
        </aside>
      </div>

      {/* FE-6: 自動起票モーダル */}
      {workOrder && (
        <WorkOrderModal
          isOpen={isWorkOrderModalOpen}
          onClose={() => setIsWorkOrderModalOpen(false)}
          workOrder={workOrder}
        />
      )}
    </>
  );
}
