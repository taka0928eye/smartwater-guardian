'use client';

import React from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export interface SpectrumDataPoint {
  freqHz: number;
  power: number;
}

interface SpectrumChartProps {
  data?: SpectrumDataPoint[];
  dominantFreqHz?: number;
  isLoading?: boolean;
}

export const SpectrumChart: React.FC<SpectrumChartProps> = ({
  data,
  dominantFreqHz,
  isLoading,
}) => {
  if (isLoading || !data || data.length === 0) {
    return (
      <div className="flex h-full w-full items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40 animate-pulse">
        <span className="text-xs text-slate-500">スペクトルデータ読み込み中...</span>
      </div>
    );
  }

  return (
    <div className="h-full w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="spectrumGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
          <XAxis
            dataKey="freqHz"
            stroke="#94a3b8"
            fontSize={10}
            tickFormatter={(val) => `${val}Hz`}
          />
          <YAxis stroke="#94a3b8" fontSize={10} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f172a',
              borderColor: '#334155',
              borderRadius: '0.375rem',
              fontSize: '12px',
            }}
            formatter={(value: unknown) => [Number(value).toFixed(2), 'パワー']}
            labelFormatter={(label: unknown) => `周波数: ${label} Hz`}
          />
          {/* 500~1500Hz の漏水強調帯域 */}
          <ReferenceArea
            x1={500}
            x2={1500}
            fill="#ef4444"
            fillOpacity={0.15}
            stroke="#ef4444"
            strokeOpacity={0.3}
            strokeDasharray="2 2"
          />
          {/* 卓越周波数の基準線 */}
          {dominantFreqHz !== undefined && (
            <ReferenceLine
              x={dominantFreqHz}
              stroke="#f59e0b"
              strokeWidth={2}
              strokeDasharray="3 3"
              label={{
                value: `卓越: ${dominantFreqHz}Hz`,
                fill: '#f59e0b',
                fontSize: 11,
                position: 'top',
              }}
            />
          )}
          <Area
            type="monotone"
            dataKey="power"
            stroke="#60a5fa"
            strokeWidth={2}
            fillOpacity={1}
            fill="url(#spectrumGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
