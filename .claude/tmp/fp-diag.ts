import { reviewArtifactFingerprint, resolveBoltDag } from "../tools/aidlc-lib.ts";
import { join } from "node:path";
const projectDir = process.cwd();
const stage = {
  slug: "code-generation",
  phase: "construction",
  for_each: "unit-of-work",
  reviewer: "aidlc-architecture-reviewer-agent",
  produces: ["code-generation-plan", "code-summary"],
  optional_produces: [] as string[],
  produces_kinds: {},
};
const dag = resolveBoltDag(projectDir);
console.log("resolveBoltDag state:", dag.state, dag.state==="ok" ? dag.units : "");
console.log("construction dirs:", require("node:fs").readdirSync(join(projectDir,"aidlc/spaces/default/intents/260810-be4-ledger-reconciliatio/construction")).filter(n=>require("node:fs").statSync(join(projectDir,"aidlc/spaces/default/intents/260810-be4-ledger-reconciliatio/construction",n)).isDirectory()));
console.log("fp no-unit:", reviewArtifactFingerprint(projectDir, stage, undefined));
console.log("fp unit=be4-ledger:", reviewArtifactFingerprint(projectDir, stage, "be4-ledger"));
