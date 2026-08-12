import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { WorkOrderModal } from '../WorkOrderModal';
import type { WorkOrder } from '../../../types/api';

describe('WorkOrderModal Component', () => {
  const mockWorkOrder: WorkOrder = {
    workOrderId: 'WO-2026-001',
    alertId: 'ALT-001',
    createdAt: '2026-08-12T10:00:00Z',
    parts: [{ name: '補修ソケット 50A', spec: '塩ビ管用', quantity: 1, unitPriceYen: 3500, subtotalYen: 3500 }],
    totalEstimateYen: 15000,
    workSteps: ['現場確認と安全確保', '漏水箇所の掘削', '補修ソケットの装着'],
    requiredWorkers: 2,
    estimatedDurationHours: 1.5,
    urgency: 'high',
    notificationText: '【緊急漏水修繕】◯◯地区で漏水が検知されました。対応をお願いします。',
    source: 'llm',
    costYen: 0.15,
    model: 'codex',
    inputTokens: 320,
    outputTokens: 150,
    latencyMs: 420,
    isEstimated: false,
  };

  it('部材テーブル・見積・作業手順・通知文面が正しく描画されること', () => {
    render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={mockWorkOrder} />);

    expect(screen.getByText(/補修ソケット 50A/)).toBeInTheDocument();
    expect(screen.getByText(/15,000/)).toBeInTheDocument();
    expect(screen.getByText(/現場確認と安全確保/)).toBeInTheDocument();
    expect(screen.getByText(/【緊急漏水修繕】/)).toBeInTheDocument();
  });

  it('source == "llm" のとき「AI生成」バッジが表示されること', () => {
    render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={mockWorkOrder} />);
    expect(screen.getByText('AI生成')).toBeInTheDocument();
  });

  it('source == "fallback" のとき「規定ルールによる自動算出」バッジが表示されること', () => {
    const fallbackOrder = { ...mockWorkOrder, source: 'fallback' as const, costYen: 0 };
    render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={fallbackOrder} />);
    expect(screen.getByText('規定ルールによる自動算出')).toBeInTheDocument();
  });

  it('source == "llm" のとき脚註に原価が表示されること (FR-6)', () => {
    render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={mockWorkOrder} />);
    expect(screen.getByText(/本起票のAPI原価:/)).toBeInTheDocument();
    expect(screen.getByText(/¥0.15/)).toBeInTheDocument();
    expect(screen.getByText(/モデル: codex/)).toBeInTheDocument();
  });

  it('source == "fallback" のとき脚註に「LLM未使用」が表示されること', () => {
    const fallbackOrder = { ...mockWorkOrder, source: 'fallback' as const, costYen: 0 };
    render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={fallbackOrder} />);
    expect(screen.getByText(/LLM未使用（規定ルールによる算出）/)).toBeInTheDocument();
  });

  it('閉じるボタンやオーバーレイクリックで onClose が呼ばれること', () => {
    const handleClose = vi.fn();
    render(<WorkOrderModal isOpen={true} onClose={handleClose} workOrder={mockWorkOrder} />);

    const closeButton = screen.getByRole('button', { name: /閉じる/i });
    fireEvent.click(closeButton);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
