import { reviewArtifactFingerprint } from "../tools/aidlc-lib.ts";
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
console.log("current fp:", reviewArtifactFingerprint(projectDir, stage, undefined));
console.log("recorded fp: sha256:c2531111d4a2f38a62a1868ccac5253fffc4508ae8cc25282c751c808f79d746");
