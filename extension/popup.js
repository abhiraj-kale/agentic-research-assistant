document.addEventListener('DOMContentLoaded', () => {
    const topicInput = document.getElementById('topic');
    const output = document.getElementById('output');
    const runBtn = document.getElementById('runBtn');
    const summarizeBtn = document.getElementById('summarizeBtn');

    // --- HELPER: Execute Research Task ---
    async function runTask(payload) {
        runBtn.disabled = true;
        summarizeBtn.disabled = true;
        
        // Clear previous logs and set the initial message
        output.innerText = "⏳ Connecting to AI core...\n";
        output.style.color = "var(--text-gray)";

        try {
            const response = await fetch('http://localhost:8000/research', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Backend error');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = ""; // This is the secret sauce to fix the "doing nothing" bug

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                
                // Split by the double newline that SSE uses to separate messages
                let parts = buffer.split('\n\n');
                
                // Keep the last part in the buffer because it might be incomplete
                buffer = parts.pop();

                for (const part of parts) {
                    const line = part.trim();
                    if (line.startsWith('data: ')) {
                        try {
                            const jsonStr = line.slice(6);
                            const data = JSON.parse(jsonStr);

                            if (data.status === "progress") {
                                output.innerText += `➔ ${data.message}\n`;
                                output.scrollTop = output.scrollHeight; 
                            } else if (data.status === "complete") {
                                output.innerText += "✅ Process complete! Generating PDF...\n";
                                output.scrollTop = output.scrollHeight;
                                await renderPDF(data.content, payload.topic || "Summary");
                            } else if (data.status === "error") {
                                throw new Error(data.message);
                            }
                        } catch (e) {
                            console.error("Error parsing JSON chunk:", e, "Line was:", line);
                            // If parsing fails, we ignore this specific chunk and move on
                        }
                    }
                }
            }
        } catch (error) {
            output.innerText += `\n❌ Error: ${error.message}\n`;
            output.style.color = "#e74c3c";
            output.scrollTop = output.scrollHeight;
        } finally {
            runBtn.disabled = false;
            summarizeBtn.disabled = false;
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