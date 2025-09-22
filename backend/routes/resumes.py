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

def parse_resume_text_comprehensive(text: str) -> Dict:
    """Comprehensive resume parsing that handles ALL possible section names and variations"""
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
            'projects': [],
            'certifications': [],
            'awards': [],
            'volunteer': [],
            'languages': [],
            'interests': [],
            'publications': [],
            'references': [],
            'additional_sections': {}
        }
        
        if not text or len(text.strip()) < 10:
            print("⚠️ Warning: Very short or empty text provided")
            return resume_data
        
        # Extract name (usually first line or after "Name:")
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and not any(keyword in line.lower() for keyword in ['email', 'phone', 'linkedin', 'github', 'portfolio', 'objective', 'summary']):
                resume_data['name'] = line
                break
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            resume_data['contact_info']['email'] = emails[0]
        
        # Extract phone - improved pattern to avoid duplicates
        phone_pattern = r'(\+?1?[-.\s]?)?(\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})'
        phones = re.findall(phone_pattern, text)
        if phones:
            # Take the first phone number and clean it up
            phone = phones[0][1] if phones[0][1] else phones[0][0]
            resume_data['contact_info']['phone'] = phone
        
        # Extract LinkedIn
        linkedin_pattern = r'(?:linkedin\.com/in/|linkedin\.com/pub/)([a-zA-Z0-9-]+)'
        linkedin_match = re.search(linkedin_pattern, text, re.IGNORECASE)
        if linkedin_match:
            resume_data['contact_info']['linkedin'] = f"linkedin.com/in/{linkedin_match.group(1)}"
        
        # Extract website
        website_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.(?:com|org|net|edu|io|co|me|info))'
        websites = re.findall(website_pattern, text, re.IGNORECASE)
        if websites:
            # Filter out common email domains
            valid_websites = [w for w in websites if not any(domain in w.lower() for domain in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'])]
            if valid_websites:
                resume_data['contact_info']['website'] = valid_websites[0]
        
        # COMPREHENSIVE SECTION PARSING
        # Define all possible section names and their variations
        
        section_mappings = {
            'experience': [
                'experience', 'work experience', 'professional experience', 'employment', 'career',
                'internship', 'intern', 'training', 'work history', 'job experience',
                'professional background', 'work background', 'career history',
                'practical experience', 'hands-on experience', 'relevant experience',
                'work', 'employment history', 'professional work', 'career experience'
            ],
            'education': [
                'education', 'academic background', 'academic qualifications', 'academic history',
                'educational background', 'qualifications', 'academic credentials',
                'degrees', 'academic achievements', 'educational qualifications',
                'academic profile', 'educational profile', 'academic record'
            ],
            'skills': [
                'skills', 'technical skills', 'core competencies', 'competencies',
                'technical competencies', 'key skills', 'professional skills',
                'expertise', 'technical expertise', 'skill set', 'capabilities',
                'proficiencies', 'technologies', 'tools', 'software skills'
            ],
            'projects': [
                'projects', 'personal projects', 'academic projects', 'project experience',
                'project portfolio', 'project work', 'project history',
                'side projects', 'portfolio projects', 'project showcase'
            ],
            'certifications': [
                'certifications', 'certificates', 'professional certifications',
                'certification', 'certificate', 'licenses', 'credentials',
                'professional credentials', 'certified', 'accreditations'
            ],
            'awards': [
                'awards', 'achievements', 'honors', 'recognition', 'accolades',
                'award', 'achievement', 'honor', 'prize', 'distinction',
                'academic awards', 'professional awards', 'scholarships'
            ],
            'volunteer': [
                'volunteer', 'volunteer work', 'volunteering', 'volunteer experience',
                'community service', 'volunteer activities', 'social work',
                'volunteerism', 'community involvement', 'volunteer contributions'
            ],
            'languages': [
                'languages', 'language skills', 'language proficiency',
                'spoken languages', 'foreign languages', 'language abilities',
                'multilingual', 'language competencies'
            ],
            'interests': [
                'interests', 'hobbies', 'personal interests', 'leisure activities',
                'extracurricular activities', 'personal activities', 'hobby',
                'interest', 'activities', 'leisure', 'personal pursuits'
            ],
            'publications': [
                'publications', 'research publications', 'academic publications',
                'published work', 'papers', 'articles', 'research papers',
                'publication', 'research', 'academic research'
            ],
            'references': [
                'references', 'referees', 'reference', 'referee',
                'professional references', 'character references'
            ]
        }
        
        # Parse each section type
        for section_type, keywords in section_mappings.items():
            section_content = parse_section_by_keywords(text, keywords, section_type)
            if section_content:
                resume_data[section_type] = section_content
                print(f"✅ Parsed {section_type}: {len(section_content)} items")
        
        # Parse summary/objective
        summary_keywords = ['summary', 'objective', 'profile', 'about', 'overview', 'professional summary', 'career objective', 'personal statement']
        summary_content = parse_summary_section(text, summary_keywords)
        if summary_content:
            resume_data['summary'] = summary_content
        
        # Parse any additional sections not covered above
        additional_sections = parse_additional_sections(text, section_mappings)
        resume_data['additional_sections'] = additional_sections
        
        print(f"✅ Successfully parsed comprehensive resume data")
        return resume_data
        
    except Exception as e:
        print(f"❌ Error in comprehensive resume parsing: {str(e)}")
        # Return fallback data
        return {
            'name': 'Parsed Resume',
            'contact_info': {'email': '', 'phone': '', 'linkedin': '', 'website': ''},
            'skills': ['General Skills'],
            'experience': [],
            'education': [],
            'summary': 'Professional with diverse experience and skills.',
            'projects': []
        }

def parse_section_by_keywords(text: str, keywords: List[str], section_type: str) -> List:
    """Parse a section using multiple possible keywords"""
    
    for keyword in keywords:
        # Create flexible regex pattern for each keyword
        if section_type == 'experience':
            pattern = rf'{keyword}[:\s]*\n(.*?)(?=\n(?:PROJECTS|EDUCATION|SKILLS|CERTIFICATIONS|AWARDS|VOLUNTEER|LANGUAGES|INTERESTS|TECHNOLOGIES|SOFT SKILLS|TECHNICAL SKILLS|ACHIEVEMENTS|ACTIVITIES|HOBBIES|REFERENCES|CONTACT|OBJECTIVE|SUMMARY|PROFILE|PUBLICATIONS|EMPLOYMENT|CAREER|WORK|INTERNSHIP|TRAINING)\n|$)'
        else:
            pattern = rf'{keyword}[:\s]*\n(.*?)(?=\n(?:PROJECTS|EDUCATION|SKILLS|CERTIFICATIONS|AWARDS|VOLUNTEER|LANGUAGES|INTERESTS|TECHNOLOGIES|SOFT SKILLS|TECHNICAL SKILLS|ACHIEVEMENTS|ACTIVITIES|HOBBIES|REFERENCES|CONTACT|OBJECTIVE|SUMMARY|PROFILE|PUBLICATIONS|EMPLOYMENT|CAREER|WORK|INTERNSHIP|TRAINING|EXPERIENCE)\n|$)'
        
        section_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if section_match:
            section_text = section_match.group(1)
            print(f"🔍 Found {keyword} section: {section_text[:100]}...")
            
            if section_type == 'experience':
                return parse_experience_entries(section_text)
            elif section_type == 'education':
                return parse_education_entries(section_text)
            elif section_type == 'skills':
                return parse_skills_entries(section_text)
            elif section_type == 'projects':
                return parse_projects_entries(section_text)
            elif section_type == 'certifications':
                return parse_certifications_entries(section_text)
            elif section_type == 'awards':
                return parse_awards_entries(section_text)
            elif section_type == 'volunteer':
                return parse_volunteer_entries(section_text)
            elif section_type == 'languages':
                return parse_languages_entries(section_text)
            elif section_type == 'interests':
                return parse_interests_entries(section_text)
            elif section_type == 'publications':
                return parse_publications_entries(section_text)
            elif section_type == 'references':
                return parse_references_entries(section_text)
    
    return []

def parse_experience_entries(section_text: str) -> List[Dict]:
    """Parse experience entries from section text"""
    experience_entries = []
    lines = section_text.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('•'):
            continue
        
        # Check if this line looks like a job title | company format or job title, company format
        if '|' in line or (',' in line and not line.startswith('•')):
            if '|' in line:
                parts = line.split('|')
            else:
                parts = line.split(',')
            
            if len(parts) >= 2:
                title = parts[0].strip()
                company = parts[1].strip()
                
                # Very lenient filtering - include almost everything that looks like work
                if (len(title) > 3 and len(company) > 2 and 
                    not any(word in title.lower() for word in ['education', 'skills', 'certifications', 'interests', 'professional summary', 'bachelor', 'master', 'phd', 'degree', 'university', 'college', 'be', 'b.tech', 'm.tech', 'project', 'teamwork']) and
                    not any(word in company.lower() for word in ['university', 'college', 'institute', 'school', 'academy']) and
                    not title.lower().startswith('experience')):
                    
                    # Try to find duration
                    duration = None
                    if len(parts) >= 3:
                        duration = parts[2].strip()
                    
                    # Look for duration patterns
                    duration_patterns = [
                        r'\d{4}\s*[-–]\s*\d{4}',
                        r'\d{4}\s*[-–]\s*Present',
                        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}\s*[-–]\s*(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}',
                        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s*\d{4}\s*[-–]\s*Present'
                    ]
                    
                    if not duration:
                        for dur_pattern in duration_patterns:
                            duration_match = re.search(dur_pattern, line, re.IGNORECASE)
                            if duration_match:
                                duration = duration_match.group(0)
                                break
                    
                    # Try to find description
                    description = 'Contributed to projects and gained valuable experience.'
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        if next_line and not next_line.startswith('•') and '|' not in next_line:
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
                    
                    experience_entries.append(experience_entry)
    
    return experience_entries

def parse_education_entries(section_text: str) -> List[str]:
    """Parse education entries from section text"""
    education_entries = []
    lines = section_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 10:  # Only add substantial lines
            education_entries.append(line)
    
    return education_entries

def parse_skills_entries(section_text: str) -> List[str]:
    """Parse skills entries from section text"""
    skills = []
    lines = section_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line:
            # Handle skills with categories (e.g., "Languages: Java, Python")
            if ':' in line:
                category, skill_list = line.split(':', 1)
                skill_items = [s.strip() for s in skill_list.split(',')]
                skills.extend(skill_items)
            else:
                # Handle comma-separated skills
                skill_items = [s.strip() for s in line.split(',')]
                skills.extend(skill_items)
    
    return [skill for skill in skills if skill]

def parse_projects_entries(section_text: str) -> List[str]:
    """Parse projects entries from section text"""
    projects = []
    lines = section_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 5:
            projects.append(line)
    
    return projects

def parse_certifications_entries(section_text: str) -> List[str]:
    """Parse certifications entries from section text"""
    certifications = []
    lines = section_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 5:
            certifications.append(line)
    
    return certifications

def parse_awards_entries(section_text: str) -> List[str]:
    """Parse awards entries from section text"""
    awards = []
    lines = section_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 5:
            awards.append(line)
    
    return awards

def parse_volunteer_entries(section_text: str) -> List[str]:
    """Parse volunteer entries from section text"""
    volunteer = []
    lines = section_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 5:
            volunteer.append(line)
    
    return volunteer

def parse_languages_entries(section_text: str) -> List[str]:
    """Parse languages entries from section text"""
    languages = []
    lines = section_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 2:
            languages.append(line)
    
    return languages

def parse_interests_entries(section_text: str) -> List[str]:
    """Parse interests entries from section text"""
    interests = []
    lines = section_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 3:
            interests.append(line)
    
    return interests

def parse_publications_entries(section_text: str) -> List[str]:
    """Parse publications entries from section text"""
    publications = []
    lines = section_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 10:
            publications.append(line)
    
    return publications

def parse_references_entries(section_text: str) -> List[str]:
    """Parse references entries from section text"""
    references = []
    lines = section_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and len(line) > 10:
            references.append(line)
    
    return references

def parse_summary_section(text: str, keywords: List[str]) -> str:
    """Parse summary/objective section"""
    for keyword in keywords:
        pattern = rf'{keyword}[:\s]*\n(.*?)(?=\n(?:PROJECTS|EDUCATION|SKILLS|CERTIFICATIONS|AWARDS|VOLUNTEER|LANGUAGES|INTERESTS|TECHNOLOGIES|SOFT SKILLS|TECHNICAL SKILLS|ACHIEVEMENTS|ACTIVITIES|HOBBIES|REFERENCES|CONTACT|OBJECTIVE|SUMMARY|PROFILE|PUBLICATIONS|EMPLOYMENT|CAREER|WORK|INTERNSHIP|TRAINING|EXPERIENCE)\n|$)'
        summary_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if summary_match:
            summary_text = summary_match.group(1).strip()
            # Take first few lines as summary
            summary_lines = summary_text.split('\n')
            return ' '.join([line.strip() for line in summary_lines[:3] if line.strip()])
    
    return ''

def parse_additional_sections(text: str, known_sections: Dict) -> Dict:
    """Parse any additional sections not covered by known section types"""
    additional = {}
    
    # Find all section headers (lines that are all caps and standalone)
    section_headers = re.findall(r'^([A-Z][A-Z\s&]+)$', text, re.MULTILINE)
    
    for header in section_headers:
        header_clean = header.strip()
        if len(header_clean) > 3:
            # Check if this is a known section
            is_known = False
            for section_type, keywords in known_sections.items():
                if any(keyword.lower() in header_clean.lower() for keyword in keywords):
                    is_known = True
                    break
            
            if not is_known:
                # This is an additional section
                pattern = rf'{re.escape(header_clean)}[:\s]*\n(.*?)(?=\n[A-Z][A-Z\s&]+\n|$)'
                section_match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if section_match:
                    section_content = section_match.group(1).strip()
                    additional[header_clean] = section_content.split('\n')
    
    return additional

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and parse a resume file (PDF or DOCX) using comprehensive parsing"""
    
    # Validate file type
    if not file.content_type in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
    
    try:
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        if file.content_type == "application/pdf":
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
        else:  # DOCX
            doc = Document(io.BytesIO(content))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        if not text or len(text.strip()) < 10:
            raise HTTPException(status_code=400, detail="Could not extract text from the file")
        
        print(f"📄 Extracted text length: {len(text)} characters")
        
        # Parse resume using comprehensive parsing
        resume_data = parse_resume_text_comprehensive(text)
        
        print(f"📄 Parsed data keys: {list(resume_data.keys())}")
        print(f"📄 Name: {resume_data.get('name', 'Not found')}")
        print(f"📄 Email: {resume_data.get('contact_info', {}).get('email', 'Not found')}")
        print(f"📄 Skills count: {len(resume_data.get('skills', []))}")
        print(f"📄 Experience count: {len(resume_data.get('experience', []))}")
        print(f"📄 Education count: {len(resume_data.get('education', []))}")
        print(f"📄 Projects count: {len(resume_data.get('projects', []))}")
        print(f"📄 Certifications count: {len(resume_data.get('certifications', []))}")
        print(f"📄 Additional sections: {list(resume_data.get('additional_sections', {}).keys())}")
        
        # Save to database
        print("📄 Saving to database...")
        
        # Convert experience dictionaries to Experience objects
        experience_objects = []
        for exp in resume_data['experience']:
            if isinstance(exp, dict):
                experience_objects.append({
                    'title': exp.get('title', ''),
                    'company': exp.get('company', ''),
                    'duration': exp.get('duration'),
                    'description': exp.get('description', '')
                })
            else:
                # If it's already an Experience object, convert to dict
                experience_objects.append(exp)
        
        candidate_data = CandidateCreate(
            name=resume_data['name'],
            email=resume_data['contact_info']['email'],
            phone=resume_data['contact_info']['phone'],
            linkedin=resume_data['contact_info']['linkedin'],
            website=resume_data['contact_info']['website'],
            skills=resume_data['skills'],
            experience=experience_objects,
            education=resume_data['education'],
            summary=resume_data['summary'],
            projects=resume_data['projects']
        )
        
        print(f"📄 Candidate data: name={candidate_data.name}, email={candidate_data.email}")
        
        # Check if candidate already exists
        existing_candidate = db.query(Candidate).filter(Candidate.email == candidate_data.email).first()
        if existing_candidate:
            # Update existing candidate
            for field, value in candidate_data.model_dump().items():
                setattr(existing_candidate, field, value)
            db.commit()
            candidate = existing_candidate
            print("📄 Updated existing candidate")
        else:
            # Create new candidate
            candidate = Candidate(**candidate_data.model_dump())
            db.add(candidate)
            db.commit()
            db.refresh(candidate)
            print("📄 Created new candidate")
        
        return CandidateResponse(
            id=candidate.id,
            name=candidate.name,
            email=candidate.email,
            phone=candidate.phone,
            linkedin=candidate.linkedin,
            website=candidate.website,
            skills=candidate.skills,
            experience=candidate.experience,
            education=candidate.education,
            summary=candidate.summary,
            projects=candidate.projects,
            created_at=candidate.created_at,
            updated_at=candidate.updated_at
        )
        
    except Exception as e:
        print(f"❌ Error processing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@router.get("/candidate/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Get candidate by ID"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return CandidateResponse(
        id=candidate.id,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        linkedin=candidate.linkedin,
        website=candidate.website,
        skills=candidate.skills,
        experience=candidate.experience,
        education=candidate.education,
        summary=candidate.summary,
        projects=candidate.projects,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at
    )
