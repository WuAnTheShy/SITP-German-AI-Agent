import React from "react";
import ReactMarkdown from "react-markdown";

const normalizeMarkdownText = (content) => {
  if (typeof content === "string") return content;
  if (content == null) return "";
  return String(content);
};

const MarkdownContent = ({ content, className = "" }) => (
  <div className={`markdown-content ${className}`.trim()}>
    <ReactMarkdown
      components={{
        a: ({ node, ...props }) => (
          <a {...props} target="_blank" rel="noreferrer noopener" />
        ),
      }}
    >
      {normalizeMarkdownText(content)}
    </ReactMarkdown>
  </div>
);

export default MarkdownContent;
