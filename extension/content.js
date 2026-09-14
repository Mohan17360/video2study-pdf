chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "EXTRACT_VIDEO_CONTEXT") {
    try {
      const titleEl = document.querySelector("h1.ytd-watch-metadata yt-formatted-string, h1.title");
      const channelEl = document.querySelector("#channel-name #text, #owner #channel-name a");
      const chapterNodes = document.querySelectorAll(".ytd-macro-markers-list-item-renderer");
      const chapters = Array.from(chapterNodes).map(node => ({
        title: node.querySelector("#details #title")?.textContent?.trim(),
        time: node.querySelector("#time")?.textContent?.trim()
      })).filter(c => c.title && c.time);

      sendResponse({
        success: true,
        data: {
          title: titleEl ? titleEl.textContent.trim() : null,
          channel: channelEl ? channelEl.textContent.trim() : null,
          chapters: chapters
        }
      });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
  }
  return true;
});