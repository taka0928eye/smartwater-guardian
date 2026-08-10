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
 * Level 0 は PRD §2 更新（2026-08-10）で追加された。BE-6 の一覧APIは Level 0 も返すため、
 * 一覧側（FE-5）では既定で非表示にし「正常も表示」トグルで切替える。
 */
export type SeverityLevel = 0 | 1 | 2 | 3;

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

/** アラート詳細（GET /api/v1/alerts/{telemetryId}）。 */
export interface AlertDetail extends AlertSummary {
  location: GeoLocation;
  analysis: AnalysisResult | null;
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
}
