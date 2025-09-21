from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db, GeneratedDocument, Candidate, Job
from models import AIGenerationRequest, AIGenerationResponse
from openai import AzureOpenAI
import os
import json
from datetime import datetime

router = APIRouter()

def get_azure_client():
    """Get Azure OpenAI client"""
    return AzureOpenAI(
        api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2023-07-01-preview'),
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
    )

def generate_ai_content_with_job_details(resume_data: dict, job_description: str, job_title: str, company_name: str, content_type: str) -> str:
    """Generate tailored resume or cover letter using Azure OpenAI with specific job details"""
    try:
        print(f"🔍 Generating {content_type} for {job_title} at {company_name}")
        print(f"Resume data keys: {list(resume_data.keys()) if resume_data else 'None'}")
        
        client = get_azure_client()
        
        # Get candidate details
        candidate_name = resume_data.get('name', 'Candidate')
        candidate_email = resume_data.get('contact_info', {}).get('email', 'candidate@email.com')
        candidate_phone = resume_data.get('contact_info', {}).get('phone', 'Phone Number')
        candidate_linkedin = resume_data.get('contact_info', {}).get('linkedin', 'LinkedIn Profile')
        
        if content_type == "resume":
            # Clean the resume data for better formatting
            resume_data_cleaned = json.dumps(resume_data, indent=2)
            
            prompt = f"""
            You are a professional resume writer. 
            Generate a clean, modern, ATS-friendly resume for {candidate_name} applying for the role of {job_title} at {company_name}.

            CANDIDATE INFO (from resume):
            {resume_data_cleaned}

            JOB DESCRIPTION:
            {job_description}

            STRICT RULES:
            - Use ONLY candidate's actual information. No fake companies, roles, or achievements.
            - If a section has no data, OMIT it completely. Do not create empty sections.
            - Use only explicitly listed skills, tools, or experiences. Do not invent.
            - Tailor wording to match {job_title} at {company_name} by aligning with the job description keywords.
            - Do NOT include location or address unless specifically provided.
            - CRITICAL: Do NOT use asterisk (*) symbols anywhere in the resume - use only bullet points (•).
            - Do NOT use "|" symbols in project names or anywhere in the resume.
            - Output only the final resume. No extra notes, explanations, or markdown.

            RESUME BLUEPRINT TEMPLATE:

            {candidate_name.upper()}
            {candidate_phone} | {candidate_email}{' | ' + resume_data.get('contact_info', {}).get('linkedin', '') if resume_data.get('contact_info', {}).get('linkedin') else ''}{' | ' + resume_data.get('contact_info', {}).get('website', '') if resume_data.get('contact_info', {}).get('website') else ''}

            PROFESSIONAL SUMMARY
            [Write 2-3 lines highlighting experience, top skills, and career goals tailored to {job_title} at {company_name}. Focus on skills and experience that directly match the job requirements. Use metrics if available. Emphasize relevant achievements that align with the job description.]

            WORK EXPERIENCE
            [For each real experience found, format as:]
            Job Title | Company | Duration (exactly as in resume data)
            • Achievement #1 (use metrics if possible, emphasize skills relevant to {job_title})
            • Achievement #2 (highlight experience that matches job requirements)
            • Achievement #3 (focus on results that demonstrate value for {company_name})

            [Repeat for multiple roles, in reverse chronological order. Prioritize experiences most relevant to {job_title}.]

            EDUCATION
            [Only if present in resume data, format as:]
            Degree | University | Graduation Year

            SKILLS
            [Format as comma-separated list, NOT bullet points. Group by category if multiple categories exist. Prioritize skills mentioned in the job description:]
            Programming Languages: [list from resume data, emphasize those mentioned in job description and all from resume data]
            Frameworks & Libraries: [list from resume data, highlight relevant frameworks for {job_title}]
            Tools & Technologies: [list from resume data, focus on tools relevant to {company_name}]
            Databases: [list from resume data]
            Other Skills: [list from resume data, emphasize soft skills relevant to the role]

            PROJECTS
            [Only if present in resume data, format as. Prioritize projects most relevant to {job_title}:]
            Project Name
            • Description of what was built/accomplished (emphasize technologies/skills relevant to job)
            • Key feature or measurable outcome (highlight results that demonstrate value)

            CERTIFICATIONS
            [Only if present in resume data, format as:]
            Certification Name | Issuing Organization | Date

            EXTRACURRICULAR ACTIVITIES
            [Only if present in resume data, format as:]
            Activity/Role | Organization | Duration
            • Key achievement or responsibility

            AWARDS & ACHIEVEMENTS
            [Only if present in resume data, format as:]
            Award Name | Organization | Date
            • Brief description of achievement

            VOLUNTEER / LEADERSHIP ROLES
            [Only if present in resume data, format as:]
            Role | Organization | Duration
            • Key responsibility or achievement

            LANGUAGES
            [Only if present in resume data, format as:]
            Language: Proficiency Level

            INTERESTS
            [Only if present in resume data, format as comma-separated list]

            FORMATTING REQUIREMENTS:
            - Left align all text
            - Use consistent bullet points (•) ONLY - NEVER use asterisk (*) symbols
            - Maintain clear spacing between sections
            - Ensure ATS compatibility with standard section headers
            - 1 page if under 10 years experience, max 2 pages
            - Clean fonts, bullets, and whitespace
            - No photos or personal info beyond contact details
            - Must be ATS-friendly (no tables, graphics, or complex formatting)
            - CRITICAL: Do NOT use asterisk (*) symbols anywhere in the resume - use only bullet points (•)
            - Do NOT use "|" symbols in project names or anywhere in the resume
            - FONT SIZES: Name should be 14pt, section headers should be 10pt, body text should be 9pt
            """
        else:  # cover letter
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Clean the resume data for better formatting
            resume_data_cleaned = json.dumps(resume_data, indent=2)
            
            prompt = f"""
            You are a professional career coach and resume writer. 
            Generate a clean, professional cover letter for {candidate_name}, applying for the role of {job_title} at {company_name}.

            CANDIDATE INFO (from resume):
            {resume_data_cleaned}

            JOB DESCRIPTION:
            {job_description}

            STRICT RULES:
            - Use ONLY candidate's real information. No fake experience, projects, or achievements.
            - If a section of information is missing, skip it completely.
            - Do NOT invent company values or mission statements. Use only details in the JD.
            - Be specific: use keywords from the JD that match the candidate's actual skills.
            - Do not repeat the resume content verbatim; rewrite it as a persuasive narrative.
            - Output ONLY the cover letter in plain text, no markdown, no extra notes.
            - Keep cover letter 3-4 short paragraphs, one page max.
            - Tone: Professional, confident, and tailored to the job.
            - Must be ATS-friendly (plain text, no special formatting).
            - FONT SIZES: Name should be 12pt, body text should be 10pt, keep headings minimal

            COVER LETTER BLUEPRINT TEMPLATE:

            {candidate_name}
            {candidate_phone} | {candidate_email}{' | ' + resume_data.get('contact_info', {}).get('linkedin', '') if resume_data.get('contact_info', {}).get('linkedin') else ''}

            {current_date}

            {company_name}
            Human Resources Department

            Dear Hiring Manager,

            [Opening Paragraph: Express genuine enthusiasm for the specific {job_title} position at {company_name}. Mention specific aspects of the company or role that attracted the candidate. Reference the job posting or company values that align with the candidate's career goals. Keep it concise and engaging.]

            [Body Paragraph 1 - Relevant Experience: Highlight the most relevant work experience or achievements tailored to the {job_title} role. Use measurable results where possible. Focus on 1-2 key accomplishments that directly relate to the job requirements. Emphasize how past experience has prepared the candidate for this specific role.]

            [Body Paragraph 2 - Skills & Value Add: Show how candidate's skills and qualifications directly match the job requirements. Mention key technical or soft skills from the resume that align with the job description. Explain how these skills will benefit {company_name} and contribute to their success. Reference specific technologies or methodologies mentioned in the job description.]

            [Closing Paragraph: Reaffirm excitement for the role and what the candidate can contribute to {company_name}. Mention specific ways the candidate can add value to the team. Express availability for interview and thank the hiring manager for consideration. Keep it professional, confident, and forward-looking.]

            Sincerely,
            {candidate_name}
            """
        
        print(f"📝 Sending request to Azure OpenAI...")
        print(f"Model: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')}")
        print(f"Prompt length: {len(prompt)}")
        
        response = client.chat.completions.create(
            model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
            messages=[
                {"role": "system", "content": "You are an expert career coach and professional resume writer. You specialize in creating compelling, tailored resumes and cover letters that get candidates hired. CRITICAL: Use ONLY the candidate's actual information provided. Do NOT create fake companies, fake experience, fake achievements, or fake details. If information is missing, simply omit that section. Focus on tailoring the existing real information to match the job requirements. NEVER use asterisk (*) symbols in resumes - use only bullet points (•)."},
                
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.2
        )
        
        print(f"✅ Received response from Azure OpenAI")
        print(f"Response length: {len(response.choices[0].message.content)}")
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error generating {content_type}: {str(e)}")
        import traceback
        traceback.print_exc()
        return ""

@router.post("/generate", response_model=AIGenerationResponse)
async def generate_content(request: dict, db: Session = Depends(get_db)):
    """Generate AI-powered resume or cover letter"""
    
    try:
        # Validate required environment variables
        required_vars = [
            'AZURE_OPENAI_API_KEY',
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_DEPLOYMENT_NAME'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise HTTPException(
                status_code=500, 
                detail=f"Missing environment variables: {', '.join(missing_vars)}"
            )
        
        # Extract data from request
        resume_data = request.get('resume_data', {})
        job_description = request.get('job_description', '')
        job_title = request.get('job_title', '')
        company_name = request.get('company_name', '')
        content_type = request.get('contentType', 'resume')
        
        # Generate content using existing function
        content = generate_ai_content_with_job_details(
            resume_data,
            job_description,
            job_title,
            company_name,
            content_type
        )
        
        if not content:
            print("No content generated - this might be due to Azure OpenAI issues")
            raise HTTPException(status_code=500, detail="Failed to generate content - check Azure OpenAI configuration")
        
        # Save to database (optional - you might want to implement this)
        # For now, we'll just return the generated content
        
        return AIGenerationResponse(
            content=content,
            status="success",
            message=f"{content_type.title()} generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def ai_health_check():
    """Health check for AI service"""
    try:
        # Check if Azure OpenAI is configured
        required_vars = [
            'AZURE_OPENAI_API_KEY',
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_DEPLOYMENT_NAME'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            return {
                "status": "unhealthy",
                "message": f"Missing environment variables: {', '.join(missing_vars)}"
            }
        
        return {
            "status": "healthy",
            "message": "AI service is ready"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"AI service error: {str(e)}"
        }
