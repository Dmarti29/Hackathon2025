// background.js
const productiveSites = [
    "docs.google.com",
    "github.com",
    "stackoverflow.com",
    "linkedin.com",
    "notion.so",
    "trello.com",
    "asana.com",
    "jira.com",
    "slack.com",
    "kaggle.com",
    "coursera.org",
    "udemy.com",
    "edx.org",
    "overleaf.com",
];

const unproductiveSites = [
    "youtube.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "reddit.com",
    "netflix.com",
    "tiktok.com",
    "twitch.tv",
    "pinterest.com",
    "buzzfeed.com",
    "9gag.com",
    "theonion.com",
    "fb.com",
    "m.facebook.com",
    "www.facebook.com",
];

// Initialize the timer variables
let timer = null;
// CHANGE: Define default times and add testing mode variables
const DEFAULT_PROD_TIME = 2 * 60 * 1000; // 2 minutes in milliseconds
const DEFAULT_TEST_TIME = 5 * 1000; // 5 seconds for testing
let TIME_BEFORE_SUGGESTION = DEFAULT_PROD_TIME;
let inTestingMode = false;

// Add tab duration tracking
let tabDurations = {};
let lastActiveTab = null;
let lastActiveTime = null;

// Add productivity variable
let productivity = 95; // Default value

// CHANGE: Load testing settings when extension starts
chrome.storage.local.get(["inTestingMode"], (data) => {
    inTestingMode = data.inTestingMode || false;
    TIME_BEFORE_SUGGESTION = inTestingMode
        ? DEFAULT_TEST_TIME
        : DEFAULT_PROD_TIME;
    console.log(
        "Testing mode:",
        inTestingMode,
        "Initial delay:",
        TIME_BEFORE_SUGGESTION
    );
});

// CHANGE: Listen for setting changes
chrome.storage.onChanged.addListener((changes, area) => {
    if (area === "local" && changes.inTestingMode) {
        inTestingMode = changes.inTestingMode.newValue;
        TIME_BEFORE_SUGGESTION = inTestingMode
            ? DEFAULT_TEST_TIME
            : DEFAULT_PROD_TIME;
        console.log("Testing mode updated:", inTestingMode);
    }
});

// Listen for tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete" && tab.url) {
        checkSiteType(tab.url, tabId);
    }
});

// Load saved tab durations when extension starts
chrome.storage.local.get("tabDurations", function (data) {
    if (data.tabDurations) {
        tabDurations = data.tabDurations;
    }
});

// Track tab activation time
chrome.tabs.onActivated.addListener((activeInfo) => {
    const currentTime = Date.now();

    // If there was a previously active tab, update its duration
    if (lastActiveTab && lastActiveTime) {
        const duration = currentTime - lastActiveTime;
        if (!tabDurations[lastActiveTab]) {
            tabDurations[lastActiveTab] = 0;
        }
        tabDurations[lastActiveTab] += duration;

        // Save updated durations
        chrome.storage.local.set({ tabDurations: tabDurations });

        // Log the duration for the previous tab
        chrome.tabs.get(lastActiveTab, (tab) => {
            if (tab && tab.url) {
                const hostname = new URL(tab.url).hostname;
                console.log(
                    `Time spent on ${hostname}: ${Math.round(
                        tabDurations[lastActiveTab] / 1000
                    )} seconds`
                );
            }
        });
    }

    // Update the current active tab
    lastActiveTab = activeInfo.tabId;
    lastActiveTime = currentTime;

    chrome.tabs.get(activeInfo.tabId, (tab) => {
        if (chrome.runtime.lastError) {
            console.error("Error getting tab:", chrome.runtime.lastError);
            return;
        }

        if (tab && tab.url) {
            checkSiteType(tab.url, tab.id);
        } else {
            console.log("Tab activated but no URL available yet");
        }
    });
});

// Also track when tabs are closed to ensure we don't lose data
chrome.tabs.onRemoved.addListener((tabId) => {
    if (tabId === lastActiveTab) {
        lastActiveTab = null;
        lastActiveTime = null;
    }
    // Remove the tab's duration data when the tab is closed
    delete tabDurations[tabId];
    chrome.storage.local.set({ tabDurations: tabDurations });
});

// Add a function to get tab duration data
function getTabDurations() {
    return tabDurations;
}

function checkSiteType(url, tabId) {
    // Reset the timer whenever we navigate
    if (timer) {
        clearTimeout(timer);
    }

    try {
        const hostname = new URL(url).hostname;

        let isProductive = false;
        let isUnproductive = false;

        // FIXED: Debug log the hostname we're checking
        console.log("Checking site:", hostname);

        // Check if the site is in our productive or unproductive lists
        for (const site of productiveSites) {
            if (hostname.includes(site)) {
                isProductive = true;
                console.log("Matched productive site:", site);
                break;
            }
        }

        if (!isProductive) {
            for (const site of unproductiveSites) {
                if (hostname.includes(site)) {
                    isUnproductive = true;
                    console.log("Matched unproductive site:", site);
                    break;
                }
            }
        }

        // FIXED: Debug log the site type
        console.log(
            "Site categorized as:",
            isProductive
                ? "productive"
                : isUnproductive
                ? "unproductive"
                : "neutral"
        );

        // Store the site type
        chrome.storage.local.set({
            currentSiteType: isProductive
                ? "productive"
                : isUnproductive
                ? "unproductive"
                : "neutral",
        });

        // Set timer to start showing suggestions
        if (isProductive || isUnproductive) {
            timer = setTimeout(() => {
                // FIXED: Check if the tab still exists before sending a message
                chrome.tabs.get(tabId, function (tab) {
                    if (chrome.runtime.lastError) {
                        console.log(
                            "Tab no longer exists:",
                            chrome.runtime.lastError
                        );
                        return;
                    }

                    // FIXED: Wrap message sending in try-catch
                    try {
                        // Update productivity based on site type
                        updateProductivity(isProductive);

                        chrome.tabs.sendMessage(
                            tabId,
                            {
                                action: "showSuggestion",
                                isProductive: isProductive,
                                inTestingMode: inTestingMode,
                                productiveScale: productivity,
                            },
                            (response) => {
                                if (chrome.runtime.lastError) {
                                    console.log(
                                        "Error sending message:",
                                        chrome.runtime.lastError.message
                                    );
                                } else if (response) {
                                    console.log(
                                        "Message received by content script:",
                                        response
                                    );
                                }
                            }
                        );
                    } catch (err) {
                        console.error("Error sending message:", err);
                    }
                });
            }, TIME_BEFORE_SUGGESTION);

            // Log for testing
            console.log(
                `Will show ${
                    isProductive ? "unproductive" : "productive"
                } suggestion in ${TIME_BEFORE_SUGGESTION / 1000} seconds`
            );
        }
    } catch (err) {
        console.error("Error in checkSiteType:", err);
    }
}

// Add message listener for getting tab duration data
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "getTabDurations") {
        sendResponse({ durations: tabDurations });
    }
    return true;
});

// new methods!!

// COCA: This function opens multiple URLs as tabs in the browser. Delete when no longer needed.
/**
 * Opens multiple URLs as tabs in the current browser window
 * @param {Array<string>} urls - Array of URLs to open as tabs
 * @param {boolean} active - Whether to make the first new tab active (focused)
 * @return {Promise<Array>} Promise resolving to an array of created tab objects
 */
function openMultipleUrls(urls, active = false) {
    return new Promise((resolve, reject) => {
        if (!urls || !Array.isArray(urls) || urls.length === 0) {
            console.error("Invalid URLs provided to openMultipleUrls");
            reject(new Error("Invalid URLs provided"));
            return;
        }

        console.log(`Opening ${urls.length} tabs with URLs:`, urls);

        // Get the current window to open tabs in
        chrome.windows.getCurrent((currentWindow) => {
            if (chrome.runtime.lastError) {
                console.error(
                    "Error getting current window:",
                    chrome.runtime.lastError
                );
                reject(chrome.runtime.lastError);
                return;
            }

            const createdTabs = [];
            let tabsToCreate = urls.length;
            let tabsCreated = 0;

            // Create each tab sequentially
            urls.forEach((url, index) => {
                try {
                    // Ensure URL has a protocol
                    if (
                        !url.startsWith("http://") &&
                        !url.startsWith("https://")
                    ) {
                        url = "https://" + url;
                    }

                    // Create a new tab with the URL
                    chrome.tabs.create(
                        {
                            url: url,
                            active: active && index === 0, // Only make the first tab active if requested
                            windowId: currentWindow.id,
                        },
                        (tab) => {
                            if (chrome.runtime.lastError) {
                                console.error(
                                    `Error creating tab for ${url}:`,
                                    chrome.runtime.lastError
                                );
                                tabsToCreate--;

                                // If we've processed all tabs (even with errors), resolve
                                if (tabsCreated === tabsToCreate) {
                                    resolve(createdTabs);
                                }

                                return;
                            }

                            console.log(
                                `Created tab with URL: ${url}, tab ID: ${tab.id}`
                            );
                            createdTabs.push(tab);
                            tabsCreated++;

                            // If we've created all tabs, resolve the promise
                            if (tabsCreated === tabsToCreate) {
                                resolve(createdTabs);
                            }
                        }
                    );
                } catch (err) {
                    console.error(`Error creating tab for ${url}:`, err);
                    tabsToCreate--;

                    // If we've processed all tabs (even with errors), resolve
                    if (tabsCreated === tabsToCreate) {
                        resolve(createdTabs);
                    }
                }
            });
        });
    });
}

// COCA: Test function to open 5 predefined URLs. Delete when no longer needed.
/**
 * Example function to open 5 test URLs
 * In the future, this will fetch URLs from a backend
 */
function openTestUrls() {
    const testUrls = [
        "google.com",
        "github.com",
        "stackoverflow.com",
        "mozilla.org",
        "developer.chrome.com",
    ];

    return openMultipleUrls(testUrls, true);
}

// COCA: Message handler for URL opening functionality. Modify as needed when removing COCA-marked functions.
// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "openUrls") {
        // If URLs are provided in the message, use those
        if (message.urls && Array.isArray(message.urls)) {
            openMultipleUrls(message.urls, message.makeFirstTabActive)
                .then((tabs) => {
                    sendResponse({ success: true, tabs: tabs });
                })
                .catch((error) => {
                    sendResponse({ success: false, error: error.message });
                });
            return true; // Keep message channel open for async response
        }
        // Otherwise use test URLs
        else {
            openTestUrls()
                .then((tabs) => {
                    sendResponse({ success: true, tabs: tabs });
                })
                .catch((error) => {
                    sendResponse({ success: false, error: error.message });
                });
            return true; // Keep message channel open for async response
        }
    }
});

// Function to update productivity based on user behavior
function updateProductivity(isProductive) {
    if (isProductive) {
        productivity = Math.min(100, productivity + 5);
    } else {
        productivity = Math.max(0, productivity - 5);
    }
    console.log("Productivity updated:", productivity);
}
