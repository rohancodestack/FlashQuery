
const chatWindow = document.getElementById("chat-window");
const inputField = document.getElementById("user-input");
const historyList = document.querySelector(".history-list");
const headerContainer = document.getElementById("header-container");
const inputRow = document.querySelector(".input-row");
const subtitle = document.querySelector(".subtitle");
const mainHeader = document.querySelector(".main-header");
const BASE_URL = "http://127.0.0.1:8000";

let currentChatId = null;
let chatHistory = JSON.parse(localStorage.getItem("flashquery_history")) || [];
let pdfContext = "";

// ⏎ Shift+Enter = newline | Enter = send
inputField.addEventListener("keydown", function (e) {
  if (e.key === "Enter") {
    if (e.shiftKey) {
      e.preventDefault();
      const start = inputField.selectionStart;
      const end = inputField.selectionEnd;
      inputField.value = inputField.value.substring(0, start) + "\n" + inputField.value.substring(end);
      inputField.selectionStart = inputField.selectionEnd = start + 1;
    } else {
      e.preventDefault();
      handleSend();
    }
  }
});

// ✅ Send Handler
function handleSend() {
  const userText = inputField.value.trim();
  if (!userText) return;

  headerContainer.classList.add("move-to-top");
  chatWindow.classList.add("show");
  inputRow.classList.add("input-slide-down");
  document.querySelector(".chat-wrapper").style.paddingBottom = "120px";

  addMessage("user", userText);
  inputField.value = "";

  const thinking = document.createElement("div");
  thinking.className = "thinking-line";
  thinking.innerHTML = `<div style="text-align:center; font-style:italic; padding: 10px; animation: pulse 1s infinite;">FlashQuery is thinking…</div>`;
  chatWindow.appendChild(thinking);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: userText, context: pdfContext || null })
  })
    .then(res => res.json())
    .then(data => {
      const aiText = data.answer || "Sorry, I couldn't understand that.";
      setTimeout(() => {
        chatWindow.removeChild(thinking);
        addMessage("ai", aiText);
        saveToHistory(currentChatId, userText, aiText);
      }, 400);
    })
    .catch(err => {
      console.error("Error:", err);
      const fallback = "Oops! Something went wrong.";
      setTimeout(() => {
        chatWindow.removeChild(thinking);
        addMessage("ai", fallback);
        saveToHistory(currentChatId, userText, fallback);
      }, 400);
    });
}

function addMessage(role, content) {
  const message = document.createElement("div");
  message.classList.add("message", role);

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");
  bubble.innerText = content;
  message.appendChild(bubble);

  chatWindow.appendChild(message);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  requestAnimationFrame(() => message.classList.add("show"));

  chatHistory.push({ role, content });
  localStorage.setItem("flashquery_history", JSON.stringify(chatHistory));
  updateChatSidebar();
}

function updateChatSidebar() {
  historyList.innerHTML = "";
  const summaries = chatHistory.filter(m => m.role === "user").map(m => m.content.slice(0, 40)).reverse();
  summaries.forEach((summary, index) => {
    const entry = document.createElement("div");
    entry.classList.add("chat-entry");
    entry.innerHTML = `
      <span>${summary}</span>
      <button class="delete-btn" onclick="deleteHistoryPair(${summaries.length - index - 1})">×</button>
    `;
    historyList.appendChild(entry);
  });
}

function deleteHistoryPair(index) {
  chatHistory.splice(index * 2, 2);
  localStorage.setItem("flashquery_history", JSON.stringify(chatHistory));
  updateChatSidebar();
}

function saveToHistory(chatId, userText, aiText) {
  let chats = JSON.parse(localStorage.getItem("flashQueryChats") || "{}");
  if (!chatId) {
    chatId = Date.now().toString();
    currentChatId = chatId;
    chats[chatId] = { title: userText, messages: [] };
  }
  chats[chatId].messages.push({ role: "user", text: userText });
  chats[chatId].messages.push({ role: "ai", text: aiText });
  localStorage.setItem("flashQueryChats", JSON.stringify(chats));
  updateSidebar(chats);
}

function updateSidebar(chats) {
  historyList.innerHTML = "";
  for (const id in chats) addChatToSidebar(id, chats[id].title);
}

function addChatToSidebar(chatId, title) {
  const entry = document.createElement("div");
  entry.className = "chat-entry";
  const textSpan = document.createElement("span");
  textSpan.innerText = title;
  textSpan.style.flex = "1";
  textSpan.style.cursor = "pointer";
  textSpan.onclick = () => loadChat(chatId);

  const deleteBtn = document.createElement("button");
  deleteBtn.innerText = "🗑️";
  deleteBtn.className = "delete-btn";
  deleteBtn.onclick = (e) => {
    e.stopPropagation();
    deleteChat(chatId);
  };

  entry.appendChild(textSpan);
  entry.appendChild(deleteBtn);
  historyList.appendChild(entry);
}

function deleteChat(chatId) {
  let chats = JSON.parse(localStorage.getItem("flashQueryChats") || "{}");
  delete chats[chatId];
  localStorage.setItem("flashQueryChats", JSON.stringify(chats));
  updateSidebar(chats);

  if (chatId === currentChatId) {
    currentChatId = null;
    chatWindow.innerHTML = "";
    headerContainer.classList.remove("move-to-top");
    chatWindow.classList.remove("show");
  }
}

function restoreChats() {
  const chats = JSON.parse(localStorage.getItem("flashQueryChats") || "{}");
  updateSidebar(chats);
}

function loadChat(chatId) {
  chatWindow.innerHTML = "";
  const chats = JSON.parse(localStorage.getItem("flashQueryChats") || "{}");
  const selected = chats[chatId];
  if (!selected) return;

  currentChatId = chatId;
  selected.messages.forEach(msg => addMessage(msg.role, msg.text));
  headerContainer.classList.add("move-to-top");
  chatWindow.classList.add("show");
}

// ✅ Updated summarizeYouTube with dark red YouTube via CSS class
function summarizeYouTube() {
  mainHeader.innerHTML = `Ready to summarize your <span class="youtube-red">YouTube</span> content?`;
  subtitle.innerText = "Summarize in a blink.";
  const url = prompt("📹 Enter the YouTube video URL:");
  if (url) {
    addMessage("user", `Summarize this YouTube video: ${url}`);
    fetch(`${BASE_URL}/youtube`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    })
      .then(res => res.json())
      .then(data => addMessage("ai", data.summary || "Sorry, couldn't summarize."))
      .catch(err => {
        console.error("YT Summary Error:", err);
        addMessage("ai", "⚠️ Failed to summarize the video.");
      });
  }
}

function activateMathMode() {
  mainHeader.innerHTML = `Hi, I'm <span style="color:#38bdf8;">FlashQuery</span>`;
  subtitle.innerText = "Solve in a blink.";
  inputField.focus();
}

function activateDeepResearch() {
  mainHeader.innerHTML = `Hi, I'm <span style="color:#38bdf8;">FlashQuery</span>`;
  subtitle.innerText = "Connect dots in a blink.";
  inputField.focus();
}

// ✅ Init
restoreChats();
updateChatSidebar();