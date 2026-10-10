export const MAX_ANALYSIS_REQUIREMENT_LENGTH = 2000;

export function normalizeAnalysisRequirement(value: unknown): string {
  if (value === undefined) {
    return "";
  }

  if (typeof value !== "string") {
    throw new Error("分析需求必須是文字。");
  }

  const requirement = value.trim();

  if (requirement.length > MAX_ANALYSIS_REQUIREMENT_LENGTH) {
    throw new Error(`分析需求最多 ${MAX_ANALYSIS_REQUIREMENT_LENGTH} 字。`);
  }

  return requirement;
}
