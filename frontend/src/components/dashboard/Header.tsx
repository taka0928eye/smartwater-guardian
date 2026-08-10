"use client";

/**
 * FE-2: ダッシュボードヘッダー。
 *
 * タイトル・リアルタイム時刻・監視ステータス（システム正常稼働中）を表示する。
 * 時刻は Client Component として useSyncExternalStore で更新する。
 */
import { useSyncExternalStore } from "react";
import { ShieldCheck } from "lucide-react";

/** JST 表記の現在時刻（例: 2026-08-10 10:00 JST）。 */
function formatJstNow(date: Date): string {
  const formatted = new Intl.DateTimeFormat("ja-JP", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
  return `${formatted.replace(/\//g, "-")} JST`;
}

// ----------------------------------------------------
// モジュールレベルで状態を管理するストアを作成
// ----------------------------------------------------
let currentTimestamp: number | null = null;
const listeners = new Set<() => void>();

function subscribe(callback: () => void) {
  listeners.add(callback);

  // 初回購読時かつ未初期化の場合のみタイマーを開始
  if (currentTimestamp === null) {
    currentTimestamp = Date.now();
  }

  const id = setInterval(() => {
    currentTimestamp = Date.now();
    // 登録されているリスナーに通知
    listeners.forEach((listener) => listener());
  }, 30_000);

  return () => {
    listeners.delete(callback);
    if (listeners.size === 0) {
      clearInterval(id);
      currentTimestamp = null;
    }
  };
}

function getSnapshot() {
  // キャッシュされた同じ値を返す（setInterval で更新された時だけ値が変わる）
  return currentTimestamp;
}

function getServerSnapshot() {
  return null; // SSR 時は null
}

// ----------------------------------------------------
// コンポーネント本体
// ----------------------------------------------------
export default function Header() {
  const timestamp = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const now = timestamp ? new Date(timestamp) : null;

  return (
    <header className="flex flex-wrap items-center justify-between gap-3 bg-slate-900 px-6 py-4 text-white">
      <div className="flex items-center gap-2">
        <ShieldCheck className="h-6 w-6 text-emerald-400" aria-hidden="true" />
        <h1 className="text-base font-bold sm:text-lg">
          SmartWater Guardian - 漏水監視＆アセットマネジメント
        </h1>
      </div>
      <div className="flex items-center gap-4 text-sm">
        <time
          className="tabular-nums text-slate-200"
          dateTime={now ? now.toISOString() : undefined}
        >
          {now ? formatJstNow(now) : "-- JST"}
        </time>
        <span className="inline-flex items-center gap-2 font-medium text-emerald-300">
          <span className="relative flex h-2.5 w-2.5" aria-hidden="true">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
          </span>
          システム正常稼働中
        </span>
      </div>
    </header>
  );
}