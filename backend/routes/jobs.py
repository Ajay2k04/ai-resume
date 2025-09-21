from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db, Job, SelectedJob, Candidate
from models import JobSearchRequest, JobSearchResponse, JobResponse, JobSelectionRequest
from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime, timedelta
from typing import List

router = APIRouter()

@router.post("/search", response_model=JobSearchResponse)
async def search_jobs(request: JobSearchRequest, db: Session = Depends(get_db)):
    """Search for jobs using multiple sources"""
    
    print(f"🔍 Job search request: {request.job_titles} in {request.location}")
    
    try:
        # Prepare search parameters
        if request.job_titles:
            search_terms = request.job_titles[:2]  # Limit to 2 for better performance
            search_term = " OR ".join(search_terms)
        else:
            search_term = "Software Engineer"
        
        # Optimize parameters for speed
        optimized_results = min(request.num_results, 30)  # Cap at 30 for faster results
        optimized_days = min(request.posted_within_days, 14)  # Cap at 14 days for speed
        
        # Scrape jobs with optimized settings
        print(f"🔍 Scraping jobs with term: '{search_term}' in {request.location}")
        try:
            jobs_df = scrape_jobs(
                site_name=["linkedin"],
                search_term=search_term,
                location=request.location if request.location else "United States",
                results_wanted=optimized_results,
                hours_old=optimized_days * 24,
                country_indeed="us",
                linkedin_fetch_description=True
            )
            print(f"✅ Scraped {len(jobs_df)} jobs from LinkedIn")
        except Exception as scrape_error:
            print(f"⚠️ LinkedIn scraping failed: {scrape_error}")
            # Try with more conservative settings
            jobs_df = scrape_jobs(
                site_name=["linkedin"],
                search_term=search_term,
                location=request.location if request.location else "United States",
                results_wanted=min(optimized_results, 15),
                hours_old=optimized_days * 24,
                country_indeed="us",
                linkedin_fetch_description=False
            )
            print(f"✅ Scraped {len(jobs_df)} jobs with conservative settings")
        
        if jobs_df.empty:
            return JobSearchResponse(
                jobs=[],
                total_count=0,
                search_params=request
            )
        
        # Filter for remote jobs if requested
        if request.remote_only:
            jobs_df = jobs_df[jobs_df['location'].str.contains('remote|Remote|REMOTE', case=False, na=False)]
        
        # Select and rename columns
        job_columns = ['title', 'company', 'location', 'job_url', 'description', 'company_url']
        available_columns = [col for col in job_columns if col in jobs_df.columns]
        
        result_df = jobs_df[available_columns].copy()
        
        # Rename columns to match expected format
        column_mapping = {}
        for i, col in enumerate(available_columns):
            if i < len(job_columns):
                column_mapping[col] = job_columns[i]
        result_df = result_df.rename(columns=column_mapping)
        
        # Clean up the data efficiently
        result_df = result_df.fillna('N/A')
        result_df = result_df.drop_duplicates(subset=['job_url'])
        
        # Filter out jobs without descriptions
        if 'description' in result_df.columns:
            result_df = result_df[result_df['description'] != 'N/A']
            result_df = result_df[result_df['description'].str.len() > 30]
        
        # Limit final results for better performance
        result_df = result_df.head(min(len(result_df), 25))
        
        # Convert to list of JobResponse objects
        jobs = []
        for _, row in result_df.iterrows():
            # Check if job already exists in database
            existing_job = db.query(Job).filter(Job.job_url == row['job_url']).first()
            
            if existing_job:
                job_response = JobResponse(
                    id=existing_job.id,
                    title=existing_job.title,
                    company=existing_job.company,
                    location=existing_job.location,
                    description=existing_job.description,
                    job_url=existing_job.job_url,
                    company_url=existing_job.company_url,
                    source=existing_job.source,
                    posted_date=existing_job.posted_date
                )
            else:
                # Create new job in database
                new_job = Job(
                    title=row['title'],
                    company=row['company'],
                    location=row['location'],
                    description=row['description'],
                    job_url=row['job_url'],
                    company_url=row['company_url'],
                    source='scraped',
                    scraped_at=datetime.utcnow()
                )
                db.add(new_job)
                db.commit()
                db.refresh(new_job)
                
                job_response = JobResponse(
                    id=new_job.id,
                    title=new_job.title,
                    company=new_job.company,
                    location=new_job.location,
                    description=new_job.description,
                    job_url=new_job.job_url,
                    company_url=new_job.company_url,
                    source=new_job.source,
                    posted_date=new_job.posted_date
                )
            
            jobs.append(job_response)
        
        return JobSearchResponse(
            jobs=jobs,
            total_count=len(jobs),
            search_params=request
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching jobs: {str(e)}")

@router.post("/select")
async def select_job(request: JobSelectionRequest, db: Session = Depends(get_db)):
    """Select a job for a candidate"""
    
    try:
        # Verify candidate exists
        candidate = db.query(Candidate).filter(Candidate.id == request.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Verify job exists
        job = db.query(Job).filter(Job.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Check if already selected
        existing_selection = db.query(SelectedJob).filter(
            SelectedJob.candidate_id == request.candidate_id,
            SelectedJob.job_id == request.job_id
        ).first()
        
        if existing_selection:
            return {
                "message": "Job already selected",
                "selection_id": existing_selection.id
            }
        
        # Create new selection
        selection = SelectedJob(
            candidate_id=request.candidate_id,
            job_id=request.job_id
        )
        db.add(selection)
        db.commit()
        db.refresh(selection)
        
        return {
            "message": "Job selected successfully",
            "selection_id": selection.id,
            "candidate_id": request.candidate_id,
            "job_id": request.job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting job: {str(e)}")

@router.get("/candidate/{candidate_id}/selected")
async def get_selected_jobs(candidate_id: int, db: Session = Depends(get_db)):
    """Get all selected jobs for a candidate"""
    
    try:
        # Verify candidate exists
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        # Get selected jobs
        selected_jobs = db.query(SelectedJob).filter(
            SelectedJob.candidate_id == candidate_id
        ).all()
        
        jobs = []
        for selection in selected_jobs:
            job = selection.job
            jobs.append(JobResponse(
                id=job.id,
                title=job.title,
                company=job.company,
                location=job.location,
                description=job.description,
                job_url=job.job_url,
                company_url=job.company_url,
                source=job.source,
                posted_date=job.posted_date
            ))
        
        return {
            "candidate_id": candidate_id,
            "selected_jobs": jobs,
            "total_count": len(jobs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting selected jobs: {str(e)}")
