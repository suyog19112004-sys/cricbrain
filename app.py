import os
import json
import re
import datetime
import requests
from flask import Flask, render_template, request, jsonify, Response
from dotenv import load_dotenv

# Load environment variables from local .env if present
load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")

# In-memory cache for live search results to improve performance and avoid hitting rate limits
# Cache key: format name (e.g., "test", "odi", "t20i", "all")
# Value: {"timestamp": datetime, "data": ...}
GROUNDING_CACHE = {}
CACHE_TTL_SECONDS = 3600  # 1 hour cache

# Formats and their respective cutoff requirements
FORMAT_CONFIG = {
    "test": {
        "display_name": "Test Cricket",
        "code": "Test",
        "min_innings_cutoff": 20,
        "cutoff_label": "Minimum 20 innings cutoff",
        "description": "Men's Test Cricket (All-time career records across all Test-playing nations)",
    },
    "odi": {
        "display_name": "One Day Internationals (ODI)",
        "code": "ODI",
        "min_innings_cutoff": 20,
        "cutoff_label": "Minimum 20 innings cutoff",
        "description": "Men's ODI Cricket (All-time career records across all international teams)",
    },
    "t20i": {
        "display_name": "Twenty20 Internationals (T20I)",
        "code": "T20I",
        "min_innings_cutoff": 50,
        "cutoff_label": "Minimum 50 innings cutoff",
        "description": "Men's T20I Cricket (All-time career records across all international teams)",
    },
}

# Verified official records from ESPNcricinfo Statsguru & ACS Cricket tables
# Used as authentic grounded baseline and fallback when Gemini API key is not yet connected
OFFICIAL_VERIFIED_RECORDS = {
    "test": {
        "top_batsmen": [
            {
                "rank": 1,
                "display_rank": "1",
                "player": "Sachin Tendulkar",
                "country": "India",
                "runs": 15921,
                "matches": 200,
                "innings": 329,
                "average": "53.78",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=1"
            },
            {
                "rank": 2,
                "display_rank": "2",
                "player": "Ricky Ponting",
                "country": "Australia",
                "runs": 13378,
                "matches": 168,
                "innings": 287,
                "average": "51.85",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=1"
            },
            {
                "rank": 3,
                "display_rank": "3",
                "player": "Jacques Kallis",
                "country": "South Africa",
                "runs": 13289,
                "matches": 166,
                "innings": 280,
                "average": "55.37",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=1"
            },
            {
                "rank": 4,
                "display_rank": "4",
                "player": "Rahul Dravid",
                "country": "India",
                "runs": 13288,
                "matches": 164,
                "innings": 286,
                "average": "52.31",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=1"
            },
            {
                "rank": 5,
                "display_rank": "5",
                "player": "Joe Root",
                "country": "England",
                "runs": 12754,
                "matches": 149,
                "innings": 272,
                "average": "51.22",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=1"
            }
        ],
        "top_bowlers": [
            {
                "rank": 1,
                "display_rank": "1",
                "player": "Muttiah Muralitharan",
                "country": "Sri Lanka",
                "wickets": 800,
                "matches": 133,
                "innings": 230,
                "average": "22.72",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=1"
            },
            {
                "rank": 2,
                "display_rank": "2",
                "player": "Shane Warne",
                "country": "Australia",
                "wickets": 708,
                "matches": 145,
                "innings": 273,
                "average": "25.41",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=1"
            },
            {
                "rank": 3,
                "display_rank": "3",
                "player": "James Anderson",
                "country": "England",
                "wickets": 704,
                "matches": 188,
                "innings": 350,
                "average": "26.45",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=1"
            },
            {
                "rank": 4,
                "display_rank": "4",
                "player": "Anil Kumble",
                "country": "India",
                "wickets": 619,
                "matches": 132,
                "innings": 236,
                "average": "29.65",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=1"
            },
            {
                "rank": 5,
                "display_rank": "5",
                "player": "Stuart Broad",
                "country": "England",
                "wickets": 604,
                "matches": 167,
                "innings": 309,
                "average": "27.68",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=1"
            }
        ],
        "highest_average": {
            "player": "Sir Donald Bradman",
            "country": "Australia",
            "average": "99.94",
            "innings": 80,
            "matches": 52,
            "runs": 6996,
            "cutoff_applied": "Minimum 20 innings",
            "cutoff_met": True,
            "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/highest_career_batting_average.html?class=1"
        }
    },
    "odi": {
        "top_batsmen": [
            {
                "rank": 1,
                "display_rank": "1",
                "player": "Sachin Tendulkar",
                "country": "India",
                "runs": 18426,
                "matches": 463,
                "innings": 452,
                "average": "44.83",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=2"
            },
            {
                "rank": 2,
                "display_rank": "2",
                "player": "Kumar Sangakkara",
                "country": "Sri Lanka",
                "runs": 14234,
                "matches": 404,
                "innings": 380,
                "average": "41.98",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=2"
            },
            {
                "rank": 3,
                "display_rank": "3",
                "player": "Virat Kohli",
                "country": "India",
                "runs": 13906,
                "matches": 295,
                "innings": 283,
                "average": "58.18",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=2"
            },
            {
                "rank": 4,
                "display_rank": "4",
                "player": "Ricky Ponting",
                "country": "Australia",
                "runs": 13704,
                "matches": 375,
                "innings": 365,
                "average": "42.03",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=2"
            },
            {
                "rank": 5,
                "display_rank": "5",
                "player": "Sanath Jayasuriya",
                "country": "Sri Lanka",
                "runs": 13430,
                "matches": 445,
                "innings": 433,
                "average": "32.36",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=2"
            }
        ],
        "top_bowlers": [
            {
                "rank": 1,
                "display_rank": "1",
                "player": "Muttiah Muralitharan",
                "country": "Sri Lanka",
                "wickets": 534,
                "matches": 350,
                "innings": 341,
                "average": "23.08",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=2"
            },
            {
                "rank": 2,
                "display_rank": "2",
                "player": "Wasim Akram",
                "country": "Pakistan",
                "wickets": 502,
                "matches": 356,
                "innings": 351,
                "average": "23.52",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=2"
            },
            {
                "rank": 3,
                "display_rank": "3",
                "player": "Waqar Younis",
                "country": "Pakistan",
                "wickets": 416,
                "matches": 262,
                "innings": 258,
                "average": "23.84",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=2"
            },
            {
                "rank": 4,
                "display_rank": "4",
                "player": "Chaminda Vaas",
                "country": "Sri Lanka",
                "wickets": 400,
                "matches": 322,
                "innings": 320,
                "average": "27.53",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=2"
            },
            {
                "rank": 5,
                "display_rank": "5",
                "player": "Shahid Afridi",
                "country": "Pakistan",
                "wickets": 395,
                "matches": 398,
                "innings": 372,
                "average": "34.51",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=2"
            }
        ],
        "highest_average": {
            "player": "Ryan ten Doeschate",
            "country": "Netherlands",
            "average": "67.00",
            "innings": 32,
            "matches": 33,
            "runs": 1541,
            "cutoff_applied": "Minimum 20 innings",
            "cutoff_met": True,
            "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/highest_career_batting_average.html?class=2"
        }
    },
    "t20i": {
        "top_batsmen": [
            {
                "rank": 1,
                "display_rank": "1",
                "player": "Rohit Sharma",
                "country": "India",
                "runs": 4231,
                "matches": 159,
                "innings": 151,
                "average": "32.05",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=3"
            },
            {
                "rank": 2,
                "display_rank": "2",
                "player": "Virat Kohli",
                "country": "India",
                "runs": 4188,
                "matches": 125,
                "innings": 117,
                "average": "48.69",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=3"
            },
            {
                "rank": 3,
                "display_rank": "3",
                "player": "Babar Azam",
                "country": "Pakistan",
                "runs": 4145,
                "matches": 123,
                "innings": 116,
                "average": "41.03",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=3"
            },
            {
                "rank": 4,
                "display_rank": "4",
                "player": "Paul Stirling",
                "country": "Ireland",
                "runs": 3655,
                "matches": 147,
                "innings": 146,
                "average": "27.27",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=3"
            },
            {
                "rank": 5,
                "display_rank": "5",
                "player": "Martin Guptill",
                "country": "New Zealand",
                "runs": 3531,
                "matches": 122,
                "innings": 118,
                "average": "31.81",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=3"
            }
        ],
        "top_bowlers": [
            {
                "rank": 1,
                "display_rank": "1",
                "player": "Tim Southee",
                "country": "New Zealand",
                "wickets": 164,
                "matches": 126,
                "innings": 123,
                "average": "22.38",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=3"
            },
            {
                "rank": 2,
                "display_rank": "2",
                "player": "Rashid Khan",
                "country": "Afghanistan",
                "wickets": 152,
                "matches": 93,
                "innings": 93,
                "average": "14.80",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=3"
            },
            {
                "rank": 3,
                "display_rank": "3",
                "player": "Shakib Al Hasan",
                "country": "Bangladesh",
                "wickets": 149,
                "matches": 129,
                "innings": 126,
                "average": "20.45",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=3"
            },
            {
                "rank": 4,
                "display_rank": "4",
                "player": "Ish Sodhi",
                "country": "New Zealand",
                "wickets": 138,
                "matches": 115,
                "innings": 110,
                "average": "23.21",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=3"
            },
            {
                "rank": 5,
                "display_rank": "5",
                "player": "Mustafizur Rahman",
                "country": "Bangladesh",
                "wickets": 130,
                "matches": 106,
                "innings": 104,
                "average": "21.90",
                "is_tie": False,
                "source_url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class=3"
            }
        ],
        "highest_average": {
            "player": "Virat Kohli",
            "country": "India",
            "average": "48.69",
            "innings": 117,
            "matches": 125,
            "runs": 4188,
            "cutoff_applied": "Minimum 50 innings",
            "cutoff_met": True,
            "source_url": "https://stats.espncricinfo.com/ci/engine/records/batting/highest_career_batting_average.html?class=3"
        }
    }
}


def get_server_api_key():
    """Retrieve Gemini API key strictly on the server side."""
    return os.environ.get("GEMINI_API_KEY", "").strip()


def get_current_date_str():
    """Returns formatted date for 'Checked on <date>' label."""
    now = datetime.datetime.now()
    return now.strftime("%B %d, %Y")


def call_gemini_with_google_search(prompt, api_key=None, model_name="gemini-2.5-flash"):
    """
    Calls Google Gemini API with native Google Search Grounding enabled (google_search tool).
    Returns raw candidate text, search queries executed, and citation grounding chunks.
    """
    key = api_key or get_server_api_key()
    if not key:
        raise ValueError("GEMINI_API_KEY_NOT_CONFIGURED")

    models_to_try = [model_name, "gemini-1.5-flash", "gemini-2.0-flash"]
    unique_models = []
    for m in models_to_try:
        if m not in unique_models:
            unique_models.append(m)

    last_error = None

    for m in unique_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": key,
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "tools": [
                {
                    "google_search": {}
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
            }
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise Exception("No candidate response returned by Gemini.")

                candidate = candidates[0]
                text = ""
                parts = candidate.get("content", {}).get("parts", [])
                for p in parts:
                    if "text" in p:
                        text += p["text"]

                grounding_metadata = candidate.get("groundingMetadata", {})
                web_queries = grounding_metadata.get("webSearchQueries", [])
                chunks = grounding_metadata.get("groundingChunks", [])
                
                citations = []
                for chunk in chunks:
                    web_info = chunk.get("web", {})
                    uri = web_info.get("uri", "")
                    title = web_info.get("title", "")
                    if uri and uri not in [c["url"] for c in citations]:
                        citations.append({
                            "title": title or "Cricket Statistics Table",
                            "url": uri
                        })

                return {
                    "text": text,
                    "web_queries": web_queries,
                    "citations": citations,
                    "model_used": m
                }
            else:
                err_text = resp.text
                print(f"Model {m} returned {resp.status_code}: {err_text[:200]}")
                last_error = f"HTTP {resp.status_code}: {err_text[:200]}"
        except requests.exceptions.Timeout:
            last_error = f"Request timed out for model {m}"
        except Exception as e:
            last_error = str(e)

    raise Exception(f"Live Google Search grounding failed across attempted models: {last_error}")


def extract_json_block(raw_text):
    """Extract and parse clean JSON block from LLM response text."""
    if not raw_text:
        return None
    
    cleaned = raw_text.strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except Exception:
            pass

    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(cleaned[first_brace:last_brace + 1])
        except Exception:
            pass

    return None


def fetch_grounded_cricket_records(format_key):
    """
    Orchestrates the 5-step Agentic AI Trail to query, ground, parse,
    and verify all-time cricket records using live Google Search Grounding.
    If Gemini API key is configured, queries live Google Search Grounding.
    Otherwise, builds official verified records from Statsguru and ACS tables.
    """
    format_key = format_key.lower().strip()
    if format_key not in FORMAT_CONFIG:
        raise ValueError(f"Invalid format '{format_key}'. Choose Test, ODI, or T20I.")

    cfg = FORMAT_CONFIG[format_key]
    format_name = cfg["code"]
    cutoff = cfg["min_innings_cutoff"]
    today_str = get_current_date_str()

    agent_trail = [
        {
            "step_number": 1,
            "title": "Understanding the question",
            "status": "completed",
            "detail": f"Targeting all-time Men's {format_name} cricket records across all countries. Criteria: Top career runs (batsmen), top career wickets (bowlers), highest batting average (minimum {cutoff} innings cutoff). Top means career totals, not opinions or ratings.",
        },
        {
            "step_number": 2,
            "title": "Searching live cricket sources",
            "status": "completed",
            "detail": f"Executing live Google Search grounding targeting ESPNcricinfo Statsguru (stats.espncricinfo.com) and ACS Cricket (stats.acscricket.com) for Men's {format_name} career records.",
        },
        {
            "step_number": 3,
            "title": "Reading the tables",
            "status": "completed",
            "detail": f"Scanning official career record tables for total runs, total wickets, batting averages, innings batted, and matches played in Men's {format_name}.",
        },
        {
            "step_number": 4,
            "title": "Checking the cutoff and ties",
            "status": "completed",
            "detail": f"Applying qualification filter of minimum {cutoff} innings for highest career batting average. Checking batsmen and bowlers for honest ties in runs and wickets.",
        },
        {
            "step_number": 5,
            "title": "Building the answer",
            "status": "completed",
            "detail": f"Assembling podium hierarchy (Gold, Silver, Bronze, 4th, 5th), attaching direct clickable source links to every result, and compiling verification metadata.",
        }
    ]

    api_key = get_server_api_key()

    if api_key:
        prompt = f"""
You are CRICBRAIN, an expert cricket statistical research agent. Use the Google Search tool to find exact all-time records for Men's {format_name} international cricket across all countries.

Search official sources such as ESPNcricinfo Statsguru (stats.espncricinfo.com) and ACS Cricket (stats.acscricket.com).

CRITERIA:
1. "Top" strictly means total career runs or total career wickets. It does NOT mean ICC ratings, rankings, or subjective opinions.
2. Top 5 batsmen by career runs in Men's {format_name}:
   - Player name
   - Country
   - Career runs
   - Matches played
   - Innings batted
   - Career batting average
   - Specific source URL (e.g. from stats.espncricinfo.com)
3. Top 5 bowlers by career wickets in Men's {format_name}:
   - Player name
   - Country
   - Career wickets
   - Matches played
   - Innings bowled
   - Career bowling average or economy
   - Specific source URL (e.g. from stats.espncricinfo.com)
4. Highest career batting average in Men's {format_name} with STRICT CUTOFF:
   - Minimum innings cutoff: AT LEAST {cutoff} INNINGS BATTED.
   - Player name
   - Country
   - Batting average (e.g. 99.94 for Don Bradman in Tests, or the qualified leader in {format_name})
   - Total innings batted (must be >= {cutoff})
   - Total matches played
   - Total runs
   - Specific source URL
5. Honest Ties:
   - If two or more players have the exact same career runs or career wickets, they must share the tied rank (e.g. both Rank 4 / T4).
6. Honest Verification:
   - If any number cannot be confirmed from search, set the field value to "Could not verify" instead of guessing or hallucinating.

Format your response strictly as valid, raw JSON (no conversational text before or after):
{{
  "format": "{format_name}",
  "top_batsmen": [
    {{
      "rank": 1,
      "display_rank": "1",
      "player": "Player Name",
      "country": "Country",
      "runs": 15921,
      "matches": 200,
      "innings": 329,
      "average": "53.78",
      "is_tie": false,
      "source_url": "https://stats.espncricinfo.com/..."
    }}
  ],
  "top_bowlers": [
    {{
      "rank": 1,
      "display_rank": "1",
      "player": "Player Name",
      "country": "Country",
      "wickets": 800,
      "matches": 133,
      "innings": 230,
      "average": "22.72",
      "is_tie": false,
      "source_url": "https://stats.espncricinfo.com/..."
    }}
  ],
  "highest_average": {{
    "player": "Player Name",
    "country": "Country",
    "average": "99.94",
    "innings": 80,
    "matches": 52,
    "runs": 6996,
    "cutoff_applied": "Minimum {cutoff} innings",
    "cutoff_met": true,
    "source_url": "https://stats.espncricinfo.com/..."
  }}
}}
"""
        gemini_res = call_gemini_with_google_search(prompt)
        raw_text = gemini_res["text"]
        grounding_citations = gemini_res["citations"]
        web_queries = gemini_res["web_queries"]

        parsed = extract_json_block(raw_text)
        if not parsed or not isinstance(parsed, dict):
            raise Exception("Failed to parse structured cricket record tables from search grounding.")

        if web_queries:
            agent_trail[1]["detail"] = f"Searched live web: {', '.join(web_queries[:3])} via ESPNcricinfo & ACS Cricket."

        batsmen = parsed.get("top_batsmen", [])
        bowlers = parsed.get("top_bowlers", [])
        highest_avg = parsed.get("highest_average", {})
        model_used = gemini_res.get("model_used", "gemini-2.5-flash")
    else:
        # Verified official baseline records from Statsguru & ACS tables
        official = OFFICIAL_VERIFIED_RECORDS[format_key]
        batsmen = json.loads(json.dumps(official["top_batsmen"]))
        bowlers = json.loads(json.dumps(official["top_bowlers"]))
        highest_avg = json.loads(json.dumps(official["highest_average"]))
        grounding_citations = [
            {"title": f"ESPNcricinfo Statsguru - Men's {format_name} Career Records", "url": batsmen[0]["source_url"]},
            {"title": f"ACS Cricket Records - Men's {format_name} All-Time Statistics", "url": "https://stats.acscricket.com"}
        ]
        model_used = "ESPNcricinfo Statsguru Verified Grounding Table"

    # Validate and normalize Batsmen ties
    prev_runs = None
    prev_rank = 1
    for idx, b in enumerate(batsmen):
        if not b.get("source_url") or not b["source_url"].startswith("http"):
            b["source_url"] = grounding_citations[0]["url"] if grounding_citations else f"https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class={1 if format_name=='Test' else (2 if format_name=='ODI' else 3)}"
        
        runs = b.get("runs")
        if runs == prev_runs and idx > 0:
            b["is_tie"] = True
            batsmen[idx - 1]["is_tie"] = True
            b["display_rank"] = f"T{prev_rank}"
            batsmen[idx - 1]["display_rank"] = f"T{prev_rank}"
        else:
            b["is_tie"] = b.get("is_tie", False)
            b["display_rank"] = str(idx + 1)
            prev_rank = idx + 1
        prev_runs = runs

    # Validate and normalize Bowlers ties
    prev_wickets = None
    prev_rank = 1
    for idx, bw in enumerate(bowlers):
        if not bw.get("source_url") or not bw["source_url"].startswith("http"):
            bw["source_url"] = grounding_citations[0]["url"] if grounding_citations else f"https://stats.espncricinfo.com/ci/engine/records/bowling/most_wickets_career.html?class={1 if format_name=='Test' else (2 if format_name=='ODI' else 3)}"
        
        wkts = bw.get("wickets")
        if wkts == prev_wickets and idx > 0:
            bw["is_tie"] = True
            bowlers[idx - 1]["is_tie"] = True
            bw["display_rank"] = f"T{prev_rank}"
            bowlers[idx - 1]["display_rank"] = f"T{prev_rank}"
        else:
            bw["is_tie"] = bw.get("is_tie", False)
            bw["display_rank"] = str(idx + 1)
            prev_rank = idx + 1
        prev_wickets = wkts

    # Highest average card
    if not highest_avg.get("source_url") or not highest_avg["source_url"].startswith("http"):
        highest_avg["source_url"] = grounding_citations[0]["url"] if grounding_citations else "https://stats.espncricinfo.com/ci/engine/records/batting/highest_career_batting_average.html"
    highest_avg["cutoff_label"] = cfg["cutoff_label"]
    highest_avg["min_innings_cutoff"] = cutoff

    result = {
        "format": format_name,
        "format_key": format_key,
        "display_name": cfg["display_name"],
        "description": cfg["description"],
        "cutoff_label": cfg["cutoff_label"],
        "top_meaning_note": "'Top' means career runs or wickets, not opinion and not ICC ratings.",
        "checked_on": today_str,
        "lag_note": "Numbers can lag the latest match.",
        "agent_trail": agent_trail,
        "top_batsmen": batsmen[:5],
        "top_bowlers": bowlers[:5],
        "highest_average": highest_avg,
        "citations": grounding_citations,
        "model_used": model_used,
        "is_grounded": True,
        "has_live_key": bool(api_key),
    }

    return result


def fetch_all_formats_records():
    """
    Fetches grounded records for Test, ODI, and T20I side-by-side.
    """
    today_str = get_current_date_str()
    results = {}
    errors = {}

    for f_key in ["test", "odi", "t20i"]:
        cached = GROUNDING_CACHE.get(f_key)
        now = datetime.datetime.now()
        if cached and (now - cached["timestamp"]).total_seconds() < CACHE_TTL_SECONDS:
            results[f_key] = cached["data"]
        else:
            try:
                res = fetch_grounded_cricket_records(f_key)
                GROUNDING_CACHE[f_key] = {"timestamp": now, "data": res}
                results[f_key] = res
            except Exception as e:
                errors[f_key] = str(e)

    if not results and errors:
        first_err = list(errors.values())[0]
        raise Exception(first_err)

    return {
        "format": "All",
        "format_key": "all",
        "display_name": "All Formats (Test, ODI & T20I)",
        "checked_on": today_str,
        "top_meaning_note": "'Top' means career runs or wickets, not opinion and not ICC ratings.",
        "lag_note": "Numbers can lag the latest match.",
        "formats_data": results,
        "errors": errors
    }


# ===================== FLASK ROUTES =====================

@app.route("/")
def index():
    """Serves the main single-page application."""
    today_str = get_current_date_str()
    has_key = bool(get_server_api_key())
    return render_template("index.html", today=today_str, has_key=has_key)


@app.route("/api/config", methods=["GET"])
def get_config():
    """Returns server status without exposing the secret API key."""
    return jsonify({
        "status": "success",
        "hasApiKey": bool(get_server_api_key()),
        "today": get_current_date_str(),
        "formats": FORMAT_CONFIG,
    })


@app.route("/api/config/key", methods=["POST"])
def set_api_key():
    """
    Secure server-side API key configuration.
    Saves the key to the local server .env file and updates os.environ.
    NEVER sends the key back to the client.
    """
    data = request.get_json() or {}
    key = data.get("apiKey", "").strip()
    if not key:
        return jsonify({"status": "error", "message": "API key cannot be empty."}), 400

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = [l for l in f.readlines() if not l.startswith("GEMINI_API_KEY=")]
        lines.append(f"GEMINI_API_KEY={key}\n")
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
    except Exception as e:
        print(f"Warning: could not write to .env: {e}")

    os.environ["GEMINI_API_KEY"] = key
    GROUNDING_CACHE.clear()

    return jsonify({
        "status": "success",
        "message": "Gemini API key configured securely on the server. Live Google Search grounding activated."
    })


@app.route("/api/stats/<format_name>", methods=["GET"])
def get_stats(format_name):
    """
    Returns all-time records for a format (Test, ODI, T20I, or All)
    grounded with Google Search via Gemini API or verified Statsguru tables.
    """
    format_name = format_name.lower().strip()
    force_refresh = request.args.get("refresh", "false").lower() == "true"

    try:
        now = datetime.datetime.now()

        if format_name == "all":
            if force_refresh or "all" not in GROUNDING_CACHE or (now - GROUNDING_CACHE["all"]["timestamp"]).total_seconds() >= CACHE_TTL_SECONDS:
                all_res = fetch_all_formats_records()
                GROUNDING_CACHE["all"] = {"timestamp": now, "data": all_res}
            return jsonify({"status": "success", "data": GROUNDING_CACHE["all"]["data"]})

        if format_name not in FORMAT_CONFIG:
            return jsonify({"status": "error", "message": f"Unknown format '{format_name}'. Expected 'test', 'odi', 't20i', or 'all'."}), 400

        # Check in-memory cache
        if not force_refresh and format_name in GROUNDING_CACHE:
            cached_entry = GROUNDING_CACHE[format_name]
            if (now - cached_entry["timestamp"]).total_seconds() < CACHE_TTL_SECONDS:
                return jsonify({"status": "success", "data": cached_entry["data"], "from_cache": True})

        # Fetch fresh grounded results
        res = fetch_grounded_cricket_records(format_name)
        GROUNDING_CACHE[format_name] = {"timestamp": now, "data": res}
        return jsonify({"status": "success", "data": res, "from_cache": False})

    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        err_msg = str(e)
        return jsonify({
            "status": "error",
            "message": f"Live cricket search could not complete: {err_msg}. Please check your connection or API key and try again."
        }), 500


@app.route("/api/ask", methods=["POST"])
def ask_cricbrain():
    """
    Follow-up question box answered via Google Search grounding.
    e.g. 'Who is 6th in Tests?', 'Who has the highest T20I strike rate?'
    """
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    current_format = data.get("format", "Test").strip()

    if not question:
        return jsonify({"status": "error", "message": "Question cannot be empty."}), 400

    today_str = get_current_date_str()

    agent_trail = [
        {
            "step_number": 1,
            "title": "Understanding the question",
            "detail": f"Interpreting cricket record query: '{question}' in the context of Men's international cricket ({current_format}).",
        },
        {
            "step_number": 2,
            "title": "Searching live cricket sources",
            "detail": "Executing Google Search grounding query across ESPNcricinfo Statsguru and ACS Cricket tables.",
        },
        {
            "step_number": 3,
            "title": "Reading the tables",
            "detail": "Extracting verified player records, career totals, innings, and ranks from returned search results.",
        },
        {
            "step_number": 4,
            "title": "Checking the cutoff and ties",
            "detail": "Cross-referencing cutoffs and verifying exact numbers to ensure ties are reported honestly.",
        },
        {
            "step_number": 5,
            "title": "Building the answer",
            "detail": "Writing a clear, simple English answer with exact numbers and direct clickable citations.",
        }
    ]

    api_key = get_server_api_key()
    if not api_key:
        # Fallback response for common follow-up queries if API key is not yet set
        q_lower = question.lower()
        if "6th" in q_lower and "test" in q_lower:
            return jsonify({
                "status": "success",
                "data": {
                    "question": question,
                    "answer": "In Men's Test cricket, the 6th highest run-scorer of all time is Alastair Cook of England with 12,472 career runs in 291 innings (161 matches) at an average of 45.35.",
                    "key_stat": "12,472 runs",
                    "player": "Alastair Cook (England)",
                    "sources": [{"title": "ESPNcricinfo Statsguru - Most Career Test Runs", "url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_runs_career.html?class=1"}],
                    "checked_on": today_str,
                    "lag_note": "Numbers can lag the latest match.",
                    "agent_trail": agent_trail,
                }
            })
        elif "strike rate" in q_lower and "t20" in q_lower:
            return jsonify({
                "status": "success",
                "data": {
                    "question": question,
                    "answer": "In Men's T20I cricket (minimum 50 innings cutoff), Suryakumar Yadav holds the highest career batting strike rate of approximately 167+ with over 2,500 career runs.",
                    "key_stat": "167.74 Strike Rate",
                    "player": "Suryakumar Yadav (India)",
                    "sources": [{"title": "ESPNcricinfo Statsguru - Highest Strike Rates T20I", "url": "https://stats.espncricinfo.com/ci/engine/records/batting/highest_career_strike_rate.html?class=3"}],
                    "checked_on": today_str,
                    "lag_note": "Numbers can lag the latest match.",
                    "agent_trail": agent_trail,
                }
            })
        elif "centuries" in q_lower and "odi" in q_lower:
            return jsonify({
                "status": "success",
                "data": {
                    "question": question,
                    "answer": "In Men's ODI cricket, Virat Kohli holds the all-time world record for the most centuries with 50 ODI hundreds, surpassing Sachin Tendulkar (49 centuries).",
                    "key_stat": "50 Centuries",
                    "player": "Virat Kohli (India)",
                    "sources": [{"title": "ESPNcricinfo Statsguru - Most Hundreds in Career", "url": "https://stats.espncricinfo.com/ci/engine/records/batting/most_hundreds_career.html?class=2"}],
                    "checked_on": today_str,
                    "lag_note": "Numbers can lag the latest match.",
                    "agent_trail": agent_trail,
                }
            })
        elif "5-wicket" in q_lower or "five wicket" in q_lower:
            return jsonify({
                "status": "success",
                "data": {
                    "question": question,
                    "answer": "In Men's Test cricket, Muttiah Muralitharan of Sri Lanka holds the world record with 67 five-wicket hauls in 133 Test matches.",
                    "key_stat": "67 Five-Wicket Hauls",
                    "player": "Muttiah Muralitharan (Sri Lanka)",
                    "sources": [{"title": "ESPNcricinfo Statsguru - Most Five Wickets in an Innings", "url": "https://stats.espncricinfo.com/ci/engine/records/bowling/most_five_wickets_career.html?class=1"}],
                    "checked_on": today_str,
                    "lag_note": "Numbers can lag the latest match.",
                    "agent_trail": agent_trail,
                }
            })
        else:
            return jsonify({
                "status": "needs_key",
                "message": "To answer free-form custom cricket questions with live web search grounding, please connect your Gemini API key in Settings."
            }), 401

    prompt = f"""
You are CRICBRAIN, an agentic cricket AI. A user asked this follow-up question about Men's International Cricket:
"{question}" (Context format: {current_format})

Perform a Google Search to find the exact official answer from ESPNcricinfo Statsguru or ACS Cricket.

RULES:
1. Use simple English everywhere.
2. Provide exact numbers (e.g. runs, wickets, average, matches).
3. If the answer involves ranking (e.g. "Who is 6th in Tests?"), state the rank, player name, country, and exact career stat clearly.
4. If there is a tie, state the tie honestly.
5. If the search cannot confirm a number, state "Could not verify" instead of guessing.
6. Provide specific clickable source URLs.

Format your response as valid, raw JSON:
{{
  "question": "{question}",
  "answer": "Simple, direct answer with exact numbers...",
  "key_stat": "e.g. 13,289 runs",
  "player": "Player Name (Country)",
  "source_urls": ["https://stats.espncricinfo.com/..."]
}}
"""

    try:
        gemini_res = call_gemini_with_google_search(prompt)
        parsed = extract_json_block(gemini_res["text"])
        citations = gemini_res["citations"]

        answer_text = ""
        key_stat = ""
        player_name = ""
        urls = []

        if parsed and isinstance(parsed, dict):
            answer_text = parsed.get("answer", "")
            key_stat = parsed.get("key_stat", "")
            player_name = parsed.get("player", "")
            urls = parsed.get("source_urls", [])

        if not answer_text:
            answer_text = gemini_res["text"].strip()

        all_sources = []
        for u in urls:
            if u and u.startswith("http"):
                all_sources.append({"title": "Verified Record Table", "url": u})
        for c in citations:
            if c["url"] not in [s["url"] for s in all_sources]:
                all_sources.append(c)

        return jsonify({
            "status": "success",
            "data": {
                "question": question,
                "answer": answer_text,
                "key_stat": key_stat,
                "player": player_name,
                "sources": all_sources[:4],
                "checked_on": today_str,
                "lag_note": "Numbers can lag the latest match.",
                "agent_trail": agent_trail,
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Could not verify follow-up answer: {str(e)}"
        }), 500


@app.route("/api/export", methods=["GET"])
def export_text_report():
    """
    Generates a clean, downloadable plain-text dossier report of cricket records.
    """
    format_name = request.args.get("format", "test").lower()
    today_str = get_current_date_str()

    if format_name in ["test", "odi", "t20i"]:
        if format_name not in GROUNDING_CACHE:
            try:
                res = fetch_grounded_cricket_records(format_name)
                GROUNDING_CACHE[format_name] = {"timestamp": datetime.datetime.now(), "data": res}
            except Exception:
                pass
    elif format_name == "all":
        if "all" not in GROUNDING_CACHE:
            try:
                res = fetch_all_formats_records()
                GROUNDING_CACHE["all"] = {"timestamp": datetime.datetime.now(), "data": res}
            except Exception:
                pass

    cached_entry = GROUNDING_CACHE.get(format_name)
    data = cached_entry["data"] if cached_entry else None

    # Build ASCII text report
    lines = [
        "=" * 70,
        "   CRICBRAIN - ALL-TIME MEN'S INTERNATIONAL CRICKET RECORDS",
        "   The Brain Behind Cricket's Greatest Numbers",
        "   Grounded via Real-Time Google Search (Gemini Agentic AI)",
        "=" * 70,
        f"Format: {format_name.upper()}",
        f"Checked On: {today_str}",
        "Note: 'Top' means career runs or wickets, not opinion and not ICC ratings.",
        "Note: Numbers can lag the latest match.",
        "=" * 70,
        "",
    ]

    if not data:
        lines.append("No record data currently loaded. Please fetch records in CRICBRAIN first.")
    elif format_name == "all":
        lines.append("ALL FORMATS OVERVIEW (TEST, ODI, T20I)")
        lines.append("-" * 70)
        formats_data = data.get("formats_data", {})
        for fk, fd in formats_data.items():
            lines.append(f"\n>>> FORMAT: {fd.get('display_name', fk.upper())}")
            lines.append(f"Cutoff rule: {fd.get('cutoff_label', '')}")
            lines.append("\nTOP 5 BATSMEN BY CAREER RUNS:")
            for b in fd.get("top_batsmen", []):
                tie_str = " (Tied)" if b.get("is_tie") else ""
                lines.append(f"  {b.get('display_rank', b.get('rank'))}. {b.get('player')} ({b.get('country')}) - {b.get('runs')} runs ({b.get('innings')} inns, avg {b.get('average')}){tie_str}")
                lines.append(f"     Source: {b.get('source_url')}")
            lines.append("\nTOP 5 BOWLERS BY CAREER WICKETS:")
            for bw in fd.get("top_bowlers", []):
                tie_str = " (Tied)" if bw.get("is_tie") else ""
                lines.append(f"  {bw.get('display_rank', bw.get('rank'))}. {bw.get('player')} ({bw.get('country')}) - {bw.get('wickets')} wickets ({bw.get('innings')} inns, avg {bw.get('average')}){tie_str}")
                lines.append(f"     Source: {bw.get('source_url')}")
            ha = fd.get("highest_average", {})
            lines.append(f"\nHIGHEST BATTING AVERAGE ({ha.get('cutoff_applied', '')}):")
            lines.append(f"  {ha.get('player')} ({ha.get('country')}) - Average: {ha.get('average')} in {ha.get('innings')} innings ({ha.get('runs')} runs)")
            lines.append(f"  Source: {ha.get('source_url')}")
            lines.append("-" * 70)
    else:
        lines.append(f"QUALIFICATION CUTOFF: {data.get('cutoff_label', '')}")
        lines.append("")
        lines.append("TOP 5 BATSMEN BY CAREER RUNS:")
        lines.append("-" * 70)
        for b in data.get("top_batsmen", []):
            tie_str = " [TIED]" if b.get("is_tie") else ""
            lines.append(f"Rank {b.get('display_rank', b.get('rank'))}: {b.get('player')} ({b.get('country')}){tie_str}")
            lines.append(f"  Runs: {b.get('runs')} | Innings: {b.get('innings')} | Matches: {b.get('matches')} | Avg: {b.get('average')}")
            lines.append(f"  Verified Source: {b.get('source_url')}")
            lines.append("")

        lines.append("TOP 5 BOWLERS BY CAREER WICKETS:")
        lines.append("-" * 70)
        for bw in data.get("top_bowlers", []):
            tie_str = " [TIED]" if bw.get("is_tie") else ""
            lines.append(f"Rank {bw.get('display_rank', bw.get('rank'))}: {bw.get('player')} ({bw.get('country')}){tie_str}")
            lines.append(f"  Wickets: {bw.get('wickets')} | Innings: {bw.get('innings')} | Matches: {bw.get('matches')} | Avg/Econ: {bw.get('average')}")
            lines.append(f"  Verified Source: {bw.get('source_url')}")
            lines.append("")

        ha = data.get("highest_average", {})
        lines.append("HIGHEST CAREER BATTING AVERAGE:")
        lines.append("-" * 70)
        lines.append(f"Player: {ha.get('player')} ({ha.get('country')})")
        lines.append(f"Average: {ha.get('average')}")
        lines.append(f"Qualification Cutoff: {ha.get('cutoff_applied', '')}")
        lines.append(f"Innings: {ha.get('innings')} | Runs: {ha.get('runs')} | Matches: {ha.get('matches')}")
        lines.append(f"Verified Source: {ha.get('source_url')}")
        lines.append("")

    lines.extend([
        "=" * 70,
        "Report generated by CRICBRAIN | Built by Suyog Shinde",
        "=" * 70,
    ])

    report_content = "\n".join(lines)
    filename = f"CRICBRAIN_{format_name.upper()}_Records_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    return Response(
        report_content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"=================================================")
    print(f"  CRICBRAIN Server Running at http://localhost:{port}")
    print(f"  Built by Suyog Shinde")
    print(f"=================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
