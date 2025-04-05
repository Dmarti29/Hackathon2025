let currentState = null;
let suggestionBox = null;
let dismissTimeout = null;

// CHANGE: Add timing variables for regular and test mode
const REGULAR_DISMISS_TIME = 30000; // 30 seconds
const TEST_DISMISS_TIME = 5000; // 5 seconds
const REGULAR_NEXT_MIN = 5 * 60 * 1000; // 5 minutes
const REGULAR_NEXT_MAX = 10 * 60 * 1000; // 10 minutes
const TEST_NEXT_MIN = 5 * 1000; // 5 seconds
const TEST_NEXT_MAX = 10 * 1000; // 10 seconds
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
    "Work will still be there tomorrow. Time to relax!",
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
    "Your competition is probably being productive right now!",
];

// CHANGE: Helper function to get proper time interval based on testing mode
function getNextSuggestionTime() {
    if (inTestingMode) {
        return TEST_NEXT_MIN + Math.random() * (TEST_NEXT_MAX - TEST_NEXT_MIN);
    } else {
        return (
            REGULAR_NEXT_MIN +
            Math.random() * (REGULAR_NEXT_MAX - REGULAR_NEXT_MIN)
        );
    }
}

// CHANGE: Helper function to get proper dismiss time based on testing mode
function getDismissTime() {
    return inTestingMode ? TEST_DISMISS_TIME : REGULAR_DISMISS_TIME;
}

// FIXED: Add proper message listener with response
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log("Content script received message:", message);

    if (message.action === "showSuggestion") {
        // Update testing mode flag from background script
        inTestingMode = message.inTestingMode || false;
        showSuggestionBox(message.isProductive);

        // FIXED: Send a response to confirm message was received
        sendResponse({ received: true, status: "Showing suggestion" });
        return true; // Indicates we want to send a response asynchronously
    }

    if (message.action === "injectAnchors") {
        injectQuickLinks();
        sendResponse({ received: true, status: "Anchors injected" });
        return true;
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
        suggestionBox = document.createElement("div");
        suggestionBox.className = "productivity-battle-suggestion";

        // Choose a random suggestion based on the site type
        const suggestions = isProductive
            ? unproductiveSuggestions
            : productiveSuggestions;
        const randomIndex = Math.floor(Math.random() * suggestions.length);

        // FIXED: Add site type indicator for debugging
        const siteType = isProductive ? "PRODUCTIVE" : "UNPRODUCTIVE";

        // FIXED: Create a container for the text to separate from the site indicator
        const textContainer = document.createElement("div");
        textContainer.className = "suggestion-text";
        textContainer.textContent = suggestions[randomIndex];
        suggestionBox.appendChild(textContainer);

        // FIXED: Add site type indicator just for testing purposes
        const siteIndicator = document.createElement("div");
        siteIndicator.className = "site-type-indicator";
        siteIndicator.textContent = siteType;
        siteIndicator.style.fontSize = "10px";
        siteIndicator.style.opacity = "0.7";
        siteIndicator.style.marginTop = "5px";
        suggestionBox.appendChild(siteIndicator);

        // Create dismiss button
        const dismissButton = document.createElement("button");
        dismissButton.textContent = "×";
        dismissButton.className = "productivity-battle-dismiss";
        dismissButton.addEventListener("click", () => {
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
                    const testIndicator = document.createElement("div");
                    testIndicator.className = "testing-mode-indicator";
                    testIndicator.textContent = "TESTING MODE";
                    suggestionBox.appendChild(testIndicator);
                }

                // Get dismiss time based on mode
                const dismissTime = getDismissTime();
                dismissTimeout = setTimeout(() => {
                    if (
                        suggestionBox &&
                        document.body.contains(suggestionBox)
                    ) {
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
                console.log(
                    `Suggestion shown (${
                        isProductive ? "productive site" : "unproductive site"
                    }). Will dismiss in ${
                        dismissTime / 1000
                    }s and show next in ${nextTime / 1000}s`
                );
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

// Add function to inject quick links
function injectQuickLinks() {
    console.log("Starting link injection...");

    const quickLinks = [
        { text: "Google", url: "https://www.google.com" },
        { text: "GitHub", url: "https://github.com" },
        { text: "Stack Overflow", url: "https://stackoverflow.com" },
        { text: "YouTube", url: "https://www.youtube.com" },
        { text: "Reddit", url: "https://www.reddit.com" },
    ];

    // Add YouTube Shorts videos
    const youtubeShorts = [
        { id: "zZ7AimPACzc", title: "Subway Surfers" },
        { id: "M5V_IXMewl4", title: "stickbug" },
        { id: "zea0Z3xOVs8", title: "Petercopter" },
        { id: "dcU-5Kh91eA", title: "Minecraft Movie" },
    ];

    // Detect the current website
    const isLinkedIn = window.location.hostname.includes("linkedin.com");
    const isWikipedia = window.location.hostname.includes("wikipedia.org");

    console.log(
        "Current website:",
        isLinkedIn ? "LinkedIn" : isWikipedia ? "Wikipedia" : "Other"
    );

    // Find article content based on the website
    let articleContent;
    let paragraphs;

    if (isLinkedIn) {
        // LinkedIn specific selectors
        articleContent =
            document.querySelector(".feed-shared-update-v2") ||
            document.querySelector(".feed-shared-text") ||
            document.querySelector(".feed-shared-text-view") ||
            document.querySelector(".feed-shared-article") ||
            document.querySelector(".feed-shared-external-video") ||
            document.querySelector(".feed-shared-document") ||
            document.querySelector(".feed-shared-poll") ||
            document.querySelector(
                ".feed-shared-article__description-container"
            ) ||
            document.querySelector(".feed-shared-text-view__text-container") ||
            document.body;

        // LinkedIn has different paragraph structure
        paragraphs = articleContent.querySelectorAll(
            ".feed-shared-text-view__text-container, .feed-shared-article__description-container, .feed-shared-text"
        );

        // If no paragraphs found, try to find feed items
        if (paragraphs.length === 0) {
            paragraphs = document.querySelectorAll(".feed-shared-update-v2");
        }
    } else if (isWikipedia) {
        // Wikipedia specific selector
        articleContent = document.querySelector("#mw-content-text");
        if (!articleContent) {
            console.log(
                "Wikipedia content not found, trying fallback selectors..."
            );
            articleContent =
                document.querySelector("article") ||
                document.querySelector("main") ||
                document.querySelector(".content") ||
                document.querySelector("#content") ||
                document.body;
        }

        // Find paragraphs in Wikipedia
        paragraphs = articleContent.querySelectorAll("p");
    } else {
        // Generic selectors for other websites
        articleContent =
            document.querySelector("article") ||
            document.querySelector("main") ||
            document.querySelector(".content") ||
            document.querySelector("#content") ||
            document.body;

        paragraphs = articleContent.querySelectorAll("p");
    }

    console.log("Found article content:", articleContent);
    console.log("Found paragraphs:", paragraphs.length);

    if (paragraphs.length > 0) {
        // Insert links after random paragraphs
        const numLinksToInsert = Math.min(5, paragraphs.length); // Increased to 5 links
        const usedIndices = new Set();

        for (let i = 0; i < numLinksToInsert; i++) {
            // Find a random paragraph index that hasn't been used
            let randomIndex;
            do {
                randomIndex = Math.floor(Math.random() * paragraphs.length);
            } while (usedIndices.has(randomIndex));

            usedIndices.add(randomIndex);
            console.log("Inserting link after paragraph:", randomIndex);

            // Create link container
            const linkContainer = document.createElement("div");
            linkContainer.className = "injected-quick-link";
            linkContainer.style.cssText = `
        margin: 15px 0;
        padding: 12px 20px;
        background-color: #fff;
        border-radius: 8px;
        border: 2px solid #ff0000;
        display: inline-block;
        animation: fadeIn 0.5s ease-in;
        box-shadow: 0 4px 8px rgba(255, 0, 0, 0.2);
        z-index: 9999;
        position: relative;
      `;

            // Create arrow pointing to the link/video
            const arrow = document.createElement("div");
            arrow.className = "injected-arrow";
            arrow.style.cssText = `
        position: absolute;
        width: 0;
        height: 0;
        border-style: solid;
        border-width: 0 20px 40px 20px;
        border-color: transparent transparent #ff0000 transparent;
        bottom: -50px;
        left: 50%;
        transform: translateX(-50%);
        animation: bounce 1s infinite;
        z-index: 10000;
      `;

            // Create arrow line
            const arrowLine = document.createElement("div");
            arrowLine.className = "injected-arrow-line";
            arrowLine.style.cssText = `
        position: absolute;
        width: 4px;
        height: 30px;
        background-color: #ff0000;
        bottom: -80px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 10000;
      `;

            // Add arrow and line to container
            linkContainer.appendChild(arrow);
            linkContainer.appendChild(arrowLine);

            // Randomly decide whether to show a link or a video
            const showVideo = Math.random() < 0.4; // 40% chance of showing a video

            if (showVideo) {
                // Create embedded YouTube video
                const randomVideo =
                    youtubeShorts[
                        Math.floor(Math.random() * youtubeShorts.length)
                    ];
                const iframe = document.createElement("iframe");
                iframe.src = `https://www.youtube.com/embed/${randomVideo.id}?autoplay=0&controls=1&modestbranding=1&rel=0&enablejsapi=1&playsinline=1&mute=0`;
                iframe.title = randomVideo.title;
                iframe.width = "315";
                iframe.height = "560";
                iframe.style.cssText = `
          border: none;
          border-radius: 8px;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
          max-width: 100%;
        `;
                iframe.allow =
                    "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
                iframe.allowFullscreen = true;

                // Add a data attribute to store the video ID for later use
                iframe.dataset.videoId = randomVideo.id;

                // Add a class to identify this as a video iframe
                iframe.classList.add("injected-video-iframe");

                linkContainer.appendChild(iframe);
            } else {
                // Create random link
                const randomLink =
                    quickLinks[Math.floor(Math.random() * quickLinks.length)];
                const anchor = document.createElement("a");
                anchor.href = randomLink.url;
                anchor.textContent = randomLink.text;
                anchor.target = "_blank";
                anchor.style.cssText = `
          color: #ff0000;
          text-decoration: none;
          font-weight: bold;
          transition: all 0.2s ease;
          font-size: 24px;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        `;

                anchor.addEventListener("mouseover", () => {
                    anchor.style.color = "#cc0000";
                    linkContainer.style.backgroundColor = "#fff5f5";
                    linkContainer.style.transform = "scale(1.1)";
                    linkContainer.style.boxShadow =
                        "0 6px 12px rgba(255, 0, 0, 0.3)";
                });

                anchor.addEventListener("mouseout", () => {
                    anchor.style.color = "#ff0000";
                    linkContainer.style.backgroundColor = "#fff";
                    linkContainer.style.transform = "scale(1)";
                    linkContainer.style.boxShadow =
                        "0 4px 8px rgba(255, 0, 0, 0.2)";
                });

                linkContainer.appendChild(anchor);
            }

            // Insert after the paragraph
            paragraphs[randomIndex].parentNode.insertBefore(
                linkContainer,
                paragraphs[randomIndex].nextSibling
            );
        }
    } else {
        console.log("No paragraphs found, using fallback insertion");
        // Fallback: If no paragraphs found, insert at the beginning
        const linkContainer = document.createElement("div");
        linkContainer.className = "injected-quick-link";
        linkContainer.style.cssText = `
      margin: 15px 0;
      padding: 12px 20px;
      background-color: #fff;
      border-radius: 8px;
      border: 2px solid #ff0000;
      display: inline-block;
      animation: fadeIn 0.5s ease-in;
      box-shadow: 0 4px 8px rgba(255, 0, 0, 0.2);
      z-index: 9999;
      position: relative;
    `;

        // Create arrow pointing to the link/video
        const arrow = document.createElement("div");
        arrow.className = "injected-arrow";
        arrow.style.cssText = `
      position: absolute;
      width: 0;
      height: 0;
      border-style: solid;
      border-width: 0 20px 40px 20px;
      border-color: transparent transparent #ff0000 transparent;
      bottom: -50px;
      left: 50%;
      transform: translateX(-50%);
      animation: bounce 1s infinite;
      z-index: 10000;
    `;

        // Create arrow line
        const arrowLine = document.createElement("div");
        arrowLine.className = "injected-arrow-line";
        arrowLine.style.cssText = `
      position: absolute;
      width: 4px;
      height: 30px;
      background-color: #ff0000;
      bottom: -80px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 10000;
    `;

        // Add arrow and line to container
        linkContainer.appendChild(arrow);
        linkContainer.appendChild(arrowLine);

        // Randomly decide whether to show a link or a video
        const showVideo = Math.random() < 0.4; // 40% chance of showing a video

        if (showVideo) {
            // Create embedded YouTube video
            const randomVideo =
                youtubeShorts[Math.floor(Math.random() * youtubeShorts.length)];
            const iframe = document.createElement("iframe");
            iframe.src = `https://www.youtube.com/embed/${randomVideo.id}?autoplay=0&controls=1&modestbranding=1&rel=0&enablejsapi=1&playsinline=1&mute=0`;
            iframe.title = randomVideo.title;
            iframe.width = "315";
            iframe.height = "560";
            iframe.style.cssText = `
        border: none;
        border-radius: 8px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        max-width: 100%;
      `;
            iframe.allow =
                "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
            iframe.allowFullscreen = true;

            // Add a data attribute to store the video ID for later use
            iframe.dataset.videoId = randomVideo.id;

            // Add a class to identify this as a video iframe
            iframe.classList.add("injected-video-iframe");

            linkContainer.appendChild(iframe);
        } else {
            const randomLink =
                quickLinks[Math.floor(Math.random() * quickLinks.length)];
            const anchor = document.createElement("a");
            anchor.href = randomLink.url;
            anchor.textContent = randomLink.text;
            anchor.target = "_blank";
            anchor.style.cssText = `
        color: #ff0000;
        text-decoration: none;
        font-weight: bold;
        transition: all 0.2s ease;
        font-size: 24px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      `;

            linkContainer.appendChild(anchor);
        }

        // Insert at the beginning
        articleContent.insertBefore(linkContainer, articleContent.firstChild);
    }

    // Add animation keyframes
    const style = document.createElement("style");
    style.textContent = `
    @keyframes fadeIn {
      from { 
        opacity: 0; 
        transform: translateY(-20px) scale(0.8);
        filter: blur(5px);
      }
      to { 
        opacity: 1; 
        transform: translateY(0) scale(1);
        filter: blur(0);
      }
    }
    
    @keyframes bounce {
      0%, 20%, 50%, 80%, 100% {
        transform: translateX(-50%) translateY(0);
      }
      40% {
        transform: translateX(-50%) translateY(10px);
      }
      60% {
        transform: translateX(-50%) translateY(5px);
      }
    }
  `;
    document.head.appendChild(style);

    // Set up Intersection Observer to play/pause videos based on visibility
    setupVideoVisibilityObserver();

    console.log("Link injection completed");
}

// Function to set up the Intersection Observer for videos
function setupVideoVisibilityObserver() {
    // Load the YouTube IFrame API
    const tag = document.createElement("script");
    tag.src = "https://www.youtube.com/iframe_api";
    const firstScriptTag = document.getElementsByTagName("script")[0];
    firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

    // Create an Intersection Observer
    const videoObserver = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                const iframe = entry.target;
                const videoId = iframe.dataset.videoId;

                if (entry.isIntersecting) {
                    // Video is visible, play it
                    console.log(`Playing video: ${videoId}`);
                    // Use a more reliable way to update the iframe src
                    const newSrc = `https://www.youtube.com/embed/${videoId}?autoplay=1&controls=1&modestbranding=1&rel=0&enablejsapi=1&playsinline=1&mute=0`;
                    if (iframe.src !== newSrc) {
                        iframe.src = newSrc;
                    }
                } else {
                    // Video is not visible, pause it
                    console.log(`Pausing video: ${videoId}`);
                    // Use a more reliable way to update the iframe src
                    const newSrc = `https://www.youtube.com/embed/${videoId}?autoplay=0&controls=1&modestbranding=1&rel=0&enablejsapi=1&playsinline=1&mute=0`;
                    if (iframe.src !== newSrc) {
                        iframe.src = newSrc;
                    }
                }
            });
        },
        {
            root: null, // Use the viewport as the root
            rootMargin: "0px",
            threshold: 0.5, // Consider visible when 50% of the video is in view
        }
    );

    // Observe all video iframes
    const videoIframes = document.querySelectorAll(".injected-video-iframe");
    videoIframes.forEach((iframe) => {
        videoObserver.observe(iframe);
    });

    // Also observe any new videos that might be added later
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length) {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
                        // Element node
                        const newVideos = node.querySelectorAll(
                            ".injected-video-iframe"
                        );
                        newVideos.forEach((iframe) => {
                            videoObserver.observe(iframe);
                        });
                    }
                });
            }
        });
    });

    // Start observing the document body for added nodes
    observer.observe(document.body, { childList: true, subtree: true });
}
