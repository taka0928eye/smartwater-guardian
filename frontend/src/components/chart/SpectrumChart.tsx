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

export const LEAK_BAND_MIN_HZ = 500;
export const LEAK_BAND_MAX_HZ = 1500;
const FREQUENCY_TICK_INTERVAL_HZ = 1000;

export function formatSpectrumPower(value: number): string {
  if (value === 0) return '0';

  const absoluteValue = Math.abs(value);
  if (absoluteValue < 0.000001) return value.toExponential(3);

  return value.toFixed(6).replace(/\.?0+$/, '');
}

export function buildFrequencyTicks(data: SpectrumDataPoint[]): number[] {
  const maxFrequency = Math.max(...data.map((point) => point.freqHz), 0);
  const axisMax = Math.max(
    FREQUENCY_TICK_INTERVAL_HZ,
    Math.ceil(maxFrequency / FREQUENCY_TICK_INTERVAL_HZ) * FREQUENCY_TICK_INTERVAL_HZ,
  );

  return Array.from(
    { length: axisMax / FREQUENCY_TICK_INTERVAL_HZ + 1 },
    (_, index) => index * FREQUENCY_TICK_INTERVAL_HZ,
  );
}

interface SpectrumChartProps {
  data?: SpectrumDataPoint[];
  isLoading?: boolean;
}

export const SpectrumChart: React.FC<SpectrumChartProps> = ({
  data,
  isLoading,
}) => {
  if (isLoading || !data || data.length === 0) {
    return (
      <div className="flex h-full w-full items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40 animate-pulse">
        <span className="text-xs text-slate-500">スペクトルデータ読み込み中...</span>
      </div>
    );
  }

  const frequencyTicks = buildFrequencyTicks(data);
  const frequencyMax = frequencyTicks.at(-1) ?? FREQUENCY_TICK_INTERVAL_HZ;

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
            type="number"
            domain={[0, frequencyMax]}
            ticks={frequencyTicks}
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
            formatter={(value: unknown) => [formatSpectrumPower(Number(value)), 'パワー']}
            labelFormatter={(label: unknown) => `周波数: ${label} Hz`}
          />
          {/* 500~1500Hz の漏水強調帯域 */}
          <ReferenceArea
            x1={LEAK_BAND_MIN_HZ}
            x2={LEAK_BAND_MAX_HZ}
            fill="#ef4444"
            fillOpacity={0.08}
          />
          <ReferenceLine
            x={LEAK_BAND_MIN_HZ}
            stroke="#ef4444"
            strokeOpacity={0.8}
            strokeDasharray="4 4"
          />
          <ReferenceLine
            x={LEAK_BAND_MAX_HZ}
            stroke="#ef4444"
            strokeOpacity={0.8}
            strokeDasharray="4 4"
          />
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
