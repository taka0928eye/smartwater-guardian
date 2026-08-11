**Collaborator:** aidlc-devsecops-agent

## Contribution

Blind Support Review（DevSecOps 視点: lint/format ルール・SAST/DAST・シークレット/依存関係スキャン・サプライチェーン統制）。
実リポジトリ（`.github/workflows/ci.yml`・`frontend/package.json`・`backend/requirements.txt`・`frontend/eslint.config.mjs`・`.gitignore`）と codekb 3点（code-quality-assessment / dependencies / technology-stack）を照合して検証した。

### 1. ドラフトの正確性確認（証拠と一致）

- **「BE はリント未導入（ruff / mypy なし）」**: 一致。`pyproject.toml`・`ruff.toml`・`mypy.ini` は存在せず、CI に Python lint ステップなし。
- **「FE は ESLint 9 flat config + eslint-config-next を CI ゲートに組込」**: 一致。`frontend/eslint.config.mjs` は `core-web-vitals` + `typescript` 構成で、`ci.yml` の `npm run lint` がゲート。セキュリティ系プラグイン（eslint-plugin-security 等）は未導入。
- **「`any` 禁止」**: 一致。code-quality-assessment に「`any` 使用なし」、現状 grep でも TS/Python に `any` なし。
- **「backend 依存は == ピン固定」**: 一致。`backend/requirements.txt` は全パッケージ `==` ピン。frontend は `package-lock.json` がコミット済み（`npm ci` が再現可能）。
- **「CI はテスト・カバレッジ・lint・build のみ」**: 一致。`.github/workflows/` は `ci.yml` 単独で、**セキュリティ系スキャンは一切含まれない**（依存・シークレット・SAST・DAST とも未導入）。この「未整備」である点はドラフトに明記されていないため、下記 2〜4 で補強を提案する。
- **`MOCK_KPI_DATA` 撤去**: `frontend/src/app/page.tsx:25` に `MOCK_KPI_DATA` が現存することを確認。discovered-rules の `NEVER ... モック値残置禁止` は FE-7 スコープと整合。

### 2. シークレット管理 — 現状は健全（追加の明文化を推奨）

- `backend/.env` は **untracked かつ gitignore 済み**（`.gitignore:9` の `.env` ルールが `backend/.env` にヒット）。実シークレットのコミット痕跡なし。
- コミット済みはプレースホルダのみ（`backend/.env.example`・`backend/README.md`・`frontend/.env.local.example`）。`frontend/.env.local.example` は `NEXT_PUBLIC_*` への機密混入を警告済み。
- ただし **シークレット検知の自動化はゼロ**（gitleaks / trufflehog / pre-commit フック / GitHub secret scanning 設定のいずれも不在）。`.gitignore` 依存のみで、今後 Orcarouter API キー（BE-5）を扱う際の事故防止として、CI への gitleaks 追加か GitHub secret scanning 有効化をインタビューで確認することを推奨。
- **discovered-rules への追加候補**（インタビュー確認用）:
  - `NEVER: 本番または共有リポジトリへシークレット・API キーをコミットすること（実キーは環境変数/シークレット管理で注入し、.env は gitignore で管理する）。`

### 3. 依存関係・サプライチェーン統制 — 最大の欠落（対応を推奨）

- 依存脆弱性スキャンが**全面的に不在**（`pip-audit` / `npm audit` / Dependabot / Snyk / Trivy / SBOM のいずれもなし）。
- backend は `==` ピンで再現性は担保されているが、**既知 CVE の検知経路がない**。frontend は next/react のみ完全ピンで、axios `^1.19.0`・leaflet `^1.9.4` 等は caret 範囲のため**推移的依存のドリフトが未監視**。
- デモスコープ（8/10〜8/15）の費用対効果を考慮した最小提案:
  - **Dependabot**（GitHub ネイティブ・設定ファイル1つ・ゼロコスト）を最優先で有効化。
  - 併せて CI に軽量ゲートを追加: frontend `npm audit --audit-level=high`、backend `pip-audit`（未導入のため `pip install pip-audit` を CI に追加するか、`pip list --outdated` に留める）。
- **discovered-rules への追加候補**（インタビュー確認用）:
  - `ALWAYS: 依存関係の脆弱性スキャン（Dependabot または npm audit / pip-audit）を CI に組み込むこと。`

### 4. SAST / DAST — デモスコープでは N/A 寄り（方針の明記を推奨）

- **SAST**: Python 用 bandit / Semgrep、FE のセキュリティ ESLint プラグインは未導入。`any` 禁止・Pydantic v2 strict 等で入力検証は強固だが、静的な脆弱性検知は不在。デモスコープでは「非ブロッキング警告（warning）として導入」か「スコープ外として明記」かをインタビューで確認することを推奨。
- **DAST**: 本プロジェクトはデプロイ環境（staging）が存在せず、ローカル実行のみ。DAST は実行対象となる稼働環境が無いため **現状 N/A**。将来ホスティング環境ができた時点で OWASP ZAP 等を再評価する、と evidence に記録することを推奨。

### 5. 既知のセキュリティ負債としての記録（ドラフト未記載）

- **CORS ハードコード**（`backend/main.py:10`）: `allow_origins=["http://localhost:3000"]`・`allow_credentials=True`・`allow_methods=["*"]`・`allow_headers=["*"]`。固定オリジンなのでデモでは機能上安全だが、`allow_credentials=True` と組み合わせて `*` にしてはいけない（その場合の設定事故リスクを孕む）。ホスティング時に環境変数化（`ALLOWED_ORIGINS`）することを既知負債として Code Style または evidence の「未確定/既知負債」に明記することを推奨（codekb code-quality-assessment #9 と整合）。
- **CI 内の unpinned install**（`ci.yml` の `pip install pytest pytest-cov httpx`）: バージョン未指定のためサプライチェーンの再現性がやや劣る。`requirements-dev.txt` 化を将来提案。

### 6. evidence.md への追記提案（インタビュー質問）

未確定欄に次を追加することを推奨する:

1. 依存脆弱性スキャン（Dependabot / `npm audit` / `pip-audit`）をデモスコープで導入するか。
2. シークレット検知（gitleaks 等）を CI に追加するか、GitHub secret scanning に委ねるか。
3. Python SAST（bandit）を非ブロッキングで導入するか、スコープ外とするか。
4. CORS 硬コード（localhost:3000）はデモのまま維持し、ホスティング時に環境変数化する方針でよいか。

## Positions

- AGREE: ドラフトの「BE リント未導入」「FE ESLint ゲート」「`any` 禁止」「backend 依存 `==` ピン」は CI・codekb の実態と正確に一致している — 証拠整合が取れており、そのまま promote 候補にできる。
- AGREE: discovered-rules の `NEVER: テスト・カバレッジ・lint・build が成功していない状態のコードを main へマージすること` は `ci.yml` のゲート実態を正しく反映している — 実効性のあるハード制約として妥当。
- OBJECT: セキュリティ統制の現状（依存・シークレット・SAST が全て未整備、DAST は N/A）がドラフトに未記載で、supply-chain 統制の欠落が隠れている — 「未整備であること」と「デモスコープでの方針」を evidence とインタビュー質問に明示し、少なくとも Dependabot 導入を確認すべき。
- OBJECT: CORS ハードコード（`main.py` の固定オリジン + `allow_credentials=True`）が既知のセキュリティ負債として記録されていない — デモでは許容だが、将来の設定事故を防ぐため環境変数化の方針を Code Style または evidence に明記すべき。
