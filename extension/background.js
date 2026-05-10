chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error(error));

// Optional: Adds a context menu to summarize selected text directly
chrome.runtime.onInstalled.addListener(() => {
  console.log("Extension installed and permissions active.");
});

// Optional: Listen for tab changes to reset state if needed
chrome.tabs.onUpdated.addListener(async (tabId, info, tab) => {
  if (!tab.url) return;
  const url = new URL(tab.url);
  // Keep the side panel enabled on all sites
  await chrome.sidePanel.setOptions({
    tabId,
    path: 'popup.html',
    enabled: true
  });
});