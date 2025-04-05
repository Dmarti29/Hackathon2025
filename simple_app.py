from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
from datetime import datetime
import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# ============================================================================
# CONFIGURATION
# ============================================================================

# Supabase credentials - replace with your own from Supabase dashboard
SUPABASE_URL = "https://pieavugnpmilwweysycb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBpZWF2dWducG1pbHd3ZXlzeWNiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM4NDcxMjcsImV4cCI6MjA1OTQyMzEyN30.n7cbXhyZdmyFS2r3wSJNeTvM6xCGrj79D4zGDkDoNws"

# AI Configuration
USE_AI_CATEGORIZATION = True  # Set to True to use AI for URL categorization

# Import the expanded domain lists from sentiment_analysis.py
# These are just a subset of the full lists for brevity
PRODUCTIVE_DOMAINS = [
    # Educational
    'wikipedia.org', 'scholar.google.com', 'coursera.org', 'edx.org', 
    'khanacademy.org', 'jstor.org', 'researchgate.net', 'arxiv.org',
    'github.com', 'stackoverflow.com', 'docs.google.com', 'medium.com',
    'dev.to', 'freecodecamp.org', 'udemy.com', 'pluralsight.com',
    'lynda.com', 'skillshare.com', 'codecademy.com', 'brilliant.org',
    'datacamp.com', 'futurelearn.com', 'canvas.net', 'canvas.edu',
    'blackboard.com', 'moodle.org', 'duolingo.com', 'memrise.com'
]

UNPRODUCTIVE_DOMAINS = [
    # Social media
    'facebook.com', 'twitter.com', 'instagram.com', 'snapchat.com', 'tiktok.com',
    'reddit.com', 'tumblr.com', 'pinterest.com', 'discord.com', 'telegram.org',
    # Streaming
    'youtube.com/shorts', 'youtube.com/reels', 'netflix.com', 'hulu.com', 'disneyplus.com',
    'primevideo.com', 'hbomax.com', 'peacocktv.com', 'twitch.tv', 'tiktok.com'
]

# Keywords for content analysis
EDUCATIONAL_KEYWORDS = [
    'learn', 'study', 'education', 'academic', 'research', 'science', 'knowledge',
    'university', 'college', 'school', 'course', 'lecture', 'tutorial', 'lesson',
    'homework', 'assignment', 'project', 'thesis', 'dissertation', 'exam', 'quiz',
    'test', 'grade', 'professor', 'teacher', 'instructor', 'student', 'scholar',
    'theory', 'concept', 'analysis', 'method', 'technique', 'skill', 'practice',
    'exercise', 'problem', 'solution', 'answer', 'question', 'challenge', 'critical',
    'thinking', 'understanding', 'comprehension', 'knowledge', 'wisdom', 'insight'
]

ENTERTAINMENT_KEYWORDS = [
    'fun', 'entertainment', 'game', 'play', 'watch', 'stream', 'video', 'movie',
    'show', 'series', 'episode', 'season', 'tv', 'film', 'actor', 'actress',
    'celebrity', 'star', 'famous', 'viral', 'trending', 'popular', 'hit', 'top',
    'best', 'new', 'latest', 'release', 'trailer', 'preview', 'teaser', 'clip',
    'highlight', 'reaction', 'review', 'unboxing', 'haul', 'challenge', 'prank',
    'funny', 'comedy', 'laugh', 'joke', 'humor', 'meme', 'viral', 'trend', 'challenge'
]

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes to allow Chrome extension to make requests

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

# Initialize Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connected to Supabase successfully!")
except Exception as e:
    print(f"❌ Failed to connect to Supabase: {e}")
    supabase = None

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_domain(url):
    """
    Extract the domain from a URL.
    
    Args:
        url (str): The URL to extract domain from
        
    Returns:
        str: The domain name
    """
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def check_known_domains(url):
    """
    Check if the URL belongs to known productive or unproductive domains.
    
    Args:
        url (str): The URL to check
        
    Returns:
        dict or None: Result of domain-based analysis or None if domain not recognized
    """
    domain = extract_domain(url)
    
    # Check for exact domain matches
    for prod_domain in PRODUCTIVE_DOMAINS:
        if prod_domain in domain:
            return {"productive": True, "confidence": 0.9, 
                    "reason": f"Domain '{domain}' is known for educational content"}
    
    # Special case for YouTube - check if it's shorts/reels or educational content
    if 'youtube.com' in domain:
        if any(term in url.lower() for term in ['/shorts', '/reels']):
            return {"productive": False, "confidence": 0.85, 
                    "reason": "Short-form video content tends to be distracting"}
        if any(term in url.lower() for term in ['/lecture', '/education', '/learn', '/course']):
            return {"productive": True, "confidence": 0.8, 
                    "reason": "Educational YouTube content"}
    
    for unprod_domain in UNPRODUCTIVE_DOMAINS:
        if unprod_domain in domain:
            return {"productive": False, "confidence": 0.85, 
                    "reason": f"Domain '{domain}' is generally entertainment-focused"}
    
    return None

def analyze_url_content(url):
    """
    Fetch and analyze content from the URL.
    
    Args:
        url (str): The URL to analyze
        
    Returns:
        dict: Result of content-based analysis
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title and description
        title = soup.title.string if soup.title else ""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc['content'] if meta_desc else ""
        
        # Extract main text content (simplified)
        paragraphs = soup.find_all('p')
        content_text = ' '.join([p.text for p in paragraphs[:10]])  # First 10 paragraphs
        
        # Combine text for analysis
        full_text = f"{title} {description} {content_text}".lower()
        
        # Count educational and entertainment keywords
        edu_count = sum(1 for keyword in EDUCATIONAL_KEYWORDS if keyword in full_text)
        ent_count = sum(1 for keyword in ENTERTAINMENT_KEYWORDS if keyword in full_text)
        
        # Simple scoring without sentiment analysis
        if edu_count > ent_count and edu_count >= 3:
            return {"productive": True, "confidence": min(0.5 + (edu_count - ent_count) * 0.05, 0.9), 
                    "reason": f"Content contains educational keywords ({edu_count} found)"}
        elif ent_count > edu_count and ent_count >= 3:
            return {"productive": False, "confidence": min(0.5 + (ent_count - edu_count) * 0.05, 0.9), 
                    "reason": f"Content contains entertainment keywords ({ent_count} found)"}
        else:
            return {"productive": None, "confidence": 0.5, 
                    "reason": "Neutral content, could be either"}
            
    except Exception as e:
        print(f"❌ Error analyzing URL content: {e}")
        return {"productive": None, "confidence": 0.3, 
                "reason": f"Failed to analyze content: {str(e)}"}

def ai_categorize_url(url):
    """
    Use AI to determine if a URL is productive or unproductive
    
    Args:
        url (str): The URL to categorize
        
    Returns:
        str: 'productive', 'unproductive', or 'unknown'
    """
    print(f"🤖 AI analyzing: {url}")
    
    # First check if domain is in our known lists
    domain_result = check_known_domains(url)
    
    if domain_result and domain_result["confidence"] > 0.7:
        is_productive = domain_result["productive"]
        print(f"✅ Domain-based analysis: {'Productive' if is_productive else 'Unproductive'} ({domain_result['confidence']:.2f} confidence)")
        print(f"   Reason: {domain_result['reason']}")
        return 'productive' if is_productive else 'unproductive'
    
    # If not confident or domain not in lists, analyze content
    content_result = analyze_url_content(url)
    
    # Combine domain and content analysis if both available
    if domain_result and content_result and content_result["productive"] is not None:
        is_productive = domain_result["productive"] if domain_result["confidence"] > content_result["confidence"] else content_result["productive"]
        confidence = max(domain_result["confidence"], content_result["confidence"])
        reason = f"{domain_result['reason']} and {content_result['reason']}"
        print(f"✅ Combined analysis: {'Productive' if is_productive else 'Unproductive'} ({confidence:.2f} confidence)")
        print(f"   Reason: {reason}")
    elif content_result and content_result["productive"] is not None:
        is_productive = content_result["productive"]
        confidence = content_result["confidence"]
        reason = content_result["reason"]
        print(f"✅ Content-based analysis: {'Productive' if is_productive else 'Unproductive'} ({confidence:.2f} confidence)")
        print(f"   Reason: {reason}")
    elif domain_result:
        is_productive = domain_result["productive"]
        confidence = domain_result["confidence"]
        reason = domain_result["reason"]
        print(f"✅ Domain-based analysis: {'Productive' if is_productive else 'Unproductive'} ({confidence:.2f} confidence)")
        print(f"   Reason: {reason}")
    else:
        print(f"❓ Inconclusive analysis: Unknown")
        return 'unknown'
    
    return 'productive' if is_productive else 'unproductive'

def categorize_url(url):
    """
    Determine if a URL is productive (study mode) or unproductive (brain rot)
    
    Args:
        url (str): The URL to categorize
        
    Returns:
        str: 'productive', 'unproductive', or 'unknown'
    """
    if USE_AI_CATEGORIZATION:
        # Use AI to categorize the URL
        return ai_categorize_url(url)
    else:
        # Use simple domain-based categorization
        # Check if URL is in productive domains
        for domain in PRODUCTIVE_DOMAINS:
            if domain in url:
                return 'productive'
        
        # Check if URL is in unproductive domains
        for domain in UNPRODUCTIVE_DOMAINS:
            if domain in url:
                return 'unproductive'
        
        # If not found in either list
        return 'unknown'

def store_url(user_id, url):
    """
    Store a URL in the Supabase database
    
    Args:
        user_id (str): The ID of the user
        url (str): The URL to store
        
    Returns:
        dict: The stored URL data including category and timestamp
    """
    # Determine URL category
    category = categorize_url(url)
    
    # Current timestamp
    timestamp = datetime.now().isoformat()
    
    try:
        # Make sure user exists (upsert will create if not exists)
        supabase.table('users').upsert({
            'id': user_id,
            'updated_at': timestamp
        }).execute()
        
        # Store URL in history table
        result = supabase.table('url_history').insert({
            'user_id': user_id,
            'url': url,
            'category': category,
            'timestamp': timestamp
        }).execute()
        
        # Return the stored data
        return {
            'url': url,
            'category': category,
            'timestamp': timestamp
        }
    except Exception as e:
        print(f"❌ Error storing URL: {e}")
        # If database operation fails, still return the categorized data
        return {
            'url': url,
            'category': category,
            'timestamp': timestamp,
            'error': str(e)
        }

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the API is running
    """
    return jsonify({
        "status": "healthy",
        "database": "connected" if supabase else "disconnected",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/url/submit', methods=['POST'])
def submit_url():
    """
    Receive a URL from the frontend, store it, and return its category
    
    Expected JSON payload:
    {
        "url": "https://example.com",
        "user_id": "user123"
    }
    """
    # Get data from request
    data = request.json
    
    # Validate required fields
    if not data or 'url' not in data or 'user_id' not in data:
        return jsonify({
            "error": "Missing required fields: url and user_id"
        }), 400
    
    # Extract URL and user ID
    url = data['url']
    user_id = data['user_id']
    
    # Store URL in database
    result = store_url(user_id, url)
    
    # Return result to frontend
    return jsonify({
        "status": "success",
        "message": "URL processed successfully",
        "data": result
    })

@app.route('/api/url/categorize', methods=['POST'])
def categorize_url_endpoint():
    """
    Categorize a URL without storing it
    
    Expected JSON payload:
    {
        "url": "https://example.com"
    }
    """
    # Get data from request
    data = request.json
    
    # Validate required fields
    if not data or 'url' not in data:
        return jsonify({
            "error": "Missing required field: url"
        }), 400
    
    # Extract URL
    url = data['url']
    
    # Categorize URL
    category = categorize_url(url)
    
    # Return result to frontend
    return jsonify({
        "url": url,
        "category": category
    })

@app.route('/api/user/<user_id>/history', methods=['GET'])
def get_user_history(user_id):
    """
    Get a list of URLs the user has visited
    
    Returns the most recent URLs first
    """
    try:
        # Get user's URL history from Supabase
        response = supabase.table('url_history').select('*').eq('user_id', user_id).order('timestamp', desc=True).execute()
        
        if hasattr(response, 'data'):
            return jsonify({
                "user_id": user_id,
                "history": response.data
            })
        else:
            return jsonify({
                "user_id": user_id,
                "history": []
            })
    except Exception as e:
        print(f"❌ Error getting user history: {e}")
        return jsonify({
            "error": "Failed to retrieve user history",
            "user_id": user_id,
            "history": []
        }), 500

@app.route('/api/user/<user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """
    Get statistics on how many productive vs unproductive sites a user has visited
    """
    try:
        # Get counts from Supabase
        productive_response = supabase.table('url_history').select('*', count='exact').eq('user_id', user_id).eq('category', 'productive').execute()
        unproductive_response = supabase.table('url_history').select('*', count='exact').eq('user_id', user_id).eq('category', 'unproductive').execute()
        unknown_response = supabase.table('url_history').select('*', count='exact').eq('user_id', user_id).eq('category', 'unknown').execute()
        
        productive_count = len(productive_response.data) if hasattr(productive_response, 'data') else 0
        unproductive_count = len(unproductive_response.data) if hasattr(unproductive_response, 'data') else 0
        unknown_count = len(unknown_response.data) if hasattr(unknown_response, 'data') else 0
        
        total_count = productive_count + unproductive_count + unknown_count
        productivity_score = productive_count / total_count if total_count > 0 else 0
        
        return jsonify({
            "user_id": user_id,
            "productive_count": productive_count,
            "unproductive_count": unproductive_count,
            "unknown_count": unknown_count,
            "total_count": total_count,
            "productivity_score": productivity_score
        })
    except Exception as e:
        print(f"❌ Error getting user stats: {e}")
        return jsonify({
            "error": "Failed to retrieve user statistics",
            "user_id": user_id,
            "productive_count": 0,
            "unproductive_count": 0,
            "unknown_count": 0,
            "total_count": 0,
            "productivity_score": 0
        }), 500

@app.route('/api/user/<user_id>/locked-in', methods=['GET'])
def get_user_locked_in_sessions(user_id):
    """
    Get a user's locked-in study sessions
    """
    try:
        # Get user's locked-in sessions from Supabase
        response = supabase.table('user_state').select('*').eq('user_id', user_id).eq('locked_in', True).order('start_time', desc=True).execute()
        
        if hasattr(response, 'data'):
            return jsonify({
                "user_id": user_id,
                "sessions": response.data
            })
        else:
            return jsonify({
                "user_id": user_id,
                "sessions": []
            })
    except Exception as e:
        print(f"❌ Error getting user locked-in sessions: {e}")
        return jsonify({
            "error": "Failed to retrieve user locked-in sessions",
            "user_id": user_id,
            "sessions": []
        }), 500

@app.route('/api/user/<user_id>/state/start', methods=['POST'])
def start_user_state(user_id):
    """
    Start a new state for a user (locked in or brain rotting)
    
    Expected JSON payload:
    {
        "locked_in": true,  // true for studying, false for brain rotting
        "notes": "Optional notes about this session"
    }
    """
    try:
        # Get data from request
        data = request.json
        
        # Validate required fields
        if not data or 'locked_in' not in data:
            return jsonify({
                "error": "Missing required field: locked_in"
            }), 400
        
        # Extract data
        locked_in = data['locked_in']
        notes = data.get('notes', '')
        
        # Current timestamp
        timestamp = datetime.now().isoformat()
        
        # Make sure user exists
        supabase.table('users').upsert({
            'id': user_id,
            'updated_at': timestamp
        }).execute()
        
        # Check if there's an active session that needs to be ended
        active_sessions = supabase.table('user_state')\
            .select('*')\
            .eq('user_id', user_id)\
            .is_('end_time', 'null')\
            .execute()
            
        if hasattr(active_sessions, 'data') and len(active_sessions.data) > 0:
            # End the active session
            active_session = active_sessions.data[0]
            end_session(user_id, active_session['id'])
        
        # Create new state
        result = supabase.table('user_state').insert({
            'user_id': user_id,
            'locked_in': locked_in,
            'start_time': timestamp,
            'notes': notes
        }).execute()
        
        if hasattr(result, 'data') and len(result.data) > 0:
            return jsonify({
                "status": "success",
                "message": f"Started {'locked-in study' if locked_in else 'brain rotting'} session",
                "session": result.data[0]
            })
        else:
            return jsonify({
                "error": "Failed to start session",
                "user_id": user_id
            }), 500
            
    except Exception as e:
        print(f"❌ Error starting user state: {e}")
        return jsonify({
            "error": f"Failed to start session: {str(e)}",
            "user_id": user_id
        }), 500

def end_session(user_id, session_id):
    """
    Helper function to end a session and calculate duration
    """
    # Current timestamp
    end_time = datetime.now().isoformat()
    
    # Get the session to calculate duration
    session_response = supabase.table('user_state')\
        .select('*')\
        .eq('id', session_id)\
        .execute()
        
    if hasattr(session_response, 'data') and len(session_response.data) > 0:
        session = session_response.data[0]
        start_time = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
        end_time_dt = datetime.now()
        
        # Calculate duration in seconds
        duration = int((end_time_dt - start_time).total_seconds())
        
        # Update the session
        supabase.table('user_state')\
            .update({
                'end_time': end_time,
                'duration': duration
            })\
            .eq('id', session_id)\
            .execute()
            
        return {
            'session_id': session_id,
            'duration': duration,
            'end_time': end_time
        }
    
    return None

@app.route('/api/user/<user_id>/state/end', methods=['POST'])
def end_user_state(user_id):
    """
    End the current active state for a user
    
    Expected JSON payload:
    {
        "session_id": 123  // Optional, if not provided will end the most recent active session
    }
    """
    try:
        # Get data from request
        data = request.json or {}
        
        # If session_id is provided, use it
        if 'session_id' in data:
            session_id = data['session_id']
            result = end_session(user_id, session_id)
            
            if result:
                return jsonify({
                    "status": "success",
                    "message": "Session ended successfully",
                    "session": result
                })
            else:
                return jsonify({
                    "error": "Session not found or already ended",
                    "user_id": user_id,
                    "session_id": session_id
                }), 404
        
        # Otherwise, find the active session
        active_sessions = supabase.table('user_state')\
            .select('*')\
            .eq('user_id', user_id)\
            .is_('end_time', 'null')\
            .execute()
            
        if hasattr(active_sessions, 'data') and len(active_sessions.data) > 0:
            # End the active session
            active_session = active_sessions.data[0]
            result = end_session(user_id, active_session['id'])
            
            return jsonify({
                "status": "success",
                "message": "Session ended successfully",
                "session": result
            })
        else:
            return jsonify({
                "error": "No active session found",
                "user_id": user_id
            }), 404
            
    except Exception as e:
        print(f"❌ Error ending user state: {e}")
        return jsonify({
            "error": f"Failed to end session: {str(e)}",
            "user_id": user_id
        }), 500

@app.route('/api/user/<user_id>/state/toggle', methods=['POST'])
def toggle_user_state(user_id):
    """
    Toggle between locked-in and brain rotting states
    Ends the current state (if any) and starts a new one with the opposite locked_in value
    
    Expected JSON payload:
    {
        "notes": "Optional notes about this new session"
    }
    """
    try:
        # Get data from request
        data = request.json or {}
        notes = data.get('notes', '')
        
        # Find the active session
        active_sessions = supabase.table('user_state')\
            .select('*')\
            .eq('user_id', user_id)\
            .is_('end_time', 'null')\
            .execute()
            
        # Default to starting a locked-in session if no active session
        new_locked_in = True
        
        if hasattr(active_sessions, 'data') and len(active_sessions.data) > 0:
            # End the active session
            active_session = active_sessions.data[0]
            end_session(user_id, active_session['id'])
            
            # Toggle the locked_in value
            new_locked_in = not active_session['locked_in']
        
        # Start a new session with the toggled state
        # Current timestamp
        timestamp = datetime.now().isoformat()
        
        # Create new state
        result = supabase.table('user_state').insert({
            'user_id': user_id,
            'locked_in': new_locked_in,
            'start_time': timestamp,
            'notes': notes
        }).execute()
        
        if hasattr(result, 'data') and len(result.data) > 0:
            return jsonify({
                "status": "success",
                "message": f"Toggled to {'locked-in study' if new_locked_in else 'brain rotting'} mode",
                "session": result.data[0],
                "locked_in": new_locked_in
            })
        else:
            return jsonify({
                "error": "Failed to toggle session",
                "user_id": user_id
            }), 500
            
    except Exception as e:
        print(f"❌ Error toggling user state: {e}")
        return jsonify({
            "error": f"Failed to toggle session: {str(e)}",
            "user_id": user_id
        }), 500

@app.route('/api/brainrot/trigger', methods=['POST'])
def trigger_brainrot():
    """
    Endpoint to receive brain rot triggers from eye detection
    
    Expected JSON payload:
    {
        "user_id": "user123",
        "timestamp": "2025-04-05T11:52:40-05:00",  # Optional
        "look_away_count": 5,  # Optional
        "notes": "User looked away 5 times"  # Optional
    }
    """
    try:
        # Get data from request
        data = request.json
        
        # Validate required fields
        if not data or 'user_id' not in data:
            return jsonify({
                "error": "Missing required field: user_id"
            }), 400
        
        # Extract data
        user_id = data['user_id']
        timestamp = data.get('timestamp', datetime.now().isoformat())
        look_away_count = data.get('look_away_count', 5)
        notes = data.get('notes', f"User looked away {look_away_count} times")
        
        # Make sure user exists
        supabase.table('users').upsert({
            'id': user_id,
            'updated_at': timestamp
        }).execute()
        
        # Check if there's an active session
        active_sessions = supabase.table('user_state')\
            .select('*')\
            .eq('user_id', user_id)\
            .is_('end_time', 'null')\
            .execute()
            
        if hasattr(active_sessions, 'data') and len(active_sessions.data) > 0:
            # If there's an active session and it's locked_in (studying), toggle it to brain rot
            active_session = active_sessions.data[0]
            if active_session['locked_in']:
                # End the current locked-in session
                end_session(user_id, active_session['id'])
                
                # Start a new brain rot session
                result = supabase.table('user_state').insert({
                    'user_id': user_id,
                    'locked_in': False,  # brain rotting
                    'start_time': timestamp,
                    'notes': f"Brain rot detected: {notes}"
                }).execute()
                
                return jsonify({
                    "status": "success",
                    "message": "Brain rot detected, switched from locked-in to brain rot mode",
                    "session": result.data[0] if hasattr(result, 'data') and len(result.data) > 0 else None,
                    "action": "toggled"
                })
            else:
                # Already in brain rot mode, just acknowledge
                return jsonify({
                    "status": "success",
                    "message": "Brain rot already active",
                    "session": active_session,
                    "action": "none"
                })
        else:
            # No active session, start a new brain rot session
            result = supabase.table('user_state').insert({
                'user_id': user_id,
                'locked_in': False,  # brain rotting
                'start_time': timestamp,
                'notes': f"Brain rot detected: {notes}"
            }).execute()
            
            return jsonify({
                "status": "success",
                "message": "Brain rot detected, started brain rot session",
                "session": result.data[0] if hasattr(result, 'data') and len(result.data) > 0 else None,
                "action": "started"
            })
            
    except Exception as e:
        print(f"❌ Error triggering brain rot: {e}")
        return jsonify({
            "error": f"Failed to trigger brain rot: {str(e)}",
            "user_id": data.get('user_id', 'unknown')
        }), 500

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == '__main__':
    # Get port from environment variable or use default 5001
    port = int(os.environ.get('PORT', 5001))
    
    # Start Flask server
    print(f"🚀 Starting BrainBot API server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
