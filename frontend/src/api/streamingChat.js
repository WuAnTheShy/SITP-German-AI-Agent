// ---------------------------------------------------------------
// SSE 流式 chat 客户端
// ---------------------------------------------------------------
// 浏览器原生 EventSource 不支持 POST + 自定义 header,
// 所以用 fetch ReadableStream 自己解析 SSE 格式。
//
// 使用:
//   const stop = streamChat(API_STUDENT_CHAT_STREAM, body, {
//     onMeta:           (data) => {},
//     onRagStart:       (data) => {},
//     onRagDone:        (data) => {},
//     onToolCallStart:  (data) => {},
//     onToolCallDone:   (data) => {},
//     onToken:          (delta) => {},   // 每个 token chunk
//     onDone:           (data) => {},    // 流结束
//     onError:          (error) => {},   // 网络/SSE 错误
//   });
//   stop();  // 中断流(用户取消时)

/**
 * 解析单个 SSE event 块,返回 [event, data] 或 null。
 */
function parseSSEBlock(block) {
  let event = "message";
  let dataLines = [];
  for (const line of block.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
    // 忽略以 ":" 开头的注释行(SSE keep-alive)
  }
  if (dataLines.length === 0) return null;
  const dataStr = dataLines.join("\n");
  try {
    return [event, JSON.parse(dataStr)];
  } catch {
    return [event, dataStr];
  }
}

/**
 * 发起 SSE 流式 chat 请求。
 *
 * @param {string} url       - 端点 URL(如 API_STUDENT_CHAT_STREAM)
 * @param {object} body      - 请求体(如 { message, session_id, new_thread })
 * @param {object} handlers  - 各事件回调
 * @returns {() => void}     - 中断流的函数
 */
export function streamChat(url, body, handlers = {}) {
  const {
    onMeta,
    onRagStart,
    onRagDone,
    onToolCallStart,
    onToolCallDone,
    onToken,
    onDone,
    onError,
  } = handlers;

  const token = localStorage.getItem("authToken");
  const controller = new AbortController();

  (async () => {
    try {
      const resp = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });

      if (!resp.ok) {
        const errText = await resp.text();
        if (resp.status === 401) {
          // 401:清登录态,跳登录页(对齐现有 axios 拦截器行为)
          localStorage.removeItem("authToken");
          localStorage.removeItem("userInfo");
          window.location.hash = "#/student/login";
          return;
        }
        if (onError)
          onError(new Error(`HTTP ${resp.status}: ${errText.slice(0, 200)}`));
        return;
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // 按 SSE 规范,事件之间用空行分隔(\n\n)
        let sepIdx;
        while ((sepIdx = buffer.indexOf("\n\n")) !== -1) {
          const block = buffer.slice(0, sepIdx);
          buffer = buffer.slice(sepIdx + 2);

          const parsed = parseSSEBlock(block);
          if (!parsed) continue;
          const [event, data] = parsed;

          switch (event) {
            case "meta":
              onMeta?.(data);
              break;
            case "rag_start":
              onRagStart?.(data);
              break;
            case "rag_done":
              onRagDone?.(data);
              break;
            case "tool_call_start":
              onToolCallStart?.(data);
              break;
            case "tool_call_done":
              onToolCallDone?.(data);
              break;
            case "token":
              onToken?.(data?.delta ?? "");
              break;
            case "done":
              onDone?.(data);
              break;
            case "error":
              if (onError) onError(new Error(data?.message || "服务器错误"));
              break;
            default:
              // 未知事件类型忽略
              break;
          }
        }
      }
    } catch (err) {
      if (err.name === "AbortError") return; // 用户主动中断
      if (onError) onError(err);
    }
  })();

  return () => controller.abort();
}
