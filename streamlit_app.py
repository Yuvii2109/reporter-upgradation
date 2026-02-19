import streamlit as st
import pandas as pd
import io
import time
import subprocess
import sys
import os
import tempfile
import matplotlib.pyplot as plt
import base64
from io import BytesIO

# --- IMPORTS ---
from google import genai
from dotenv import load_dotenv

# --- PLAYWRIGHT INSTALL ---
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])

# --- CONFIGURATION ---
st.set_page_config(page_title="EDXSO Report Generator", layout="wide")

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# --- HTML TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Well-Being Survey Report - [SCHOOL_NAME]</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f9fafb; color: #1e293b; -webkit-print-color-adjust: exact; }
        .report-section { background: #ffffff; margin-bottom: 3rem; overflow: hidden; border: 1px solid #f1f5f9; border-radius: 1.5rem; }
        .text-navy { color: #0c4a6e; }
        /* Reverted to the original professional gradient */
        .hero-gradient { background: linear-gradient(135deg, #0c4a6e 0%, #075985 100%); }
        .chart-bar-bg { background-color: #f1f5f9; border-radius: 9999px; height: 1.5rem; width: 100%; overflow: hidden; position: relative; }
        .chart-bar-fill { height: 100%; border-radius: 9999px; }
    </style>
</head>
<body class="p-8">
    <div class="max-w-5xl mx-auto">
        <header class="report-section hero-gradient text-white p-12 flex flex-col items-center text-center border-none">
            <div class="mb-10 bg-white p-4 rounded-xl shadow-lg">
                <img src="[SCHOOL_LOGO_URL]" alt="School Logo" class="h-24 w-auto" style="max-height: 96px; object-fit: contain;">
            </div>
            <p class="text-xl uppercase tracking-widest text-blue-200 font-semibold mb-2">[SCHOOL_NAME]</p>
            <h1 class="text-5xl font-extrabold mb-6 leading-tight">Student Exam Stress Manometer</h1>
            <div class="w-24 h-1 bg-blue-400 mb-8"></div>
            
            <div class="space-y-3 text-blue-100">
                <p class="text-xl font-medium">SURVEY REPORT</p>
                <p>Published 2026</p>
                
                <div class="flex items-center justify-center gap-2 text-lg font-medium mt-4">
                    <p>- By</p>
                    <p>EDXSO Research Team (New Delhi)</p>
                </div>
                
                <p class="opacity-80 pt-2">www.edxso.com</p>
            </div>
        </header>

        <section id="executive-summary" class="report-section">
            <div class="p-10 md:p-12">
                <div class="flex items-center gap-3 mb-8 border-b border-gray-50 pb-6">
                    <span class="p-2 bg-blue-50 rounded-lg">
                        <svg class="w-6 h-6 text-blue-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                    </span>
                    <h2 class="text-3xl font-bold text-navy uppercase tracking-tight">Executive Summary</h2>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-12 mb-10">
                    <div class="space-y-4 text-gray-700 leading-relaxed text-lg">
                        <p>[EXEC_SUMMARY_P1]</p>
                        <p>[EXEC_SUMMARY_P2]</p>
                    </div>
                    <div class="space-y-4 text-gray-700 leading-relaxed text-lg">
                        <p class="font-semibold text-navy">[EXEC_SUMMARY_KEY_FINDING]</p>
                        <p>[EXEC_SUMMARY_CONCLUSION]</p>
                    </div>
                </div>
                <div class="p-8 border-l-4 border-blue-600 mb-12 italic text-gray-600 bg-slate-50/50 text-xl rounded-r-xl">
                    "Behind every exam score is a student navigating unseen emotional pressures."
                </div>
            </div>
        </section>

        <section id="overview" class="report-section p-10 md:p-12">
            <div class="flex flex-col md:flex-row gap-12">
                <div class="md:w-1/3">
                    <img src="https://i.ibb.co/VYdmHbWy/Screenshot-2026-01-30-at-5-19-42-PM.png" alt="Overview Icon" class="rounded-xl mb-6 w-full object-cover">
                    <h2 class="text-2xl font-bold text-navy mb-4 uppercase">Survey Overview</h2>
                    <p class="text-gray-600 leading-relaxed">Structured snapshot outlining scale, mode, and analytical logic used to capture student perspectives.</p>
                </div>
                <div class="md:w-2/3 space-y-2">
                    <div class="flex items-center p-5 border-b border-gray-100">
                        <div class="w-40 font-bold text-navy uppercase text-xs tracking-wider">Survey Name:</div>
                        <div class="text-gray-700">Student Well-Being & Assessment Experience Survey</div>
                    </div>
                    <div class="flex items-center p-5 border-b border-gray-100">
                        <div class="w-40 font-bold text-navy uppercase text-xs tracking-wider">Participants:</div>
                        <div class="text-gray-700">[COUNT] Students</div>
                    </div>
                    <div class="flex items-center p-5 border-b border-gray-100">
                        <div class="w-40 font-bold text-navy uppercase text-xs tracking-wider">Mode:</div>
                        <div class="text-gray-700">[MODE]</div>
                    </div>
                    <div class="flex items-center p-5 border-b border-gray-100">
                        <div class="w-40 font-bold text-navy uppercase text-xs tracking-wider">Nature:</div>
                        <div class="text-gray-700">Anonymous, self-reported</div>
                    </div>
                    <div class="flex items-center p-5 border-b border-gray-100">
                        <div class="w-40 font-bold text-navy uppercase text-xs tracking-wider">Focus:</div>
                        <div class="text-gray-700">Emotional impact of assessments</div>
                    </div>
                </div>
            </div>
        </section>

        <section class="grid grid-cols-1 md:grid-cols-2 gap-12 mb-16">
            <div class="p-10 border border-slate-100 rounded-2xl bg-white">
                <h2 class="text-2xl font-bold text-navy mb-8 uppercase tracking-widest flex items-center gap-2">Objectives</h2>
                <ul class="space-y-6">
                    <li class="flex gap-4"><span class="text-blue-600 font-bold text-xl">01</span><p class="text-gray-700">Collect evidence on emotional responses to tests.</p></li>
                    <li class="flex gap-4"><span class="text-blue-600 font-bold text-xl">02</span><p class="text-gray-700">Analyze stress associated with performance expectations.</p></li>
                    <li class="flex gap-4"><span class="text-blue-600 font-bold text-xl">03</span><p class="text-gray-700">Classify students into defined stress categories.</p></li>
                </ul>
            </div>
            <div class="p-0">
                <img src="https://i.ibb.co/kV9wrJ8q/Screenshot-2026-01-30-at-5-20-37-PM.png" alt="Methodology" class="rounded-2xl mb-6 w-full">
                <h2 class="text-2xl font-bold text-navy mb-4 uppercase">Design & Methodology</h2>
                <p class="text-gray-600 mb-6">20 structured statements on a 5-point scale from <span class="font-semibold">Never</span> to <span class="font-semibold">Always</span>.</p>
            </div>
        </section>

        <section id="scoring" class="report-section p-10 md:p-12">
            <div class="mb-12">
                <h2 class="text-4xl font-extrabold text-navy tracking-tight mb-2 uppercase">Scoring Framework</h2>
                <div class="h-1 w-20 bg-blue-600"></div>
            </div>
            <div class="space-y-1">
                 [INSERT_FULL_SCORING_TABLE_FROM_USER_PROMPT]
            </div>
            <div class="mt-12 p-6 bg-slate-50 rounded-xl text-gray-500 text-sm">
                <p>Note: Participation was anonymous. Scoring logic was applied strictly without subjective interpretation.</p>
            </div>
        </section>

        <section id="results" class="report-section p-10 md:p-12">
            <div class="mb-12 text-center">
                <h2 class="text-3xl font-bold text-navy mb-2 uppercase tracking-tighter">Student Well-Being</h2>
                <p class="text-xl text-gray-400">Stress Category Distribution</p>
            </div>
            <div class="mb-16 flex justify-center">
                <img src="[DYNAMIC_CHART_IMAGE]" alt="Stress Distribution Chart" class="w-full max-w-4xl rounded-xl shadow-sm">
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-12">
                <div class="pb-6 border-b-2 border-green-500">
                    <div class="flex justify-between items-baseline mb-2">
                        <h3 class="font-bold text-gray-900 uppercase text-sm tracking-widest">Emotionally Balanced</h3>
                        <span class="text-3xl font-black text-green-600">[VAL_BALANCED]</span>
                    </div>
                    <p class="text-sm text-gray-500">[PCT_BALANCED]% — Stable emotional states.</p>
                </div>
                <div class="pb-6 border-b-2 border-blue-500">
                    <div class="flex justify-between items-baseline mb-2">
                        <h3 class="font-bold text-gray-900 uppercase text-sm tracking-widest">Mildly Stressed</h3>
                        <span class="text-3xl font-black text-blue-600">[VAL_MILD]</span>
                    </div>
                    <p class="text-sm text-gray-500">[PCT_MILD]% — Minor stress levels.</p>
                </div>
                <div class="pb-6 border-b-2 border-yellow-500">
                    <div class="flex justify-between items-baseline mb-2">
                        <h3 class="font-bold text-gray-900 uppercase text-sm tracking-widest">Moderately Stressed</h3>
                        <span class="text-3xl font-black text-yellow-600">[VAL_MOD]</span>
                    </div>
                    <p class="text-sm text-gray-500">[PCT_MOD]% — Significant challenges.</p>
                </div>
                <div class="pb-6 border-b-2 border-orange-500">
                    <div class="flex justify-between items-baseline mb-2">
                        <h3 class="font-bold text-gray-900 uppercase text-sm tracking-widest">Highly Stressed</h3>
                        <span class="text-3xl font-black text-orange-600">[VAL_HIGH]</span>
                    </div>
                    <p class="text-sm text-gray-500">[PCT_HIGH]% — Intense experiences.</p>
                </div>
                <div class="pb-6 border-b-2 border-red-500">
                    <div class="flex justify-between items-baseline mb-2">
                        <h3 class="font-bold text-gray-900 uppercase text-sm tracking-widest">Severely Stressed</h3>
                        <span class="text-3xl font-black text-red-600">[VAL_SEVERE]</span>
                    </div>
                    <p class="text-sm text-gray-500">[PCT_SEVERE]% — Extreme stress levels.</p>
                </div>
                <div class="pb-6 border-b-2 border-gray-900">
                    <div class="flex justify-between items-baseline mb-2">
                        <h3 class="font-bold text-gray-900 uppercase text-sm tracking-widest">Total Surveyed</h3>
                        <span class="text-3xl font-black text-gray-900">[VAL_TOTAL]</span>
                    </div>
                    <p class="text-sm text-gray-500">100% Valid Responses.</p>
                </div>
            </div>
        </section>

        <section id="national-benchmark" class="report-section p-10 md:p-12">
            <div class="mb-10">
                <h2 class="text-3xl font-bold text-navy mb-4 uppercase tracking-tighter">National Benchmark Comparison: <span class="text-blue-600">Student Stress Levels (India)</span></h2>
                <div class="h-1 w-24 bg-blue-600 mb-6"></div>
                <p class="text-gray-600 leading-relaxed text-lg">
                    To contextualize findings, student responses were compared against established benchmarks from the <strong>NCERT National Survey (2022)</strong> and Indian academic morbidity studies (2020–2024).
                </p>
            </div>
            <div class="mb-16">
                <h3 class="text-2xl font-bold text-navy mb-6 text-center">Stress Category Distribution: School vs. National Benchmark</h3>
                <div class="space-y-8 max-w-3xl mx-auto">
                    <div>
                        <div class="flex justify-between mb-2 text-sm font-bold uppercase tracking-widest text-gray-500">
                            <span>[SCHOOL_NAME]</span>
                            <span>Valid N=[VAL_TOTAL]</span>
                        </div>
                        <div class="flex h-12 w-full rounded-xl overflow-hidden shadow-inner">
                            <div class="bg-green-500" style="width: [PCT_BALANCED]%;" title="Balanced"></div>
                            <div class="bg-blue-500" style="width: [PCT_MILD]%;" title="Mild"></div>
                            <div class="bg-yellow-500" style="width: [PCT_MOD]%;" title="Moderate"></div>
                            <div class="bg-orange-500" style="width: [PCT_HIGH]%;" title="High"></div>
                            <div class="bg-red-500" style="width: [PCT_SEVERE]%;" title="Severe"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="mb-12">
                <h3 class="text-2xl font-bold text-navy mb-10 text-center">Key Stress Indicator Comparison</h3>
                <div class="grid grid-cols-1 gap-8">
                    <div>
                        <div class="flex justify-between text-sm font-bold text-gray-600 mb-2">
                            <span>Exam Anxiety (Frequent Nervousness)</span>
                            <div class="flex gap-4">
                                <span class="text-blue-600">School: [PCT_ANXIETY]%</span>
                                <span class="text-gray-400">National: 81%</span>
                            </div>
                        </div>
                        <div class="chart-bar-bg">
                            <div class="chart-bar-fill bg-blue-600" style="width: [PCT_ANXIETY]%;"></div>
                            <div class="absolute top-0 bottom-0 w-1 bg-red-400 border-x border-white" style="left: 81%;"></div>
                        </div>
                    </div>
                    <div>
                        <div class="flex justify-between text-sm font-bold text-gray-600 mb-2">
                            <span>Parental Performance Pressure</span>
                            <div class="flex gap-4">
                                <span class="text-blue-600">School: [PCT_PARENT_PRESSURE]%</span>
                                <span class="text-gray-400">National: 66%</span>
                            </div>
                        </div>
                        <div class="chart-bar-bg">
                            <div class="chart-bar-fill bg-blue-600" style="width: [PCT_PARENT_PRESSURE]%;"></div>
                            <div class="absolute top-0 bottom-0 w-1 bg-red-400 border-x border-white" style="left: 66%;"></div>
                        </div>
                    </div>
                    <div>
                        <div class="flex justify-between text-sm font-bold text-gray-600 mb-2">
                            <span>Support Accessibility (Can talk to teachers/counselors)</span>
                            <div class="flex gap-4">
                                <span class="text-blue-600">School: [PCT_SUPPORT]%</span>
                                <span class="text-gray-400">National: 28%</span>
                            </div>
                        </div>
                        <div class="chart-bar-bg">
                            <div class="chart-bar-fill bg-green-500" style="width: [PCT_SUPPORT]%;"></div>
                            <div class="absolute top-0 bottom-0 w-1 bg-red-400 border-x border-white" style="left: 28%;"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="p-10 border border-blue-50 rounded-2xl bg-blue-50/20">
                <h3 class="text-2xl font-bold text-navy mb-6">Interpretation & Insights</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
                    <div class="space-y-4">
                        <div class="p-4 bg-white rounded-xl">
                            <h4 class="text-green-700 font-bold flex items-center gap-2 mb-2">Strengths vs. National Trend</h4>
                            <p class="text-sm text-gray-600 leading-relaxed">[INSIGHT_STRENGTHS]</p>
                        </div>
                    </div>
                    <div class="space-y-4">
                        <div class="p-4 bg-white rounded-xl">
                            <h4 class="text-orange-700 font-bold flex items-center gap-2 mb-2">Points of Intervention</h4>
                            <p class="text-sm text-gray-600 leading-relaxed">[INSIGHT_WEAKNESS]</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <footer class="text-center p-12 text-gray-400 text-xs mt-12">
            <div class="flex justify-center mb-8">
                <img src="[SCHOOL_LOGO_URL]" alt="Logo Small" class="h-8 grayscale opacity-30">
            </div>
            <p class="uppercase tracking-widest mb-2 font-bold">
                &copy; 2026 EDXSO Survey Reports
            </p>
            <p>[SCHOOL_NAME] — Student Assessment Experience</p><br><br>
            <p class="mb-2"><b>Confidentiality & Ownership Notice:</b>
            This report is confidential and jointly owned by EDXSO and [SCHOOL_NAME]. 
            All rights are reserved. Any unauthorized use, reproduction, or distribution, 
            in whole or in part, without written consent from both parties is strictly 
            prohibited.</p>
        </footer>

    </div>
</body>
</html>
"""

# --- HELPER FUNCTIONS ---

def create_stress_chart(stats):
    categories = ['Balanced', 'Mild', 'Moderate', 'High', 'Severe']
    values = [stats['pct_balanced'], stats['pct_mild'], stats['pct_moderate'], 
              stats['pct_high'], stats['pct_severe']]
    colors = ['#22c55e', '#3b82f6', '#eab308', '#f97316', '#ef4444']
    
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(categories, values, color=colors, edgecolor='white', linewidth=2)
    
    ax.set_facecolor('#f8fafc')
    fig.patch.set_facecolor('#ffffff')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#cbd5e1')
    
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height}%', ha='center', va='bottom', fontsize=12, fontweight='bold', color='#475569')

    plt.yticks([])
    plt.xticks(fontsize=11, fontweight='600', color='#334155')
    plt.title('Student Stress Distribution', pad=20, fontsize=14, fontweight='bold', color='#0f172a')
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"data:image/png;base64,{data}"

def convert_image_to_base64(uploaded_file):
    if uploaded_file is None:
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    try:
        bytes_data = uploaded_file.getvalue()
        b64_str = base64.b64encode(bytes_data).decode()
        mime = "image/png" if uploaded_file.name.lower().endswith(".png") else "image/jpeg"
        return f"data:{mime};base64,{b64_str}"
    except Exception as e:
        return ""

def create_monogram_fallback(school_name):
    initials = school_name[:2].upper()
    fig, ax = plt.subplots(figsize=(2, 2))
    circle = plt.Circle((0.5, 0.5), 0.5, color='#0f172a')
    ax.add_patch(circle)
    ax.text(0.5, 0.5, initials, ha='center', va='center', 
            fontsize=40, fontweight='bold', color='white', fontfamily='sans-serif')
    ax.axis('off')
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, transparent=True)
    plt.close(fig)
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"data:image/png;base64,{data}"

def generate_insights_with_gemini(api_key, stats, school_name):
    if not api_key:
        return {
            "p1": "The students exhibited a diverse range of emotional responses.",
            "p2": "Detailed analysis suggests that while some students possess robust coping mechanisms, a notable segment requires targeted intervention.",
            "key_finding": "Moderate Correlation between Preparation and Panic.",
            "conclusion": "Implementing structured mentorship programs is recommended.",
            "quote": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
            "strengths": f"Support Accessibility score of {stats['support_pct']:.1f}% indicates positive interaction.",
            "weaknesses": f"Exam anxiety is recorded at {stats['anxiety_pct']:.1f}%."
        }
    
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        ROLE: You are an Expert Education Data Analyst with a calm, professional, and clinical demeanor. You transform complex data into clear, narrative-driven insights. You have a deep understanding of student psychology and the nuances of stress related to academic assessments. Your tone is polite, empathetic yet authoritative, providing guidance that is grounded in evidence.

        CRITICAL INSTRUCTION: You MUST weave the provided statistics directly into the narrative of the executive summary. Do not simply list numbers; integrate them seamlessly into sentences, making sure to explicitly compare school data against National (Nat) averages where provided.

        TASK: Write an analytical report section for School: "{school_name}".

        DATA:
        - Total Students: {stats['count']}
        - Balanced: {stats['pct_balanced']}%
        - Mild: {stats['pct_mild']}%
        - Moderate: {stats['pct_moderate']}%
        - High: {stats['pct_high']}%
        - Severe: {stats['pct_severe']}%
        - Anxiety: {stats['anxiety_pct']}% (Nat: 81%)
        - Pressure: {stats['parent_pressure_pct']}% (Nat: 66%)
        - Support: {stats['support_pct']}% (Nat: 28%)

        OUTPUT FORMAT (JSON):
        {{
            "p1": "Executive Summary P1 (Approx 40-60 words). State the school name, total students assessed, and summarize the emotional category distribution. Specifically contrast the 'Balanced' percentage against the 'High' and 'Severe' percentages to establish the baseline need.",
            "p2": "Executive Summary P2 (Approx 50-70 words). Compare the school's Anxiety and Pressure percentages to their National (Nat) averages. Then, mention the Support percentage compared to its National benchmark, framing it as a foundation for interventions.",
            "key_finding": "Key Finding Headline summarizing the primary emotional concern (Max 10 words).",
            "conclusion": "Executive Summary P3 / Conclusion (Approx 40-50 words). Synthesize the findings from p1 and p2 into an actionable takeaway. Call for focused, holistic well-being strategies based on the concentration of high/severe stress.",
            "quote": "A very positive, motivational, optimistic, and inspirational quote relevant to student well-being.",
            "strengths": "Insight on Strengths based on the data, such as support levels (Max 40 words).",
            "weaknesses": "Insight on Points of Intervention based on the data (Max 40 words)."
        }}
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        import json
        return json.loads(response.text)
    except Exception:
        return {
            "p1": "Analysis generation failed.",
            "p2": "Please check API Key.",
            "key_finding": "Data Processing Complete",
            "conclusion": "Review numerical data below.",
            "quote": "Data speaks for itself.",
            "strengths": "N/A",
            "weaknesses": "N/A"
        }

def safe_generate_pdf(html_content):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as tf:
        tf.write(html_content)
        html_path = tf.name
    
    pdf_path = html_path.replace(".html", ".pdf")
    
    script = f"""
from playwright.sync_api import sync_playwright
import sys

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, 
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        page = browser.new_page()
        page.set_content(open(r"{html_path}", encoding="utf-8").read())
        body_height = page.evaluate("document.body.scrollHeight")
        final_height = body_height + 100
        page.pdf(
            path=r"{pdf_path}", 
            width="1200px", 
            height=f"{{final_height}}px", 
            print_background=True,
            margin={{"top": "40px", "bottom": "40px", "left": "40px", "right": "40px"}}
        )
        browser.close()
except Exception as e:
    print(f"INTERNAL PLAYWRIGHT ERROR: {{e}}", file=sys.stderr)
    sys.exit(1)
"""
    try:
        subprocess.run([sys.executable, "-c", script], check=True, capture_output=True)
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        return pdf_bytes
    except subprocess.CalledProcessError:
        return None
    finally:
        if os.path.exists(html_path): os.remove(html_path)
        if os.path.exists(pdf_path): os.remove(pdf_path)

# --- MAIN LOGIC ---
def process_single_school(df, api_key, school_name, logo_file, output_format):
    scale_map = {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5}
    reverse_map = {'Never': 5, 'Rarely': 4, 'Sometimes': 3, 'Often': 2, 'Always': 1}
    cols = df.columns.tolist()

    if len(cols) < 28:
        st.error("CSV format incorrect.")
        return None, None

    # --- AGGRESSIVE CLEANING ---
    def clean_and_score(row):
        score = 0
        def get_val(val, mapping):
            if pd.isna(val): return 3 # Default to 3 if blank
            s = str(val).strip().replace('\xa0', ' ') # Remove weird spaces
            # Handle casing "always" -> "Always"
            s = s.capitalize() 
            # Handle typos or mapping
            return mapping.get(s, 3) 

        for i in range(8, 23): score += get_val(row[cols[i]], scale_map)
        for i in range(23, 28): score += get_val(row[cols[i]], reverse_map)
        return score

    df['total_score'] = df.apply(clean_and_score, axis=1)
    
    def get_category(s):
        if s <= 39: return 'Balanced'
        elif s <= 54: return 'Mild'
        elif s <= 69: return 'Moderate'
        elif s <= 84: return 'High'
        else: return 'Severe'
        
    df['category'] = df['total_score'].apply(get_category)

    sdf = df[df['sname'] == school_name].copy()
    total = len(sdf)
    if total == 0: 
        st.error("No data found for this school.")
        return None, None

    # --- RETURN DATAFRAME FOR DEBUGGING ---
    return sdf, total

def generate_final_report(sdf, total, api_key, school_name, logo_file, output_format, cols):
    cats = sdf['category'].value_counts()
    stats = {
        'count': total,
        'balanced': cats.get('Balanced', 0),
        'mild': cats.get('Mild', 0),
        'moderate': cats.get('Moderate', 0),
        'high': cats.get('High', 0),
        'severe': cats.get('Severe', 0),
        'pct_balanced': round(cats.get('Balanced', 0)/total*100, 1),
        'pct_mild': round(cats.get('Mild', 0)/total*100, 1),
        'pct_moderate': round(cats.get('Moderate', 0)/total*100, 1),
        'pct_high': round(cats.get('High', 0)/total*100, 1),
        'pct_severe': round(cats.get('Severe', 0)/total*100, 1),
        # Helper to clean boolean check for stats
        'anxiety_pct': round(len(sdf[sdf[cols[8]].astype(str).str.capitalize().isin(['Often', 'Always'])]) / total * 100, 1),
        'parent_pressure_pct': round(len(sdf[sdf[cols[12]].astype(str).str.capitalize().isin(['Often', 'Always'])]) / total * 100, 1),
        'support_pct': round(len(sdf[sdf[cols[26]].astype(str).str.capitalize().isin(['Often', 'Always'])]) / total * 100, 1)
    }

    chart_base64 = create_stress_chart(stats)
    
    if logo_file:
        logo_url = convert_image_to_base64(logo_file)
    else:
        logo_url = create_monogram_fallback(school_name)
    
    ai_content = generate_insights_with_gemini(api_key, stats, school_name)

    html = HTML_TEMPLATE
    replacements = {
        "[SCHOOL_NAME]": str(school_name),
        "[SCHOOL_LOGO_URL]": logo_url,
        "[DYNAMIC_CHART_IMAGE]": chart_base64,
        "[EST_YEAR]": "2024",
        "[MODE]": "Online Survey",
        "[COUNT]": str(stats['count']),
        "[EXEC_SUMMARY_P1]": ai_content.get("p1", ""),
        "[EXEC_SUMMARY_P2]": ai_content.get("p2", ""),
        "[EXEC_SUMMARY_KEY_FINDING]": ai_content.get("key_finding", ""),
        "[EXEC_SUMMARY_CONCLUSION]": ai_content.get("conclusion", ""),
        "[INSERT_KEY_QUOTE]": ai_content.get("quote", ""),
        "[INSERT_FULL_SCORING_TABLE_FROM_USER_PROMPT]": """
        <div class="grid grid-cols-5 gap-2 text-center text-xs font-medium text-gray-500">
            <div class="bg-green-100 p-2 rounded">20-39<br>Balanced</div>
            <div class="bg-blue-100 p-2 rounded">40-54<br>Mild</div>
            <div class="bg-yellow-100 p-2 rounded">55-69<br>Moderate</div>
            <div class="bg-orange-100 p-2 rounded">70-84<br>High</div>
            <div class="bg-red-100 p-2 rounded">85-100<br>Severe</div>
        </div>
        """,
        "[VAL_BALANCED]": str(stats['balanced']),
        "[PCT_BALANCED]": str(stats['pct_balanced']),
        "[VAL_MILD]": str(stats['mild']),
        "[PCT_MILD]": str(stats['pct_mild']),
        "[VAL_MOD]": str(stats['moderate']),
        "[PCT_MOD]": str(stats['pct_moderate']),
        "[VAL_HIGH]": str(stats['high']),
        "[PCT_HIGH]": str(stats['pct_high']),
        "[VAL_SEVERE]": str(stats['severe']),
        "[PCT_SEVERE]": str(stats['pct_severe']),
        "[VAL_TOTAL]": str(stats['count']),
        "[PCT_ANXIETY]": str(stats['anxiety_pct']),
        "[PCT_PARENT_PRESSURE]": str(stats['parent_pressure_pct']),
        "[PCT_SUPPORT]": str(stats['support_pct']),
        "[INSIGHT_STRENGTHS]": ai_content.get("strengths", ""),
        "[INSIGHT_WEAKNESS]": ai_content.get("weaknesses", "")
    }

    for key, val in replacements.items():
        html = html.replace(key, str(val))
        
    if output_format == "PDF":
        return safe_generate_pdf(html)
    else:
        return html.encode('utf-8')

# --- UI ---
st.title("EDXSO Report Generator")
st.markdown("Generate Gold Standard Reports on Student Assessment Experience with Gemini AI Insights.")

with st.sidebar:
    st.header("Settings")
    # api_key = st.text_input("Gemini API Key", type="password")
    output_format = st.radio("Output Format", ["HTML (Fast)", "PDF (High Quality)"])
    # A subtle status check so WE know it's working
    if api_key:
        st.caption("API Key securely loaded.")
    else:
        st.error("API Key missing from environment variables.")

uploaded_file = st.file_uploader("Step 1: Upload Survey Data (Excel/CSV)", type=['xlsx', 'csv'])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    all_schools = df['sname'].dropna().unique().tolist()
    st.success(f"Data Loaded! Found {len(all_schools)} schools.")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        selected_school = st.selectbox("Step 2: Select School to Report", options=all_schools)
    with col2:
        logo_file = st.file_uploader("Step 3: Upload School Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
        if logo_file:
            st.image(logo_file, width=100, caption="Preview")
    
    st.markdown("---")
    
    # --- INSPECTION BUTTON ---
    if st.button("Check Data & Scores (Debug)"):
        sdf, total = process_single_school(df, api_key, selected_school, logo_file, output_format)
        if sdf is not None:
            st.write(f"**Found {total} Students.** Here is how they were scored:")
            st.dataframe(sdf[['total_score', 'category'] + sdf.columns.tolist()[8:13]])
            
            # Allow Download of Processed Data
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                sdf.to_excel(writer, index=False)
            st.download_button("Download Processed Excel", output.getvalue(), "debug_scores.xlsx")

    # --- GENERATE BUTTON ---
    if st.button("Generate Final Report", type="primary"):
        with st.spinner("Analyzing data and generating report..."):
            sdf, total = process_single_school(df, api_key, selected_school, logo_file, output_format)
            if sdf is not None:
                file_data = generate_final_report(sdf, total, api_key, selected_school, logo_file, output_format.split(" ")[0], df.columns.tolist())
                
                if file_data:
                    ext = "pdf" if "PDF" in output_format else "html"
                    mime = "application/pdf" if "PDF" in output_format else "text/html"
                    st.balloons()
                    st.download_button(
                        label=f"Download Report for {selected_school}",
                        data=file_data,
                        file_name=f"{selected_school}_Report.{ext}",
                        mime=mime
                    )