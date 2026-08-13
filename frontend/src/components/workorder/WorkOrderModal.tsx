import React, { useEffect } from 'react';
import type { WorkOrder } from '../../types/api';

interface WorkOrderModalProps {
  isOpen: boolean;
  onClose: () => void;
  workOrder: WorkOrder | null;
}

export const WorkOrderModal: React.FC<WorkOrderModalProps> = ({
  isOpen,
  onClose,
  workOrder,
}) => {
  // ESCキーを押したときにモーダルを閉じる
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen || !workOrder) return null;

  return (
    <div
      className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/50 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="work-order-modal-title"
    >
      {/* モーダルコンテンツ領域（クリックイベントの伝播を防止） */}
      <div
        className="w-full max-w-2xl rounded-lg bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b pb-3">
          <h2 id="work-order-modal-title" className="text-lg font-bold text-gray-900">
            作業指示書 (Work Order)
          </h2>
          <button
            onClick={onClose}
            className="rounded-md text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            type="button"
            aria-label="閉じる"
          >
            ✕
          </button>
        </div>

        <div className="mt-4 space-y-4 text-sm text-gray-700">
          <div>
            <span className="font-semibold">緊急度:</span> {workOrder.urgency ?? '未設定'}
          </div>
          <div>
            <span className="font-semibold">概算見積合計:</span> ¥
            {workOrder.totalEstimateYen !== undefined && workOrder.totalEstimateYen !== null
              ? workOrder.totalEstimateYen.toLocaleString()
              : '0'}
          </div>
          <div>
            <span className="font-semibold">想定作業時間:</span>{' '}
            {workOrder.estimatedDurationHours ?? 0}時間 ({workOrder.requiredWorkers ?? 1}名)
          </div>
        </div>

        {/* 原価表示フッター脚註 (FR-6) */}
        <div className="mt-6 border-t border-gray-100 pt-3 text-xs text-gray-500 flex justify-between items-center">
          {workOrder.source === 'fallback' ? (
            <span>
              ※ 本起票のAPI原価: <strong>LLM未使用（規定ルールによる算出）</strong>
            </span>
          ) : (
            <span>
              ※ 本起票のAPI原価: <strong>¥{workOrder.costYen?.toFixed(2) ?? '0.00'}</strong>
              {workOrder.isEstimated && ' (概算)'}
              {workOrder.model && ` (モデル: ${workOrder.model})`}
              {workOrder.latencyMs !== undefined && ` [${workOrder.latencyMs}ms]`}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
