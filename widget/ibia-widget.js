(function () {

  const CONFIG = {
    apiUrl:
      (window.IBIA_CONFIG && window.IBIA_CONFIG.apiUrl) ||
      "http://127.0.0.1:8000/chat",
  };

 
  function injectStyles() {
    const style = document.createElement("style");
    style.innerHTML = `
      .ibia-fab {
        position: fixed;
        right: 20px;
        bottom: 20px;
        width: 64px;
        height: 64px;
        border-radius: 999px;
        border: none;
        background: transparent;
        cursor: pointer;
        z-index: 99999;
      }

      .ibia-fab img {
        width: 100%;
        height: 100%;
        border-radius: 999px;
        object-fit: cover;
        box-shadow: 0 10px 25px rgba(0,0,0,.35);
      }

      .ibia-widget {
        position: fixed;
        right: 20px;
        bottom: 96px;
        width: 360px;
        max-width: calc(100vw - 40px);
        z-index: 99999;
        opacity: 0;
        transform: translateY(12px) scale(.98);
        pointer-events: none;
        transition: opacity .16s ease, transform .16s ease;
      }

      .ibia-widget.is-open {
        opacity: 1;
        transform: translateY(0) scale(1);
        pointer-events: auto;
      }

      .ibia-app {
        background: #111a2e;
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,.08);
        color: #e7eefc;
        font-family: system-ui, Arial, sans-serif;
      }

      .ibia-topbar {
        padding: 14px 16px;
        background: #0f1830;
        border-bottom: 1px solid rgba(255,255,255,.08);
      }

      .ibia-title { font-weight: 700; }
      .ibia-subtitle { font-size: 13px; opacity: .8; }

      .ibia-messages {
        padding: 16px;
        max-height: 420px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 10px;
      }

      .ibia-bubble {
        padding: 10px 12px;
        border-radius: 12px;
        max-width: 80%;
        white-space: pre-wrap;
        line-height: 1.35;
      }

      .ibia-user {
        align-self: flex-end;
        background: #1a73e8;
        color: #fff;
      }

      .ibia-assistant {
        align-self: flex-start;
        background: rgba(255,255,255,.08);
      }

      .ibia-composer {
        display: flex;
        gap: 8px;
        padding: 12px;
        background: #0f1830;
        border-top: 1px solid rgba(255,255,255,.08);
      }

      .ibia-composer input {
        flex: 1;
        padding: 10px 12px;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,.12);
        background: #0b1220;
        color: #e7eefc;
        outline: none;
      }

      .ibia-composer button {
        padding: 10px 14px;
        border-radius: 10px;
        border: none;
        background: #22c55e;
        font-weight: 700;
        cursor: pointer;
      }
    `;
    document.head.appendChild(style);
  }

 
  function injectUI() {
    const fab = document.createElement("button");
    fab.className = "ibia-fab";
    fab.innerHTML = `<img src="./assets/IBIA.png" alt="IBIA" />`;

    const widget = document.createElement("div");
    widget.className = "ibia-widget";
    widget.innerHTML = `
      <div class="ibia-app">
        <div class="ibia-topbar">
          <div class="ibia-title">IBIA</div>
          <div class="ibia-subtitle">Assistente de CNH</div>
        </div>
        <div class="ibia-messages"></div>
        <form class="ibia-composer">
          <input type="text" placeholder="Digite sua dúvida sobre CNH..." />
          <button type="submit">Enviar</button>
        </form>
      </div>
    `;

    document.body.appendChild(fab);
    document.body.appendChild(widget);

    return { fab, widget };
  }

  function initChat(fab, widget) {
    const messagesEl = widget.querySelector(".ibia-messages");
    const form = widget.querySelector("form");
    const input = widget.querySelector("input");

    let history = [];

    function toggle() {
      widget.classList.toggle("is-open");
      if (widget.classList.contains("is-open")) input.focus();
    }

    fab.addEventListener("click", toggle);

    function addBubble(role, text = "") {
      const div = document.createElement("div");
      div.className = `ibia-bubble ${
        role === "user" ? "ibia-user" : "ibia-assistant"
      }`;
      div.textContent = text;
      messagesEl.appendChild(div);
      messagesEl.scrollTop = messagesEl.scrollHeight;
      return div;
    }

    addBubble(
      "assistant",
      "Olá! Sou a IBIA. Em que posso ajudar com CNH hoje?"
    );

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const msg = input.value.trim();
      if (!msg) return;

      addBubble("user", msg);
      history.push({ role: "user", content: msg });
      input.value = "";

      const assistantBubble = addBubble("assistant", "");

      const resp = await fetch(CONFIG.apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, history }),
      });

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();

      let full = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        full += chunk;
        assistantBubble.textContent += chunk;
        messagesEl.scrollTop = messagesEl.scrollHeight;
      }

      history.push({ role: "assistant", content: full });
    });
  }

 
  injectStyles();
  const { fab, widget } = injectUI();
  initChat(fab, widget);
})();
