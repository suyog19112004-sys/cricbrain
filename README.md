# CRICBRAIN 🏏
> **The brain behind cricket's greatest numbers.**  
> *Built by Suyog Shinde*

An agentic AI web application that discovers and verifies all-time men's international cricket career records across **Test**, **ODI**, and **T20I** cricket, powered by real-time Google Search grounding (Gemini API with the `google_search` tool). Written in simple English everywhere.

---

## 🌟 Features & Highlights

### 1. What the App Does
- **Format Selector:** Test, ODI, T20I (Men's International Cricket, all countries).
- **All Formats Side-by-Side:** A 3-column view comparing Test, ODI, and T20I simultaneously.
- **Top 5 Batsmen by Career Runs:** Rank, Player Name, Country, Total Runs, Matches, Innings, Career Average, and clickable source links.
- **Top 5 Bowlers by Career Wickets:** Rank, Player Name, Country, Total Wickets, Matches, Innings, Career Average, and clickable source links.
- **Highest Career Batting Average:** With strictly enforced minimum-innings cutoffs:
  - **Test:** Minimum 20 innings (e.g. Sir Donald Bradman, 99.94)
  - **ODI:** Minimum 20 innings (e.g. Ryan ten Doeschate, 67.00)
  - **T20I:** Minimum 50 innings (e.g. Virat Kohli, 48.69)
- **Clear Record Definition:** On-screen notice clearly states:  
  `"Top" means career runs or wickets, not opinion and not ICC ratings.`
- **Honest Ties:** When two players have identical runs or wickets, they are displayed honestly as tied at the same rank (e.g., `🤝 Tied Rank T4`).
- **Lag & Verification Notices:** Every view includes `"Checked on <today's date>"` and `"Numbers can lag the latest match."` Unconfirmed numbers show `"Could not verify"`.
- **"Ask CRICBRAIN" Follow-up Box:** Grounded Q&A assistant to answer queries like *"Who is 6th in Tests?"*, *"Highest T20I strike rate?"*, and *"Most ODI centuries?"*.
- **Download & Print Dossier:** Export official plain-text `.txt` report or print clean PDF format (`Save as PDF`).

### 2. 3D Stadium Landing Page
- **Atmospheric Stadium Aesthetic:** Floodlights at night, deep navy (`#050b18`), pitch green (`#0f5132`), cricket-ball red (`#991b1b`), and gold accents (`#f59e0b`).
- **3D Interactive Cricket Ball (Three.js):**
  - Red leather sphere with procedural stitching and raised white equatorial seam.
  - Interactive mouse and touch parallax tilt physics.
  - Automatic CSS 3D fallback for devices without WebGL or with reduced motion enabled.
- **Floating 3D Stumps, Bails & Willow Bat:** Drift gently with harmonic oscillation in the stadium background.
- **3D Perspective Pitch Strip:** 22-yard strip with bowling crease and popping creases that tilts and tracks as you scroll down the page.
- **Glowing Floodlight Beams:** Translucent light cones in stadium corners with subtle volumetric dust.
- **Animated Teaser Counters:** Ticking up to famous numbers (e.g., 15,921 runs, 800 wickets, 99.94 average), clearly marked as teasers.
- **"Start the Innings" Action & "SIX!" Burst:** Explosive confetti burst and celebration banner when records load.
- **Permanent Footer:** `"Built by Suyog Shinde"` visible on all pages and printouts.

### 3. Agentic AI Behaviour & Security
- **Server-Side Grounding:** Uses Google Gemini API with native `google_search` tool.
- **5-Step Live Agent Trail:**
  1. *Understanding the question*
  2. *Searching live cricket sources* (ESPNcricinfo Statsguru & ACS Cricket tables)
  3. *Reading the tables*
  4. *Checking the cutoff and ties*
  5. *Building the answer*
- **Absolute API Key Security:** The API key is stored **only on the server** in `.env` or system environment. It is **never** sent to the client, never visible in page source, and never included in JavaScript bundles.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+ installed on your system.
- Required packages: `flask`, `requests`, `python-dotenv`.

### Quick Start (Windows)
Double-click `run.bat` or run:
```powershell
python app.py
```
Then open [http://localhost:5050](http://localhost:5050) in your web browser.

### Activating Live Google Search Grounding
1. Click the **"Settings"** or **"Connect Gemini API Key"** button in the header.
2. Enter your Google Gemini API key.
3. The key is securely saved to your local `.env` file on the server and immediately activates real-time Google Search grounding.

---

## 🧪 Automated Test Suite

To run the verification test suite:
```powershell
python test_app.py
```
Tests pass all 8 requirements:
1. `test_1_all_formats_load` - Test, ODI, T20I, and All Formats load with full podiums and highest average.
2. `test_2_sources_appear_as_links` - Clickable source links present on every single result.
3. `test_3_cutoff_labels_visible` - Minimum innings cutoff labels verified for Test (20), ODI (20), and T20I (50).
4. `test_4_ties_display_correctly` - Honest tie detection verified with tied rank badges.
5. `test_5_error_shows_friendly_message` - Friendly error handling for invalid queries.
6. `test_6_no_api_key_visible_in_page_source` - Strict verification that no API key or prefix leaks in HTML or API responses.
7. `test_7_built_by_suyog_shinde_visible` - Footer attribution verified.
8. `test_8_top_means_career_runs_or_wickets_on_screen` - Mandatory definition verified.

---

## 📁 Project Structure
```
cricbrain/
├── app.py                  # Flask backend with Gemini Search Grounding & tie/cutoff logic
├── run.bat                 # One-click Windows runner
├── test_app.py             # Complete test suite
├── README.md               # Documentation
├── static/
│   ├── css/
│   │   └── style.css       # Stadium floodlights, 3D tilt cards, podiums, print CSS
│   └── js/
│       ├── ball3d.js       # Three.js 3D ball, bat, stumps, pitch strip, mouse parallax
│       └── app.js          # Live agent trail, format tabs, "SIX!" burst, Ask CRICBRAIN
└── templates/
    └── index.html          # Main application page
```

---
*Built with ❤️ for cricket fans by **Suyog Shinde**.*
