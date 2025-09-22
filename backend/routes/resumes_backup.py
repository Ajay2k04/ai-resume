from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db, Candidate
from models import ResumeData, CandidateCreate, CandidateResponse
import pdfplumber
from docx import Document
import io
import re
from typing import Dict, List
import json

router = APIRouter()

def parse_resume_text(text: str) -> Dict:
    """Parse resume text and extract structured information"""
    try:
        resume_data = {
            'name': '',
            'contact_info': {
                'email': '',
                'phone': '',
                'linkedin': '',
                'website': ''
            },
            'skills': [],
            'experience': [],
            'education': [],
            'summary': '',
            'projects': []
        }
        
        if not text or len(text.strip()) < 10:
            print("⚠️ Warning: Very short or empty text provided")
            return resume_data
        
        # Extract name (usually first line or after "Name:")
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and not any(keyword in line.lower() for keyword in ['email', 'phone', 'linkedin', 'github', 'portfolio']):
                resume_data['name'] = line
                break
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            resume_data['contact_info']['email'] = emails[0]
        
        # Extract phone - improved pattern to avoid duplicates
        phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        phones = re.findall(phone_pattern, text)
        if phones:
            # Take only the first phone number found and format it properly
            phone_parts = phones[0]
            # Remove empty parts and join with dashes
            phone_digits = ''.join([part for part in phone_parts if part])
            # Format as (XXX) XXX-XXXX or XXX-XXX-XXXX
            if len(phone_digits) == 10:
                resume_data['contact_info']['phone'] = f"({phone_digits[:3]}) {phone_digits[3:6]}-{phone_digits[6:]}"
            elif len(phone_digits) == 11 and phone_digits[0] == '1':
                resume_data['contact_info']['phone'] = f"({phone_digits[1:4]}) {phone_digits[4:7]}-{phone_digits[7:]}"
            else:
                resume_data['contact_info']['phone'] = phone_digits
        
        # Extract LinkedIn
        linkedin_pattern = r'linkedin\.com/in/[\w-]+'
        linkedin_matches = re.findall(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_matches:
            resume_data['contact_info']['linkedin'] = f"https://{linkedin_matches[0]}"
        
        # Extract website/portfolio
        website_pattern = r'(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?'
        websites = re.findall(website_pattern, text)
        for website in websites:
            if 'linkedin' not in website.lower() and 'github' not in website.lower():
                resume_data['contact_info']['website'] = website
                break
        
        # Enhanced skills extraction
        skill_keywords = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue', 'node.js', 'sql',
            'machine learning', 'ai', 'artificial intelligence', 'data science', 'analytics', 'aws', 'azure', 'gcp',
            'docker', 'kubernetes', 'git', 'agile', 'scrum', 'project management', 'html', 'css', 'bootstrap',
            'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch', 'tensorflow', 'pytorch', 'pandas',
            'numpy', 'scikit-learn', 'flask', 'django', 'fastapi', 'spring', 'express', 'rest api', 'graphql',
            'microservices', 'ci/cd', 'jenkins', 'terraform', 'ansible', 'linux', 'unix', 'bash', 'powershell'
        ]
        
        text_lower = text.lower()
        for skill in skill_keywords:
            if skill in text_lower:
                resume_data['skills'].append(skill.title())
        
        # Look for duration patterns
        duration_patterns = [
            r'(\d+)\s*(?:years?|yrs?)\s*(?:\d+\s*months?)?',
            r'(\d+)\s*months?',
            r'(\d+)\s*-\s*(\d+)\s*years?',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}\s*-\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}',
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}\s*-\s*Present'
        ]
        
        # Look for work experience section first (try both "WORK EXPERIENCE" and "Experience")
        work_exp_section = re.search(r'(?:WORK\s+)?EXPERIENCE[:\s]*\n(.*?)(?=\n(?:PROJECTS|EDUCATION|SKILLS|CERTIFICATIONS|AWARDS|VOLUNTEER|LANGUAGES|INTERESTS|TECHNOLOGIES|SOFT SKILLS|TECHNICAL SKILLS)\n|$)', text, re.IGNORECASE | re.DOTALL)
        if work_exp_section:
            work_exp_text = work_exp_section.group(1)
            print(f"🔍 Found experience section: {work_exp_text[:200]}...")
            # Split into lines and process each experience entry
            lines = work_exp_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('•'):
                    continue
                    
                # Check if this line looks like a job title | company format or job title, company format
                if '|' in line or (',' in line and not line.startswith('•')):
                    # This looks like a job title | company line or job title, company line
                    if '|' in line:
                        parts = line.split('|')
                    else:
                        # Handle comma-separated format like "Associate Front-end Developer, Digtai -Bangalore Dec 2024 – Feb 2025"
                        parts = line.split(',')
                    
                    if len(parts) >= 2:
                        title = parts[0].strip()
                        company = parts[1].strip()
                        
                        # More lenient filtering - include more job titles and be less restrictive
                        if (len(title) > 3 and len(company) > 2 and 
                            not any(word in title.lower() for word in ['education', 'skills', 'certifications', 'interests', 'professional summary', 'bachelor', 'master', 'phd', 'degree', 'university', 'college', 'be', 'b.tech', 'm.tech']) and
                            # Only exclude if company looks like an educational institution
                            not any(word in company.lower() for word in ['university', 'college', 'institute', 'school', 'academy']) and
                            not title.lower().startswith('work experience') and
                            # Include more job-related keywords
                            any(word in title.lower() for word in ['developer', 'engineer', 'manager', 'analyst', 'designer', 'consultant', 'specialist', 'coordinator', 'assistant', 'director', 'lead', 'senior', 'junior', 'intern', 'internship', 'trainee', 'associate', 'executive', 'officer', 'representative', 'technician', 'programmer', 'architect', 'administrator', 'supervisor', 'coordinator', 'training', 'front-end', 'backend', 'full-stack', 'software', 'web', 'mobile', 'data', 'cloud', 'devops', 'qa', 'test', 'support', 'sales', 'marketing', 'hr', 'finance', 'operations'])):
                            
                            # Try to find duration in the same line
                            duration = None
                            if len(parts) >= 3:
                                duration = parts[2].strip()
                            
                            # Look for duration patterns in the line
                            if not duration:
                                for dur_pattern in duration_patterns:
                                    duration_match = re.search(dur_pattern, line, re.IGNORECASE)
                                    if duration_match:
                                        duration = duration_match.group(0)
                                        break
                            
                            # Try to find description from the next lines
                            description = 'Contributed to software development projects using modern technologies and best practices.'
                            
                            # Look for bullet points or description in the next few lines
                            current_line_index = lines.index(line)
                            for i in range(current_line_index + 1, min(current_line_index + 5, len(lines))):
                                next_line = lines[i].strip()
                                if next_line.startswith('•'):
                                    # Found bullet point description
                                    description = next_line[1:].strip()  # Remove the bullet point
                                    break
                                elif next_line and not next_line.startswith('•') and '|' not in next_line:
                                    # Found a description line
                                    description = next_line
                                    break
                            
                            # Create experience entry
                            experience_entry = {
                                'title': title,
                                'company': company,
                                'description': description
                            }
                            
                            if duration:
                                experience_entry['duration'] = duration
                            
                            resume_data['experience'].append(experience_entry)
                            print(f"✅ Added experience: {title} at {company}")
        
        # If no experience found, don't add generic experience - leave it empty
        if not resume_data['experience']:
            print("ℹ️ No work experience found in resume - leaving experience section empty")
        
        # No fallback experience - only use real work experience from resume
        
        # Extract education with comprehensive patterns
        education_patterns = [
            # Degree patterns
            r'(Bachelor|Master|PhD|B\.S\.|M\.S\.|Ph\.D\.|B\.A\.|M\.A\.|B\.Tech|M\.Tech|B\.E\.|M\.E\.|B\.Com|M\.Com|B\.Sc|M\.Sc)\s+[A-Za-z\s]+',
            # University/College patterns
            r'[A-Za-z\s]+(?:University|College|Institute|School)\s*[A-Za-z\s]*',
            # Degree with year patterns
            r'(Bachelor|Master|PhD|B\.S\.|M\.S\.|Ph\.D\.|B\.A\.|M\.A\.)\s+[A-Za-z\s]+\s*[A-Za-z\s]+\s*(?:University|College|Institute)\s*[A-Za-z\s]*\s*(?:20\d{2}|19\d{2})',
            # Simple degree patterns
            r'(?:Bachelor|Master|PhD|B\.S\.|M\.S\.|Ph\.D\.|B\.A\.|M\.A\.)\s+[A-Za-z\s]+(?:in|of)\s+[A-Za-z\s]+'
        ]
        
        # Also look for education section specifically
        education_section_pattern = r'EDUCATION[:\s]*(.*?)(?=SKILLS|EXPERIENCE|PROJECTS|CERTIFICATIONS|$)'
        education_section = re.search(education_section_pattern, text, re.IGNORECASE | re.DOTALL)
        
        if education_section:
            education_text = education_section.group(1)
            print(f"🔍 Found education section: {education_text[:200]}...")
            # Extract individual education entries from the section
            education_lines = education_text.split('\n')
            for line in education_lines:
                line = line.strip()
                if line and len(line) > 10:  # Only add substantial lines
                    resume_data['education'].append(line)
                    print(f"✅ Added education: {line}")
        
        # Fallback to pattern matching if no education section found
        if not resume_data['education']:
            for pattern in education_patterns:
                educations = re.findall(pattern, text, re.IGNORECASE)
                for edu in educations[:3]:  # Limit to 3 education entries
                    if len(edu.strip()) > 10:  # Only add substantial entries
                        resume_data['education'].append(edu.strip())
        
        # Extract projects with better formatting
        project_keywords = ['project', 'developed', 'built', 'created', 'implemented', 'designed']
        lines = text.split('\n')
        
        # Look for projects section first
        projects_section = re.search(r'PROJECTS[:\s]*(.*?)(?=EDUCATION|SKILLS|CERTIFICATIONS|INTERESTS|$)', text, re.IGNORECASE | re.DOTALL)
        if projects_section:
            projects_text = projects_section.group(1)
            project_lines = projects_text.split('\n')
            current_project = ""
            for line in project_lines:
                line = line.strip()
                if line and not line.startswith('•') and len(line) > 3:
                    # This looks like a project name
                    if current_project:
                        resume_data['projects'].append(current_project)
                    current_project = line
                elif line.startswith('•') and current_project:
                    # This is a project description
                    current_project += f" - {line[1:].strip()}"
            
            # Add the last project
            if current_project:
                resume_data['projects'].append(current_project)
        
        # Fallback to general text search if no projects section found
        if not resume_data['projects']:
            for i, line in enumerate(lines):
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in project_keywords):
                    if len(line.strip()) > 20:  # Filter out short lines
                        # Clean up the project description
                        clean_line = line.strip()
                        # Add proper spacing between words
                        clean_line = re.sub(r'([a-z])([A-Z])', r'\1 \2', clean_line)
                        clean_line = re.sub(r'([a-z])(\d)', r'\1 \2', clean_line)
                        clean_line = re.sub(r'(\d)([A-Z])', r'\1 \2', clean_line)
                        resume_data['projects'].append(clean_line)
        
        # Extract additional sections
        resume_data['certifications'] = []
        resume_data['extracurricular'] = []
        resume_data['awards'] = []
        resume_data['volunteer'] = []
        resume_data['languages'] = []
        resume_data['interests'] = []
        
        # Extract certifications
        cert_patterns = [
            r'([A-Z][^.]*certification[^.]*)',
            r'([A-Z][^.]*certificate[^.]*)',
            r'([A-Z][^.]*license[^.]*)',
            r'([A-Z][^.]*credential[^.]*)'
        ]
        
        for pattern in cert_patterns:
            certs = re.findall(pattern, text, re.IGNORECASE)
            for cert in certs:
                if len(cert.strip()) > 10:  # Filter out very short matches
                    resume_data['certifications'].append(cert.strip())
        
        # Extract extracurricular activities
        activity_patterns = [
            r'([A-Z][^.]*club[^.]*)',
            r'([A-Z][^.]*society[^.]*)',
            r'([A-Z][^.]*organization[^.]*)',
            r'([A-Z][^.]*association[^.]*)',
            r'([A-Z][^.]*team[^.]*)'
        ]
        
        for pattern in activity_patterns:
            activities = re.findall(pattern, text, re.IGNORECASE)
            for activity in activities:
                if len(activity.strip()) > 10:
                    resume_data['extracurricular'].append(activity.strip())
        
        # Extract awards
        award_patterns = [
            r'([A-Z][^.]*award[^.]*)',
            r'([A-Z][^.]*recognition[^.]*)',
            r'([A-Z][^.]*honor[^.]*)',
            r'([A-Z][^.]*achievement[^.]*)'
        ]
        
        for pattern in award_patterns:
            awards = re.findall(pattern, text, re.IGNORECASE)
            for award in awards:
                if len(award.strip()) > 10:
                    resume_data['awards'].append(award.strip())
        
        # Extract volunteer work
        volunteer_patterns = [
            r'([A-Z][^.]*volunteer[^.]*)',
            r'([A-Z][^.]*community service[^.]*)',
            r'([A-Z][^.]*non-profit[^.]*)'
        ]
        
        for pattern in volunteer_patterns:
            volunteer = re.findall(pattern, text, re.IGNORECASE)
            for vol in volunteer:
                if len(vol.strip()) > 10:
                    resume_data['volunteer'].append(vol.strip())
        
        # Extract languages
        language_patterns = [
            r'([A-Z][a-z]+)\s*:\s*(native|fluent|intermediate|beginner|advanced)',
            r'([A-Z][a-z]+)\s*-\s*(native|fluent|intermediate|beginner|advanced)',
            r'([A-Z][a-z]+)\s*\(([^)]+)\)'
        ]
        
        for pattern in language_patterns:
            languages = re.findall(pattern, text, re.IGNORECASE)
            for lang in languages:
                if len(lang[0].strip()) > 2:
                    resume_data['languages'].append(f"{lang[0].strip()}: {lang[1].strip()}")
        
        # Extract interests
        interest_keywords = [
            'photography', 'music', 'sports', 'reading', 'travel', 'cooking', 'gaming',
            'hiking', 'swimming', 'running', 'cycling', 'art', 'design', 'writing',
            'volunteering', 'mentoring', 'teaching', 'learning', 'research'
        ]
        
        for interest in interest_keywords:
            if interest in text_lower:
                resume_data['interests'].append(interest.title())
        
        # Create a basic summary
        if resume_data['skills']:
            skills_text = ', '.join(resume_data['skills'][:5])
            resume_data['summary'] = f"Experienced professional with expertise in {skills_text}. Passionate about technology and innovation with a strong foundation in software development and problem-solving."
        
        print(f"✅ Successfully parsed resume data")
        return resume_data
        
    except Exception as e:
        print(f"❌ Error in parse_resume_text: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return minimal valid data structure
        return {
            'name': 'Candidate',
            'contact_info': {
                'email': 'candidate@email.com',
                'phone': '',
                'linkedin': '',
                'website': ''
            },
            'skills': ['General Skills'],
            'experience': [],
            'education': [],
            'summary': 'Professional with diverse experience and skills.',
            'projects': []
        }

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and parse a resume file (PDF or DOCX)"""
    
    # Validate file type
    if not file.content_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
    
    try:
        print(f"📄 Processing file: {file.filename}, type: {file.content_type}")
        
        # Read file content
        file_content = await file.read()
        print(f"📄 File size: {len(file_content)} bytes")
        
        # Parse based on file type
        if file.content_type == "application/pdf":
            print("📄 Parsing PDF file...")
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                text = ""
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    text += page_text
                    print(f"📄 Page {page_num + 1}: {len(page_text)} characters")
        else:  # DOCX
            print("📄 Parsing DOCX file...")
            doc = Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        
        print(f"📄 Total extracted text: {len(text)} characters")
        print(f"📄 First 200 characters: {text[:200]}")
        
        if not text or len(text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Unable to extract text from the file. Please ensure the file contains readable text.")
        
        # Parse the text
        print("📄 Parsing resume data...")
        resume_data = parse_resume_text(text)
        print(f"📄 Parsed data keys: {list(resume_data.keys())}")
        print(f"📄 Name: {resume_data.get('name', 'Not found')}")
        print(f"📄 Email: {resume_data.get('contact_info', {}).get('email', 'Not found')}")
        print(f"📄 Skills count: {len(resume_data.get('skills', []))}")
        print(f"📄 Experience count: {len(resume_data.get('experience', []))}")
        
        # Save to database
        print("📄 Saving to database...")
        candidate_data = CandidateCreate(
            name=resume_data['name'],
            email=resume_data['contact_info']['email'],
            phone=resume_data['contact_info']['phone'],
            linkedin=resume_data['contact_info']['linkedin'],
            website=resume_data['contact_info']['website'],
            skills=resume_data['skills'],
            experience=resume_data['experience'],
            education=resume_data['education'],
            summary=resume_data['summary'],
            projects=resume_data['projects']
        )
        
        print(f"📄 Candidate data: name={candidate_data.name}, email={candidate_data.email}")
        
        # Check if candidate already exists
        existing_candidate = db.query(Candidate).filter(Candidate.email == candidate_data.email).first()
        if existing_candidate:
            print("📄 Updating existing candidate...")
            # Update existing candidate
            for field, value in candidate_data.model_dump().items():
                setattr(existing_candidate, field, value)
            db.commit()
            db.refresh(existing_candidate)
            candidate = existing_candidate
        else:
            print("📄 Creating new candidate...")
            # Create new candidate
            candidate = Candidate(**candidate_data.model_dump())
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
        
        print(f"📄 Successfully saved candidate with ID: {candidate.id}")
        
        return {
            "candidate_id": candidate.id,
            "resume_data": resume_data,
            "message": "Resume parsed and saved successfully"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"❌ Error parsing resume: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error parsing resume: {str(e)}")

@router.get("/candidate/{candidate_id}")
async def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Get candidate by ID"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return CandidateResponse.from_orm(candidate)
