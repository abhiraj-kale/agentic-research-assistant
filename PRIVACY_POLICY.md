# Privacy Policy — AI Research Assistant (Chrome Extension)

**Last updated:** June 23, 2026

This Privacy Policy explains what information the **AI Research Assistant** browser
extension ("the Extension", "we", "us") collects, how it is used, and the choices you
have. By installing and using the Extension you agree to the practices described here.

> **Note for the developer:** the contact name and email below are pre-filled with sensible
> defaults — replace them if you want a different public contact.

---

## 1. Who we are

The Extension is provided by **Abhiraj Kale**.
For any privacy questions or requests, contact us at **abhirajk@uci.edu**.

---

## 2. What the Extension does

The Extension is an AI research assistant that runs in the browser side panel. It offers
two functions:

1. **Research a topic** — you type a topic, and the Extension requests an AI‑generated
   research report. To produce it, the topic is used to search the web.
2. **Summarize this page** — when you click the button, the Extension reads the text of
   the page you are currently viewing and requests an AI‑generated summary.

In both cases the Extension generates a report and downloads it to your device as a PDF.
The PDF is created **locally on your device**; the file itself is not uploaded anywhere.

---

## 3. Information we collect and process

The Extension only processes data you actively provide by using one of the two functions
above. Specifically:

| Data | When it is collected | Why |
|------|----------------------|-----|
| **Research topic / query text** | When you type a topic and start research | To research the topic and generate a report |
| **Active web page content** | **Only** when you click "Summarize This Page" — the visible text of the current tab (up to the first 8,000 characters) and the tab's title | To generate a summary of that page |

The Extension does **not** collect:

- Your name, email address, or account credentials (the Extension has no login).
- Browsing history, or the content of pages you did **not** explicitly ask to summarize.
- Cookies, advertising identifiers, or analytics/telemetry.
- Keystrokes, form data, passwords, or financial information.

The Extension does not use Chrome `storage` and does not persist your data locally between
sessions.

---

## 4. How your data is processed and shared

When you use either function, the relevant text (your topic, or the page content you chose
to summarize) is sent over an encrypted HTTPS connection to our backend service at
`https://agentic-research-assistant-yoh8.onrender.com` for the sole purpose of generating
the report you requested. Our backend is hosted on **Render (render.com)**.

To produce the report, our backend submits that text to third‑party AI and search providers:

- **Google (Gemini API)** — AI language model used to analyze and write the report.
- **Mistral AI** and **Groq (Llama models)** — additional AI language model providers used
  as automatic fallbacks if the primary model is unavailable.
- **Tavily** — a web‑search API used **only for topic research** (not for page
  summarization) to find relevant sources for your topic.

Each of these providers processes the submitted text under its own privacy and data‑use
terms. We do **not**:

- Sell or rent your data to anyone.
- Use your data for advertising or to build user profiles.
- Share your data with any party other than the service providers listed above, except as
  required by law.

---

## 5. Data retention

We do **not** save the text you submit to a database or any persistent storage. It is held
in memory only for the time needed to generate your report, and is discarded when the
request completes. Our server may record technical error messages in operational logs for
debugging, which can incidentally include short fragments of a failed request; these logs
are not used for any other purpose.

The third‑party AI and search providers listed in Section 4 receive the submitted text and
retain it according to their own policies, over which we have no control.

---

## 6. Permissions and why we request them

| Permission | Reason |
|------------|--------|
| `sidePanel` | To display the Extension's interface in the browser side panel. |
| `activeTab` + `scripting` | To read the text of the current tab **only when you click "Summarize This Page."** No script runs on, and no content is read from, pages you do not ask to summarize. |
| Host access to `agentic-research-assistant-yoh8.onrender.com` | To send your request to, and receive the report from, our backend service. |

The Extension does not request access to all websites and does not read page content in the
background.

---

## 7. Your choices and rights

- You control when any data leaves your device — nothing is sent unless you start a research
  task or click "Summarize This Page."
- You can stop all data processing at any time by removing the Extension from
  `chrome://extensions`.
- To ask questions about, or request deletion of, any data associated with you, contact us
  at **abhirajk@uci.edu**.

---

## 8. Children's privacy

The Extension is not directed to children under 13 and we do not knowingly collect data from
children.

---

## 9. Security

Data in transit between the Extension, our backend, and our AI provider(s) is protected using
HTTPS/TLS. No method of transmission or storage is completely secure, and we cannot guarantee
absolute security.

---

## 10. Changes to this policy

We may update this Privacy Policy from time to time. Material changes will be reflected by
updating the "Last updated" date above and, where appropriate, the Extension's store listing.

---

## 11. Limited Use disclosure (Chrome Web Store)

Our use of information received from the Extension adheres to the
[Chrome Web Store User Data Policy](https://developer.chrome.com/docs/webstore/program-policies/user-data-faq/),
including the **Limited Use** requirements. We only use the data you submit to provide the
user‑facing feature that requested it, and we do not transfer or use it for any unrelated
purpose, for advertising, for creditworthiness, or for sale.

---

## 12. Contact

**Abhiraj Kale**
Email: **abhirajk@uci.edu**
