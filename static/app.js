/* =====================================================================
   SHL Assessment Recommender – Frontend Application Logic
   ===================================================================== */

(function () {
  "use strict";

  /* ── DOM References ──────────────────────────────────────────────── */
  const chatMessages   = document.getElementById("chat-messages");
  const chatForm       = document.getElementById("chat-form");
  const chatInput      = document.getElementById("chat-input");
  const sendBtn        = document.getElementById("send-btn");
  const resetBtn       = document.getElementById("reset-chat-btn");
  const suggestionsBox = document.getElementById("suggestions-container");

  /* ── Sidebar Profile Refs ────────────────────────────────────────── */
  const profileStatus   = document.getElementById("profile-status");
  const profileRole     = document.getElementById("profile-role");
  const profileSeniority= document.getElementById("profile-seniority");
  const profileSkills   = document.getElementById("profile-skills");
  const focusChips      = document.querySelectorAll(".focus-chip");

  /* ── State ───────────────────────────────────────────────────────── */
  let conversationHistory = []; // [{role, content}]
  let isLoading = false;

  /* ── Utility: Simple Markdown → HTML ─────────────────────────────── */
  function markdownToHtml(text) {
    if (!text) return "";

    // Escape HTML first
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Code blocks (``` ... ```)
    html = html.replace(/```[\w]*\n?([\s\S]*?)```/g, "<pre><code>$1</code></pre>");

    // Bold (**text** or __text__)
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/__(.+?)__/g, "<strong>$1</strong>");

    // Italic (*text* or _text_)
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
    html = html.replace(/_(.+?)_/g, "<em>$1</em>");

    // Markdown tables
    html = parseMarkdownTable(html);

    // Unordered lists (lines starting with - or *)
    html = html.replace(/^[-*] (.+)/gm, "<li>$1</li>");
    html = html.replace(/(<li>[\s\S]*?<\/li>)/g, (match) => {
      if (match.startsWith("<li>")) return "<ul>" + match + "</ul>";
      return match;
    });
    // Collapse consecutive </ul><ul>
    html = html.replace(/<\/ul>\s*<ul>/g, "");

    // Ordered lists (lines starting with 1. 2. etc.)
    html = html.replace(/^\d+\. (.+)/gm, "<li>$1</li>");

    // Headings
    html = html.replace(/^### (.+)/gm, "<h4>$1</h4>");
    html = html.replace(/^## (.+)/gm, "<h3>$1</h3>");
    html = html.replace(/^# (.+)/gm, "<h2>$1</h2>");

    // Horizontal rules
    html = html.replace(/^---$/gm, "<hr>");

    // Paragraphs: double line breaks
    html = html
      .split(/\n{2,}/)
      .map((para) => {
        para = para.trim();
        if (!para) return "";
        // Don't wrap block-level elements in <p>
        if (/^<(ul|ol|li|h[2-6]|pre|table|hr)/.test(para)) return para;
        return "<p>" + para.replace(/\n/g, "<br>") + "</p>";
      })
      .join("\n");

    return html;
  }

  function parseMarkdownTable(text) {
    const lines = text.split("\n");
    const result = [];
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      // Detect table header line (contains |)
      if (line.includes("|") && i + 1 < lines.length && /^\|?[\s\-|:]+\|/.test(lines[i + 1])) {
        const headers = line.split("|").filter((c) => c.trim() !== "");
        i += 2; // skip separator
        let tableHtml = "<table><thead><tr>";
        headers.forEach((h) => { tableHtml += `<th>${h.trim()}</th>`; });
        tableHtml += "</tr></thead><tbody>";
        while (i < lines.length && lines[i].includes("|")) {
          const cells = lines[i].split("|").filter((c) => c.trim() !== "");
          tableHtml += "<tr>";
          cells.forEach((c) => { tableHtml += `<td>${c.trim()}</td>`; });
          tableHtml += "</tr>";
          i++;
        }
        tableHtml += "</tbody></table>";
        result.push(tableHtml);
      } else {
        result.push(line);
        i++;
      }
    }
    return result.join("\n");
  }

  /* ── Render Recommendation Cards ─────────────────────────────────── */
  function renderRecommendations(recommendations) {
    if (!recommendations || recommendations.length === 0) return "";

    const typeMap = {
      "Ability & Aptitude": "cognitive",
      "Cognitive": "cognitive",
      "Personality & Behaviour": "personality",
      "Personality": "personality",
      "Behavioral": "behavioral",
      "Behaviour": "behavioral",
      "Skills & Simulations": "skills",
      "Skills": "skills",
      "Biodata & Situational Judgement": "behavioral",
    };

    const cards = recommendations
      .map((rec) => {
        const rawType = rec.assessment_type || rec.type || "";
        const typeKey = typeMap[rawType] || "generic";
        const url = rec.url || rec.link || "#";
        const name = rec.name || rec.title || "Assessment";
        const desc = rec.description || "";
        const duration = rec.duration ? `<span class="rec-meta">⏱ ${rec.duration}</span>` : "";
        const remote = rec.remote_testing !== undefined
          ? `<span class="rec-meta">${rec.remote_testing ? "✔ Remote" : "✘ On-site"}</span>`
          : "";

        return `
          <div class="rec-card type-${typeKey}">
            <span class="rec-badge type-${typeKey}">${rawType || "Assessment"}</span>
            <div class="rec-title">${name}</div>
            ${desc ? `<p class="rec-desc">${desc.substring(0, 100)}${desc.length > 100 ? "…" : ""}</p>` : ""}
            <div class="rec-meta-row">${duration}${remote}</div>
            <a href="${url}" target="_blank" rel="noopener" class="rec-action">
              View Details <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
            </a>
          </div>`;
      })
      .join("");

    return `<div class="recommendations-container">${cards}</div>`;
  }

  /* ── Append a message bubble ──────────────────────────────────────── */
  function appendMessage(role, content, recommendations) {
    const msgEl = document.createElement("div");
    msgEl.className = `message message-${role} animate-fade-in`;

    const avatar = role === "assistant"
      ? `<div class="message-avatar">🤖</div>`
      : `<div class="message-avatar">👤</div>`;

    const bubbleHtml = markdownToHtml(content);
    const recHtml = recommendations ? renderRecommendations(recommendations) : "";

    msgEl.innerHTML = `
      ${avatar}
      <div class="message-content-wrapper">
        <div class="message-bubble">${bubbleHtml}${recHtml}</div>
      </div>`;

    chatMessages.appendChild(msgEl);
    scrollToBottom();
    return msgEl;
  }

  /* ── Typing Indicator ─────────────────────────────────────────────── */
  function showTyping() {
    const el = document.createElement("div");
    el.className = "message message-assistant animate-fade-in";
    el.id = "typing-indicator";
    el.innerHTML = `
      <div class="message-avatar">🤖</div>
      <div class="message-content-wrapper">
        <div class="message-bubble">
          <div class="typing-indicator">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
          </div>
        </div>
      </div>`;
    chatMessages.appendChild(el);
    scrollToBottom();
  }

  function hideTyping() {
    const el = document.getElementById("typing-indicator");
    if (el) el.remove();
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  /* ── Update Sidebar Profile ───────────────────────────────────────── */
  function updateProfile(context) {
    if (!context) return;

    if (context.role) {
      profileRole.textContent = context.role;
      profileStatus.textContent = "Profile Active";
    }
    if (context.seniority) {
      profileSeniority.textContent = context.seniority;
    }
    if (context.skills && context.skills.length > 0) {
      profileSkills.innerHTML = context.skills
        .map((s) => `<span class="skill-tag">${s}</span>`)
        .join("");
    }
    if (context.focus_areas && context.focus_areas.length > 0) {
      focusChips.forEach((chip) => {
        const focus = chip.dataset.focus;
        if (context.focus_areas.includes(focus)) {
          chip.classList.add("active");
        } else {
          chip.classList.remove("active");
        }
      });
    }
  }

  /* ── Reset Profile Sidebar ────────────────────────────────────────── */
  function resetProfile() {
    profileRole.textContent = "—";
    profileSeniority.textContent = "—";
    profileSkills.innerHTML = `<span class="empty-msg">No skills identified yet</span>`;
    profileStatus.textContent = "Awaiting Input";
    focusChips.forEach((chip) => chip.classList.remove("active"));
  }

  /* ── Set UI Loading State ─────────────────────────────────────────── */
  function setLoading(state) {
    isLoading = state;
    chatInput.disabled = state;
    sendBtn.disabled = state;
    sendBtn.style.opacity = state ? "0.6" : "1";
  }

  /* ── API Call ─────────────────────────────────────────────────────── */
  async function sendMessage(userText) {
    if (!userText.trim() || isLoading) return;

    // Add user message to history and UI
    conversationHistory.push({ role: "user", content: userText });
    appendMessage("user", userText);

    // Hide suggestion chips after first real send
    suggestionsBox.style.display = "none";

    setLoading(true);
    showTyping();

    try {
      const response = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: conversationHistory }),
      });

      hideTyping();

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        const errMsg = errData.detail || `Server error (${response.status})`;
        appendMessage("assistant", `⚠️ **Error:** ${errMsg}`);
        return;
      }

      const data = await response.json();

      // data shape: { reply, context, recommendations }
      const reply = data.reply || data.message || "I'm not sure how to respond to that.";
      const recommendations = data.recommendations || null;
      const context = data.context || null;

      conversationHistory.push({ role: "assistant", content: reply });
      appendMessage("assistant", reply, recommendations);

      if (context) updateProfile(context);

    } catch (err) {
      hideTyping();
      appendMessage("assistant", `⚠️ **Network Error:** Could not reach the server. Please ensure the backend is running.\n\n\`${err.message}\``);
    } finally {
      setLoading(false);
    }
  }

  /* ── Event Listeners ──────────────────────────────────────────────── */
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;
    chatInput.value = "";
    sendMessage(text);
  });

  // Quick suggestion chips
  suggestionsBox.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    const query = chip.dataset.query;
    if (query) {
      chatInput.value = query;
      chatInput.focus();
    }
  });

  // Reset conversation
  resetBtn.addEventListener("click", () => {
    conversationHistory = [];
    // Clear messages except the first welcome message
    while (chatMessages.children.length > 1) {
      chatMessages.removeChild(chatMessages.lastChild);
    }
    suggestionsBox.style.display = "flex";
    resetProfile();
    chatInput.focus();
  });

  // Enter key behaviour (Shift+Enter = new line if textarea, plain Enter = submit)
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event("submit"));
    }
  });

  /* ── Extra CSS for rec-meta (injected once) ───────────────────────── */
  const extraStyle = document.createElement("style");
  extraStyle.textContent = `
    .rec-desc { font-size: 0.8rem; color: var(--text-muted); margin: 6px 0 10px; line-height: 1.4; }
    .rec-meta-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
    .rec-meta { font-size: 0.72rem; color: var(--text-muted); background: hsla(224,20%,20%,0.4);
                padding: 2px 7px; border-radius: 4px; border: 1px solid var(--border-color); }
    .message-bubble h2, .message-bubble h3, .message-bubble h4 {
      font-family: var(--font-heading); margin: 12px 0 6px; color: var(--text-primary); }
    .message-bubble pre { background: hsla(224,25%,10%,0.6); border-radius: 8px; 
      padding: 12px; overflow-x: auto; font-size: 0.82rem; margin: 8px 0; }
    .message-bubble code { font-family: monospace; }
    .message-bubble hr { border: none; border-top: 1px solid var(--border-color); margin: 12px 0; }
  `;
  document.head.appendChild(extraStyle);

  /* ── Init ─────────────────────────────────────────────────────────── */
  chatInput.focus();
})();
