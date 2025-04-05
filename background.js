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
    "overleaf.com"
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
    "www.facebook.com"
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
  
  // CHANGE: Load testing settings when extension starts
  chrome.storage.local.get(['inTestingMode'], (data) => {
    inTestingMode = data.inTestingMode || false;
    TIME_BEFORE_SUGGESTION = inTestingMode ? DEFAULT_TEST_TIME : DEFAULT_PROD_TIME;
    console.log("Testing mode:", inTestingMode, "Initial delay:", TIME_BEFORE_SUGGESTION);
  });
  
  // CHANGE: Listen for setting changes
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && changes.inTestingMode) {
      inTestingMode = changes.inTestingMode.newValue;
      TIME_BEFORE_SUGGESTION = inTestingMode ? DEFAULT_TEST_TIME : DEFAULT_PROD_TIME;
      console.log("Testing mode updated:", inTestingMode);
    }
  });
  
  // Listen for tab updates
  chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
      checkSiteType(tab.url, tabId);
    }
  });
  
  // Load saved tab durations when extension starts
  chrome.storage.local.get('tabDurations', function(data) {
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
                console.log(`Time spent on ${hostname}: ${Math.round(tabDurations[lastActiveTab] / 1000)} seconds`);
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
      console.log("Site categorized as:", isProductive ? "productive" : (isUnproductive ? "unproductive" : "neutral"));
      
      // Store the site type
      chrome.storage.local.set({
        currentSiteType: isProductive ? 'productive' : (isUnproductive ? 'unproductive' : 'neutral')
      });
      
      // Set timer to start showing suggestions
      if (isProductive || isUnproductive) {
        timer = setTimeout(() => {
          // FIXED: Check if the tab still exists before sending a message
          chrome.tabs.get(tabId, function(tab) {
            if (chrome.runtime.lastError) {
              console.log("Tab no longer exists:", chrome.runtime.lastError);
              return;
            }
            
            // FIXED: Wrap message sending in try-catch
            try {
              chrome.tabs.sendMessage(tabId, {
                action: 'showSuggestion',
                isProductive: isProductive,
                inTestingMode: inTestingMode
              }, (response) => {
                if (chrome.runtime.lastError) {
                  console.log("Error sending message:", chrome.runtime.lastError.message);
                } else if (response) {
                  console.log("Message received by content script:", response);
                }
              });
            } catch (err) {
              console.error("Error sending message:", err);
            }
          });
        }, TIME_BEFORE_SUGGESTION);
        
        // Log for testing
        console.log(`Will show ${isProductive ? 'unproductive' : 'productive'} suggestion in ${TIME_BEFORE_SUGGESTION/1000} seconds`);
      }
    } catch (err) {
      console.error("Error in checkSiteType:", err);
    }
  }
  
  // Add message listener for getting tab duration data
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === 'getTabDurations') {
        sendResponse({ durations: tabDurations });
    }
    return true;
  });
  