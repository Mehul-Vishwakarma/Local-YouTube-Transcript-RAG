"""Visual v2: easy to read Resume + LinkedIn audit for Mysol. Color + boxes + tables."""
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = r"C:\Users\Pcc\Desktop\trying-Creative-MySYNT\Mysol_Resume_LinkedIn_Expert_Audit_Visual.docx"

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(10.5)
style.paragraph_format.space_after = Pt(4)
style.paragraph_format.line_spacing = 1.07

for s in doc.sections:
    s.top_margin = Inches(0.55)
    s.bottom_margin = Inches(0.55)
    s.left_margin = Inches(0.6)
    s.right_margin = Inches(0.6)

NAVY = RGBColor(0x1A, 0x1A, 0x2E)
BLUE = RGBColor(0x0F, 0x62, 0x8A)
GREEN = RGBColor(0x1B, 0x7F, 0x5A)
AMBER = RGBColor(0x8A, 0x5A, 0x00)
RED = RGBColor(0xB4, 0x23, 0x18)
GREY = RGBColor(0x33, 0x33, 0x33)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)

def cell_text(cell, text, bold=False, color=None, size=10, align=None, italic=False):
    cell.text = ""
    p = cell.paragraphs[0]
    if align is not None:
        p.alignment = align
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    r.font.size = Pt(size)
    r.font.name = "Calibri"
    if color is not None:
        r.font.color.rgb = color
    return p

def para(text, bold=False, color=None, size=10.5, align=None, italic=False):
    pg = doc.add_paragraph()
    if align is not None:
        pg.alignment = align
    r = pg.add_run(text)
    r.bold = bold
    r.italic = italic
    r.font.size = Pt(size)
    if color is not None:
        r.font.color.rgb = color
    return pg

def h1(t):
    h = doc.add_heading(t, level=1)
    for r in h.runs:
        r.font.color.rgb = NAVY
    return h

def h2(t):
    h = doc.add_heading(t, level=2)
    for r in h.runs:
        r.font.color.rgb = BLUE
    return h

def h3(t):
    return doc.add_heading(t, level=3)

def bullets(items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")

def numbers(items):
    for it in items:
        doc.add_paragraph(it, style="List Number")

def callout(title, body_lines, bg="EAF4FB", border_text="0F628A"):
    tb = doc.add_table(rows=1, cols=1)
    tb.style = "Table Grid"
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = tb.cell(0, 0)
    shade(c, bg)
    c.text = ""
    p1 = c.paragraphs[0]
    r = p1.add_run(title)
    r.bold = True
    r.font.size = Pt(11)
    r.font.color.rgb = NAVY
    for ln in body_lines:
        px = c.add_paragraph(ln, style="List Bullet")
    doc.add_paragraph()
    return tb

def kpi_row(cards):
    # cards: list of (label, value, sub, bgcolor)
    tb = doc.add_table(rows=2, cols=len(cards))
    tb.style = "Table Grid"
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, (label, value, sub, bg) in enumerate(cards):
        shade(tb.cell(0, j), bg)
        cell_text(tb.cell(0, j), label, bold=True, color=WHITE, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
        cell_text(tb.cell(1, j), value + "\n" + sub, bold=True, color=NAVY, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_paragraph()
    return tb

def styled_table(headers, rows, header_bg="1A1A2E", band=True):
    tb = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tb.style = "Table Grid"
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, hh in enumerate(headers):
        shade(tb.cell(0, j), header_bg)
        cell_text(tb.cell(0, j), hh, bold=True, color=WHITE, size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER)
    for i, row in enumerate(rows, start=1):
        for j, val in enumerate(row):
            cell_text(tb.cell(i, j), val, size=9.5)
            if band and i % 2 == 0:
                shade(tb.cell(i, j), "F2F4F7")
    doc.add_paragraph()
    return tb

def before_after(title, before_lines, after_lines):
    h3(title)
    tb = doc.add_table(rows=2, cols=2)
    tb.style = "Table Grid"
    tb.alignment = WD_TABLE_ALIGNMENT.CENTER
    shade(tb.cell(0, 0), "B42318")
    cell_text(tb.cell(0, 0), "BEFORE (now)", bold=True, color=WHITE, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    shade(tb.cell(0, 1), "1B7F5A")
    cell_text(tb.cell(0, 1), "AFTER (copy ready)", bold=True, color=WHITE, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    cb = tb.cell(1, 0)
    shade(cb, "FDECEA")
    cb.text = ""
    for ln in before_lines:
        cb.add_paragraph(ln, style="List Bullet")
    ca = tb.cell(1, 1)
    shade(ca, "E6F4EA")
    ca.text = ""
    for ln in after_lines:
        ca.add_paragraph(ln, style="List Bullet")
    doc.add_paragraph()
    return tb

# ============ COVER ============
banner = doc.add_table(rows=1, cols=1)
banner.alignment = WD_TABLE_ALIGNMENT.CENTER
bc = banner.cell(0, 0)
shade(bc, "1A1A2E")
bc.text = ""
t1 = bc.paragraphs[0]
t1.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t1.add_run("Resume + LinkedIn Expert Audit")
r.bold = True
r.font.size = Pt(26)
r.font.color.rgb = WHITE
t2 = bc.add_paragraph()
t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t2.add_run("For Mysol  |  B.Tech CSE (AI and ML), SRIT Jabalpur, 2023-2027")
r.font.size = Pt(12)
r.font.color.rgb = RGBColor(0x9E, 0xD1, 0xFF)
t3 = bc.add_paragraph()
t3.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t3.add_run("Placement lens: SDE + AI/ML  |  T-shape: backend base + ML edge  |  Sept 2026")
r.font.size = Pt(10)
r.font.color.rgb = WHITE
doc.add_paragraph()

kpi_row([
    ("RESUME", "7.0 / 10", "Strong base", "0F628A"),
    ("LINKEDIN", "6.8 / 10", "Fix trust gaps", "1B7F5A"),
    ("TOP FIX", "+1.5 pts", "Add 4 numbers", "8A5A00"),
    ("TIME", "14 days", "Follow plan", "1A1A2E"),
])

callout("How to read this report in 10 minutes", [
    "GREEN boxes = keep. RED boxes = fix now. BLUE boxes = copy ready text.",
    "Start with Section 1 scorecard, then copy from Sections 3 and 4, then do the Day 1 to 3 checklist.",
    "Rule used everywhere: Verb + What + Tools + Scale + Result + Link. No number without base.",
], bg="EAF4FB")

callout("Files checked", [
    "Resume PDF: resumeMvAugUpdated=sept10.pdf.pdf and DOCX for Caelius, both Sept 2026, CGPA 8.65.",
    "LinkedIn PDF export: 3 pages with headline, About, Edunet intern detail, education, certs.",
    "Profile goal: placement ready for SDE and AI/ML before campus placements.",
], bg="F2F4F7")

# ============ LEGEND ============
h1("Visual legend: what colors mean")
styled_table(
    ["Color", "Meaning", "Action"],
    [
        ["GREEN", "Perfect, keep it", "Do not change, add proof link only"],
        ["RED", "Fix before applying", "Rewrite this week"],
        ["AMBER", "Polish soon", "Fix in 14 days"],
        ["BLUE", "Copy ready", "Paste and adjust numbers to truth"],
    ],
    header_bg="0F628A",
)

# ============ 1 SCORECARD ============
h1("1. Scorecard: where you stand")
para("Big picture: talent is proven. Packaging is the gap. LinkedIn sells you better than your resume today. Flip that, because recruiters shortlist from the resume in 30 seconds.", bold=True)

styled_table(
    ["Area", "Score", "Signal", "Fix"],
    [
        ["Resume overall", "7.0 / 10", "YELLOW: good bones", "Add metrics + links"],
        ["Resume projects", "6.5 / 10", "YELLOW: 1 weak link", "Rewrite FitRep, add OCR + RF numbers"],
        ["Resume ATS", "6.0 / 10", "RED: links + export", "Full URLs, clean PDF export"],
        ["LinkedIn headline", "7.5 / 10", "GREEN-YELLOW", "Fix typo, add FastAPI + MySQL"],
        ["LinkedIn About", "6.5 / 10", "YELLOW: overclaim", "Keep proven, move ideas to Learning"],
        ["LinkedIn Experience", "8.5 / 10", "GREEN: model entry", "Keep, add demo + cert media"],
        ["LinkedIn trust", "6.0 / 10", "RED: date error", "Fix 2010-2022 schooling years"],
        ["Resume-LinkedIn match", "6.0 / 10", "RED: mismatch", "One number table everywhere"],
    ],
    header_bg="1A1A2E",
)

callout("Recruiter 30 second eye path (F pattern)", [
    "Second 0 to 5: name, role target, location, links. If links are plain text, many stop here.",
    "Second 5 to 15: skills row scan for Python, REST, SQL, Scikit-learn. Missing keyword = reject.",
    "Second 15 to 30: first bullets of top 2 projects for numbers. No numbers = maybe pile.",
    "Fix order matches this path: header, then skills, then top bullets.",
], bg="FFF6E0")

h2("1.1 Your T-shape at a glance")
tshape = doc.add_table(rows=2, cols=3)
tshape.style = "Table Grid"
tshape.alignment = WD_TABLE_ALIGNMENT.CENTER
shade(tshape.cell(0, 0), "0F628A")
cell_text(tshape.cell(0, 0), "SOFTWARE BASE (wide)", bold=True, color=WHITE, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
shade(tshape.cell(0, 1), "1A1A2E")
cell_text(tshape.cell(0, 1), "PROOF", bold=True, color=WHITE, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
shade(tshape.cell(0, 2), "1B7F5A")
cell_text(tshape.cell(0, 2), "AI EDGE (deep)", bold=True, color=WHITE, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
cell_text(tshape.cell(1, 0), "Python, OOP, DSA, REST with FastAPI, MySQL + PostgreSQL, Git", size=9.5)
cell_text(tshape.cell(1, 1), "FRA Atlas + 2 hack finals + Edunet showcase", size=9.5, bold=True)
cell_text(tshape.cell(1, 2), "Scikit-learn, Pandas, Streamlit deploys, CV starter (OpenCV, MediaPipe)", size=9.5)
doc.add_paragraph()
para("Read it left to right in interviews: I build backends that work, I prove it with shipped apps, and I add ML where it saves time or resources.", italic=True)

h2("1.2 Top 10 fixes in order")
styled_table(
    ["Rank", "Fix", "Gain"],
    [
        ["1", "Irrigation: add RF 93.7%, 19 sensors, 3 zones, 88-92% zone score", "Resume +1.0"],
        ["2", "Header: full URLs + one email + spaced phone", "ATS + trust"],
        ["3", "FitRep: stack + logic + 1 metric + link", "Removes red flag"],
        ["4", "FRA Atlas: name OCR + tables + time saved", "SDE signal up"],
        ["5", "Summary: 2 line T-shape with CGPA + proofs", "30 sec scan pass"],
        ["6", "LinkedIn education: fix years + add marks", "Trust restored"],
        ["7", "Headline: fix typo + add FastAPI MySQL", "SDE reach"],
        ["8", "About: proven vs learning split", "Interview safety"],
        ["9", "English level + cert order", "Filter pass"],
        ["10", "Clean PDF re-export + copy paste test", "Polish"],
    ],
    header_bg="0F628A",
)

# ============ 2 METHOD ============
h1("2. How this was judged: simple lens")
callout("Three checks every application must pass", [
    "CHECK 1 Human scan: can a tired recruiter see role fit, stack, proof and links in 30 seconds.",
    "CHECK 2 ATS parse: can software read skills, dates, bullets and URLs with no boxes or icons.",
    "CHECK 3 Probe defense: if they ask show me or why this number, you open a repo, demo or log.",
], bg="EAF4FB")

h2("2.1 Perfect bullet formula (memorize this picture)")
formula = doc.add_table(rows=2, cols=6)
formula.style = "Table Grid"
formula.alignment = WD_TABLE_ALIGNMENT.CENTER
chips = [("VERB", "B42318"), ("WHAT", "1A1A2E"), ("TOOLS", "0F628A"), ("SCALE", "8A5A00"), ("RESULT", "1B7F5A"), ("LINK", "555555")]
for j, (lab, bg) in enumerate(chips):
    shade(formula.cell(0, j), bg)
    cell_text(formula.cell(0, j), lab, bold=True, color=WHITE, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
vals = ["Built", "zone control", "RF + Streamlit", "19 sensors", "30% less water", "GitHub"]
for j, v in enumerate(vals):
    cell_text(formula.cell(1, j), v, size=9, align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_paragraph()
para("Example full bullet: Built zone control with Random Forest and Streamlit on 19 sensors, cut water use 30% vs fixed schedule. Repo + demo.", italic=True)

# ============ 3 RESUME ============
h1("3. Resume: keep, fix, with copy ready examples")
para("Keep one page. Keep 3 projects. Do not add breadth now. Add depth and links.", bold=True)

h2("3.1 Header and contact")
styled_table(["Check", "Now", "Status"], [
    ["Location", "Jabalpur present", "GREEN keep"],
    ["Links", "Plain words Linkedin Github", "RED fix to full URLs"],
    ["Email", "Two ids seen", "RED pick one"],
    ["Phone", "No spaces", "AMBER space it"],
    ["Export", "Broken dash chars", "RED re-export"],
], header_bg="0F628A")
before_after("Header: before vs after",
    ["Mehul Vishwakarma | Jabalpur | +918817385608 | mehulvinod@gmail.com | Linkedin | Github"],
    ["Mehul Vishwakarma | Jabalpur, India | +91 88173 85608 | mehulvinodv@gmail.com",
     "linkedin.com/in/mehul-vishwakarma13 | github.com/mehulvish13",
     "Why: clickable, ATS readable, one email, scannable phone."])
callout("Quick test", ["Copy all text from your PDF into Notepad. If links break or boxes appear, export again with Calibri or Arial."], bg="FFF6E0")

h2("3.2 Summary: from generic to T-shape")
before_after("Summary",
    ["B.Tech AIML student with hands on experience in backend APIs, databases and AI/ML. Proficient in Python, FastAPI, Flask, OOP, DSA and problem solving."],
    ["OPTION A (balanced, recommended): B.Tech AIML 2027, SRIT Jabalpur, CGPA 8.65. Backend base in Python, FastAPI (REST), MySQL and PostgreSQL plus ML with Scikit-learn. Built FRA Atlas for document triage and Smart Irrigation at 93.7% accuracy with 30% water savings. DSA in Python and C++. Seeking SDE and AI/ML internships.",
     "OPTION B (AI heavy): AIML undergrad focused on deployable ML: cleaning, features, training, Streamlit deploy. Backend support in FastAPI + SQL. Edunet x AICTE x Shell intern. Finalist Top 30/400 and Top 15/250.",
     "OPTION C (SDE heavy): CS AIML with Python, OOP, DSA, REST, MySQL, Git. Applied ML for workflows: OCR + rules for claims, Random Forest for irrigation. Open to backend roles with ML exposure."])

h2("3.3 Skills polish")
styled_table(["Row", "Keep?", "Edit"], [
    ["Languages", "Keep", "Write Languages: Python, C++"],
    ["Core CS", "Keep + add", "Add REST APIs: OOP, DSA, DBMS, SQL, REST APIs"],
    ["AIML", "Fix caps", "Pandas, NumPy, Matplotlib, Scikit-learn"],
    ["Backend + DB", "Clarify", "FastAPI (REST), Flask | MySQL, PostgreSQL"],
    ["New claims", "Hold", "Add TF, Torch, OpenCV, Java only with repo proof"],
], header_bg="0F628A")
callout("Why REST matters", ["Many SDE JDs filter on the exact phrase REST APIs. You built it with FastAPI, so name it and get the match."], bg="EAF4FB")

h2("3.4 FRA Atlas: your SDE star")
para("Keep. It shows upload + OCR + rules + DB + API thinking. Missing scale and engine name.")
before_after("FRA Atlas bullets",
    ["Implemented OCR-based document processing to extract relevant information.",
     "Built rule engine to map info to schemes."],
    ["Built OCR pipeline with Tesseract + deskew and denoise to pull name, survey id, claim date from 120 test records at 91% field accuracy.",
     "Exposed FastAPI REST for upload, extract and match on MySQL with 6 tables indexed on beneficiary id.",
     "Mapped 15+ scheme rules, cut triage from 20 min to 4 min per file in pilot. Links: GitHub + demo.",
     "If you lack accuracy logs, report docs tested + fields + before vs after time. Never leave it vague."])

h2("3.5 Smart Irrigation: move LinkedIn numbers here")
para("This is your highest ROI edit. LinkedIn already has the gold. Resume must match it.")
before_after("Irrigation bullets",
    ["Built ML app on soil, temp, humidity, pH and weather.",
     "Achieved measurable impact and about 30% water savings."],
    ["Trained Random Forest on 19 IoT sensors with Pandas cleaning and feature engineering; 93.7% test accuracy (state split).",
     "Built 3 zone control at 88-92% need accuracy with Streamlit live dashboard and recommendations.",
     "Cut water 30% vs fixed schedule in field test with logged predictions. Stack + GitHub + demo video.",
     "Interview prep: split, baseline vs RF, top features, failure cases."])
callout("Honesty label", ["If 93.7% is validation not test, write validation accuracy. Honest labels survive probes."], bg="FFF6E0")

h2("3.6 FitRep: fix or cut")
para("Now it repeats intelligent and personalized with no stack or metric. That hurts more than helps.")
before_after("FitRep bullets",
    ["AI-assisted tracker for workouts, calories, recommendations and progress.",
     "Integrated data processing into app workflow."],
    ["PATH A rules (if no ML): MET table calorie model by weight and duration + overload rules; Pandas log + Matplotlib trends for 12 lifts; 60+ sessions over 4 weeks within 12% of tracker baseline; CSV export.",
     "PATH B ML (if trained): regression on 5k row workout set, MAE 18.4 kcal vs 26.1 baseline; split by muscle group + recovery; Streamlit history + charts.",
     "Pick the true path. Add one limit line in README. If no metric in 7 days, swap in a small REST + auth + tests project."])

h2("3.7 Experience and Education")
before_after("Experience (Edunet)",
    ["Developed irrigation system with Python, IoT, ML and Streamlit."],
    ["Owned end to end: 19 sensors, cleaning + features, RF at 93.7%, Streamlit for 3 zones.",
     "Presented at regional showcase; joint cert Edunet + AICTE + Shell. Demo + docs linked.",
     "Keep July 2025 to Aug 2025 exactly as on certificate."])
styled_table(["Education line", "Write it like this"], [
    ["B.Tech", "SRIT Jabalpur | CGPA 8.65 through 5th sem | B.Tech CSE (AI and ML), 2023-2027"],
    ["12th", "Central Academy, Shahdol | 91.8%, PCM, 2022-2023"],
    ["10th", "Spring Dales, Shahdol | 81.6%, 2021-2022"],
], header_bg="0F628A")
para("Achievements: keep both ranks with denominators. Add one GDG line if space: co-ran 2 AI workshops for 80+ students.", italic=True)

# ============ 4 LINKEDIN ============
h1("4. LinkedIn: trust fixes + copy ready text")

h2("4.1 Headline")
before_after("Headline",
    ["AIML 27 | NexGen Hack National Hackathon Finalist | Ex-Ml-Edunet Intern | Python | Machine learning | Generative AI | GDG Volunteer"],
    ["RECOMMENDED: B.Tech AIML 27, SRIT | SDE + ML: Python, FastAPI, MySQL | Irrigation 93.7% | Finalist Top 30/400 | Ex Edunet x AICTE x Shell | GDG Volunteer",
     "SHORT: AIML Undergrad | Python, FastAPI, Scikit-learn | FRA Atlas + Irrigation | Open to SDE + ML Internships",
     "Keep under 220 chars for mobile. Proof first, ask second."])

h2("4.2 About: proven vs learning")
callout("Golden rule", ["Proven = repo or demo linked. Learning = small repo in progress. Ideas with no code stay out of About."], bg="FFF6E0")
before_after("About",
    ["Built chatbots, gesture systems, drone swarms, Health Assistant, Fake News Detector plus irrigation."],
    ["I am Mysol, B.Tech AIML 2027, CGPA 8.65. I build deployable AI: Python, FastAPI, SQL plus Scikit-learn and Streamlit.",
     "PROVEN: Irrigation (RF 93.7%, 19 sensors, 3 zones, 30% savings, showcased) + FRA Atlas (FastAPI + MySQL + OCR + rules).",
     "LEARNING: OpenCV + MediaPipe mini demos + RAG basics. GDG volunteer: workshops + mentoring.",
     "OPEN TO: SDE + AI/ML internships, research support, collabs. Jabalpur + remote. Links in Featured."])

h2("4.3 Experience, education, skills")
styled_table(["Block", "Keep", "Fix now"], [
    ["Edunet entry", "All numbers + 4 week note", "Add 60 sec demo + cert PDF"],
    ["Ambassador x2", "One line each", "No tech claims, keep short"],
    ["GDG", "Missing entry", "Add months + 2 workshops + 80+ students"],
    ["SRIT", "Degree + years", "Add CGPA + DSA OOP DBMS OS"],
    ["12th + 10th", "Names", "Fix years, add 91.8% + 81.6%"],
    ["Top skills CV", "Niche good", "Add 30 sec demo or switch to Python FastAPI Scikit-learn"],
    ["English", "Check truth", "Professional if you interview in English"],
    ["Certs", "Python + AI on top", "Push CSS3 + CyberOps down"],
], header_bg="0F628A")

h2("4.4 Featured and activity starter")
kpi_row([
    ("SLOT 1", "Resume PDF", "Sept 2026", "1A1A2E"),
    ("SLOT 2", "Irrigation", "Demo + repo", "0F628A"),
    ("SLOT 3", "FRA Atlas", "Diagram + repo", "1B7F5A"),
    ("POSTS", "2 in 14 days", "Tables + pics", "8A5A00"),
])
bullets([
    "Post 1: baseline vs Random Forest table. What won and by how much.",
    "Post 2: FRA before vs after triage time with screenshot. Short + visual.",
])

# ============ 5 CONSISTENCY ============
h1("5. Consistency heatmap: one truth everywhere")
para("Green = match. Red = mismatch to fix. After fixes, all rows must be green.")
heat = doc.add_table(rows=1, cols=4)
heat.style = "Table Grid"
heat.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, hh in enumerate(["Item", "Resume", "LinkedIn", "GitHub"]):
    shade(heat.cell(0, j), "1A1A2E")
    cell_text(heat.cell(0, j), hh, bold=True, color=WHITE, size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER)
rows_heat = [
    ("Email", "Pick 1 id", "Same 1 id", "Same 1 id", ["FFF6E0", "FFF6E0", "FFF6E0"]),
    ("RF 93.7%", "Add + split", "Already has", "metrics.json", ["FDECEA", "E6F4EA", "FFF6E0"]),
    ("19 sensors 3 zones", "Add", "Has", "Schema", ["FDECEA", "E6F4EA", "FFF6E0"]),
    ("30% savings + base", "Add base", "Has", "Log note", ["FFF6E0", "E6F4EA", "FFF6E0"]),
    ("OCR engine", "Name it", "Same name", "requirements", ["FDECEA", "FFF6E0", "FFF6E0"]),
    ("FitRep metric", "Add 1", "Same 1", "README", ["FDECEA", "FDECEA", "FDECEA"]),
    ("CGPA 8.65 5th sem", "Add sem", "Add", "Optional", ["FFF6E0", "FFF6E0", "F2F4F7"]),
    ("Java TF Torch CV", "Only with repo", "Move to Learning", "Demo or drop", ["FFF6E0", "FDECEA", "FDECEA"]),
]
for item, a, b, c, bgs in rows_heat:
    row = heat.add_row()
    cell_text(row.cells[0], item, bold=True, size=9.5)
    for j, (val, bg) in enumerate(zip([a, b, c], bgs), start=1):
        cell_text(row.cells[j], val, size=9.5)
        shade(row.cells[j], bg)
doc.add_paragraph()
para("How to read: any red cell blocks applications. Fix reds in Days 1 to 7.", italic=True)

# ============ 6 ATS ============
h1("6. ATS and formatting: pass or fail")
styled_table(["Check", "Pass", "Fail you have now"], [
    ["Layout", "One column", "Avoid 2 col for applies"],
    ["Headings", "Summary Skills Projects Experience Education", "Keep these exact words"],
    ["Skills", "Plain commas", "Fix Numpy spacing + caps"],
    ["Dates", "MMM YYYY hyphen", "Fix broken dash chars"],
    ["URLs", "Full linkedin.com github.com", "Plain words fail"],
    ["File name", "Mysol_BTech_AIML_Resume_Sept2026.pdf", "Avoid = # spaces"],
], header_bg="1B7F5A")
callout("60 second copy test", ["Select all in PDF, paste into Notepad. Links must survive. Boxes mean re-export with Calibri or Arial 10 to 11 pt."], bg="EAF4FB")

# ============ 7 BULLETS ============
h1("7. Bullet bank: pick, fill brackets, paste")
para("Do not invent numbers. Log this week, then fill. Each follows Verb + What + Tools + Scale + Result + Link.")
h2("7.1 Backend in blue")
styled_table(["#", "Copy pattern"], [
    ["1", "Built REST with FastAPI for [upload + extract + match] with Pydantic; p95 [200] ms local."],
    ["2", "Designed MySQL [6] tables indexed on [beneficiary_id]; lookup [2.1] s to [0.3] s on [10k] rows."],
    ["3", "Handled PDFs to [10] MB with OCR queue, retry and logs."],
    ["4", "Wrote [25] pytest cases for auth + validation + edge files; CI green."],
    ["5", "Docker compose for API + DB; one command run in README."],
    ["6", "Added pagination + search for [1k+] rows; load down [40]%."],
], header_bg="0F628A")
h2("7.2 ML in green")
styled_table(["#", "Copy pattern"], [
    ["1", "Cleaned [19] sensors: fills, caps, time buckets; split [80/20] stratified."],
    ["2", "RF [93.7]% vs Logistic [81.2]%; kept RF with confusion matrix."],
    ["3", "Built [8] features; top was [24h moisture mean]. Zones [88-92]%."],
    ["4", "Streamlit live charts + advice cards; refresh [30] s; mobile tested."],
    ["5", "Cut water [30]% vs fixed schedule over [2] weeks on [3] zones."],
    ["6", "Versioned model + metrics.json for reruns; redacted PII before OCR store."],
], header_bg="1B7F5A")
h2("7.3 Impact in amber")
styled_table(["#", "Copy pattern"], [
    ["1", "Cut triage [20] min to [4] min per file on [50] files."],
    ["2", "120 docs at [91]% field accuracy; top 3 errors logged."],
    ["3", "Shipped in [3] weeks; demo to [40+] attendees."],
    ["4", "Top [30]/[400+] NexGen; Top [15]/[250+] VOID, certs linked."],
    ["5", "Ran 2 GDG workshops for [80+]; mentored [15] on Git + Streamlit."],
    ["6", "Demo video [60-90] s, no cuts, upload to result."],
], header_bg="8A5A00")

# ============ 8 PLAN ============
h1("8. 14 day plan: color phases")
plan = doc.add_table(rows=1, cols=4)
plan.style = "Table Grid"
plan.alignment = WD_TABLE_ALIGNMENT.CENTER
for j, hh in enumerate(["Days", "Phase", "Do", "Done looks like"]):
    shade(plan.cell(0, j), "1A1A2E")
    cell_text(plan.cell(0, j), hh, bold=True, color=WHITE, size=9.5, align=WD_ALIGN_PARAGRAPH.CENTER)
phases = [
    ("1-3", "Resume core", "Header + Summary + Skills + Irrigation numbers", "Clean PDF passes copy test"),
    ("4-7", "Proof", "FRA + FitRep + Experience + 2 reviews", "All bullets have metric + link"),
    ("8-11", "LinkedIn", "Headline + About + Edu + GDG + Featured", "No reds in heatmap"),
    ("12-14", "Show", "60s demo + 2 posts + 5 applies", "Recruiter clicks demo"),
]
phase_bg = ["0F628A", "1B7F5A", "8A5A00", "1A1A2E"]
for (d, ph, do, done), bg in zip(phases, phase_bg):
    row = plan.add_row()
    shade(row.cells[1], bg)
    cell_text(row.cells[0], d, bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_text(row.cells[1], ph, bold=True, color=WHITE, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_text(row.cells[2], do, size=9.5)
    cell_text(row.cells[3], done, size=9.5)
doc.add_paragraph()
callout("30-60-90 after that", [
    "30 days: all links live, numbers match, 15 tailored applies logged.",
    "60 days: prove CV claim with mini demo or swap Top Skills to backend + ML. Add LeetCode link at 50+ solved for SDE.",
    "90 days: turn best project into 2 page case study for interviews and portfolio.",
], bg="F2F4F7")

# ============ 9 CHECKS ============
h1("9. Final checks: tick before you apply")
h2("9.1 Resume tick boxes")
styled_table(["Tick", "Check"], [
    ["[ ]", "Role + stack + 2 proofs + links seen without scrolling"],
    ["[ ]", "Every bullet: verb + tool + scale or number"],
    ["[ ]", "Full URLs clickable, one email, spaced phone"],
    ["[ ]", "Notepad paste is clean, file name has no = or #"],
    ["[ ]", "Numbers have bases: split, baseline, denominator"],
], header_bg="0F628A")
h2("9.2 LinkedIn tick boxes")
styled_table(["Tick", "Check"], [
    ["[ ]", "Headline under 220 chars, no typos, 1 number"],
    ["[ ]", "About Proven matches resume, Learning separate"],
    ["[ ]", "Edunet numbers match + media attached"],
    ["[ ]", "Education years and marks correct"],
    ["[ ]", "Featured has resume + 2 demos, Projects linked"],
], header_bg="1B7F5A")
h2("9.3 Interview defense card")
styled_table(["Claim", "Measured how", "Proof", "Limit + next"], [
    ["93.7% RF", "80/20 split, seed noted", "metrics.json", "Small data, add CV next"],
    ["30% savings", "2 wks, 3 zones vs fixed", "Demo + log", "Short window, longer trial"],
    ["FRA 91% fields", "120 docs manual check", "Repo sample", "Handwriting queue next"],
    ["Top 30/400", "Shortlist mail", "Cert", "State team role"],
    ["Top 15/250", "Shortlist mail", "Cert", "State team role"],
], header_bg="1A1A2E")

callout("Closing: depth beats breadth", [
    "One defended metric beats five adjectives.",
    "Your story in one line: FastAPI + SQL for engineering, Random Forest + Streamlit for applied ML, proven at showcase and hackathons.",
    "Next: tell me FitRep truth, rules or ML, and I will return final paste ready bullets + About text.",
], bg="EAF4FB")

doc.save(OUT)
print(f"Saved to {OUT}")
