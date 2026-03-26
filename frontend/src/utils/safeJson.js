/**
 * 安全解析 localStorage 中的 userInfo，避免损坏 JSON 导致整页白屏。
 */
export function parseStoredUserInfo() {
  try {
    const raw = localStorage.getItem("userInfo");
    if (!raw || raw === "undefined") return {};
    const o = JSON.parse(raw);
    return o && typeof o === "object" ? o : {};
  } catch {
    return {};
  }
}
