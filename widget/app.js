document.addEventListener("DOMContentLoaded", () => {
  const API_URL = "http://127.0.0.1:8000/chat";

  const messagesEl = document.getElementById("messages");
  const form = document.getElementById("chatForm");
  const input = document.getElementById("text");
  const sendBtn = document.getElementById("send");

  let history = [];

  function addBubble(role, text) {
    const div = document.createElement("div");
    div.className = `bubble ${role === "user" ? "user" : "assistant"}`;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }

 
  addBubble(
    "assistant",
    "Olá! Eu sou a IBIA. Em que posso ajudar com CNH hoje?"
  );

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const message = input.value.trim();
    if (!message) return;

 
    addBubble("user", message);
    input.value = "";
    input.focus();

    history.push({ role: "user", content: message });
    sendBtn.disabled = true;

    try {
      const resp = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, history }),
      });

      if (!resp.ok) {
        const t = await resp.text();
        throw new Error(`HTTP ${resp.status}: ${t}`);
      }

 
      const reader = resp.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let reply = "";
      const assistantBubble = addBubble("assistant", "");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        reply += chunk;
        assistantBubble.textContent += chunk;
        messagesEl.scrollTop = messagesEl.scrollHeight;
      }

 
      history.push({ role: "assistant", content: reply });
    } catch (err) {
      addBubble("assistant", `Erro ao chamar a API: ${err.message}`);
    } finally {
      sendBtn.disabled = false;
    }
  });
});
