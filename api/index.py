import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from groq import Groq
from dotenv import load_dotenv
from supabase import create_client, Client
import pypdf
import json

# Load environment variables from local .env file
load_dotenv()

# Fail-safe template path lookup to support raw root layout configuration across environments
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSSIBLE_PATHS = [
    os.path.abspath(os.path.join(BASE_DIR, '../templates')),  # Standard local development layout
    os.path.abspath(os.path.join(BASE_DIR, 'templates')),     # Flattened serverless runtime layout
    os.path.abspath(os.path.join(os.getcwd(), 'templates'))   # Root working directory fallback layout
]

TEMPLATE_DIR = POSSIBLE_PATHS[0]
for path in POSSIBLE_PATHS:
    if os.path.exists(os.path.join(path, 'index.html')):
        TEMPLATE_DIR = path
        break

app = Flask(__name__, template_folder=TEMPLATE_DIR)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "resumerise-ai-default-key-2026")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Initialize clients securely using verified environment variables
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

@app.route('/')
def home():
    """Renders the main application dashboard configuration with session payload context."""
    user = session.get('user')
    return render_template('index.html', user=user)

@app.route('/auth')
def auth_page():
    """Renders the toggleable Login and Registration structural portal interface."""
    if session.get('user'):
        return redirect(url_for('home'))
    return render_template('auth.html', supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

@app.route('/auth/callback')
def auth_callback():
    """Renders a secure client-side intermediary token synchronization screen."""
    return render_template('callback.html', supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

@app.route('/logout')
def logout():
    """Clears localized identity parameters and routes back to the root application instance."""
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/api/auth/set_session', methods=['POST'])
def api_set_session():
    """Registers authentication payload objects natively within the Flask application architecture."""
    data = request.get_json() or {}
    user_data = data.get('user')
    if user_data:
        session['user'] = user_data
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Invalid token session initialization dataset"}), 400

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """Verifies existing credentials against the data cluster or requests signup direction."""
    if not supabase:
        return jsonify({"status": "error", "message": "Supabase structural integration missing."}), 500
    
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"status": "error", "message": "Credentials criteria are unfulfilled."}), 400

    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        session['user'] = {
            "id": res.user.id,
            "email": res.user.email
        }
        return jsonify({"status": "success", "message": "Identity verification approved."})
    except Exception as e:
        err_str = str(e)
        if "Invalid login credentials" in err_str or "User not found" in err_str:
            return jsonify({
                "status": "not_found", 
                "message": "Account metrics are unrecognized. Forwarding vector to registration portal..."
            })
        return jsonify({"status": "error", "message": err_str}), 400

@app.route('/api/auth/signup', methods=['POST'])
def api_signup():
    """Appends explicit registration definitions directly into the Supabase authorization tables."""
    if not supabase:
        return jsonify({"status": "error", "message": "Supabase structural integration missing."}), 500

    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"status": "error", "message": "Registration criteria are unfulfilled."}), 400

    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            session['user'] = {
                "id": res.user.id,
                "email": res.user.email
            }
            return jsonify({"status": "success", "message": "Account compilation processed successfully."})
        return jsonify({"status": "error", "message": "Verification parameters required or compilation failure."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/analyze', methods=['POST'])
def analyze_resume():
    """
    Gathers student text inputs, target career profiles, and regional details,
    then processes them via Groq's active production engine using JSON mode.
    """
    if not GROQ_API_KEY or not groq_client:
        return jsonify({
            "status": "error", 
            "message": "Groq API Key is missing! Check your local .env configuration."
        }), 500

    resume_text = ""

    # 1. Process uploaded PDF files if attached
    if 'resume_file' in request.files and request.files['resume_file'].filename != '':
        file = request.files['resume_file']
        try:
            pdf_reader = pypdf.PdfReader(file)
            resume_text = "\n".join([page.extract_text() for page in pdf_reader.pages])
        except Exception as e:
            return jsonify({"status": "error", "message": f"Failed to parse PDF file: {str(e)}"}), 400
    else:
        # Fall back to reading pasted form raw text entries
        resume_text = request.form.get("resume_text", "").strip()

    # 2. Capture demographic and industry interest vectors
    career_interest = request.form.get("career_interest", "General/Undecided")
    
    location_scope = request.form.get("location_scope", "Nationwide").strip()
    location_detail = request.form.get("location_detail", "").strip()

    if location_scope == "Nationwide":
        location_info = "Nationwide (United States)"
    else:
        location_info = f"{location_scope}: {location_detail}"

    if not resume_text:
        return jsonify({"status": "error", "message": "Please input your experience details or upload a draft PDF resume."}), 400

    try:
        # STRONGLY GROUNDED STUDENT WAGE PROMPT CONTROLS
        system_prompt = (
            "You are an expert high school career coach specializing in helping teenagers find part-time jobs and summer internships.\n"
            "Analyze the student's background information and map it against their targeted field with strict realism.\n\n"
            "REALISTIC STUDENT WAGE & POSITION RULES:\n"
            "1. Only suggest standard, youth-accessible positions (e.g., Cashier, Barista, Local Tutor, Camp Counselor, Help-Desk/IT Assistant, Social Media Updater, Office Helper).\n"
            "2. NEVER output corporate internship titles like 'Data Analyst', 'Software Engineer', or 'Researcher'. Downscale them to student roles (e.g., 'Tech Support Help' instead of 'IT Engineer').\n"
            "3. Hourly wages MUST match true entry-level youth pay scales, strictly bounded between $11.00/hr and $16.00/hr (depending on state norms).\n"
            "4. CRITICAL: High schoolers work part-time (~15 hours/week). You MUST calculate the projected annual salary based on a PART-TIME schedule (approx. 750 hours/year total), NOT a full-time corporate schedule. Annual projections should look realistically low (e.g., $8,000 - $12,000/yr).\n"
            "5. CRITICAL LINK GENERATION RULE: The 'platform_link' field within the 'simulated_jobs' array MUST be a direct, fully-formed, operational job search URL targeting the specific job title and location. Use the format 'https://www.indeed.com/jobs?q=JOB_TITLE&l=LOCATION' where JOB_TITLE and LOCATION are properly URL-encoded (e.g., replace spaces with '+' or '%20'). If the location parameter is Nationwide, omit the '&l=' parameter entirely and search across the entire United States (e.g., 'https://www.indeed.com/jobs?q=JOB_TITLE').\n"
            "6. STRICT LOCATION OVERRIDE RULE: You MUST base all geographic job search results, the 'location' fields, and the 'platform_link' query parameters exclusively on the 'Student Geographic Region/Zip' parameter explicitly provided in the user prompt. DO NOT use or extract any location, city, state, or address mentioned inside the resume text or experience details. The user's explicitly provided location input takes absolute priority over anything inside the resume.\n"
            "7. CRITICAL COURSERA ROADMAP LINK RULE: For every step generated inside the 'roadmap_steps' array, you MUST exclusively choose Coursera as the education provider. The 'resource_name' field MUST always be set to exactly 'Coursera'. Furthermore, the 'resource_link' field MUST be a direct, fully-formed deep link pointing directly to relevant program or training options on Coursera using the search structure: 'https://www.coursera.org/search?query=COURSE_KEYWORDS' where COURSE_KEYWORDS is a highly relevant, context-specific course keyword or skill name that is completely URL-encoded (e.g., replace spaces with '+' or '%20'). NEVER output generic landing pages like 'https://coursera.com'.\n\n"
            "You MUST respond ONLY with a single JSON object structured exactly like this template:\n"
            "{\n"
            "  \"formatting_score\": 85,\n"
            "  \"formatting_critique\": \"Review feedback on layout, readability, and overall structural profile.\",\n"
            "  \"common_mistakes\": [\"Example mistake 1\", \"Example mistake 2\"],\n"
            "  \"extracted_skills\": [\n"
            "     {\"casual\": \"Casual phrase\", \"professional\": \"Industry terminology\", \"type\": \"Hard or Soft Skill\"}\n"
            "  ],\n"
            "  \"roadmap_steps\": [\n"
            "     {\"step\": 1, \"title\": \"Skill Focus\", \"description\": \"Action step\", \"resource_name\": \"Coursera\", \"resource_link\": \"https://www.coursera.org/search?query=Skill+Focus\"}\n"
            "  ],\n"
            "  \"predicted_roles\": [\n"
            "     {\"title\": \"Job Position Name\", \"salary_hourly\": \"$12 - $14\", \"salary_annual\": \"$9,000 - $10,500 (Part-Time)\"}\n"
            "  ],\n"
            "  \"simulated_jobs\": [\n"
            "     {\"title\": \"Position\", \"company\": \"Local Brand Inc.\", \"location\": \"City/State\", \"platform_link\": \"https://www.indeed.com/jobs?q=Position&l=Location\"}\n"
            "  ]\n"
            "}"
        )

        user_prompt = (
            f"Target Career Field: {career_interest}\n"
            f"Student Geographic Region/Zip: {location_info}\n"
            f"Profile Experience Details:\n{resume_text}"
        )

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            max_tokens=3000,
            temperature=0.3
        )

        ai_data = json.loads(chat_completion.choices[0].message.content)
        return jsonify({"status": "success", "data": ai_data})

    except Exception as e:
        return jsonify({"status": "error", "message": f"AI Processing Interruption: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=1234)
