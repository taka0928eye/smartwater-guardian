"use client";

/**
 * FE-5: アラート詳細ドロワー。
 *
 * 選択されたアラートの解析結果（漏水確信度・卓越周波数・帯域エネルギー比）と
 * 配管情報（配管台帳）を表示する。詳細は GET /api/v1/alerts/{telemetryId}（BE-6）から
 * 取得し、取得中・失敗時もドロワー自体は表示を維持する。
 *
 * children は FE-4（Recharts による音響波形・スペクトル表示）を差し込むための
 * スロットとして用意する。FE-4 と並行作業できるように props 契約のみ先に固定する。
 */
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { X } from "lucide-react";

import SeverityBadge from "@/components/common/SeverityBadge";
import { fetchAlertDetail } from "@/lib/api";
import type { AlertDetail, AlertSummary } from "@/types/api";

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
  // 選択アラートが変わるときは親が key={telemetryId} で再マウントするため、
  // 初期状態を「読み込み中」にできる（effect 内での同期 setState を避ける）。
  const [detail, setDetail] = useState<AlertDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 詳細を取得する。アンマウント後に状態を更新しないよう cancelled フラグで保護する。
  // setState は非同期コールバック内でのみ呼ぶ（set-state-in-effect 規則に従う）。
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

  return (
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

            {/* FE-4 のチャート差込スロット */}
            {children ? (
              <section
                aria-label="スペクトルチャート"
                className="mt-3"
              >
                {children}
              </section>
            ) : null}
          </>
        ) : null}
      </aside>
    </div>
  );
}
