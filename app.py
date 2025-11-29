import os
import re
import streamlit as st
from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import io
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
# Add these lines right after the other imports at the top of app.py
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except:
    nltk.download('punkt')
    nltk.download('stopwords')

# Common resume sections
RESUME_SECTIONS = [
    'experience', 'education', 'skills', 'summary', 
    'work experience', 'projects', 'certifications',
    'languages', 'interests', 'awards', 'publications'
]

# Load and display the AI-generated image


class ATSAnalyzer:
    @staticmethod
    def extract_text_from_pdf(uploaded_file):
        """Extract text from a PDF resume, with OCR fallback for image-based PDFs."""
        try:
            pdf_reader = PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text() or ""
                text += page_text
            
            # If no text is extracted, try OCR on each page
            if not text.strip():
                st.warning("No text detected. Attempting OCR on image-based PDF...")
                images = convert_from_bytes(uploaded_file.read(), first_page=1, last_page=len(pdf_reader.pages))
                for image in images:
                    text += pytesseract.image_to_string(image) + "\n"
            
            return text.strip() if text.strip() else None
        except Exception as e:
            st.error(f"Error extracting PDF text: {str(e)}")
            return None

    @staticmethod
    def extract_keywords(text, top_n=20):
        """Extract top keywords from text."""
        stop_words = set(stopwords.words('english'))
        words = word_tokenize(text.lower())
        words = [word for word in words if word.isalnum() and word not in stop_words and len(word) > 2]
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        return sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]

    @staticmethod
    def analyze_resume_sections(text):
        """Analyze resume sections and return found sections."""
        text_lower = text.lower()
        found_sections = [section for section in RESUME_SECTIONS if section in text_lower]
        return found_sections

    @staticmethod
    def perform_ats_checks(pdf_text, job_description):
        """Perform comprehensive ATS compatibility checks."""
        # Extract keywords from job description
        job_keywords = [word[0] for word in ATSAnalyzer.extract_keywords(job_description, top_n=20)]
        
        # Check for resume sections
        found_sections = ATSAnalyzer.analyze_resume_sections(pdf_text)
        
        # Basic ATS checks
        checks = {
            "Keywords Match": sum(1 for keyword in job_keywords if keyword in pdf_text.lower()) / len(job_keywords) * 100 if job_keywords else 0,
            "Has Experience Section": any(sec in ['experience', 'work experience'] for sec in found_sections),
            "Has Education Section": 'education' in found_sections,
            "Has Skills Section": 'skills' in found_sections,
            "Ideal Length (500-1000 words)": 500 <= len(pdf_text.split()) <= 1000,
            "No Complex Formatting": not ("table" in pdf_text.lower() or "image" in pdf_text.lower()),
            "Contact Information Present": any(info in pdf_text.lower() for info in ['@', 'phone', 'email', 'linkedin', 'github'])
        }
        
        # Calculate overall score (weighted average)
        weights = {
            "Keywords Match": 0.4,
            "Has Experience Section": 0.15,
            "Has Education Section": 0.1,
            "Has Skills Section": 0.1,
            "Ideal Length (500-1000 words)": 0.1,
            "No Complex Formatting": 0.1,
            "Contact Information Present": 0.05
        }
        
        score = sum(checks[check] * weights[check] for check in checks if check in weights)
        
        return score, checks, job_keywords, found_sections

def main():
    # Page configuration with theme
    st.set_page_config(
        page_title="ResumeWizard 🧙‍♂️ | AI-Powered Resume Analyzer",
        page_icon="✨",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Custom CSS for enhanced UI with animations
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
        
        /* Global Styles */
        * {
            font-family: 'Poppins', sans-serif;
        }
        
        /* Main container */
        .main {
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
            background-attachment: fixed;
        }
        
        /* Animated Gradient Header */
        .header {
            background: linear-gradient(-45deg, #4b6cb7, #3b5998, #2c3e50, #182848);
            background-size: 400% 400%;
            color: white;
            padding: 3rem 2rem 4rem;
            margin: -2rem -2rem 3rem -2rem;
            border-radius: 0 0 25px 25px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            animation: gradient 15s ease infinite;
            position: relative;
            overflow: hidden;
        }
        
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url("data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M11 18c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm48 25c3.866 0 7-3.134 7-7s-3.134-7-7-7-7 3.134-7 7 3.134 7 7 7zm-43-7c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm63 31c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM34 90c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zm56-76c1.657 0 3-1.343 3-3s-1.343-3-3-3-3 1.343-3 3 1.343 3 3 3zM12 86c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm28-65c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm23-11c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-6 60c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm29 22c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zM32 63c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm57-13c2.76 0 5-2.24 5-5s-2.24-5-5-5-5 2.24-5 5 2.24 5 5 5zm-9-21c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM60 91c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM35 41c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2zM12 60c1.105 0 2-.895 2-2s-.895-2-2-2-2 .895-2 2 .895 2 2 2z' fill='%23ffffff' fill-opacity='0.05' fill-rule='evenodd'/%3E%3C/svg%3E");
            opacity: 0.6;
        }
        
        /* Animated Buttons */
        .stButton>button {
            width: 100%;
            background: linear-gradient(45deg, #4b6cb7, #3b5998);
            color: white !important;
            border: none;
            border-radius: 12px;
            padding: 14px 28px;
            font-weight: 600;
            font-size: 1.1em;
            letter-spacing: 0.5px;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 15px rgba(75, 108, 183, 0.3);
            position: relative;
            overflow: hidden;
            z-index: 1;
        }
        
        .stButton>button::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 0;
            height: 100%;
            background: linear-gradient(45deg, #3a56a8, #2c3e50);
            transition: width 0.4s ease;
            z-index: -1;
        }
        
        .stButton>button:hover::before {
            width: 100%;
        }
        
        .stButton>button:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(75, 108, 183, 0.4);
        }
        
        .stButton>button:active {
            transform: translateY(1px);
            box-shadow: 0 2px 10px rgba(75, 108, 183, 0.3);
        }
        
        /* Animated Cards */
        .card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 1.75rem;
            margin-bottom: 1.75rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 5px;
            background: linear-gradient(90deg, #4b6cb7, #3b5998);
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.1);
            border-color: rgba(75, 108, 183, 0.3);
        }
        
        /* Animated Progress Bar */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #4b6cb7 0%, #3b5998 50%, #2c3e50 100%);
            background-size: 200% 100%;
            animation: gradientBG 3s ease infinite;
            border-radius: 20px;
            height: 12px !important;
        }
        
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        /* Enhanced Text Areas */
        .stTextArea>div>div>textarea {
            min-height: 200px;
            border-radius: 12px;
            border: 2px solid #e9ecef;
            padding: 1rem !important;
            font-size: 0.95em;
            line-height: 1.6;
            transition: all 0.3s ease;
            background-color: rgba(255, 255, 255, 0.9);
        }
        
        .stTextArea>div>div>textarea:focus {
            border-color: #4b6cb7;
            box-shadow: 0 0 0 3px rgba(75, 108, 183, 0.2);
            outline: none;
        }
        
        .stTextArea>div>div>textarea::placeholder {
            color: #adb5bd;
        }
        
        /* Enhanced File Uploader */
        .stFileUploader>div>div>div>div>div {
            border: 2px dashed #4b6cb7;
            border-radius: 12px;
            padding: 2.5rem 1rem;
            text-align: center;
            background: rgba(255, 255, 255, 0.8);
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        
        .stFileUploader>div>div>div>div>div:hover {
            background: rgba(75, 108, 183, 0.05);
            border-color: #3b5998;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(75, 108, 183, 0.1);
        }
        
        .stFileUploader>div>div>div>div>div::before {
            content: '📄';
            font-size: 2.5rem;
            display: block;
            margin-bottom: 1rem;
            animation: bounce 2s infinite;
        }
        
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-10px); }
            60% { transform: translateY(-5px); }
        }
        
        /* Animated Icons */
        .icon {
            font-size: 2.5rem;
            margin-bottom: 1.25rem;
            color: #4b6cb7;
            display: inline-block;
            transition: all 0.3s ease;
            text-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        
        .card:hover .icon {
            transform: scale(1.1) rotate(5deg);
            color: #3b5998;
        }
        
        /* Feature Icons */
        .feature-icon {
            font-size: 2.5rem;
            width: 80px;
            height: 80px;
            background: linear-gradient(135deg, rgba(75, 108, 183, 0.1), rgba(59, 89, 152, 0.2));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 1.5rem;
            color: #4b6cb7;
            transition: all 0.3s ease;
        }
        
        .feature-card:hover .feature-icon {
            transform: translateY(-5px) scale(1.1);
            box-shadow: 0 10px 20px rgba(75, 108, 183, 0.2);
        }
        
        /* Responsive design */
        @media (max-width: 768px) {
            .header {
                padding: 1.5rem 1rem 2rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Header Section
    st.markdown("""
    <div class="header">
        <h1 style="color: white; margin-bottom: 0.5rem;">✨ Resume Analyzer Pro</h1>
        <p style="opacity: 0.9; margin-bottom: 0;">AI-powered resume analysis for better job matching</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Introduction
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        <div class="card">
            <h3>🔍 How It Works</h3>
            <p>Get instant feedback on your resume's ATS compatibility and improve your chances of landing interviews.</p>
            <ol>
                <li>Upload your resume (PDF format)</li>
                <li>Paste the job description</li>
                <li>Get detailed analysis and improvement suggestions</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card" style="text-align: center;">
            <div class="icon">📊</div>
            <h3>Why Use Our Analyzer?</h3>
            <p>• Beat ATS systems</p>
            <p>• Match job requirements</p>
            <p>• Get hired faster</p>
        </div>
        """, unsafe_allow_html=True)

    # Input Section
    st.markdown("## 🔍 Analyze Your Resume")
    
    # Input columns
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("""
        <div class="card">
            <h3 style="margin-top: 0;">📝 Job Description</h3>
        """, unsafe_allow_html=True)
        job_description = st.text_area(
            "",
            height=250,
            placeholder="Paste the complete job description here..."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="card">
            <h3 style="margin-top: 0;">📎 Upload Your Resume</h3>
            <p style="color: #666; font-size: 0.9em;">Supported format: PDF (max 2MB)</p>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "",
            type=["pdf"],
            help="Please ensure your resume is in PDF format"
        )

        if uploaded_file:
            if uploaded_file.size > 2 * 1024 * 1024:  # 2MB limit
                st.error("❌ File size exceeds 2MB. Please upload a smaller file.")
            else:
                st.success("✅ Resume uploaded successfully!")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Analysis Options
        st.markdown("""
        <div class="card">
            <h4 style="margin-top: 0;">⚙️ Analysis Options</h4>
        """, unsafe_allow_html=True)
        
        analysis_type = st.radio(
            "Choose analysis type:",
            ["Detailed Resume Review", "ATS Match Percentage Analysis"],
            index=0
        )
        
        st.markdown("</div>", unsafe_allow_html=True)

    # Analysis button and results
    if uploaded_file and job_description.strip():
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
        """, unsafe_allow_html=True)
        
        if st.button("✨ Analyze Resume Now", key="analyze_btn"):
            with st.spinner("Analyzing your resume... Please wait"):
                # Extract PDF text with OCR fallback
                pdf_text = ATSAnalyzer.extract_text_from_pdf(uploaded_file)
                
                if not pdf_text:
                    st.error("No text could be extracted from the resume. Please check the file or ensure it’s a text-based PDF. For scanned PDFs, OCR is attempted.")
                    return

                # Perform ATS checks and get detailed analysis
                ats_score, ats_checks, job_keywords, found_sections = ATSAnalyzer.perform_ats_checks(pdf_text, job_description)
                
                # Display ATS Score prominently
                st.markdown("## 🎯 ATS Compatibility Score")
                st.metric("", f"{ats_score:.1f}%", "")
                
                # Add a visual progress bar
                st.progress(ats_score/100)
                
                # Show quick summary
                if ats_score >= 75:
                    st.success("✅ Your resume has good ATS compatibility!")
                elif ats_score >= 50:
                    st.warning("⚠️ Your resume needs some improvements for better ATS compatibility.")
                else:
                    st.error("❌ Your resume needs significant improvements for ATS optimization.")
                
                st.markdown("---")

                # Prepare Gemini prompt based on analysis type
                if analysis_type == "Detailed Resume Review":
                    prompt = """
                    As an experienced Technical HR Manager, provide a detailed professional evaluation of the candidate's resume against the job description. Analyze:
                    1. Overall alignment with the role
                    2. Key strengths and qualifications that match
                    3. Notable gaps or areas for improvement
                    4. Specific recommendations for enhancing ATS compatibility and readability
                    5. Final verdict on suitability for the role
                    
                    Format the response with clear headings, bullet points, and professional language.
                    """
                else:  # ATS Match Percentage Analysis
                    prompt = """
                    As an ATS (Applicant Tracking System) expert, provide:
                    1. Overall match percentage (%)
                    2. Key matching keywords found
                    3. Important missing keywords
                    4. Skills gap analysis
                    5. Specific recommendations for improving ATS compatibility and keyword optimization
                    
                    Start with the percentage match prominently displayed, followed by detailed analysis in bullet points.
                    """

                # Perform ATS analysis
                ats_score, ats_checks, job_keywords, found_sections = ATSAnalyzer.perform_ats_checks(pdf_text, job_description)
                
                # Results Section
                st.markdown("""
                <div style="margin-top: 2rem;">
                    <h2 style="color: #2c3e50; border-bottom: 2px solid #4b6cb7; padding-bottom: 0.5rem;">
                        📊 Analysis Results
                    </h2>
                </div>
                """, unsafe_allow_html=True)
                
                # Score Card
                st.markdown(f"""
                <div class="card" style="text-align: center; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);">
                    <h3 style="margin-top: 0; color: #2c3e50;">Your ATS Compatibility Score</h3>
                    <div style="font-size: 3.5rem; font-weight: 700; color: #4b6cb7; margin: 1rem 0;">
                        {ats_score:.0f}<span style="font-size: 1.5rem; color: #6c757d;">/100</span>
                    </div>
                    <div style="margin: 1rem 0 1.5rem;">
                        <div style="height: 10px; background: #e9ecef; border-radius: 5px; overflow: hidden;">
                            <div style="width: {ats_score}%; height: 100%; background: linear-gradient(90deg, #4b6cb7, #182848);"></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Score Interpretation
                if ats_score >= 75:
                    st.success("""
                    🎉 Excellent! Your resume is well-optimized for ATS systems and stands a good chance of passing initial screenings.
                    """)
                elif ats_score >= 50:
                    st.info("""
                    ℹ️ Good start! Your resume has potential but could benefit from some optimizations to improve ATS compatibility.
                    """)
                else:
                    st.warning("""
                    ⚠️ Needs Improvement. Your resume requires significant optimization to pass through most ATS systems effectively.
                    """)
                
                # Key Metrics
                st.markdown("""
                <div class="card">
                    <h3 style="margin-top: 0; color: #2c3e50;">🔍 Key Metrics</h3>
                    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; margin-top: 1rem;">
                """, unsafe_allow_html=True)
                
                for check, value in ats_checks.items():
                    if isinstance(value, bool):
                        status = "✅" if value else "❌"
                        st.markdown(f"""
                        <div style="background: {'#e8f5e9' if value else '#ffebee'}; 
                                      padding: 0.75rem; border-radius: 8px; border-left: 4px solid {'#4caf50' if value else '#f44336'};">
                            <div style="font-weight: 600; margin-bottom: 0.25rem;">{status} {check}</div>
                            <div style="font-size: 0.9em; color: #666;">
                                {'Great job!' if value else 'Needs attention'}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style="background: #e3f2fd; padding: 0.75rem; border-radius: 8px; border-left: 4px solid #2196f3;">
                            <div style="font-weight: 600; margin-bottom: 0.25rem;">📊 {check}</div>
                            <div style="font-size: 1.1em; font-weight: 600; color: #1976d2;">
                                {value:.1f}%
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
                
                # Keywords Analysis
                st.markdown("""
                <div class="card" style="margin-top: 1.5rem;">
                    <h3 style="margin-top: 0; color: #2c3e50;">🔑 Keyword Analysis</h3>
                    <p style="color: #666; margin-bottom: 1rem;">
                        These are the most important keywords from the job description and how well they match your resume.
                    </p>
                """, unsafe_allow_html=True)
                
                keywords_found = [kw for kw in job_keywords if kw in pdf_text.lower()]
                keywords_missing = [kw for kw in job_keywords if kw not in pdf_text.lower()]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("""
                    <div style="background: #e8f5e9; padding: 1rem; border-radius: 8px; height: 100%;">
                        <h4 style="margin-top: 0; color: #2e7d32;">✅ Found Keywords</h4>
                        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
                    """, unsafe_allow_html=True)
                    
                    for kw in keywords_found[:15]:
                        st.markdown(f"""
                        <span style="background: white; color: #2e7d32; padding: 0.25rem 0.75rem; 
                                    border-radius: 20px; font-size: 0.85em; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                            {kw}
                        </span>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("</div></div>", unsafe_help_html=True)
                
                with col2:
                    if keywords_missing:
                        st.markdown("""
                        <div style="background: #ffebee; padding: 1rem; border-radius: 8px; height: 100%;">
                            <h4 style="margin-top: 0; color: #c62828;">❌ Missing Keywords</h4>
                            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
                        """, unsafe_help_html=True)
                        
                        for kw in keywords_missing[:15]:
                            st.markdown(f"""
                            <span style="background: white; color: #c62828; padding: 0.25rem 0.75rem; 
                                        border-radius: 20px; font-size: 0.85em; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                                {kw}
                            </span>
                            """, unsafe_help_html=True)
                        
                        st.markdown("</div></div>", unsafe_help_html=True)
                
                st.markdown("</div>", unsafe_help_html=True)
                
                # Missing Sections
                missing_sections = [s for s in ['experience', 'education', 'skills'] 
                                 if s not in [sec.lower() for sec in found_sections]]
                if missing_sections:
                    st.markdown("""
                    <div class="card" style="margin-top: 1.5rem; border-left: 4px solid #ff9800;">
                        <h3 style="margin-top: 0; color: #e65100;">⚠️ Recommended Improvements</h3>
                        <p style="color: #666;">Consider adding these important sections to your resume:</p>
                        <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem;">
                    """, unsafe_help_html=True)
                    
                    for section in missing_sections:
                        st.markdown(f"""
                        <span style="background: #fff3e0; color: #e65100; padding: 0.5rem 1rem; 
                                    border-radius: 6px; font-weight: 500; display: inline-flex; align-items: center;">
                            ✨ {section.capitalize()}
                        </span>
                        """, unsafe_help_html=True)
                    
                    st.markdown("</div></div>", unsafe_help_html=True)
                
                # Export Option
                st.markdown("""
                <div style="margin: 2rem 0; text-align: center;">
                """, unsafe_help_html=True)
                
                # Prepare the analysis text for export
                analysis_text = f"""
                ⭐ Resume Analysis Report ⭐
                
                📊 Overall ATS Score: {ats_score:.1f}%
                
                🔍 Key Metrics:
                """
                for check, value in ats_checks.items():
                    status = "✅" if (isinstance(value, bool) and value) else "❌"
                    value_str = "Yes" if isinstance(value, bool) and value else "No" if isinstance(value, bool) else f"{value:.1f}%"
                    analysis_text += f"\n{status} {check}: {value_str}"
                
                analysis_text += "\n\n🔑 Keywords Analysis:"
                analysis_text += "\n\n✅ Found Keywords:\n" + "\n".join(f"- {kw}" for kw in keywords_found[:15])
                if keywords_missing:
                    analysis_text += "\n\n❌ Missing Keywords:\n" + "\n".join(f"- {kw}" for kw in keywords_missing[:15])
                
                if missing_sections:
                    analysis_text += "\n\n⚠️ Recommended Sections to Add:\n" + "\n".join(f"- {s.capitalize()}" for s in missing_sections)
                
                analysis_text += "\n\nGenerated by Resume Analyzer Pro"
                
                # Download Button with better styling
                st.download_button(
                    label="💾 Download Full Analysis Report",
                    data=analysis_text,
                    file_name=f"resume_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    help="Download a detailed report of your resume analysis"
                )
                
                st.markdown("""
                <p style="font-size: 0.85em; color: #666; margin-top: 1rem;">
                    💡 Tip: Save this report to track your resume improvements over time!
                </p>
                </div>
                """, unsafe_help_html=True)

    else:
        # Empty state with illustration
        st.markdown("""
        <div style="text-align: center; padding: 3rem 1rem; background: #f8f9fa; border-radius: 12px; margin: 2rem 0;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">📄🔍</div>
            <h3 style="color: #2c3e50; margin-bottom: 0.5rem;">Ready to Analyze Your Resume?</h3>
            <p style="color: #666; max-width: 600px; margin: 0 auto 1.5rem;">
                Upload your resume and paste the job description to get started with your free ATS optimization analysis.
            </p>
            <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 1.5rem;">
                <div style="text-align: center; padding: 1rem; background: white; border-radius: 8px; flex: 1; max-width: 200px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📋</div>
                    <div style="font-weight: 600; margin-bottom: 0.25rem;">Step 1</div>
                    <div style="font-size: 0.9em; color: #666;">Upload your resume</div>
                </div>
                <div style="display: flex; align-items: center; color: #adb5bd; font-size: 1.5rem;">→</div>
                <div style="text-align: center; padding: 1rem; background: white; border-radius: 8px; flex: 1; max-width: 200px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">📝</div>
                    <div style="font-weight: 600; margin-bottom: 0.25rem;">Step 2</div>
                    <div style="font-size: 0.9em; color: #666;">Paste job description</div>
                </div>
                <div style="display: flex; align-items: center; color: #adb5bd; font-size: 1.5rem;">→</div>
                <div style="text-align: center; padding: 1rem; background: white; border-radius: 8px; flex: 1; max-width: 200px; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                    <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">🚀</div>
                    <div style="font-weight: 600; margin-bottom: 0.25rem;">Step 3</div>
                    <div style="font-size: 0.9em; color: #666;">Get instant analysis</div>
                </div>
            </div>
        </div>
        """, unsafe_help_html=True)

    # Footer with disclaimer and additional links
    st.markdown("""
    <footer style="margin-top: 4rem; padding: 2rem 0; border-top: 1px solid #e9ecef;">
        <div style="max-width: 1000px; margin: 0 auto; padding: 0 1rem;">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 2rem; margin-bottom: 1.5rem;">
                <div style="flex: 1; min-width: 200px;">
                    <h4 style="color: #2c3e50; margin-bottom: 1rem;">Resume Analyzer Pro</h4>
                    <p style="color: #6c757d; font-size: 0.9em; line-height: 1.6;">
                        AI-powered tools to help you optimize your resume for applicant tracking systems and land more interviews.
                    </p>
                </div>
                <div style="flex: 1; min-width: 150px;">
                    <h5 style="color: #2c3e50; margin-bottom: 1rem; font-size: 1em;">Resources</h5>
                    <ul style="list-style: none; padding: 0; margin: 0;">
                        <li style="margin-bottom: 0.5em;"><a href="#" style="color: #4b6cb7; text-decoration: none;">Resume Tips</a></li>
                        <li style="margin-bottom: 0.5em;"><a href="#" style="color: #4b6cb7; text-decoration: none;">ATS Guide</a></li>
                        <li style="margin-bottom: 0.5em;"><a href="#" style="color: #4b6cb7; text-decoration: none;">Job Search</a></li>
                    </ul>
                </div>
                <div style="flex: 1; min-width: 150px;">
                    <h5 style="color: #2c3e50; margin-bottom: 1rem; font-size: 1em;">Company</h5>
                    <ul style="list-style: none; padding: 0; margin: 0;">
                        <li style="margin-bottom: 0.5em;"><a href="#" style="color: #4b6cb7; text-decoration: none;">About Us</a></li>
                        <li style="margin-bottom: 0.5em;"><a href="#" style="color: #4b6cb7; text-decoration: none;">Contact</a></li>
                        <li style="margin-bottom: 0.5em;"><a href="#" style="color: #4b6cb7; text-decoration: none;">Privacy Policy</a></li>
                    </ul>
                </div>
                <div style="flex: 1; min-width: 200px;">
                    <h5 style="color: #2c3e50; margin-bottom: 1rem; font-size: 1em;">Connect With Us</h5>
                    <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                        <a href="#" style="color: #4b6cb7; font-size: 1.5em;">📱</a>
                        <a href="#" style="color: #4b6cb7; font-size: 1.5em;">💼</a>
                        <a href="#" style="color: #4b6cb7; font-size: 1.5em;">🐦</a>
                        <a href="#" style="color: #4b6cb7; font-size: 1.5em;">📧</a>
                    </div>
                </div>
            </div>
            <div style="border-top: 1px solid #e9ecef; padding-top: 1.5rem; margin-top: 1.5rem; text-align: center;">
                <p style="color: #6c757d; font-size: 0.85em; margin: 0;">
                    © 2023 Resume Analyzer Pro. This tool uses AI to analyze resumes but should be used as a guide, not the sole factor in your job application process.
                </p>
            </div>
        </div>
    </footer>
    """, unsafe_help_html=True)

    
if __name__ == "__main__":
    main()
