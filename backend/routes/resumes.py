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
    
    # Extract phone
    phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
    phones = re.findall(phone_pattern, text)
    if phones:
        resume_data['contact_info']['phone'] = ''.join(phones[0])
    
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
    
    # Extract experience with duration parsing
    experience_patterns = [
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*-\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*@\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*,\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\|([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    ]
    
    # Look for duration patterns
    duration_patterns = [
        r'(\d+)\s*(?:years?|yrs?)\s*(?:\d+\s*months?)?',
        r'(\d+)\s*months?',
        r'(\d+)\s*-\s*(\d+)\s*years?',
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}\s*-\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}',
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}\s*-\s*Present'
    ]
    
    for pattern in experience_patterns:
        experiences = re.findall(pattern, text)
        for exp in experiences[:3]:  # Limit to 3 experiences
            if len(exp[0]) > 3 and len(exp[1]) > 2:  # Filter out short matches
                # Clean up the extracted data
                title = exp[0].strip()
                company = exp[1].strip()
                
                # Skip if it looks like location or other non-company data
                if not any(word in company.lower() for word in ['bangalore', 'mumbai', 'delhi', 'hyderabad', 'chennai', 'pune', 'kolkata', 'salem', 'tamil']):
                    # Try to find duration in the text around this experience
                    duration = 'Duration not specified'
                    for dur_pattern in duration_patterns:
                        duration_match = re.search(dur_pattern, text, re.IGNORECASE)
                        if duration_match:
                            duration = duration_match.group(0)
                            break
                    
                    resume_data['experience'].append({
                        'title': title,
                        'company': company,
                        'duration': duration,
                        'description': f'Contributed to software development projects using modern technologies and best practices.'
                    })
    
    # If no experience found, try to extract from project descriptions
    if not resume_data['experience']:
        project_lines = [line for line in lines if any(keyword in line.lower() for keyword in ['developed', 'built', 'created', 'implemented'])]
        if project_lines:
            resume_data['experience'].append({
                'title': 'Software Developer',
                'company': 'Various Projects',
                'duration': 'Project-based experience',
                'description': 'Developed multiple software applications and projects using various technologies.'
            })
    
    # Extract education with better patterns
    education_patterns = [
        r'(Bachelor|Master|PhD|B\.S\.|M\.S\.|Ph\.D\.|B\.A\.|M\.A\.)\s+[A-Za-z\s]+',
        r'[A-Za-z]+\s+University',
        r'[A-Za-z]+\s+College',
        r'[A-Za-z]+\s+Institute'
    ]
    
    for pattern in education_patterns:
        educations = re.findall(pattern, text)
        for edu in educations[:2]:  # Limit to 2 education entries
            resume_data['education'].append(edu)
    
    # Extract projects with better formatting
    project_keywords = ['project', 'developed', 'built', 'created', 'implemented', 'designed']
    lines = text.split('\n')
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
    
    return resume_data

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and parse a resume file (PDF or DOCX)"""
    
    # Validate file type
    if not file.content_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Parse based on file type
        if file.content_type == "application/pdf":
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
        else:  # DOCX
            doc = Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        
        # Parse the text
        resume_data = parse_resume_text(text)
        
        # Save to database
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
        
        # Check if candidate already exists
        existing_candidate = db.query(Candidate).filter(Candidate.email == candidate_data.email).first()
        if existing_candidate:
            # Update existing candidate
            for field, value in candidate_data.dict().items():
                setattr(existing_candidate, field, value)
            db.commit()
            db.refresh(existing_candidate)
            candidate = existing_candidate
        else:
            # Create new candidate
            candidate = Candidate(**candidate_data.dict())
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
        
        return {
            "candidate_id": candidate.id,
            "resume_data": resume_data,
            "message": "Resume parsed and saved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing resume: {str(e)}")

@router.get("/candidate/{candidate_id}")
async def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Get candidate by ID"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return CandidateResponse.from_orm(candidate)
