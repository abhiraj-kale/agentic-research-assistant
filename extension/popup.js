document.addEventListener('DOMContentLoaded', () => {
    const topicInput = document.getElementById('topic');
    const output = document.getElementById('output');
    const runBtn = document.getElementById('runBtn');
    const summarizeBtn = document.getElementById('summarizeBtn');

    // --- HELPER: Execute Research Task ---
    async function runTask(payload) {
        runBtn.disabled = true;
        summarizeBtn.disabled = true;
        output.innerText = "Connecting to backend...";
        output.style.color = "white";

        try {
            const response = await fetch('http://localhost:8000/research', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                
                // SSE chunks start with "data: "
                const lines = chunk.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.slice(6));

                        if (data.status === "progress") {
                            // Update the UI with the live message
                            output.innerText = data.message; 
                        } else if (data.status === "complete") {
                            renderPDF(data.content, payload.topic || "Summary");
                        } else if (data.status === "error") {
                            throw new Error(data.message);
                        }
                    }
                }
            }
        } catch (error) {
            output.innerText = `❌ Error: ${error.message}`;
            output.style.color = "#e74c3c";
        } finally {
            runBtn.disabled = false;
            summarizeBtn.disabled = false;
            runBtn.innerText = "Start Research";
        }
    }

    // --- MODE 1: Topic Research (Your original logic) ---
    runBtn.addEventListener('click', async () => {
        const topic = topicInput.value;
        if (!topic) {
            output.innerText = "⚠️ Please enter a topic.";
            return;
        }
        await runTask({ topic: topic });
    });

    // --- MODE 2: Summarize Current Page ---
    summarizeBtn.addEventListener('click', async () => {
        output.innerText = "Reading page content...";
        
        try {
            // Get the current active tab
            let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

            // Execute script to get page text
            const results = await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: () => {
                    // This grabs all visible text while ignoring scripts/styles
                    return document.body.innerText;
                },
            });

            const pageText = results[0].result;
            if (!pageText || pageText.length < 50) {
                throw new Error("Page seems to have no readable text.");
            }

            // Send first 8000 characters to prevent LLM context overflow
            await runTask({ 
                textToSummarize: pageText.substring(0, 8000),
                topic: tab.title // Use page title as the PDF name
            });

        } catch (err) {
            output.innerText = `❌ Extraction Failed: ${err.message}`;
            output.style.color = "#e74c3c";
        }
    });

    // --- PDF RENDERING ENGINE ---
    async function renderPDF(content, fileName) {
        output.innerText = "Generating Professional PDF...";
        const element = document.createElement('div');
        
        // Cleanup formatting
        let cleanContent = content.replace(/```[a-zA-Z]*\n?/g, '').replace(/```/g, '');
        cleanContent = cleanContent.replace(/^(#{1,6})\s*(.*)/gm, '\n\n$1 $2\n\n');
        cleanContent = cleanContent.replace(/[â€¢•☑\-]/g, '');

        // Standardize Markdown
        marked.setOptions({ gfm: true, breaks: true });
        const htmlContent = marked.parse(cleanContent);

        element.innerHTML = `
            <div style="font-family: 'Helvetica', sans-serif; padding: 40px; color: #2c3e50; background: white;">
                <style>
                    h1 { color: #1a252f; border-bottom: 2px solid #34495e; padding-bottom: 10px; }
                    h2 { color: #2980b9; margin-top: 30px; border-bottom: 1px solid #ecf0f1; }
                    ol { padding-left: 25px; }
                    li { margin-bottom: 10px; line-height: 1.7; font-size: 14px; }
                    p { line-height: 1.7; font-size: 14px; margin-bottom: 15px; }
                </style>
                <div class="pdf-content">${htmlContent}</div>
            </div>
        `;

        const opt = {
            margin: 0.5,
            filename: `${fileName.replace(/\s+/g, '_')}.pdf`,
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
        };

        await html2pdf().set(opt).from(element).save();
        output.innerText = "✅ Report Downloaded!";
        output.style.color = "#2ecc71";
    }
});

document.getElementById('closeBtn').addEventListener('click', async () => {
    window.close(); 
});