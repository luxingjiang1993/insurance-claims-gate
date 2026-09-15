/**
 * 作业壳主导航：案件作业 vs 评测入口分离。
 * Rewrote from: REF-MISSIONS, REF-CASE-EVAL-ADVISOR
 */

import { SHELL_NAV_ITEMS, type AppRouteName } from "../appRoutes";

type Props = {
  active: Exclude<AppRouteName, "login" | "detail">;
  onNavigate: (route: "list" | "evalOps") => void;
};

export function ShellNav({ active, onNavigate }: Props) {
  return (
    <nav className="shell-nav" aria-label="作业壳主导航">
      {SHELL_NAV_ITEMS.map((item) => (
        <button
          key={item.route}
          type="button"
          className={
            active === item.route ? "shell-nav-item active" : "shell-nav-item"
          }
          aria-current={active === item.route ? "page" : undefined}
          onClick={() => onNavigate(item.route)}
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
}
