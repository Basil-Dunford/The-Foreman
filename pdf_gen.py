from fpdf import FPDF
import os

def create_hutton_pdf(filename, title, content):
    pdf = FPDF()
    pdf.add_page()
    
    # Header - Hutton Style
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="HUTTON - INTERNAL PROJECT DATA", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="Confidential: For Internal Training Only", ln=True, align='C')
    pdf.ln(10)
    
    # Title
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=title, ln=True, align='L')
    pdf.ln(5)
    
    # Body
    pdf.set_font("Arial", size=11)
    for line in content:
        pdf.multi_cell(0, 8, txt=line, align='L')
        pdf.ln(2)
        
    if not os.path.exists('test_data'):
        os.makedirs('test_data')
    pdf.output(f"test_data/{filename}")

# --- PDF 1: The Historical Win ---
create_hutton_pdf(
    "2023_Wichita_Cold_Storage.pdf",
    "Project Closeout: The Monarch Cold Storage Facility",
    [
        "Project Lead: Sarah Miller | Date: October 2023",
        "SUMMARY: Construction of a 50,000 sq ft facility for frozen goods.",
        "CHALLENGE: Encountered an unexpectedly high water table during foundation excavation.",
        "SOLUTION: Deployed specialized slurry wall shielding and an advanced sump pump system. This added $45k to the initial budget but saved 3 weeks in the schedule.",
        "LESSON LEARNED: Always conduct secondary soil samples in the North Wichita industrial zone before mobilizing heavy equipment."
    ]
)

# --- PDF 2: The Maintenance Log ---
create_hutton_pdf(
    "Facility_Log_Aerospace_HQ.pdf",
    "Facility Maintenance Audit: Global Aerospace HQ",
    [
        "Building Age: 5 Years | Status: Active",
        "HVAC SYSTEM: The primary chillers use R-410A refrigerant. Filters are replaced every 90 days.",
        "ROOFING: Flat TPO roof. Inspected July 2025. Found minor seam separation near the HVAC platform.",
        "RECOMMENDATION: Apply silicone sealant to seam 'Zone B' to prevent winter moisture ingress."
    ]
)

# --- PDF 3: The Risk/Safety Incident ---
create_hutton_pdf(
    "Safety_Report_Downtown_Lofts.pdf",
    "Incident Report: Downtown Loft Renovation",
    [
        "INCIDENT TYPE: Material Delay / Supply Chain",
        "DETAIL: Custom glass panels for the atrium were delayed by 6 weeks due to international shipping strikes.",
        "IMPACT: Interior finishing was halted, pushing the 'Design+Build' completion date into Q1 2026.",
        "RISK MITIGATION: For future projects, source glass from local fabricators in Kansas City even if the unit cost is 10% higher."
    ]
)

print("PDFs created successfully in the /test_data folder!")
