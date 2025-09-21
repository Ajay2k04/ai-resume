from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from models import ExportRequest
from docx import Document
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black
import io
import os

router = APIRouter()

def create_download_file(content: str, filename: str, file_type: str) -> bytes:
    """Create downloadable file content"""
    if file_type == "docx":
        # Create a well-formatted DOCX file
        doc = Document()
        
        # Set default font
        from docx.shared import Inches, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.shared import OxmlElement, qn
        
        # Process content with better formatting
        lines = content.split('\n')
        i = 0
        in_skills_section = False
        
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            
            # Check if it's a name (first non-empty line, all caps)
            if i == 0 or (line.isupper() and len(line) > 3 and not any(char in line for char in ['|', '@', '.', ':', '•'])):
                name_para = doc.add_paragraph()
                name_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                name_run = name_para.add_run(line)
                name_run.font.size = Pt(14)
                name_run.font.bold = True
                name_run.font.name = 'Arial'
                doc.add_paragraph()  # Add space after name
            
            # Check if it's contact info
            elif ('@' in line or 'linkedin.com' in line.lower() or 
                  (any(char.isdigit() for char in line) and len(line) > 10) or
                  'github.com' in line.lower()):
                contact_para = doc.add_paragraph()
                contact_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                contact_run = contact_para.add_run(line)
                contact_run.font.size = Pt(10)
                contact_run.font.name = 'Arial'
                doc.add_paragraph()  # Add space after contact
            
            # Check if it's a section header
            elif (line.isupper() and len(line) > 3 and 
                  any(section in line for section in [
                      'PROFESSIONAL SUMMARY', 'WORK EXPERIENCE', 'EDUCATION', 
                      'SKILLS', 'PROJECTS', 'CERTIFICATIONS', 'EXTRACURRICULAR ACTIVITIES',
                      'AWARDS & ACHIEVEMENTS', 'VOLUNTEER', 'LANGUAGES', 'INTERESTS',
                      'TECHNICAL SKILLS', 'PROFESSIONAL EXPERIENCE'
                  ])):
                in_skills_section = 'SKILLS' in line
                doc.add_paragraph()  # Add space before section
                section_para = doc.add_paragraph()
                section_run = section_para.add_run(line)
                section_run.font.size = Pt(10)
                section_run.font.bold = True
                section_run.font.name = 'Arial'
                doc.add_paragraph()  # Add space after section header
            
            # Check if it's a job title/company line
            elif '|' in line and len(line.split('|')) >= 2:
                job_para = doc.add_paragraph()
                job_run = job_para.add_run(line)
                job_run.font.size = Pt(10)
                job_run.font.bold = True
                job_run.font.name = 'Arial'
            
            # Check if it's a bullet point
            elif line.startswith('•') or line.startswith('-'):
                bullet_para = doc.add_paragraph()
                bullet_para.style = 'List Bullet'
                bullet_run = bullet_para.add_run(line[1:].strip())  # Remove bullet character
                bullet_run.font.size = Pt(9)
                bullet_run.font.name = 'Arial'
            
            # Check if it's in skills section
            elif in_skills_section and ':' in line:
                skills_para = doc.add_paragraph()
                skills_run = skills_para.add_run(line)
                skills_run.font.size = Pt(9)
                skills_run.font.name = 'Arial'
            
            # Regular text
            else:
                para = doc.add_paragraph()
                run = para.add_run(line)
                run.font.size = Pt(9)
                run.font.name = 'Arial'
            
            i += 1
        
        # Save to bytes
        doc_io = io.BytesIO()
        doc.save(doc_io)
        doc_io.seek(0)
        return doc_io.getvalue()
    elif file_type == "pdf":
        try:
            # Create PDF in memory with better margins
            pdf_io = io.BytesIO()
            doc = SimpleDocTemplate(
                pdf_io, 
                pagesize=letter,
                leftMargin=0.5*inch, 
                rightMargin=0.5*inch,
                topMargin=0.5*inch, 
                bottomMargin=0.5*inch
            )
            
            # Create custom styles with better formatting
            styles = getSampleStyleSheet()
            
            # Name style - smaller, bold, left aligned
            name_style = ParagraphStyle(
                'NameStyle',
                parent=styles['Heading1'],
                fontSize=14,
                spaceAfter=10,
                spaceBefore=0,
                alignment=0,  # Left align
                textColor=black,
                fontName='Helvetica-Bold',
                leading=16
            )
            
            # Contact style - smaller, left aligned
            contact_style = ParagraphStyle(
                'ContactStyle',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=20,
                spaceBefore=0,
                alignment=0,  # Left align
                fontName='Helvetica',
                leading=13
            )
            
            # Section header style - smaller, bold, left aligned, perfect spacing
            section_style = ParagraphStyle(
                'SectionStyle',
                parent=styles['Heading2'],
                fontSize=10,
                spaceAfter=8,
                spaceBefore=14,
                textColor=black,
                fontName='Helvetica-Bold',
                alignment=0,  # Left align
                leftIndent=0,
                rightIndent=0,
                leading=12
            )
            
            # Job title/company style - bold, perfect spacing
            job_title_style = ParagraphStyle(
                'JobTitleStyle',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=6,
                spaceBefore=0,
                fontName='Helvetica-Bold',
                leftIndent=0,
                rightIndent=0,
                alignment=0,
                leading=13
            )
            
            # Normal text style - smaller, perfect spacing
            normal_style = ParagraphStyle(
                'NormalStyle',
                parent=styles['Normal'],
                fontSize=9,
                spaceAfter=3,
                spaceBefore=0,
                fontName='Helvetica',
                leftIndent=0,
                rightIndent=0,
                alignment=0,
                leading=11
            )
            
            # Bullet point style with perfect indentation and spacing
            bullet_style = ParagraphStyle(
                'BulletStyle',
                parent=styles['Normal'],
                fontSize=9,
                spaceAfter=2,
                spaceBefore=0,
                fontName='Helvetica',
                leftIndent=20,
                rightIndent=0,
                alignment=0,
                leading=11
            )
            
            # Skills style - no bullets, perfect spacing
            skills_style = ParagraphStyle(
                'SkillsStyle',
                parent=styles['Normal'],
                fontSize=9,
                spaceAfter=3,
                spaceBefore=0,
                fontName='Helvetica',
                leftIndent=0,
                rightIndent=0,
                alignment=0,
                leading=11
            )
            
            # Date style for cover letters - left aligned
            date_style = ParagraphStyle(
                'DateStyle',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=15,
                spaceBefore=0,
                alignment=0,  # Left align
                fontName='Helvetica',
                textColor=black,
                leading=12
            )
            
            # Build content with improved formatting
            story = []
            lines = content.split('\n')
            i = 0
            in_skills_section = False
            
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue
                
                # Check if it's a name (first non-empty line, all caps, no special chars)
                if i == 0 or (line.isupper() and len(line) > 3 and not any(char in line for char in ['|', '@', '.', ':', '•'])):
                    story.append(Paragraph(line, name_style))
                    story.append(Spacer(1, 4))
                
                # Check if it's contact info (contains email, phone, or LinkedIn)
                elif ('@' in line or 'linkedin.com' in line.lower() or 
                      (any(char.isdigit() for char in line) and len(line) > 10) or
                      'github.com' in line.lower()):
                    story.append(Paragraph(line, contact_style))
                    story.append(Spacer(1, 8))
                
                # Check if it's a section header
                elif (line.isupper() and len(line) > 3 and 
                      any(section in line for section in [
                          'PROFESSIONAL SUMMARY', 'WORK EXPERIENCE', 'EDUCATION', 
                          'SKILLS', 'PROJECTS', 'CERTIFICATIONS', 'EXTRACURRICULAR ACTIVITIES',
                          'AWARDS & ACHIEVEMENTS', 'VOLUNTEER', 'LANGUAGES', 'INTERESTS',
                          'TECHNICAL SKILLS', 'PROFESSIONAL EXPERIENCE'
                      ])):
                    in_skills_section = 'SKILLS' in line
                    story.append(Paragraph(line, section_style))
                    story.append(Spacer(1, 6))
                
                # Check if it's a date (for cover letters)
                elif (len(line.split()) <= 3 and 
                      any(month in line for month in ['January', 'February', 'March', 'April', 'May', 'June',
                                                      'July', 'August', 'September', 'October', 'November', 'December'])):
                    story.append(Paragraph(line, date_style))
                
                # Check if it's a job title/company line (contains |)
                elif '|' in line and len(line.split('|')) >= 2:
                    story.append(Paragraph(line, job_title_style))
                    story.append(Spacer(1, 2))
                
                # Check if it's a bullet point
                elif line.startswith('•') or line.startswith('-'):
                    story.append(Paragraph(line, bullet_style))
                
                # Check if it's in skills section (format differently)
                elif in_skills_section and ':' in line:
                    story.append(Paragraph(line, skills_style))
                
                # Regular text
                else:
                    story.append(Paragraph(line, normal_style))
                
                i += 1
            
            # Build PDF
            doc.build(story)
            pdf_io.seek(0)
            return pdf_io.getvalue()
            
        except ImportError:
            raise HTTPException(status_code=500, detail="PDF generation requires reportlab. Please install it: pip install reportlab")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating PDF: {str(e)}")
    
    return b""

@router.post("/export")
async def export_document(request: ExportRequest):
    """Export document in specified format"""
    
    try:
        # Validate file format
        if request.format not in ["docx", "pdf"]:
            raise HTTPException(status_code=400, detail="Unsupported file format. Supported formats: docx, pdf")
        
        # Create file content
        file_content = create_download_file(request.content, request.filename, request.format)
        
        if not file_content:
            raise HTTPException(status_code=500, detail="Failed to create file content")
        
        # Determine MIME type
        mime_types = {
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "pdf": "application/pdf"
        }
        
        mime_type = mime_types.get(request.format, "application/octet-stream")
        
        # Create streaming response
        def iter_content():
            yield file_content
        
        return StreamingResponse(
            iter_content(),
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={request.filename}.{request.format}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting document: {str(e)}")

@router.get("/formats")
async def get_supported_formats():
    """Get list of supported export formats"""
    return {
        "supported_formats": [
            {
                "format": "docx",
                "description": "Microsoft Word document",
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            },
            {
                "format": "pdf",
                "description": "Portable Document Format",
                "mime_type": "application/pdf"
            }
        ]
    }
