import React from "react";
import ReactMarkdown from "react-markdown";

const normalizeMarkdownText = (content) => {
  if (typeof content === "string") return content;
  if (content == null) return "";
  return String(content);
};

const MarkdownContent = ({ content, className = "" }) => (
  <ReactMarkdown
    className={`markdown-content ${className}`.trim()}
    components={{
      a: ({ node, ...props }) => (
        <a {...props} target="_blank" rel="noreferrer noopener" />
      ),
    }}
  >
    {normalizeMarkdownText(content)}
  </ReactMarkdown>
);

export default MarkdownContent;
