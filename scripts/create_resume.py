from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()

# Set default font
style = doc.styles['Normal']
font = style.font
font.name = 'Calibri'
font.size = Pt(11)

# Adjust margins
for section in doc.sections:
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.5)
    section.left_margin = Inches(0.6)
    section.right_margin = Inches(0.6)

# ---- HEADER ----
header_para = doc.add_paragraph()
header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = header_para.add_run('Mehul Vishwakarma')
run.bold = True
run.font.size = Pt(22)
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

# Contact line
contact = doc.add_paragraph()
contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = contact.add_run('mehulvinodv@gmail.com | +91 8817385608 | LinkedIn: linkedin.com/in/mehul-vishwakarma13 | GitHub: github.com/mehulvish13')
run.font.size = Pt(9)
run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

doc.add_paragraph()  # spacer

# ---- SUMMARY ----
p = doc.add_paragraph()
run = p.add_run('PROFESSIONAL SUMMARY')
run.bold = True
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

p = doc.add_paragraph()
run = p.add_run('Enthusiastic and results-driven Artificial Intelligence & Machine Learning student with hands-on experience in developing AI-powered solutions and ML models, focusing on responsible and effective problem-solving.')
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

doc.add_paragraph()  # spacer

# ---- TECHNICAL SKILLS ----
p = doc.add_paragraph()
run = p.add_run('TECHNICAL SKILLS')
run.bold = True
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

skills = [
    ("Languages:", "C++, Python"),
    ("Frameworks:", "Pandas, NumPy, Matplotlib, Scikit-learn, Flask, FastAPI"),
    ("Tools:", "Git, GitHub, VS Code, Jupyter notebooks, Streamlit, Docker, Linux"),
    ("Platforms:", "Vercel, Netlify, Render"),
]
for label, value in skills:
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(label + ' ')
    run.bold = True
    run.font.size = Pt(10)
    run = p.add_run(value)
    run.font.size = Pt(10)

doc.add_paragraph()  # spacer

# ---- PROJECTS ----
p = doc.add_paragraph()
run = p.add_run('PROJECTS')
run.bold = True
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

projects = [
    ("FRA Atlas – Digitization & Decision Support Platform", 
     "FastAPI + MySQL platform automating tribal land claim processing. Uses OCR to extract data from documents and a rule-based engine to map beneficiaries to government schemes."),
    ("AI-based Smart Irrigation System", 
     "Machine learning system helping farmers make efficient water usage decisions. Built to reduce water wastage and improve crop health using soil data, weather conditions, and predictive analytics. Achieved 85%+ accuracy in soil moisture prediction."),
    ("HealthAI Guardian", 
     "Integrated chronic disease prediction system using ML, NLP, and sensor data. Supports symptom evaluation, personalized risk scores, and early-warning alerts. Deployed prototype with Streamlit."),
    ("SehatSathi – Personal Health & Mental Fitness Assistant", 
     "Combines physical health tracking and mental wellbeing monitoring. Includes calorie estimation, workout suggestions, stress scoring, mood analytics, and conversational health guide."),
    ("FitRep – AI Workout Tracker", 
     "Combines physical health tracking and mental wellbeing monitoring. Includes calorie estimation, workout suggestions, stress scoring, mood analytics, and conversational health guide."),
]

for title, desc in projects:
    p = doc.add_paragraph()
    run = p.add_run(title)
    run.bold = True
    run.font.size = Pt(10)
    p = doc.add_paragraph(desc)
    p.paragraph_format.space_after = Pt(2)
    for run in p.runs:
        run.font.size = Pt(9)

doc.add_paragraph()  # spacer

# ---- HACKATHON ACHIEVEMENTS ----
p = doc.add_paragraph()
run = p.add_run('HACKATHON ACHIEVEMENTS')
run.bold = True
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

hackathons = [
    ("NexGen Hack Ghaziabad 2025", "Finalist – Shortlisted from 400 teams into final 30. Top ranking among 30 finalists."),
    ("VOID Hacks 7.0", "Shortlisted from 250+ teams into final 15."),
]
for title, desc in hackathons:
    p = doc.add_paragraph()
    run = p.add_run(title + "  •  ")
    run.bold = True
    run.font.size = Pt(10)
    run = p.add_run(desc)
    run.font.size = Pt(10)

doc.add_paragraph()  # spacer

# ---- INTERNSHIP ----
p = doc.add_paragraph()
run = p.add_run('INTERNSHIP')
run.bold = True
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

internship = (
    "AICTE – Edunet Foundation (4 Weeks) • Developed ML-based irrigation decision support system using soil, moisture, and weather parameters. "
    "Deployed prototype using Streamlit for practical water planning. "
    "Built predictive models with 80%+ accuracy on test dataset."
)
p = doc.add_paragraph(internship)
for run in p.runs:
    run.font.size = Pt(10)

doc.add_paragraph()  # spacer

# ---- EDUCATION (the improved version) ----
p = doc.add_paragraph()
run = p.add_run('EDUCATION')
run.bold = True
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

# B.Tech
p = doc.add_paragraph()
run = p.add_run('B.Tech in Computer Science (Artificial Intelligence & Machine Learning)')
run.bold = True
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

p = doc.add_paragraph()
run = p.add_run('Shri Ram Institute of Technology, Jabalpur  |  CGPA: 8.8/10  |  (2023 – 2027)')
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

p = doc.add_paragraph()
run = p.add_run('Relevant Coursework: Data Structures & Algorithms, Machine Learning fundamentals, Deep Learning, Computer Vision, NLP, Probability & Statistics, DBMS, Python Programming, AI')
run.font.size = Pt(9)
run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

# Senior Secondary
doc.add_paragraph()
p = doc.add_paragraph()
run = p.add_run('Senior Secondary (12th Grade)')
run.bold = True
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

p = doc.add_paragraph()
run = p.add_run('Central Academy Higher Secondary School, Shahdol  |  Percentage: 91.8%  |  (2022 – 2023)')
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

p = doc.add_paragraph()
run = p.add_run('Stream: PCM (Physics, Chemistry, Mathematics)')
run.font.size = Pt(9)
run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

# Secondary
doc.add_paragraph()
p = doc.add_paragraph()
run = p.add_run('Secondary (10th Grade)')
run.bold = True
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

p = doc.add_paragraph()
run = p.add_run('Spring Dales Higher Secondary School, Shahdol  |  Percentage: 81.6%  |  (2020 – 2021)')
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

doc.add_paragraph()  # spacer

# ---- ADDITIONAL INFORMATION ----
p = doc.add_paragraph()
run = p.add_run('ADDITIONAL INFORMATION')
run.bold = True
run.font.size = Pt(12)
run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

p = doc.add_paragraph()
run = p.add_run('Languages: English, Hindi  |  Interests: Listening to Music, exploring upcoming technologies')
run.font.size = Pt(10)
run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

# Save
doc.save('resumeMV-formatted.docx')
print("DOCX saved successfully!")