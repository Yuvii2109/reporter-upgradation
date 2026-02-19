# EDXSO Report Generator

## Overview
The EDXSO Report Generator is an automated data analysis and reporting application built with Streamlit. It processes raw student well-being survey data, calculates standardized stress metrics, and generates comprehensive, high-fidelity reports in both HTML and PDF formats. 

The application integrates Google's Gemini AI to synthesize data into actionable narrative insights and utilizes Playwright for robust, headless PDF generation.

## Features
* **Automated Scoring:** Cleans and processes raw survey data (Excel/CSV) using predefined psychometric scoring matrices.
* **AI-Driven Insights:** Leverages Google GenAI to generate contextual executive summaries comparing school data against national benchmarks.
* **Dynamic Visualizations:** Automatically generates matplotlib-based distribution charts integrated directly into the final report.
* **High-Fidelity PDF Export:** Utilizes Playwright Chromium to render and capture pixel-perfect PDF documents from HTML templates.
* **Custom Branding:** Supports dynamic fallback monograms or custom uploaded school logos.

## Tech Stack
* **Framework:** Streamlit
* **Data Processing:** Pandas, NumPy
* **Visualization:** Matplotlib
* **AI Integration:** Google GenAI (Gemini 2.5 Flash)
* **PDF Rendering:** Playwright (Chromium)
* **Environment Management:** python-dotenv

## System Requirements
To run this application, particularly the Playwright PDF generation, specific OS-level dependencies are required. 

If deploying on a Debian/Ubuntu-based Linux environment (such as Streamlit Community Cloud), ensure the package manager installs the libraries listed in `packages.txt`. This includes essential graphical and font rendering libraries (e.g., `libnss3`, `libgbm1`, `libcups2`, `chromium-driver`) necessary for headless browser execution.

## Local Setup & Installation

**1. Clone the repository**

```bash
git clone <repository-url>
cd edxso-report-generator
```

**2. Create and activate a virtual environment**

```Bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

**3. Install Python dependencies**

```Bash
pip install -r requirements.txt
```

**4. Install Playwright browsers**

```Bash
playwright install chromium
```

**5. Configure Environment Variables**

Create a .env file in the root directory of the project. Add your organization's Gemini API key:

```GEMINI_API_KEY="your_actual_api_key_here"```

Note: Ensure .env is included in your .gitignore file to prevent credential leakage.

### Usage

* Start the Streamlit development server:

```Bash
streamlit run app.py
```

* Upload the raw survey data file (CSV or XLSX).
* Select the target school from the parsed dropdown menu.
* (Optional) Upload a specific school logo.
* Select the desired output format (HTML or PDF).
* Click "Generate Final Report" to process the data, call the AI, and render the document.

## Deployment Notes

When deploying to cloud platforms (Streamlit Community Cloud, Render, AWS, etc.):
* Do not upload the .env file. Instead, add GEMINI_API_KEY to the platform's native Environment Variables or Secrets management dashboard.
* The packages.txt file must be present in the root directory for Linux-based deployments to successfully resolve Playwright's C-library dependencies.
* The initial generation request upon cold boot may take slightly longer as the server initializes the headless Chromium instance.

### **License & Confidentiality**

This software and the generated reports are intended for internal use and authorized partners of EDXSO.