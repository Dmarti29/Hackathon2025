document.addEventListener('DOMContentLoaded', function() {
    const serverUrl = 'http://localhost:5000';
    const startButton = document.getElementById('startTracking');
    const stopButton = document.getElementById('stopTracking');
    const getStatsButton = document.getElementById('getStats');
    const statusSpan = document.getElementById('status');
    const statusBox = document.getElementById('statusBox');
    const statsContainer = document.getElementById('statsContainer');
    const statsContent = document.getElementById('statsContent');
    const errorDiv = document.getElementById('error');
    
    // Check current status on popup open
    checkStatus();
    
    startButton.addEventListener('click', function() {
      fetch(`${serverUrl}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          // Optional: Specify duration in seconds
          // duration: 300 // 5 minutes
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          updateUI(true);
          showError('');
        } else {
          showError(`Error: ${data.message}`);
        }
      })
      .catch(error => {
        showError(`Connection error: ${error.message}. Make sure the Flask server is running.`);
      });
    });
    
    stopButton.addEventListener('click', function() {
      fetch(`${serverUrl}/stop`, {
        method: 'POST'
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          updateUI(false);
          fetchAndDisplayStats();
        } else {
          showError(`Error: ${data.message}`);
        }
      })
      .catch(error => {
        showError(`Connection error: ${error.message}`);
      });
    });
    
    getStatsButton.addEventListener('click', function() {
      fetchAndDisplayStats();
    });
    
    function checkStatus() {
      fetch(`${serverUrl}/status`)
      .then(response => response.json())
      .then(data => {
        updateUI(data.status === 'active');
      })
      .catch(error => {
        showError(`Connection error: ${error.message}. Make sure the Flask server is running.`);
      });
    }
    
    function fetchAndDisplayStats() {
      fetch(`${serverUrl}/stats`)
      .then(response => response.json())
      .then(data => {
        if (data.status === 'not_started') {
          statsContent.innerHTML = '<p>No tracking data available yet.</p>';
        } else {
          let statsHtml = '';
          if (data.times_looked_away !== undefined) {
            statsHtml += `<p>Times looked away: ${data.times_looked_away}</p>`;
          }
          if (data.total_unfocused_formatted) {
            statsHtml += `<p>Total unfocused time: ${data.total_unfocused_formatted}</p>`;
          }
          if (data.currently_focused !== undefined) {
            statsHtml += `<p>Currently focused: ${data.currently_focused ? 'Yes' : 'No'}</p>`;
          }
          if (data.session_duration) {
            const minutes = Math.floor(data.session_duration / 60);
            const seconds = Math.floor(data.session_duration % 60);
            statsHtml += `<p>Session duration: ${minutes}m ${seconds}s</p>`;
          }
          
          statsContent.innerHTML = statsHtml;
        }
        statsContainer.style.display = 'block';
      })
      .catch(error => {
        showError(`Error fetching stats: ${error.message}`);
      });
    }
    
    function updateUI(isActive) {
      startButton.disabled = isActive;
      stopButton.disabled = !isActive;
      statusSpan.textContent = isActive ? 'Active' : 'Inactive';
      statusBox.className = isActive ? 'status active' : 'status inactive';
      
      if (isActive) {
        // Poll for status updates when active
        setTimeout(fetchAndDisplayStats, 2000);
      }
    }
    
    function showError(message) {
      if (message) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
      } else {
        errorDiv.style.display = 'none';
      }
    }
  });
  