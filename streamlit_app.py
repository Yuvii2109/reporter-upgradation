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
from playwright.sync_api import sync_playwright

@st.cache_resource
def install_playwright():
    import subprocess
    import sys
    # Install ONLY the browser binary. 
    # We rely on packages.txt to handle the OS dependencies.
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)

install_playwright()

# --- CONFIGURATION ---
st.set_page_config(page_title="EDXSO Report Generator", layout="wide")

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# --- HTML TEMPLATES ---

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

        <section id="executive-summary" class="report-section">
            <div class="p-10 md:p-12">
                <div class="flex items-center gap-3 mb-8 border-b border-gray-50 pb-6">
                    <span class="p-2 bg-blue-50 rounded-lg">
                        <svg class="w-6 h-6 text-blue-700" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                    </span>
                    <h2 class="text-3xl font-bold text-navy uppercase tracking-tight">Executive Summary</h2>
                    <span class="ml-auto px-4 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-bold tracking-widest uppercase border border-blue-100">
                        Profile: [RISK_BAND_LABEL]
                    </span>
                </div>
                
                <div class="bg-white p-8 rounded-2xl border border-slate-100 shadow-sm text-gray-700 leading-relaxed text-lg space-y-6">
                    <p>[EXEC_SUMMARY_PARAGRAPH_1]</p>
                    <p>[EXEC_SUMMARY_PARAGRAPH_2]</p>
                    <p>[EXEC_SUMMARY_PARAGRAPH_3]</p>
                </div>
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
        </section>

        <section id="next-steps" class="report-section p-10 md:p-12 border-t border-slate-100">
            <h2 class="text-3xl font-bold text-navy mb-6 uppercase tracking-tighter">Next Step</h2>
            <div class="p-8 bg-blue-50/40 rounded-2xl border border-blue-100">
                <p class="text-gray-700 leading-relaxed text-lg mb-4">
                    The data highlights both strengths and opportunities. A focused well-being strategy can meaningfully reduce moderate-to-severe stress levels.
                </p>
                <p class="font-semibold text-navy text-lg">
                    We welcome a leadership discussion to translate these insights into structured, measurable student support initiatives.
                </p>
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

COMPREHENSIVE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comprehensive Research Report - EDXSO</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Inter', sans-serif; background-color: #f9fafb; color: #1e293b; -webkit-print-color-adjust: exact; }
        .report-section { background: #ffffff; margin-bottom: 3rem; overflow: hidden; border: 1px solid #f1f5f9; border-radius: 1.5rem; }
        .text-navy { color: #0c4a6e; }
        .hero-gradient { background: linear-gradient(135deg, #0c4a6e 0%, #075985 100%); }
        .heading-accent { border-left: 6px solid #0c4a6e; padding-left: 1rem; }
    </style>
</head>
<body class="p-8">
    <div class="max-w-5xl mx-auto">
        
        <header class="report-section hero-gradient text-white p-12 flex flex-col items-center text-center border-none">
            
            <div class="mb-10 bg-white px-10 py-6 rounded-xl shadow-lg flex items-center justify-center gap-8 md:gap-16 text-slate-800">
                <div class="text-center">
                    <p class="text-4xl font-black text-blue-600 mb-1">[TOTAL_SCHOOLS]</p>
                    <p class="text-xs font-bold text-slate-500 uppercase tracking-widest">Institutions</p>
                </div>
                <div class="w-px h-16 bg-slate-200"></div> <div class="text-center">
                    <p class="text-4xl font-black text-blue-600 mb-1">[TOTAL_STUDENTS]</p>
                    <p class="text-xs font-bold text-slate-500 uppercase tracking-widest">Students Surveyed</p>
                </div>
            </div>
            
            <p class="text-xl uppercase tracking-widest text-blue-200 font-semibold mb-2">Anonymized Macro Dataset</p>
            <h1 class="text-5xl font-extrabold mb-6 leading-tight">National Student Well-Being &<br>Assessment Experience</h1>
            <div class="w-24 h-1 bg-blue-400 mb-8"></div>
            
            <div class="space-y-3 text-blue-100">
                <p class="text-xl font-medium">COMPREHENSIVE MACRO REPORT</p>
                <p>Published 2026</p>
                
                <div class="flex items-center justify-center gap-2 text-lg font-medium mt-4">
                    <p>- By</p>
                    <p>EDXSO Research Team (New Delhi)</p>
                </div>
                
                <p class="opacity-80 pt-2">www.edxso.com</p>
            </div>
        </header>

        <section class="report-section p-10 md:p-12">
            <h2 class="text-2xl font-bold uppercase tracking-widest mb-6 heading-accent text-navy">I. Research Abstract</h2>
            <p class="text-lg text-slate-700 leading-relaxed mb-10">[RESEARCH_ABSTRACT]</p>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
                <div class="bg-slate-50 p-8 rounded-2xl border border-slate-200 shadow-sm">
                    <h3 class="text-lg font-bold uppercase text-navy mb-4 flex items-center gap-2">
                        <span class="w-3 h-3 bg-blue-600 rounded-full"></span> Key Driving Factors
                    </h3>
                    <p class="text-slate-600 leading-relaxed">[KEY_FACTORS]</p>
                </div>
                <div class="bg-blue-50/50 p-8 rounded-2xl border border-blue-100 shadow-sm">
                    <h3 class="text-lg font-bold uppercase text-blue-900 mb-4 flex items-center gap-2">
                        <span class="w-3 h-3 bg-red-500 rounded-full"></span> Strategic Eye-Openers
                    </h3>
                    <p class="text-blue-800 leading-relaxed">[EYE_OPENERS]</p>
                </div>
            </div>
        </section>

        <section class="report-section p-10 md:p-12">
            <h2 class="text-2xl font-bold uppercase tracking-widest mb-10 heading-accent text-navy">II. Macro Data Visualizations</h2>
            
            <div class="mb-16">
                <h3 class="text-xl font-bold text-center mb-6 text-slate-800">Overall National Stress Distribution</h3>
                <img src="[DYNAMIC_CHART_IMAGE]" alt="National Stress" class="w-full max-w-4xl mx-auto rounded-xl shadow-sm border border-slate-100">
            </div>

            <div class="mb-6">
                <h3 class="text-xl font-bold text-center mb-2 text-slate-800">Regional Variance Analysis</h3>
                <p class="text-center text-slate-500 mb-8 text-sm uppercase tracking-widest font-semibold">Classified across identified geographical belts</p>
                <img src="[REGIONAL_CHART_IMAGE]" alt="Regional Variance" class="w-full max-w-5xl mx-auto rounded-xl shadow-sm border border-slate-100">
            </div>
        </section>

        <section class="report-section p-10 md:p-12">
            <h2 class="text-2xl font-bold uppercase tracking-widest mb-8 heading-accent text-navy">III. Anonymized Data Matrix</h2>
            <div class="overflow-hidden rounded-xl border border-slate-200">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-slate-100 text-sm uppercase tracking-widest text-slate-600">
                            <th class="p-5 border-b border-slate-200">Metric</th>
                            <th class="p-5 border-b border-slate-200 text-right">Aggregated Percentage</th>
                        </tr>
                    </thead>
                    <tbody class="text-slate-700 text-lg">
                        <tr><td class="p-5 border-b border-slate-100 font-medium">Emotionally Balanced</td><td class="p-5 border-b border-slate-100 text-right text-green-600 font-bold">[PCT_BALANCED]%</td></tr>
                        <tr class="bg-slate-50"><td class="p-5 border-b border-slate-100 font-medium">Mildly Stressed</td><td class="p-5 border-b border-slate-100 text-right text-blue-600 font-bold">[PCT_MILD]%</td></tr>
                        <tr><td class="p-5 border-b border-slate-100 font-medium">Moderately Stressed</td><td class="p-5 border-b border-slate-100 text-right text-yellow-600 font-bold">[PCT_MOD]%</td></tr>
                        <tr class="bg-slate-50"><td class="p-5 border-b border-slate-100 font-medium">Highly Stressed</td><td class="p-5 border-b border-slate-100 text-right text-orange-600 font-bold">[PCT_HIGH]%</td></tr>
                        <tr><td class="p-5 border-b border-slate-100 font-medium">Severely Stressed</td><td class="p-5 border-b border-slate-100 text-right text-red-600 font-bold">[PCT_SEVERE]%</td></tr>
                        <tr class="bg-slate-50"><td class="p-5 border-b border-slate-100 font-medium">Reported High Exam Anxiety</td><td class="p-5 border-b border-slate-100 text-right font-bold">[PCT_ANXIETY]%</td></tr>
                        <tr><td class="p-5 font-medium">Reported High Parental Pressure</td><td class="p-5 text-right font-bold">[PCT_PARENT_PRESSURE]%</td></tr>
                    </tbody>
                </table>
            </div>
            <p class="mt-8 text-xs text-slate-400 text-center uppercase tracking-widest">*** All personally identifiable information has been redacted to maintain strict anonymity. ***</p>
        </section>

        <footer class="text-center p-12 text-gray-400 text-xs mt-12">
            <p class="uppercase tracking-widest mb-2 font-bold text-slate-500">
                &copy; 2026 EDXSO Survey Reports
            </p>
            <p>Comprehensive National Report — Student Assessment Experience</p><br><br>
            <p class="mb-2"><b>Confidentiality & Ownership Notice:</b>
            This report is confidential and strictly owned by EDXSO. 
            All rights are reserved. Any unauthorized use, reproduction, or distribution, 
            in whole or in part, without written consent from EDXSO is strictly 
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
    initials = str(school_name)[:2].upper()
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


# --- NEW MACRO REPORT HELPER FUNCTIONS ---

def assign_region(school_name):
    # Mapping based on actual data presence in your file
    north_keywords = ['meerut', 'bhuna', 'ratia', 'khara kheri', 'puranewala', 'paonta sahib', 'haryana', 'punjab']
    east_keywords = ['madhupur', 'nalanda', 'khutadih', 'patelbagan', 'br', 'bihar', 'jharkhand']
    west_keywords = ['dwarika'] # Mapping sunrise dwarika
    
    s_lower = str(school_name).lower()
    if any(k in s_lower for k in north_keywords): return "Northern Region"
    elif any(k in s_lower for k in east_keywords): return "Eastern Region"
    elif any(k in s_lower for k in west_keywords): return "Western Region"
    else: return "Central/Other"

def create_regional_comparison_chart(df):
    if 'Region' not in df.columns:
        df['Region'] = df['sname'].apply(assign_region)
        
    region_stats = df.groupby(['Region', 'category']).size().unstack(fill_value=0)
    # Convert to percentages per region
    region_pct = region_stats.div(region_stats.sum(axis=1), axis=0) * 100
    
    cats = ['Balanced', 'Mild', 'Moderate', 'High', 'Severe']
    for c in cats:
        if c not in region_pct.columns:
            region_pct[c] = 0.0
            
    region_pct = region_pct[cats]
    colors = ['#22c55e', '#3b82f6', '#eab308', '#f97316', '#ef4444']
    
    fig, ax = plt.subplots(figsize=(12, 6))
    region_pct.plot(kind='bar', stacked=True, color=colors, ax=ax, edgecolor='white')
    
    ax.set_facecolor('#f8fafc')
    fig.patch.set_facecolor('#ffffff')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    plt.title('Stress Category Distribution by Region', pad=20, fontsize=16, fontweight='bold', color='#0f172a')
    plt.xlabel('Geographical Region', fontsize=12, fontweight='bold')
    plt.ylabel('Percentage of Students (%)', fontsize=12, fontweight='bold')
    plt.xticks(rotation=0, fontsize=11, fontweight='600', color='#334155')
    plt.legend(title="Stress Level", bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    plt.close(fig)
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return f"data:image/png;base64,{data}"

def generate_comprehensive_research_insights(api_key, stats):
    if not api_key:
        return {
            "abstract": "This report presents a macro-level analysis of student well-being across multiple surveyed institutions.",
            "key_factors": "Data indicates varying levels of exam anxiety and parental pressure driving regional stress spikes.",
            "eye_openers": "A significant percentage of students lack accessible support structures despite high academic demands."
        }
        
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        ROLE: You are an Elite Academic Researcher writing an Anonymized National Report on Student Well-Being.
        
        MACRO DATA GATHERED:
        - Total Schools Surveyed: {stats['total_schools']}
        - Total Students (Anonymized): {stats['total_students']}
        - Overall Balanced/Mild Stress: {stats['pct_balanced'] + stats['pct_mild']}%
        - Overall Moderate Stress: {stats['pct_moderate']}%
        - Overall High/Severe Stress: {stats['pct_high'] + stats['pct_severe']}%
        - National Exam Anxiety Rate: {stats['anxiety_pct']}%
        - National Parental Pressure Rate: {stats['parent_pressure_pct']}%
        
        TASK:
        Generate a comprehensive, anonymized research summary in JSON format. The tone must be clinical, objective, insightful, and authoritative (like a white paper). 

        OUTPUT FORMAT (JSON):
        {{
            "abstract": "A 4-5 sentence professional research abstract summarizing the scale of the study and the overarching national narrative regarding student stress.",
            "key_factors": "A paragraph detailing the primary drivers of stress (e.g., parental expectations, exam structures) based on the data.",
            "eye_openers": "A concluding paragraph highlighting the most critical or surprising insights (the 'eye-openers') that educational policymakers or school boards need to address immediately."
        }}
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        import json
        return json.loads(response.text)
    except Exception as e:
        print(f"API Error: {e}")
        return {"abstract": "Error generating insights.", "key_factors": "N/A", "eye_openers": "N/A"}


def generate_insights_with_gemini(api_key, stats, school_name):
    high_severe = stats['pct_high'] + stats['pct_severe']
    moderate = stats['pct_moderate']
    low_band = stats['pct_balanced'] + stats['pct_mild']
    
    if high_severe >= 20: risk_band = "Priority Support Area"
    elif high_severe >= 15 and low_band >= 40: risk_band = "Divergent Ecosystem"
    elif high_severe >= 10 or moderate >= 40: risk_band = "Elevated Pressure Zone"
    elif high_severe >= 5 or moderate >= 30: risk_band = "Proactive Monitoring"
    else: risk_band = "Balanced Ecosystem"

    if not api_key:
        return {
            "risk_band_label": risk_band,
            "p1": "Students today face an evolving landscape of academic expectations, and the data reflects the natural emotional responses to these nationwide trends.",
            "p2": "We recognize that the institution is already exercising immense care in supporting its students. However, many of the pressures students absorb—such as societal competition and parental expectations—stem from external factors that are often outside the school's direct control.",
            "p3": "Looking forward, there is a wonderful opportunity to partner together. By providing students with tailored advice and coping strategies, we can empower them to navigate these external pressures with confidence and joy."
        }
    
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
        ROLE: You are an Elite Education Strategy Consultant writing an Executive Summary for School Leadership. 
        Your tone must be highly diplomatic, professional, respectful, and empowering. 

        SCHOOL CONTEXT:
        - School Name: {school_name}
        - Total Sample: {stats['count']} students
        - Ecosystem Profile: {risk_band}
        
        RAW DATA (TRANSLATE TO MEANING, AVOID EXACT PERCENTAGES):
        - Balanced/Mild: {stats['pct_balanced'] + stats['pct_mild']}%
        - Moderate: {stats['pct_moderate']}%
        - High/Severe: {stats['pct_high'] + stats['pct_severe']}%
        - Exam Anxiety: {stats['anxiety_pct']}% (Nat Benchmark: 81%)
        - Parental Pressure: {stats['parent_pressure_pct']}% (Nat Benchmark: 66%)

        FIRM OUTPUT GUARDRAILS (STRICT COMPLIANCE REQUIRED):
        1. ZERO BLAME OR AUTHORITY: Never imply the school is at fault. 
        2. THE "EXTERNAL FACTOR" RULE: You MUST explicitly state that the stress students face is part of a broader, nationwide trend and stems from external factors (societal competition, parental expectations) that are outside the school's direct control. 
        3. VALIDATE THE INSTITUTION: Acknowledge that the school is undoubtedly putting in strong effort to support its students.
        4. STRATEGIC POSITIONING: Do not offer EDXSO's direct counseling services. Position the insights as an opportunity for the school itself to lead and differentiate its brand through systemic enhancements.
        5. FORMAT: Output three professionally written, flowing paragraphs. No bullet points.

        OUTPUT FORMAT (JSON):
        {{
            "p1": "Paragraph 1: Introduce the general landscape of student well-being today, weaving in the school's specific data profile. Start directly and professionally. Frame the data as a helpful snapshot of the current student reality.",
            "p2": "Paragraph 2: The Validation. Explicitly state that the institution is undoubtedly putting in great effort, but acknowledge that certain pressures (like parental expectations and national competition) are external and beyond the school's direct control.",
            "p3": "Paragraph 3: The Strategic Opportunity. Frame this as a powerful opportunity for {school_name} to lead in holistic student development. Use language similar to: 'uniquely positioned at an ideal juncture,' 'investing in collaborative, structured support systems,' and 'transform potential challenges into growth opportunities.' Make it sound like a strategic, forward-thinking investment in the school's ecosystem that differentiates them as a leader in student-centric excellence."
        }}
        """
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        import json
        result = json.loads(response.text)
        result["risk_band_label"] = risk_band
        return result
    except Exception as e:
        print(f"API Error: {e}")
        return {"risk_band_label": risk_band, "p1": "Error generating insights.", "p2": "", "p3": ""}

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

def generate_final_report(sdf, total, api_key, school_name, logo_file, output_format, cols):
    cats = sdf['category'].value_counts()
    stats = {
        'count': total,
        'balanced': cats.get('Balanced', 0),
        'mild': cats.get('Mild', 0),
        'moderate': cats.get('Moderate', 0),
        'high': cats.get('High', 0),
        'severe': cats.get('Severe', 0),
        'pct_balanced': round(cats.get('Balanced', 0)/total*100, 1) if total > 0 else 0,
        'pct_mild': round(cats.get('Mild', 0)/total*100, 1) if total > 0 else 0,
        'pct_moderate': round(cats.get('Moderate', 0)/total*100, 1) if total > 0 else 0,
        'pct_high': round(cats.get('High', 0)/total*100, 1) if total > 0 else 0,
        'pct_severe': round(cats.get('Severe', 0)/total*100, 1) if total > 0 else 0,
        'anxiety_pct': round(len(sdf[sdf[cols[8]].astype(str).str.capitalize().isin(['Often', 'Always'])]) / total * 100, 1) if total > 0 else 0,
        'parent_pressure_pct': round(len(sdf[sdf[cols[12]].astype(str).str.capitalize().isin(['Often', 'Always'])]) / total * 100, 1) if total > 0 else 0,
        'support_pct': round(len(sdf[sdf[cols[26]].astype(str).str.capitalize().isin(['Often', 'Always'])]) / total * 100, 1) if total > 0 else 0
    }

    chart_base64 = create_stress_chart(stats)
    
    if logo_file: logo_url = convert_image_to_base64(logo_file)
    else: logo_url = create_monogram_fallback(school_name)
    
    ai_content = generate_insights_with_gemini(api_key, stats, school_name)

    html = HTML_TEMPLATE
    replacements = {
        "[SCHOOL_NAME]": str(school_name),
        "[SCHOOL_LOGO_URL]": logo_url,
        "[DYNAMIC_CHART_IMAGE]": chart_base64,
        "[MODE]": "Online Survey",
        "[COUNT]": str(stats['count']),
        "[RISK_BAND_LABEL]": ai_content.get("risk_band_label", "Ecosystem Profile"),
        "[EXEC_SUMMARY_PARAGRAPH_1]": ai_content.get("p1", ""),
        "[EXEC_SUMMARY_PARAGRAPH_2]": ai_content.get("p2", ""),
        "[EXEC_SUMMARY_PARAGRAPH_3]": ai_content.get("p3", ""),
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
        "[PCT_SUPPORT]": str(stats['support_pct'])
    }

    for key, val in replacements.items(): html = html.replace(key, str(val))
        
    if output_format == "PDF": return safe_generate_pdf(html)
    else: return html.encode('utf-8')


# --- MAIN UI AND DATA PIPELINE ---

st.title("EDXSO Report Generator")
st.markdown("Generate Gold Standard Reports on Student Assessment Experience.")

with st.sidebar:
    st.header("Settings")
    output_format = st.radio("Output Format", ["HTML (Fast)", "PDF (High Quality)"])
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
    
    # Pre-process ALL data globally
    scale_map = {'Never': 1, 'Rarely': 2, 'Sometimes': 3, 'Often': 4, 'Always': 5}
    reverse_map = {'Never': 5, 'Rarely': 4, 'Sometimes': 3, 'Often': 2, 'Always': 1}
    cols = df.columns.tolist()

    def clean_and_score(row):
        score = 0
        def get_val(val, mapping):
            if pd.isna(val): return 3
            s = str(val).strip().replace('\xa0', ' ').capitalize() 
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
    df['Region'] = df['sname'].apply(assign_region) # Assign regions globally
    
    all_schools = df['sname'].dropna().unique().tolist()
    st.success(f"Data Loaded! Found {len(all_schools)} schools and {len(df)} total students.")
    st.markdown("---")
    
    # --- CREATE TABS ---
    tab1, tab2 = st.tabs(["Single School Report", "Comprehensive Research Report (Manager View)"])
    
    with tab1:
        st.subheader("Generate School-Specific Report")
        col1, col2 = st.columns(2)
        with col1:
            selected_school = st.selectbox("Select School", options=all_schools)
        with col2:
            logo_file = st.file_uploader("Upload School Logo (PNG/JPG)", type=['png', 'jpg', 'jpeg'], key="logo1")
            
        if st.button("Generate School Report", type="primary", key="btn1"):
            with st.spinner("Generating..."):
                sdf = df[df['sname'] == selected_school].copy()
                total = len(sdf)
                file_data = generate_final_report(sdf, total, api_key, selected_school, logo_file, output_format.split(" ")[0], cols)
                
                if file_data:
                    ext = "pdf" if "PDF" in output_format else "html"
                    mime = "application/pdf" if "PDF" in output_format else "text/html"
                    st.balloons()
                    st.download_button(f"Download Report for {selected_school}", data=file_data, file_name=f"{selected_school}_Report.{ext}", mime=mime)

    with tab2:
        st.subheader("Generate Aggregated National White Paper")
        st.info("This will generate a completely anonymized, research-grade document encompassing all schools, categorizing them by region, and calculating macroscopic trends.")
        
        if st.button("Generate Comprehensive Report", type="primary", key="btn2"):
            with st.spinner("Performing Macro Analysis and calling Gemini..."):
                total_students = len(df)
                total_schools = len(all_schools)
                cats = df['category'].value_counts()
                
                # Global Stats
                macro_stats = {
                    'total_students': total_students,
                    'total_schools': total_schools,
                    'pct_balanced': round(cats.get('Balanced', 0)/total_students*100, 1) if total_students > 0 else 0,
                    'pct_mild': round(cats.get('Mild', 0)/total_students*100, 1) if total_students > 0 else 0,
                    'pct_moderate': round(cats.get('Moderate', 0)/total_students*100, 1) if total_students > 0 else 0,
                    'pct_high': round(cats.get('High', 0)/total_students*100, 1) if total_students > 0 else 0,
                    'pct_severe': round(cats.get('Severe', 0)/total_students*100, 1) if total_students > 0 else 0,
                    'anxiety_pct': round(len(df[df[cols[8]].astype(str).str.capitalize().isin(['Often', 'Always'])]) / total_students * 100, 1) if total_students > 0 else 0,
                    'parent_pressure_pct': round(len(df[df[cols[12]].astype(str).str.capitalize().isin(['Often', 'Always'])]) / total_students * 100, 1) if total_students > 0 else 0,
                }

                # Generate Charts
                overall_chart = create_stress_chart(macro_stats)
                regional_chart = create_regional_comparison_chart(df)
                
                # Get AI Text
                ai_text = generate_comprehensive_research_insights(api_key, macro_stats)
                
                # Build HTML
                html = COMPREHENSIVE_HTML_TEMPLATE
                replacements = {
                    "[TOTAL_SCHOOLS]": str(total_schools),
                    "[TOTAL_STUDENTS]": f"{total_students:,}",
                    "[DYNAMIC_CHART_IMAGE]": overall_chart,
                    "[REGIONAL_CHART_IMAGE]": regional_chart,
                    "[RESEARCH_ABSTRACT]": ai_text.get("abstract", "N/A"),
                    "[KEY_FACTORS]": ai_text.get("key_factors", "N/A"),
                    "[EYE_OPENERS]": ai_text.get("eye_openers", "N/A"),
                    "[PCT_BALANCED]": str(macro_stats['pct_balanced']),
                    "[PCT_MILD]": str(macro_stats['pct_mild']),
                    "[PCT_MOD]": str(macro_stats['pct_moderate']),
                    "[PCT_HIGH]": str(macro_stats['pct_high']),
                    "[PCT_SEVERE]": str(macro_stats['pct_severe']),
                    "[PCT_ANXIETY]": str(macro_stats['anxiety_pct']),
                    "[PCT_PARENT_PRESSURE]": str(macro_stats['parent_pressure_pct']),
                }
                
                for key, val in replacements.items():
                    html = html.replace(key, str(val))
                    
                output_fmt = output_format.split(" ")[0]
                if output_fmt == "PDF":
                    final_file = safe_generate_pdf(html)
                else:
                    final_file = html.encode('utf-8')
                    
                if final_file:
                    ext = "pdf" if "PDF" in output_format else "html"
                    mime = "application/pdf" if "PDF" in output_format else "text/html"
                    st.success("Comprehensive Report Generated Successfully!")
                    st.download_button("Download National Report", data=final_file, file_name=f"Comprehensive_National_Report.{ext}", mime=mime)
