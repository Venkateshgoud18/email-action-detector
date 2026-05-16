const emailInput = document.querySelector("#emailInput");
const analyzeButton = document.querySelector("#analyzeButton");
const sampleButton = document.querySelector("#sampleButton");
const loginForm = document.querySelector("#loginForm");
const registerBtn = document.querySelector("#registerBtn");
const authPanel = document.querySelector("#authPanel");
const sessionBar = document.querySelector("#sessionBar");
const workspace = document.querySelector(".workspace");
const sessionText = document.querySelector("#sessionText");
const logoutButton = document.querySelector("#logoutButton");
const usernameInput = document.querySelector("#usernameInput");
const passwordInput = document.querySelector("#passwordInput");
const modeBadge = document.querySelector("#modeBadge");
const modelBadge = document.querySelector("#modelBadge");
const priority = document.querySelector("#priority");
const category = document.querySelector("#category");
const summary = document.querySelector("#summary");
const deadlines = document.querySelector("#deadlines");
const actionItems = document.querySelector("#actionItems");
const reply = document.querySelector("#reply");
const TOKEN_STORAGE_KEY = "ai_email_triage_jwt";
const USER_STORAGE_KEY = "ai_email_triage_user";

const sampleEmail = `Subject: Dashboard access needed before client meeting

Hi IT team,

I cannot access the sales analytics dashboard, and I need the latest regional report for a client meeting tomorrow at 10 AM.

Could you please check whether my account permission is pending or blocked? If manager approval is required, please let me know who should approve it.

Please confirm the access status by 5 PM today.

Thanks,
Ananya`;

function renderList(element, values) {
  element.replaceChildren();

  if (!values || values.length === 0) {
    const item = document.createElement("li");
    item.textContent = "None found";
    element.append(item);
    return;
  }

  values.forEach((value) => {
    const item = document.createElement("li");
    item.textContent = value;
    element.append(item);
  });
}

function renderResult(result) {
  modeBadge.textContent = result.mode || "OpenAI GPT";
  modelBadge.textContent = result.model || "gpt-4o-mini";
  priority.textContent = result.priority || "-";
  category.textContent = result.category || "-";
  summary.textContent = result.summary || "No summary returned.";
  reply.textContent = result.suggested_reply || "No reply returned.";
  summary.classList.remove("error");

  renderList(deadlines, result.deadlines);
  renderList(actionItems, result.action_items);
}

function renderError(message) {
  modeBadge.textContent = "Error";
  priority.textContent = "-";
  category.textContent = "-";
  summary.textContent = message;
  summary.classList.add("error");
  reply.textContent = "Fix the issue and try again.";
  renderList(deadlines, []);
  renderList(actionItems, []);
}

function getToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

function setSession(token, username) {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
  localStorage.setItem(USER_STORAGE_KEY, username);
  renderSession();
}

function clearSession() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
  renderSession();
}

function renderSession() {
  const token = getToken();
  const username = localStorage.getItem(USER_STORAGE_KEY);
  const isLoggedIn = Boolean(token);

  authPanel.classList.toggle("hidden", isLoggedIn);
  sessionBar.classList.toggle("hidden", !isLoggedIn);
  workspace.classList.toggle("hidden", !isLoggedIn);
  analyzeButton.disabled = !isLoggedIn;
  sessionText.textContent = isLoggedIn ? `Logged in as ${username}` : "Not logged in";

  if (!isLoggedIn) {
    modeBadge.textContent = "Login required";
  }
}

async function login(event) {
  event.preventDefault();
  modeBadge.textContent = "Logging in";

  try {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: usernameInput.value.trim(),
        password: passwordInput.value,
      }),
    });

    const result = await response.json();
    if (!response.ok || result.error) {
      throw new Error(result.error || "Login failed.");
    }

    setSession(result.token, result.username);
    modeBadge.textContent = "Authenticated";
  } catch (error) {
    clearSession();
    renderError(error.message);
  }
}

async function register(event) {
  event.preventDefault();
  modeBadge.textContent = "Registering";

  try {
    const response = await fetch("/api/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username: usernameInput.value.trim(),
        password: passwordInput.value,
      }),
    });

    const result = await response.json();
    if (!response.ok || result.error) {
      throw new Error(result.error || "Registration failed.");
    }

    setSession(result.token, result.username);
    modeBadge.textContent = "Registered & Authenticated";
  } catch (error) {
    clearSession();
    renderError(error.message);
  }
}

async function analyzeEmail() {
  const email = emailInput.value.trim();
  const token = getToken();

  if (!email) {
    renderError("Paste an email before analyzing.");
    return;
  }

  if (!token) {
    renderError("Please log in before analyzing emails.");
    return;
  }

  analyzeButton.disabled = true;
  analyzeButton.textContent = "Analyzing with GPT...";
  modeBadge.textContent = "Calling GPT";

  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({ email }),
    });

    const result = await response.json();
    if (!response.ok || result.error) {
      throw new Error(result.error || "Request failed.");
    }

    renderResult(result);
  } catch (error) {
    if (error.message.toLowerCase().includes("token") || error.message.toLowerCase().includes("authorization")) {
      clearSession();
    }
    renderError(error.message);
  } finally {
    analyzeButton.disabled = !getToken();
    analyzeButton.textContent = "Analyze Email";
  }
}

sampleButton.addEventListener("click", () => {
  emailInput.value = sampleEmail;
});

loginForm.addEventListener("submit", login);
registerBtn.addEventListener("click", register);
logoutButton.addEventListener("click", clearSession);
analyzeButton.addEventListener("click", analyzeEmail);

emailInput.value = sampleEmail;
renderSession();
