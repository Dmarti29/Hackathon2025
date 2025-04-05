let currentState = null;
let suggestionBox = null;
let dismissTimeout = null;

// CHANGE: Add timing variables for regular and test mode
const REGULAR_DISMISS_TIME = 30000; // 30 seconds
const TEST_DISMISS_TIME = 5000;     // 5 seconds
const REGULAR_NEXT_MIN = 5 * 60 * 1000;    // 5 minutes
const REGULAR_NEXT_MAX = 10 * 60 * 1000;   // 10 minutes
const TEST_NEXT_MIN = 5 * 1000;     // 5 seconds
const TEST_NEXT_MAX = 10 * 1000;    // 10 seconds
let inTestingMode = false;

// Productive site suggestions (suggesting to be unproductive)
const unproductiveSuggestions = [
  "You've been working too hard! Time for a break?",
  "All work and no play makes you dull. How about a quick distraction?",
  "Your brain needs a recharge. Maybe check Reddit?",
  "Productivity is overrated. Want to see what's new on YouTube?",
  "You deserve a break. Why not watch one quick video?",
  "Netflix is calling your name...",
  "Aren't you curious what's happening on social media right now?",
  "Your friends might have posted something interesting on Instagram!",
  "Have you seen the latest viral meme? Worth checking out!",
  "Work will still be there tomorrow. Time to relax!"
];

// Unproductive site suggestions (suggesting to be productive)
const productiveSuggestions = [
  "Shouldn't you be working on something important?",
  "That deadline isn't going to meet itself!",
  "Think about how good it would feel to finish that project!",
  "Your future self will thank you for being productive now.",
  "Just imagine all you could accomplish in the next hour!",
  "That email needs a response. Maybe check your inbox?",
  "Learning something new would be a better use of your time.",
  "Your to-do list isn't getting any shorter!",
  "Success comes from focused work, not endless scrolling.",
  "Your competition is probably being productive right now!"
];

// CHANGE: Helper function to get proper time interval based on testing mode
function getNextSuggestionTime() {
  if (inTestingMode) {
    return TEST_NEXT_MIN + Math.random() * (TEST_NEXT_MAX - TEST_NEXT_MIN);
  } else {
    return REGULAR_NEXT_MIN + Math.random() * (REGULAR_NEXT_MAX - REGULAR_NEXT_MIN);
  }
}

// CHANGE: Helper function to get proper dismiss time based on testing mode
function getDismissTime() {
  return inTestingMode ? TEST_DISMISS_TIME : REGULAR_DISMISS_TIME;
}

// FIXED: Add proper message listener with response
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log("Content script received message:", message);
  
  if (message.action === 'showSuggestion') {
    // Update testing mode flag from background script
    inTestingMode = message.inTestingMode || false;
    showSuggestionBox(message.isProductive);
    
    // FIXED: Send a response to confirm message was received
    sendResponse({ received: true, status: "Showing suggestion" });
    return true; // Indicates we want to send a response asynchronously
  }
  
  // Always send a response even if we don't handle the message
  sendResponse({ received: true, status: "Unknown action" });
  return true;
});

function showSuggestionBox(isProductive) {
  // FIXED: Add logging to debug
  console.log("Showing suggestion box, isProductive:", isProductive);
  
  try {
    // If a suggestion box already exists, remove it
    if (suggestionBox && document.body.contains(suggestionBox)) {
      document.body.removeChild(suggestionBox);
    }
    
    // If a dismiss timeout is set, clear it
    if (dismissTimeout) {
      clearTimeout(dismissTimeout);
    }
    
    // Create new suggestion box
    suggestionBox = document.createElement('div');
    suggestionBox.className = 'productivity-battle-suggestion';
    
    // Choose a random suggestion based on the site type
    const suggestions = isProductive ? unproductiveSuggestions : productiveSuggestions;
    const randomIndex = Math.floor(Math.random() * suggestions.length);
    
    // FIXED: Add site type indicator for debugging
    const siteType = isProductive ? "PRODUCTIVE" : "UNPRODUCTIVE";
    
    // FIXED: Create a container for the text to separate from the site indicator
    const textContainer = document.createElement('div');
    textContainer.className = 'suggestion-text';
    textContainer.textContent = suggestions[randomIndex];
    suggestionBox.appendChild(textContainer);
    
    // FIXED: Add site type indicator just for testing purposes
    const siteIndicator = document.createElement('div');
    siteIndicator.className = 'site-type-indicator';
    siteIndicator.textContent = siteType;
    siteIndicator.style.fontSize = '10px';
    siteIndicator.style.opacity = '0.7';
    siteIndicator.style.marginTop = '5px';
    suggestionBox.appendChild(siteIndicator);
    
    // Create dismiss button
    const dismissButton = document.createElement('button');
    dismissButton.textContent = '×';
    dismissButton.className = 'productivity-battle-dismiss';
    dismissButton.addEventListener('click', () => {
      if (suggestionBox && document.body.contains(suggestionBox)) {
        document.body.removeChild(suggestionBox);
        suggestionBox = null;
      }
    });
    
    suggestionBox.appendChild(dismissButton);
  // FIXED: Ensure body exists and append with error handling
  try {
    if (document.body) {
      document.body.appendChild(suggestionBox);
      
      // Add testing mode indicator
      if (inTestingMode) {
        const testIndicator = document.createElement('div');
        testIndicator.className = 'testing-mode-indicator';
        testIndicator.textContent = 'TESTING MODE';
        suggestionBox.appendChild(testIndicator);
      }
      
      // Get dismiss time based on mode
      const dismissTime = getDismissTime();
      dismissTimeout = setTimeout(() => {
        if (suggestionBox && document.body.contains(suggestionBox)) {
          document.body.removeChild(suggestionBox);
          suggestionBox = null;
        }
      }, dismissTime);
      
      // Get next suggestion time based on mode
      const nextTime = getNextSuggestionTime();
      setTimeout(() => {
        showSuggestionBox(isProductive);
      }, nextTime);
      
      // Log for testing
      console.log(`Suggestion shown (${isProductive ? 'productive site' : 'unproductive site'}). Will dismiss in ${dismissTime/1000}s and show next in ${nextTime/1000}s`);
    } else {
      console.error("Document body not available");
    }
  } catch (err) {
    console.error("Error showing suggestion box:", err);
  }
} catch (err) {
  console.error("Error in showSuggestionBox:", err);
}

}

