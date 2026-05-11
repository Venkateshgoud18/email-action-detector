const emailInput = document.querySelector("#emailInput");
const analyzeButton = document.querySelector("#analyzeButton");
const sampleButton = document.querySelector("#sampleButton");
const modeBadge = document.querySelector("#modeBadge");
const modelBadge = document.querySelector("#modelBadge");
const priority = document.querySelector("#priority");
const category = document.querySelector("#category");
const summary = document.querySelector("#summary");
const deadlines = document.querySelector("#deadlines");
const actionItems = document.querySelector("#actionItems");
const reply = document.querySelector("#reply");

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

async function analyzeEmail() {
  const email = emailInput.value.trim();

  if (!email) {
    renderError("Paste an email before analyzing.");
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
      },
      body: JSON.stringify({ email }),
    });

    const result = await response.json();
    if (!response.ok || result.error) {
      throw new Error(result.error || "Request failed.");
    }

    renderResult(result);
  } catch (error) {
    renderError(error.message);
  } finally {
    analyzeButton.disabled = false;
    analyzeButton.textContent = "Analyze Email";
  }
}

sampleButton.addEventListener("click", () => {
  emailInput.value = sampleEmail;
});

analyzeButton.addEventListener("click", analyzeEmail);

emailInput.value = sampleEmail;
