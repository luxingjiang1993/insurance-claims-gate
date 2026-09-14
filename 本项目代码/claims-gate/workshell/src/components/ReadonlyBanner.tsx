import { isReadonlyRole } from "../auth/session";

/** viewer 只读提示条。 */
export function ReadonlyBanner({ role }: { role: string }) {
  if (!isReadonlyRole(role)) {
    return null;
  }
  return (
    <div className="readonly-banner" role="status">
      当前角色 <strong>viewer</strong>：本作业壳仅提供只读浏览，不展示写操作入口。
    </div>
  );
}
