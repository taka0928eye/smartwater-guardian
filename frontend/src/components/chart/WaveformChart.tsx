'use client';

import React, { useMemo } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

export interface WaveformPoint {
  timeMs: number;
  amplitude: number;
}

interface WaveformChartProps {
  data?: WaveformPoint[];
  isLoading?: boolean;
}

export const WaveformChart: React.FC<WaveformChartProps> = ({ data, isLoading }) => {
  // 256点へダウンサンプリング（間引き）
  const downsampledData = useMemo(() => {
    if (!data || data.length === 0) return [];
    const targetPoints = 256;
    if (data.length <= targetPoints) return data;

    const step = Math.ceil(data.length / targetPoints);
    const result: WaveformPoint[] = [];
    for (let i = 0; i < data.length; i += step) {
      result.push(data[i]);
    }
    return result;
  }, [data]);

  if (isLoading || !data || data.length === 0) {
    return (
      <div className="flex h-full w-full items-center justify-center rounded-lg border border-slate-800 bg-slate-900/40 animate-pulse">
        <span className="text-xs text-slate-500">時間波形データ読み込み中...</span>
      </div>
    );
  }

  return (
    <div className="h-full w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={downsampledData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="waveformGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.6} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
          <XAxis
            dataKey="timeMs"
            stroke="#94a3b8"
            fontSize={10}
            tickFormatter={(val) => `${val}ms`}
          />
          <YAxis stroke="#94a3b8" fontSize={10} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f172a',
              borderColor: '#334155',
              borderRadius: '0.375rem',
              fontSize: '12px',
            }}
            formatter={(value: unknown) => [Number(value).toFixed(3), '振幅']}
            labelFormatter={(label: unknown) => `時間: ${label} ms`}
          />
          <Area
            type="monotone"
            dataKey="amplitude"
            stroke="#34d399"
            strokeWidth={1.5}
            fillOpacity={1}
            fill="url(#waveformGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
