const API_BASE = "http://127.0.0.1:5001/api";

/**
 * Start a new session (locked-in or brain rot)
 * @param {string} userId - The user ID
 * @param {boolean} lockedIn - true = productive mode, false = brain rot
 * @param {string} notes - Optional notes
 */
export async function startSession(userId, lockedIn = true, notes = "") {
  try {
    const response = await fetch(`${API_BASE}/user/${userId}/state/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ locked_in: lockedIn, notes })
    });
    return await response.json();
  } catch (err) {
    console.error("❌ startSession failed:", err);
    return null;
  }
}

/**
 * End the current active session or a specific session
 * @param {string} userId - The user ID
 * @param {string} sessionId - Optional session ID
 */
export async function endSession(userId, sessionId = null) {
  try {
    const response = await fetch(`${API_BASE}/user/${userId}/state/end`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(sessionId ? { session_id: sessionId } : {})
    });
    return await response.json();
  } catch (err) {
    console.error("❌ endSession failed:", err);
    return null;
  }
}

/**
 * Toggle between locked-in and brain rot states
 * @param {string} userId 
 * @param {string} notes 
 */
export async function toggleSession(userId, notes = "") {
  try {
    const response = await fetch(`${API_BASE}/user/${userId}/state/toggle`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ notes })
    });
    return await response.json();
  } catch (err) {
    console.error("❌ toggleSession failed:", err);
    return null;
  }
}

/**
 * Start the eye tracking detection system
 * @param {string} userId 
 */
export async function startEyeTracking(userId) {
  try {
    const response = await fetch(`${API_BASE}/brainrot/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ user_id: userId })
    });
    return await response.json();
  } catch (err) {
    console.error("❌ startEyeTracking failed:", err);
    return null;
  }
}

/**
 * Submit a visited URL to the backend for categorization and logging
 * @param {string} userId 
 * @param {string} url 
 */
export async function submitUrlToAPI(userId, url) {
  try {
    const response = await fetch(`${API_BASE}/url/submit`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ user_id: userId, url })
    });
    const data = await response.json();
    console.log("✅ URL submitted:", data);
    return data;
  } catch (err) {
    console.error("❌ submitUrlToAPI failed:", err);
    return null;
  }
}

/**
 * Categorize a URL without saving to database
 * @param {string} url 
 */
export async function categorizeUrl(url) {
  try {
    const response = await fetch(`${API_BASE}/url/categorize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ url })
    });
    return await response.json();
  } catch (err) {
    console.error("❌ categorizeUrl failed:", err);
    return null;
  }
}

/**
 * Get user's browsing history
 * @param {string} userId 
 */
export async function getUserHistory(userId) {
  try {
    const response = await fetch(`${API_BASE}/user/${userId}/history`);
    return await response.json();
  } catch (err) {
    console.error("❌ getUserHistory failed:", err);
    return null;
  }
}

/**
 * Get user's productivity stats
 * @param {string} userId 
 */
export async function getUserStats(userId) {
  try {
    const response = await fetch(`${API_BASE}/user/${userId}/stats`);
    return await response.json();
  } catch (err) {
    console.error("❌ getUserStats failed:", err);
    return null;
  }
}

/**
 * Get locked-in (study) sessions for the user
 * @param {string} userId 
 */
export async function getLockedInSessions(userId) {
  try {
    const response = await fetch(`${API_BASE}/user/${userId}/locked-in`);
    return await response.json();
  } catch (err) {
    console.error("❌ getLockedInSessions failed:", err);
    return null;
  }
}

/**
 * Send brain rot trigger (used by eye tracking)
 * @param {object} payload - { user_id, timestamp?, look_away_count?, notes? }
 */
export async function triggerBrainRot(payload) {
  try {
    const response = await fetch(`${API_BASE}/brainrot/trigger`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });
    return await response.json();
  } catch (err) {
    console.error("❌ triggerBrainRot failed:", err);
    return null;
  }
}
