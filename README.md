# 🚀 QuantiPeak Recruitment SaaS Platform

A comprehensive full-stack recruitment SaaS platform that streamlines the job application process with AI-powered resume tailoring, job scraping, and document generation.

## 🌟 Features

### Core Workflow (5-Step Process)
1. **🔍 Job Search** - Scrape jobs from multiple sources (LinkedIn, Indeed, Dice, Google Jobs, etc.)
2. **📄 Resume Upload** - Parse PDF/DOCX resumes into structured data
3. **🎯 Job Selection** - Choose target positions from scraped results
4. **✨ AI Generation** - Generate tailored resumes and cover letters using Azure OpenAI
5. **📥 Export** - Download documents in multiple formats (TXT, DOCX, PDF)

### Advanced Features
- **Multi-Source Job Scraping**: LinkedIn, Indeed, Dice, Google Jobs, HiringCafe, Gmail, Outlook
- **Intelligent Resume Parsing**: Extract skills, experience, education, and contact info
- **AI-Powered Tailoring**: Customize documents for specific job requirements
- **ATS-Friendly Output**: Optimized formatting for Applicant Tracking Systems
- **Professional UI**: Modern, responsive design with Tailwind CSS
- **Database Persistence**: Store candidates, jobs, and generated documents
- **Docker Support**: Full containerization for easy deployment

## 🛠️ Tech Stack

### Frontend
- **React 18** with Vite for fast development
- **Tailwind CSS** for professional, responsive UI
- **React Router** for navigation
- **Modern ES6+** with hooks and functional components

### Backend
- **FastAPI** for high-performance API
- **SQLAlchemy** with SQLite for data persistence
- **Azure OpenAI GPT** for AI-powered content generation
- **pdfplumber + python-docx** for resume parsing
- **jobspy + requests + BeautifulSoup4** for job scraping

### Infrastructure
- **Docker + Docker Compose** for containerization
- **SQLite** for development database (easily upgradeable to PostgreSQL)
- **python-dotenv** for environment management
- **Replit-compatible** deployment

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Azure OpenAI API access
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd AI-resume-cover-letter
cp env.example .env
```

### 2. Configure Environment Variables

Edit `.env` file with your credentials:

```env
# Azure OpenAI Configuration (Required)
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-06-01
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini

# Database Configuration (SQLite for development)
DATABASE_URL=sqlite:///./quantipeak.db

# Optional: RapidAPI Key for additional job scraping sources
RAPIDAPI_KEY=your_rapidapi_key_here
```

### 3. Run with Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432

## 🏗️ Local Development

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Database Setup

```bash
# SQLite database is created automatically
# No additional setup required for development
```

## 📁 Project Structure

```
quantipeak-app/
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── pages/           # Workflow step components
│   │   │   ├── ResumeUpload.jsx
│   │   │   ├── JobSearch.jsx
│   │   │   ├── JobSelection.jsx
│   │   │   ├── AIGeneration.jsx
│   │   │   └── Export.jsx
│   │   ├── components/      # Reusable components
│   │   │   ├── Header.jsx
│   │   │   └── StepProgress.jsx
│   │   └── App.jsx
│   ├── Dockerfile
│   └── package.json
├── backend/                  # FastAPI backend
│   ├── routes/              # API endpoints
│   │   ├── resumes.py       # Resume parsing
│   │   ├── jobs.py          # Job scraping
│   │   ├── ai.py            # AI generation
│   │   └── export.py        # Document export
│   ├── database.py          # Database models
│   ├── models.py            # Pydantic models
│   ├── main.py              # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml       # Container orchestration
├── .env.example            # Environment template
└── README.md
```

## 🔧 API Endpoints

### Resume Management
- `POST /api/resumes/upload` - Upload and parse resume
- `GET /api/resumes/candidate/{id}` - Get candidate data

### Job Management
- `POST /api/jobs/search` - Search for jobs
- `POST /api/jobs/select` - Select a job for candidate
- `GET /api/jobs/candidate/{id}/selected` - Get selected jobs

### AI Generation
- `POST /api/ai/generate` - Generate tailored documents
- `GET /api/ai/health` - Check AI service status

### Export
- `POST /api/export` - Export documents
- `GET /api/formats` - Get supported formats

## 🎯 Usage Guide

### 1. Job Search
- Enter job titles (one per line)
- Specify location and preferences
- Choose remote-only if desired
- Set time range and result limits

### 2. Resume Upload
- Upload PDF or DOCX resume
- System extracts structured data
- Review parsed information

### 3. Job Selection
- Browse scraped job listings
- Click to select target position
- View job details and requirements

### 4. AI Generation
- Generate tailored resume
- Create personalized cover letter
- Review AI-generated content

### 5. Export
- Download in multiple formats
- Choose TXT, DOCX, or PDF
- Ready for job applications

## 🔒 Security & Privacy

- **Data Encryption**: All data encrypted in transit and at rest
- **No Data Retention**: Generated documents not stored permanently
- **API Security**: CORS protection and input validation
- **Environment Variables**: Sensitive data in environment files

## 🚀 Deployment

### Production Deployment

1. **Set up production database**
2. **Configure environment variables**
3. **Build and deploy containers**
4. **Set up reverse proxy (nginx)**
5. **Configure SSL certificates**

### Replit Deployment

1. **Import project to Replit**
2. **Set environment variables**
3. **Run `docker-compose up`**
4. **Access via Replit URL**

## 🐛 Troubleshooting

### Common Issues

1. **Azure OpenAI Errors**
   - Verify API key and endpoint
   - Check deployment status
   - Ensure sufficient quota

2. **Database Connection Issues**
   - Verify PostgreSQL is running
   - Check connection string
   - Ensure database exists

3. **Job Scraping Failures**
   - Try different search terms
   - Reduce result limits
   - Check network connectivity

4. **Resume Parsing Issues**
   - Ensure file is not corrupted
   - Try different file format
   - Check file size limits

### Debug Mode

```bash
# Enable debug logging
export DEBUG=true
docker-compose up
```

## 📊 Performance Optimization

- **Job Scraping**: Limited to 30 results for speed
- **AI Generation**: Optimized prompts for faster processing
- **Database**: Indexed queries for better performance
- **Frontend**: Code splitting and lazy loading

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## 📄 License

This project is for educational and personal use. Please respect job board terms of service when scraping.

## 🆘 Support

For issues and questions:
- Check the troubleshooting section
- Review API documentation at `/docs`
- Open an issue on GitHub

---

**Built with ❤️ for the recruitment community**
