// @vitest-environment jsdom
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { WorkOrderModal } from '../WorkOrderModal';

describe('WorkOrderModal Component', () => {
  const mockWorkOrder: any = {
    workOrderId: 'WO-2026-001',
    alertId: 'ALT-001',
    createdAt: '2026-08-12T10:00:00Z',
    parts: [
      {
        name: '補修ソケット 50A',
        partName: '補修ソケット 50A',
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

  it('部材テーブル・見積・作業手順・通知文面が正しく描画されること', () => {
    render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={mockWorkOrder} />);

    expect(screen.getByText((_, element) => element?.textContent?.includes('補修ソケット') ?? false)).toBeInTheDocument();
    expect(screen.getByText((_, element) => element?.textContent?.includes('15,000') ?? false)).toBeInTheDocument();
    expect(screen.getByText((_, element) => element?.textContent?.includes('現場確認') ?? false)).toBeInTheDocument();
  });

  it('source == "llm" のとき AI/LLM 系のバッジが表示されること', () => {
    render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={mockWorkOrder} />);
    const badge = screen.getByText((_, element) => /AI|LLM/.test(element?.textContent || ''));
    expect(badge).toBeInTheDocument();
  });

  it('source == "fallback" のとき 規定ルール/フォールバック 系のバッジが表示されること', () => {
    const fallbackOrder = { ...mockWorkOrder, source: 'fallback', costYen: 0 };
    render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={fallbackOrder} />);
    const badge = screen.getByText((_, element) => /規定|ルール|フォールバック|fallback/i.test(element?.textContent || ''));
    expect(badge).toBeInTheDocument();
  });

  it('source == "llm" のとき脚註に原価が表示されること (FR-6)', () => {
    render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={mockWorkOrder} />);
    expect(screen.getByText((_, element) => element?.textContent?.includes('0.15') ?? false)).toBeInTheDocument();
  });

  it('source == "fallback" のとき脚註に「LLM未使用」が表示されること', () => {
    const fallbackOrder = { ...mockWorkOrder, source: 'fallback', costYen: 0 };
    render(<WorkOrderModal isOpen={true} onClose={() => {}} workOrder={fallbackOrder} />);
    expect(screen.getByText((_, element) => {
      const text = element?.textContent || '';
      return text.includes('LLM未使用') || text.includes('規定ルール');
    })).toBeInTheDocument();
  });

  it('閉じるボタンやオーバーレイクリックで onClose が呼ばれること', () => {
    const handleClose = vi.fn();
    render(<WorkOrderModal isOpen={true} onClose={handleClose} workOrder={mockWorkOrder} />);

    const buttons = screen.getAllByRole('button');
    fireEvent.click(buttons[0]);
    expect(handleClose).toHaveBeenCalled();
  });
});
