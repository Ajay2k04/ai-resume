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
        
        # Build contact info strings
        linkedin_info = f" | {candidate_linkedin}" if candidate_linkedin and candidate_linkedin.strip() else ""
        website = resume_data.get('contact_info', {}).get('website', '')
        website_info = f" | {website}" if website and website.strip() and not any(domain in website.lower() for domain in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'email.com']) else ""
        
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
            - CRITICAL: Do NOT write placeholder text like "[Omit if not present in resume data]" or "[Omit if not present]" or any similar placeholder text.
            - CRITICAL: If a section has no data, simply do not include that section at all. Do not write any text for empty sections.
            - Use only explicitly listed skills, tools, or experiences. Do not invent.
            - Tailor wording to match {job_title} at {company_name} by aligning with the job description keywords.
            - Do NOT include location or address unless specifically provided.
            - CRITICAL: Do NOT use asterisk (*) symbols anywhere in the resume - use only bullet points (•).
            - Do NOT use "|" symbols in project names or anywhere in the resume.
            - CRITICAL: Do NOT include website if it's an email domain (gmail.com, yahoo.com, hotmail.com, outlook.com, email.com).
            - Only include legitimate websites/portfolios in contact information.
            - Output only the final resume. No extra notes, explanations, or markdown.
            - CRITICAL: Do NOT include any notes, disclaimers, or explanations at the end of the resume.
            - CRITICAL: Do NOT write any text like "Note:" or "The resume has been tailored..." or any similar explanatory text.
            - CRITICAL: The output should end with the last section of the resume content only.

            RESUME BLUEPRINT TEMPLATE:

            {candidate_name.upper()}
            {candidate_phone} | {candidate_email}{linkedin_info}{website_info}

            PROFESSIONAL SUMMARY
            [Write 2-3 lines highlighting experience, top skills, and career goals tailored to {job_title} at {company_name}. Focus on skills and experience that directly match the job requirements. Use metrics if available. Emphasize relevant achievements that align with the job description.]

            WORK EXPERIENCE
            [ONLY include this section if there is actual work experience data in the resume. If no work experience is found, OMIT this entire section completely.]
            [For each real experience found, format as:]
            Job Title | Company | Duration (only if duration is available in resume data, otherwise omit duration part)
            • Achievement #1 (use metrics if possible, emphasize skills relevant to {job_title})
            • Achievement #2 (highlight experience that matches job requirements)
            • Achievement #3 (focus on results that demonstrate value for {company_name})

            [Repeat for multiple roles, in reverse chronological order. Prioritize experiences most relevant to {job_title}.]
            [IMPORTANT: If no duration is provided in the resume data, format as "Job Title | Company" without the duration part.]
            [CRITICAL: Use actual project names and descriptions from the resume data. Do not use generic descriptions.]
            [CRITICAL: If no work experience data exists, do NOT create fake experience entries. Simply omit the WORK EXPERIENCE section entirely.]

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
            
            [CRITICAL: Use actual project names and descriptions from the resume data. Do not create generic project descriptions.]

            CERTIFICATIONS
            [ONLY include this section if certifications are present in resume data. If no certifications exist, completely omit this section. Do not write any placeholder text like "[Omit if not present]" or similar.]

            EXTRACURRICULAR ACTIVITIES
            [ONLY include this section if extracurricular activities are present in resume data. If no activities exist, completely omit this section. Do not write any placeholder text like "[Omit if not present]" or similar.]

            AWARDS & ACHIEVEMENTS
            [ONLY include this section if awards are present in resume data. If no awards exist, completely omit this section. Do not write any placeholder text like "[Omit if not present]" or similar.]

            VOLUNTEER / LEADERSHIP ROLES
            [ONLY include this section if volunteer work is present in resume data. If no volunteer work exists, completely omit this section. Do not write any placeholder text like "[Omit if not present]" or similar.]

            LANGUAGES
            [ONLY include this section if languages are present in resume data. If no languages exist, completely omit this section. Do not write any placeholder text like "[Omit if not present]" or similar.]

            INTERESTS
            [ONLY include this section if interests are present in resume data. If no interests exist, completely omit this section. Do not write any placeholder text like "[Omit if not present]" or similar.]

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
            - CRITICAL: Do NOT include any notes, disclaimers, or explanatory text at the end
            - CRITICAL: The resume must end with the last section content only - no additional text
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
            {candidate_phone} | {candidate_email}{linkedin_info}{website_info}

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

def generate_mock_resume(resume_data: dict, job_title: str, company_name: str) -> str:
    """Generate a mock resume for testing when Azure OpenAI is not configured"""
    try:
        name = resume_data.get('name', 'John Doe')
        email = resume_data.get('contact_info', {}).get('email', 'john.doe@email.com')
        phone = resume_data.get('contact_info', {}).get('phone', '(555) 123-4567')
        skills = resume_data.get('skills', ['Python', 'JavaScript', 'React', 'Node.js'])
        experience_list = resume_data.get('experience', [])
        education = resume_data.get('education', [])
        projects = resume_data.get('projects', [])
        
        # Build contact info with conditional website
        contact_info = f"{phone} | {email}"
        linkedin = resume_data.get('contact_info', {}).get('linkedin', '')
        website = resume_data.get('contact_info', {}).get('website', '')
        
        if linkedin and linkedin.strip():
            contact_info += f" | {linkedin}"
        if website and website.strip() and not any(domain in website.lower() for domain in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'email.com']):
            contact_info += f" | {website}"
        
        # Build work experience section
        work_exp_section = ""
        if experience_list:
            work_exp_section = "\nWORK EXPERIENCE\n"
            for exp in experience_list[:3]:  # Limit to 3 experiences
                title = exp.get('title', 'Software Developer')
                company = exp.get('company', 'Tech Company')
                duration = exp.get('duration', '')
                
                if duration:
                    work_exp_section += f"{title} | {company} | {duration}\n"
                else:
                    work_exp_section += f"{title} | {company}\n"
                # Use the actual description from the resume data
                actual_description = exp.get('description', 'Contributed to software development projects using modern technologies and best practices')
                work_exp_section += f"• {actual_description}\n"
                work_exp_section += "• Collaborated with cross-functional teams to deliver projects on time\n"
                work_exp_section += "• Implemented best practices for code quality and performance optimization\n\n"
        # If no experience, don't add any work experience section
        
        # Build education section
        education_section = ""
        if education:
            education_section = "\nEDUCATION\n"
            for edu in education[:2]:  # Limit to 2 education entries
                education_section += f"{edu}\n"
        else:
            education_section = "\nEDUCATION\nBachelor of Science in Computer Science | University Name | 2020\n"
        
        # Build projects section
        projects_section = ""
        if projects:
            projects_section = "\nPROJECTS\n"
            for project in projects[:2]:  # Limit to 2 projects
                projects_section += f"{project}\n"
        
        # Build skills section
        skills_section = ""
        if skills:
            skills_section = "\nSKILLS\n"
            skills_section += f"Programming Languages: {', '.join(skills[:5])}\n"
            if len(skills) > 5:
                skills_section += f"Frameworks & Libraries: {', '.join(skills[5:])}\n"
        
        resume_content = f"""{name.upper()}
{contact_info}

PROFESSIONAL SUMMARY
Experienced professional with expertise in {', '.join(skills[:3])}. Passionate about technology and innovation with a strong foundation in software development and problem-solving.{work_exp_section}{skills_section}{projects_section}{education_section}"""
        return resume_content
    except Exception as e:
        print(f"Error generating mock resume: {e}")
        return "Error generating resume content"

def generate_mock_cover_letter(resume_data: dict, job_title: str, company_name: str) -> str:
    """Generate a mock cover letter for testing when Azure OpenAI is not configured"""
    try:
        from datetime import datetime
        current_date = datetime.now().strftime("%B %d, %Y")
        
        name = resume_data.get('name', 'John Doe')
        email = resume_data.get('contact_info', {}).get('email', 'john.doe@email.com')
        phone = resume_data.get('contact_info', {}).get('phone', '(555) 123-4567')
        skills = resume_data.get('skills', ['Python', 'JavaScript', 'React'])
        experience_list = resume_data.get('experience', [])
        
        # Build contact info with conditional website
        contact_info = f"{phone} | {email}"
        linkedin = resume_data.get('contact_info', {}).get('linkedin', '')
        website = resume_data.get('contact_info', {}).get('website', '')
        
        if linkedin and linkedin.strip():
            contact_info += f" | {linkedin}"
        if website and website.strip() and not any(domain in website.lower() for domain in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'email.com']):
            contact_info += f" | {website}"
        
        # Build experience context
        experience_context = ""
        if experience_list:
            exp = experience_list[0]  # Use first experience
            title = exp.get('title', 'Software Developer')
            company = exp.get('company', 'Tech Company')
            experience_context = f"my experience as a {title} at {company}"
        else:
            experience_context = "my experience in software development"
        
        cover_letter = f"""{name}
{contact_info}

{current_date}

{company_name}
Human Resources Department

Dear Hiring Manager,

I am writing to express my strong interest in the {job_title} position at {company_name}. With my background in {', '.join(skills[:2])} and passion for innovative technology solutions, I am excited about the opportunity to contribute to your team.

My experience in software development has equipped me with the technical skills and problem-solving abilities that align perfectly with the requirements for this role. Through {experience_context}, I have successfully delivered projects using {', '.join(skills)} and am confident in my ability to make an immediate impact at {company_name}.

I am particularly drawn to {company_name} because of your commitment to innovation and excellence. I am eager to bring my technical expertise and collaborative spirit to your team and contribute to your continued success.

Thank you for considering my application. I look forward to the opportunity to discuss how my skills and experience can benefit {company_name}.

Sincerely,
{name}
"""
        return cover_letter
    except Exception as e:
        print(f"Error generating mock cover letter: {e}")
        return "Error generating cover letter content"

@router.post("/generate", response_model=AIGenerationResponse)
async def generate_content(request: dict, db: Session = Depends(get_db)):
    """Generate AI-powered resume or cover letter"""
    
    try:
        # Extract data from request
        resume_data = request.get('resume_data', {})
        job_description = request.get('job_description', '')
        job_title = request.get('job_title', '')
        company_name = request.get('company_name', '')
        content_type = request.get('contentType', 'resume')
        
        print(f"🔍 AI Generation Request:")
        print(f"  Content Type: {content_type}")
        print(f"  Job Title: {job_title}")
        print(f"  Company: {company_name}")
        print(f"  Resume Data Keys: {list(resume_data.keys()) if resume_data else 'None'}")
        
        # Check if Azure OpenAI is configured
        required_vars = [
            'AZURE_OPENAI_API_KEY',
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_DEPLOYMENT_NAME'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"⚠️ Missing Azure OpenAI configuration: {missing_vars}")
            # Return a mock response for testing
            if content_type == "resume":
                content = generate_mock_resume(resume_data, job_title, company_name)
            else:
                content = generate_mock_cover_letter(resume_data, job_title, company_name)
        else:
            # Generate content using Azure OpenAI
            content = generate_ai_content_with_job_details(
                resume_data,
                job_description,
                job_title,
                company_name,
                content_type
            )
        
        if not content:
            print("No content generated")
            raise HTTPException(status_code=500, detail="Failed to generate content")
        
        print(f"✅ Generated {content_type} successfully")
        
        return AIGenerationResponse(
            content=content,
            status="success",
            message=f"{content_type.title()} generated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in generate_content: {str(e)}")
        import traceback
        traceback.print_exc()
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
                "status": "limited",
                "message": f"Azure OpenAI not configured: {', '.join(missing_vars)}. Mock generation available."
            }
        
        return {
            "status": "healthy",
            "message": "AI service is ready with Azure OpenAI"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"AI service error: {str(e)}"
        }
