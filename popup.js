// popup.js
document.addEventListener('DOMContentLoaded', function() {
    // Get the current tab to determine if it's productive or unproductive
    chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        const currentTab = tabs[0];
        
        // Check the URL against our lists
        chrome.storage.local.get('currentSiteType', function(data) {
            const statusDiv = document.getElementById('currentStatus');
            
            if (data.currentSiteType === 'productive') {
                statusDiv.innerHTML = `
                    <strong>Current site:</strong> Productive<br>
                    <small>We'll try to distract you soon!</small>
                `;
                statusDiv.style.backgroundColor = '#e6f4ea';
            } else if (data.currentSiteType === 'unproductive') {
                statusDiv.innerHTML = `
                    <strong>Current site:</strong> Unproductive<br>
                    <small>We'll try to make you productive soon!</small>
                `;
                statusDiv.style.backgroundColor = '#fce8e6';
            } else {
                statusDiv.innerHTML = `
                    <strong>Current site:</strong> Neutral<br>
                    <small>This site isn't on our radar.</small>
                `;
                statusDiv.style.backgroundColor = '#f0f0f0';
            }

            // Add URL information
            const urlDiv = document.createElement('div');
            urlDiv.style.marginTop = '10px';
            urlDiv.style.fontSize = '12px';
            urlDiv.style.wordBreak = 'break-all';
            
            // Truncate long URLs to make them more readable
            let displayUrl = currentTab.url;
            if (displayUrl.length > 50) {
                displayUrl = displayUrl.substring(0, 50) + '...';
            }
            
            urlDiv.innerHTML = `<strong>Current URL:</strong><br>${displayUrl}`;
            statusDiv.appendChild(urlDiv);
        });
    });
    
    // Setup testing mode toggle
    const testingModeCheckbox = document.getElementById('testingMode');
    const testingInfo = document.getElementById('testingInfo');
    
    testingModeCheckbox.addEventListener('change', function() {
        testingInfo.style.display = this.checked ? 'block' : 'none';
    });
    
    // Load testing mode state
    chrome.storage.local.get('inTestingMode', function(data) {
        if (data.inTestingMode !== undefined) {
            testingModeCheckbox.checked = data.inTestingMode;
            testingInfo.style.display = data.inTestingMode ? 'block' : 'none';
        }
    });
    
    // Save settings when the button is clicked
    document.getElementById('saveSettings').addEventListener('click', function() {
        const frequency = document.getElementById('suggestionFrequency').value;
        const inTestingMode = testingModeCheckbox.checked;
        
        chrome.storage.local.set({
            suggestionFrequencyMinutes: parseInt(frequency),
            inTestingMode: inTestingMode
        }, function() {
            // Provide feedback
            const button = document.getElementById('saveSettings');
            const originalText = button.textContent;
            button.textContent = 'Saved!';
            button.disabled = true;
            
            setTimeout(function() {
                button.textContent = originalText;
                button.disabled = false;
            }, 1500);
        });
    });
    
    // Load saved settings
    chrome.storage.local.get('suggestionFrequencyMinutes', function(data) {
        if (data.suggestionFrequencyMinutes) {
            document.getElementById('suggestionFrequency').value = data.suggestionFrequencyMinutes.toString();
        }
    });
});

    
    // Add event listener for the test URL opening button
    const openTestUrlsButton = document.getElementById('openTestUrls');
    if (openTestUrlsButton) {
      openTestUrlsButton.addEventListener('click', function() {
        // Disable button to prevent multiple clicks
        this.disabled = true;
        this.textContent = 'Opening URLs...';
        
        // Send message to background script to open test URLs
        chrome.runtime.sendMessage({ 
          action: 'openUrls' 
        }, function(response) {
          // Re-enable button after response is received
          openTestUrlsButton.disabled = false;
          
          if (response && response.success) {
            openTestUrlsButton.textContent = 'URLs Opened!';
            console.log('Opened tabs:', response.tabs);
            
            // Reset button text after 2 seconds
            setTimeout(function() {
              openTestUrlsButton.textContent = 'Open Test URLs';
            }, 2000);
          } else {
            openTestUrlsButton.textContent = 'Error - Try Again';
            console.error('Failed to open URLs:', response ? response.error : 'No response');
            
            // Reset button text after 2 seconds
            setTimeout(function() {
              openTestUrlsButton.textContent = 'Open Test URLs';
            }, 2000);
          }
        });
      });
    }
  