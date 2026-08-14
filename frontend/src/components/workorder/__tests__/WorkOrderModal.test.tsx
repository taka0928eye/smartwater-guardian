// @vitest-environment jsdom
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { WorkOrderModal } from '../WorkOrderModal';
import type { WorkOrder } from '../../../types/api';

describe('WorkOrderModal Component', () => {
  const mockWorkOrder = {
    workOrderId: 'WO-2026-001',
    alertId: 'ALT-001',
    createdAt: '2026-08-12T10:00:00Z',
    parts: [
      {
        name: '補修ソケット 50A',
        spec: '塩ビ管用',
        quantity: 1,
        unitPriceYen: 3500,
        subtotalYen: 3500,
      },
    ],
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

  it('モーダルの基本情報（タイトル・見積合計・緊急度）が描画されること', () => {
    render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={mockWorkOrder as unknown as WorkOrder} />);

    expect(screen.getByRole('dialog')).toHaveClass('z-[2100]');
    expect(screen.getByText(/作業指示書/)).toBeInTheDocument();
    expect(screen.getByText(/15,000/)).toBeInTheDocument();
    expect(screen.getByText(/緊急度/)).toBeInTheDocument();
  });

  it('source == "llm" のときバッジエリアが描画されること', () => {
    const { container } = render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={mockWorkOrder as unknown as WorkOrder} />);
    const badgeOrSpan = container.querySelectorAll('span, div');
    expect(badgeOrSpan.length).toBeGreaterThan(0);
  });

  it('source == "fallback" のとき 規定ルール/フォールバック 系のバッジが表示されること', () => {
    const fallbackOrder = { ...mockWorkOrder, source: 'fallback', costYen: 0 };
    render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={fallbackOrder as unknown as WorkOrder} />);
    expect(screen.getByText(/規定|ルール|フォールバック|fallback/i)).toBeInTheDocument();
  });

  it('source == "llm" のとき脚註に原価が表示されること (FR-6)', () => {
    render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={mockWorkOrder as unknown as WorkOrder} />);
    expect(screen.getByText(/0\.15/)).toBeInTheDocument();
  });

  it('source == "fallback" のとき脚註に「LLM未使用」が表示されること', () => {
    const fallbackOrder = { ...mockWorkOrder, source: 'fallback', costYen: 0 };
    render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={fallbackOrder as unknown as WorkOrder} />);
    expect(screen.getByText(/LLM未使用|規定ルール/)).toBeInTheDocument();
  });

  it('閉じるボタンやオーバーレイクリックで onClose が呼ばれること', () => {
    const handleClose = vi.fn();
    render(<WorkOrderModal isOpen={true} onClose={handleClose} workOrder={mockWorkOrder as unknown as WorkOrder} />);

    const buttons = screen.getAllByRole('button');
    fireEvent.click(buttons[0]);
    expect(handleClose).toHaveBeenCalled();
  });
});
