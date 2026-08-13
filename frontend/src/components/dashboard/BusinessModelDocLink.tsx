"use client";

/**
 * FE-7: KPI コストカードの「前提: docs/business-model.md」リンクボタン。
 *
 * クリックで GET /api/docs/business-model から docs/business-model.md の内容を取得し、
 * モーダルに表示する。取得失敗時はモーダル内に控えめなエラーを表示する（画面を壊さない）。
 * マークダウン本文はデモスコープのため raw テキストとして表示する（描画ライブラリ追加は
 * Human-in-the-Loop の承認が必要なため追加しない）。
 * コメント・docstring は日本語（NFR-4 / FE-7）。
 */

import { useCallback, useState } from "react";
import { createPortal } from "react-dom";

interface DocResponse {
  content: string | null;
  error?: string;
}

export default function BusinessModelDocLink() {
  const [open, setOpen] = useState(false);
  const [content, setContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  /** モーダルを開き、docs/business-model.md の内容を取得して表示する。 */
  const openModal = useCallback(async () => {
    setOpen(true);
    setContent(null);
    setError(null);
    try {
      const response = await fetch("/api/docs/business-model");
      const body = (await response.json()) as DocResponse;
      if (!response.ok || body.content === null) {
        setError(body.error ?? "docs/business-model.md を読み込めませんでした");
        return;
      }
      setContent(body.content);
    } catch {
      setError("docs/business-model.md の取得に失敗しました");
    }
  }, []);

  const closeModal = useCallback(() => setOpen(false), []);

  const modalContent = open ? (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="docs/business-model.md"
      className="fixed inset-0 flex items-center justify-center bg-black/40 p-4"
      style={{ zIndex: 10000 }}
      onClick={closeModal}
    >
      <div
        data-testid="bm-doc-modal"
        className="flex max-h-[80vh] w-full max-w-3xl flex-col rounded-xl bg-white shadow-xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
          <h3 className="text-sm font-semibold text-slate-700">
            docs/business-model.md
          </h3>
          <button
            type="button"
            onClick={closeModal}
            className="rounded px-2 py-1 text-xs text-slate-500 hover:bg-slate-100"
          >
            閉じる
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4">
          {error !== null ? (
            <p data-testid="bm-doc-error" className="text-xs text-amber-600">
              {error}
            </p>
          ) : content === null ? (
            <p data-testid="bm-doc-loading" className="text-xs text-slate-400">
              読み込み中...
            </p>
          ) : (
            <pre
              data-testid="bm-doc-content"
              className="whitespace-pre-wrap font-mono text-xs text-slate-700"
            >
              {content}
            </pre>
          )}
        </div>
      </div>
    </div>
  ) : null;

  return (
    <>
      <button
        type="button"
        onClick={openModal}
        className="underline decoration-slate-400 underline-offset-2 hover:text-slate-600"
      >
        docs/business-model.md
      </button>

      {/* モーダルが開いており、かつ document が利用可能なブラウザ環境でのみ createPortal を実行 */}
      {modalContent && typeof document !== "undefined"
        ? createPortal(modalContent, document.body)
        : null}
    </>
  );
}