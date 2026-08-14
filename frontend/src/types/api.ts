/**
 * FE-1: バックエンド API のレスポンスと 1:1 に対応する TypeScript 型定義。
 *
 * バックエンドは snake_case（Pydantic v2）、フロントは camelCase で統一する。
 * 変換は src/lib/api.ts の境界で一度だけ行うため、このファイルの型は
 * camelCase 側のみを公開する。
 *
 * 規約: any 型は使用しない（CLAUDE.md §5.2）。
 */

/**
 * 漏水深刻度。0=正常 / 1=微小漏水 / 2=進行性漏水 / 3=管路破裂。
 * 単一ソースは lib/severity.ts（表示メタと同居）。FE-7 で二重定義を解消し、
 * 本ファイルからも re-export する（FR-2）。本ファイル内の各型でも使用するため
 * ローカル import も併せて行う。
 */
import type { SeverityLevel } from "../lib/severity";
export type { SeverityLevel };

/** 作業指示書の生成元（AI生成 / 規定ルールによる自動算出）。 */
export type WorkOrderSource = "llm" | "fallback";

/** 補修の緊急度。 */
export type Urgency = "low" | "medium" | "high" | "critical";

/** 緯度経度。 */
export interface GeoLocation {
  latitude: number;
  longitude: number;
}

/** 周波数スペクトルの1点（FE-4 のグラフ描画用）。 */
export interface SpectrumPoint {
  freqHz: number;
  magnitude: number;
}

/** FFT解析（BE-3 / app/services/audio.py）の判定結果。 */
export interface AnalysisResult {
  leakConfidence: number;
  severityLevel: SeverityLevel;
  dominantFreqHz: number;
  bandEnergyRatio: number;
  spectrum?: SpectrumPoint[];
}

/** テレメトリ受信結果（BE-1）。 */
export interface TelemetryResponse {
  telemetryId: string;
  sensorId: string;
  receivedAt: string;
  status: "accepted";
  analysis: AnalysisResult | null;
}

/** 消火栓マスタと最新センサー状態（BE-6: GET /api/v1/sensors）。 */
export interface SensorInfo {
  sensorId: string;
  hydrantId: string;
  /** センサーの監視状態（正常 / 警告 / 異常 等）。 */
  status: string;
  location: GeoLocation;
  lastReadingAt: string;
}

/** 検知されたアラートの一覧行（BE-6: GET /api/v1/alerts）。 */
export interface AlertSummary {
  telemetryId: string;
  sensorId: string;
  hydrantId: string;
  severityLevel: SeverityLevel;
  leakConfidence: number;
  detectedAt: string;
}

/** 配管台帳情報（BE-4 / app/services/ledger.py）。 */
export interface PipeInfo {
  pipeId: string;
  material: string;
  diameterMm: number;
  installedYear: number;
  burialDepthM: number;
  ageYears: number;
}

/** 受信PCMから抽出した時間軸波形の1点。 */
export interface WaveformPoint {
  timeMs: number;
  amplitude: number;
}

/** アラート詳細（GET /api/v1/alerts/{telemetryId}）。 */
export interface AlertDetail extends AlertSummary {
  location: GeoLocation;
  analysis: AnalysisResult | null;
  hasAudio: boolean;
  waveform: WaveformPoint[];
  pipeInfo?: PipeInfo | null;
}

/** 補修部材1品目（OR-2 / OR-3）。 */
export interface RepairPart {
  name: string;
  spec: string;
  quantity: number;
  unitPriceYen: number;
  subtotalYen: number;
}

/** AI自動起票の結果（BE-5 / OR-3: POST /alerts/{id}/work-order）。 */
export interface WorkOrder {
  workOrderId: string;
  alertId: string;
  createdAt: string;
  parts: RepairPart[];
  totalEstimateYen: number;
  workSteps: string[];
  requiredWorkers: number;
  estimatedDurationHours: number;
  urgency: Urgency;
  notificationText: string;
  source: WorkOrderSource;

  // FR-6 原価フィールド（オプショナル）
  promptTokens?: number;
  completionTokens?: number;
  costYen?: number;
  model?: string;
  latencyMs?: number;
  isEstimated?: boolean;
}


/** GET /api/v1/kpi/summary のレスポンス（BE-8 契約・snake_case→camelCase 変換済み）。
 *  変換は src/lib/api.ts の unwrap で 1 回だけ行う。 */
export interface KpiSummary {
  /** 監視センサー総数（snake_case: total_sensors）。 */
  totalSensors: number;
  /** Level 1（微小漏水）検知件数（snake_case: level1_count）。 */
  level1Count: number;
  /** Level 2（進行性漏水）検知件数（snake_case: level2_count）。 */
  level2Count: number;
  /** Level 3（管路破裂）検知件数（snake_case: level3_count）。 */
  level3Count: number;
  /** 推定削減コスト（円。snake_case: estimated_cost_saved_yen）。 */
  estimatedCostSavedYen: number;
  /** 試算値かどうか（snake_case: is_estimate）。 */
  isEstimate: boolean;
  /** 試算根拠ドキュメントのパス（snake_case: assumption_doc）。 */
  assumptionDoc: string;
}
