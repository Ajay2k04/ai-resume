# QuantiPeak Recruitment Assistant

A Streamlit web application that streamlines the recruitment workflow by scraping LinkedIn jobs, parsing resumes, and generating AI-powered tailored resumes and cover letters.

## Features

- **Job Scraping**: Scrape LinkedIn jobs using jobspy (no API key required)
- **Resume Parsing**: Upload and parse PDF/DOCX resumes into structured data
- **AI Generation**: Generate tailored resumes and cover letters using Azure OpenAI
- **Download Support**: Export generated documents as TXT or DOCX files
- **Clean UI**: Step-by-step workflow with modern, responsive design

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Azure OpenAI Configuration (Required)
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-06-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Optional: RapidAPI Key for JSearch (fallback job scraping)
RAPIDAPI_KEY=your_rapidapi_key_here
```

### 3. Run the Application

```bash
streamlit run app.py
```

## Usage

The application follows a 5-step workflow:

1. **Scrape Jobs**: Enter job titles, location, and filters to scrape LinkedIn jobs
2. **Upload Resume**: Upload your resume in PDF or DOCX format for parsing
3. **Select Job**: Choose a job posting from the scraped results
4. **Generate Documents**: Create tailored resume and cover letter using AI
5. **Download**: Export the generated documents in your preferred format

## Job Scraping Filters

- **Job Titles**: Multi-line input for multiple job titles
- **Location**: Text input for job location
- **Remote Only**: Checkbox to filter for remote positions
- **Posted Within**: Number of days to filter recent postings
- **Number of Results**: Limit the number of jobs to scrape

## Resume Parsing

The application extracts the following information from uploaded resumes:

- **Personal Information**: Name, email, phone, LinkedIn profile
- **Skills**: Technical and soft skills
- **Experience**: Job titles, companies, and durations
- **Education**: Degrees and educational background

## AI Generation

The application uses Azure OpenAI GPT models to:

- **Tailor Resumes**: Customize resume content to match job requirements
- **Generate Cover Letters**: Create professional, personalized cover letters
- **Keyword Optimization**: Include relevant keywords from job descriptions

## File Formats

### Supported Resume Formats
- PDF (.pdf)
- Microsoft Word (.docx)

### Export Formats
- Plain Text (.txt)
- Microsoft Word (.docx)

## Error Handling

The application includes comprehensive error handling for:

- Missing environment variables
- Failed job scraping
- Resume parsing errors
- AI generation failures
- File upload issues

## Tech Stack

- **Frontend**: Streamlit
- **Job Scraping**: jobspy
- **Resume Parsing**: pdfplumber, python-docx
- **AI Engine**: Azure OpenAI GPT
- **Data Handling**: pandas
- **File Processing**: python-docx

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**: Ensure all required Azure OpenAI variables are set
2. **Job Scraping Fails**: Try different search terms or reduce the number of results
3. **Resume Parsing Issues**: Ensure the resume file is not corrupted and contains readable text
4. **AI Generation Errors**: Check your Azure OpenAI quota and deployment status

### Getting Help

If you encounter issues:

1. Check the console output for error messages
2. Verify your environment variables are correctly set
3. Ensure your Azure OpenAI deployment is active and accessible
4. Try with a simpler resume format if parsing fails

## License

This project is for educational and personal use. Please respect LinkedIn's terms of service when scraping jobs.
