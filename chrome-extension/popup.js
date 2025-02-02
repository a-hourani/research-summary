document.addEventListener("DOMContentLoaded", () => {
  const arxivUrlInput = document.getElementById("arxivUrl");
  const summarizeBtn = document.getElementById("summarize");
  const apiKeyInput = document.getElementById("apiKey");
  const apiUrlInput = document.getElementById("apiUrl");
  const saveSettingsBtn = document.getElementById("saveSettings");
  const statusText = document.getElementById("status");
  const settingsContainer = document.getElementById("settingsContainer");
  const toggleSettingsBtn = document.getElementById("toggleSettings");
  const loaderContainer = document.getElementById("loaderContainer");
  const timerElement = document.getElementById("timer");

  chrome.storage.local.get(["apiKey", "apiUrl"], (result) => {
    if (result.apiKey) apiKeyInput.value = result.apiKey;
    if (result.apiUrl) apiUrlInput.value = result.apiUrl;
    if (!result.apiKey || !result.apiUrl) {
      settingsContainer.style.display = "block";
    }
  });

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const currentUrl = tabs[0].url;
    if (currentUrl.includes("arxiv.org")) {
      arxivUrlInput.value = currentUrl;
    }
  });

  let startTime;
  let timerInterval;

  const startTimer = () => {
    startTime = Date.now();
    timerInterval = setInterval(updateTimer, 1000);
    loaderContainer.style.display = "block";
    document.getElementById('timer').textContent = '00:00';
  };

  const stopTimer = () => {
    clearInterval(timerInterval);
    loaderContainer.style.display = "none";
  };

  const updateTimer = () => {
    const elapsedTime = Date.now() - startTime;
    const minutes = Math.floor(elapsedTime / 60000);
    const seconds = Math.floor((elapsedTime % 60000) / 1000);
    timerElement.textContent = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  };

  toggleSettingsBtn.addEventListener("click", () => {
    settingsContainer.style.display = settingsContainer.style.display === "none" ? "block" : "none";
  });

  saveSettingsBtn.addEventListener("click", () => {
    chrome.storage.local.set(
      {
        apiKey: apiKeyInput.value,
        apiUrl: apiUrlInput.value,
      },
      () => {
        statusText.textContent = "Settings saved!";
        setTimeout(() => (statusText.textContent = ""), 2000);
        settingsContainer.style.display = "none";
      }
    );
  });

  summarizeBtn.addEventListener("click", async () => {
    const arxivUrl = arxivUrlInput.value;
    try {
      const credentials = await new Promise((resolve, reject) => {
        chrome.storage.local.get(["apiKey", "apiUrl"], (result) => {
          if (!result.apiKey || !result.apiUrl) {
            reject(new Error("Please set API key and endpoint first!"));
          } else {
            resolve(result);
          }
        });
      });

      startTimer();
      summarizeBtn.disabled = true;
      summarizeBtn.textContent = "Generating...";

      const response = await fetch(credentials.apiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": credentials.apiKey,
        },
        body: JSON.stringify({ arxivUrl }),
        mode: "cors",
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(`Error ${response.status}: ${errorData.message || "Unknown error"}`);
      }

      const data = await response.json();
      const requestId = data.request_id;
      if (!requestId) throw new Error("Invalid response: No request_id received.");

      // Poll for the summary result
      const maxAttempts = 24; // 2 minutes, checking every 5 seconds
      let attempts = 0;

      while (attempts < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, 10000));
        const pollResponse = await fetch(credentials.apiUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "x-api-key": credentials.apiKey,
          },
          body: JSON.stringify({ requestId }),
          mode: "cors",
        });

        if (!pollResponse.ok) {
          throw new Error(`Polling error: ${pollResponse.status}`);
        }

        const pollData = await pollResponse.json();
        if (pollData.status === "pending") {
          attempts++;
          continue;
        }

        if (pollData.html) {
          const newWindow = window.open();
          newWindow.document.open();  // Ensure document is ready to write
          newWindow.document.write(pollData.html);
          newWindow.document.close(); // Finalize document writing
          break
        }
      
      }
    } catch (error) {
      console.error("Error details:", error);
      alert(`Failed to summarize: ${error.message}`);
    } finally {
      stopTimer();
      summarizeBtn.disabled = false;
      summarizeBtn.textContent = "Generate Summary";
    }
  });
});
