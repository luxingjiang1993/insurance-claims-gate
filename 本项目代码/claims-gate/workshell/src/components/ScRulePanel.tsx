import { useState } from "react";

import { ApiClientError, type ClaimsApiClient } from "../api/client";
import type { ClaimDetail, DecisionDraft } from "../api/types";
import { isReadonlyRole } from "../auth/session";
import { ApiErrorView } from "./ApiErrorView";

type Props = {
  api: ClaimsApiClient;
  role: string;
  caseId: string;
  claim: ClaimDetail;
  draft: DecisionDraft | null;
  onClaimUpdated: (claim: ClaimDetail) => void;
  onDraftUpdated: (draft: DecisionDraft | null) => void;
};

/** 将逗号/空白分隔的材料码解析为列表；不在壳内推断缺项。 */
function parseCodes(raw: string): string[] {
  return raw
    .split(/[,，\s]+/)
    .map((part) => part.trim())
    .filter((part) => part.length > 0);
}

function checklistCodes(draft: DecisionDraft | null): string[] {
  return (draft?.supplement_checklist ?? []).map((item) => item.code);
}

/**
 * SC 规则路径作业区：材料登记 / evaluate / 一次补件。
 * 清单与裁决字段原样来自 API，壳不另立门禁规则。
 * Rewrote from: REF-MISSIONS
 */
export function ScRulePanel({
  api,
  role,
  caseId,
  claim,
  draft,
  onClaimUpdated,
  onDraftUpdated,
}: Props) {
  const readonly = isReadonlyRole(role);
  const [materialCodes, setMaterialCodes] = useState(
    claim.material_codes.join(", "),
  );
  const [imageIds, setImageIds] = useState(claim.image_ids.join(", "));
  const [notifyCodes, setNotifyCodes] = useState(
    checklistCodes(draft).join(", "),
  );
  const [busy, setBusy] = useState(false);
  const [okMessage, setOkMessage] = useState<string | null>(null);
  const [error, setError] = useState<ApiClientError | Error | null>(null);

  async function refreshAfterWrite() {
    const nextClaim = await api.getClaim(caseId);
    onClaimUpdated(nextClaim);
    try {
      const nextDraft = await api.getDecision(caseId);
      onDraftUpdated(nextDraft);
      setNotifyCodes(checklistCodes(nextDraft).join(", "));
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 404) {
        onDraftUpdated(null);
        return;
      }
      throw err;
    }
  }

  async function runWrite(action: () => Promise<void>, successText: string) {
    setBusy(true);
    setError(null);
    setOkMessage(null);
    try {
      await action();
      await refreshAfterWrite();
      setOkMessage(successText);
    } catch (err) {
      setOkMessage(null);
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setBusy(false);
    }
  }

  if (readonly) {
    return null;
  }

  return (
    <section className="action-panel">
      <h2>规则路径作业</h2>
      <p className="muted">
        无 LLM Key 亦可点完。清单与裁决以服务端 evaluate / machine_check 为准，本壳不另立规则。
      </p>
      {okMessage ? (
        <p className="ok-banner" role="status">
          {okMessage}
        </p>
      ) : null}
      {error ? (
        <div>
          <p className="error-title">未记为成功</p>
          <ApiErrorView error={error} />
        </div>
      ) : null}

      <div className="form-grid">
        <label>
          材料码（逗号分隔，须与服务端认可码一致）
          <input
            value={materialCodes}
            onChange={(e) => setMaterialCodes(e.target.value)}
            disabled={busy}
          />
        </label>
        <label>
          影像 ID（可选，逗号分隔）
          <input
            value={imageIds}
            onChange={(e) => setImageIds(e.target.value)}
            disabled={busy}
          />
        </label>
        <div className="header-actions">
          <button
            type="button"
            disabled={busy}
            onClick={() =>
              runWrite(async () => {
                const codes = parseCodes(materialCodes);
                await api.registerMaterials(caseId, {
                  material_codes: codes,
                  image_ids: parseCodes(imageIds),
                });
              }, "材料登记已被 API 接受。正式材料齐套结论仍以再次 evaluate 为准。")
            }
          >
            登记材料
          </button>
          <button
            type="button"
            className="secondary"
            disabled={busy || !draft?.supplement_checklist?.length}
            onClick={() =>
              setMaterialCodes(checklistCodes(draft).join(", "))
            }
          >
            按补件清单填入材料码
          </button>
        </div>
      </div>

      <div className="action-row">
        <button
          type="button"
          disabled={busy}
          onClick={() =>
            runWrite(async () => {
              const next = await api.evaluateClaim(caseId);
              onDraftUpdated(next);
            }, "evaluate 已被 API 接受。裁决草案字段如下方所示，壳未改写门禁语义。")
          }
        >
          触发 evaluate
        </button>
      </div>

      <div className="form-grid">
        <p className="muted">
          一次补件：通知清单须与冻结完整缺项一致（同 hash 禁止拆轮）。下方缺项码默认为最近草案清单，可改以观察 API 拒绝。
        </p>
        <label>
          补件缺项码（逗号分隔）
          <input
            value={notifyCodes}
            onChange={(e) => setNotifyCodes(e.target.value)}
            disabled={busy}
          />
        </label>
        <div className="header-actions">
          <button
            type="button"
            disabled={busy || !draft?.one_shot_hash}
            onClick={() =>
              runWrite(async () => {
                await api.notifySupplement(caseId, {
                  one_shot_hash: draft!.one_shot_hash as string,
                  missing_item_codes: parseCodes(notifyCodes),
                });
              }, "一次补件通知已被 API 接受。")
            }
          >
            发起一次补件
          </button>
          <button
            type="button"
            className="secondary"
            disabled={busy || !draft?.supplement_checklist?.length}
            onClick={() => setNotifyCodes(checklistCodes(draft).join(", "))}
          >
            填入完整清单码
          </button>
        </div>
      </div>
    </section>
  );
}
