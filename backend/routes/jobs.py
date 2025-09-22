from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db, Job, SelectedJob, Candidate
from models import JobSearchRequest, JobSearchResponse, JobResponse, JobSelectionRequest
from jobspy import scrape_jobs
import pandas as pd
from datetime import datetime, timedelta
from typing import List
import requests
from bs4 import BeautifulSoup
import time
import random

router = APIRouter()

# NOTE: Direct scraping functions below are no longer used - we now use jobspy for all platforms
def scrape_indeed_jobs(search_term: str, location: str, num_results: int = 20) -> List[dict]:
    """Scrape jobs from Indeed"""
    jobs = []
    try:
        # Indeed search URL
        base_url = "https://www.indeed.com/jobs"
        params = {
            'q': search_term,
            'l': location,
            'sort': 'date',
            'fromage': '7'  # Last 7 days
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for Indeed's changing structure
            job_selectors = [
                'div[data-jk]',  # Indeed job cards
                'div.job_seen_beacon',
                'div[data-testid="job-card"]',
                'div.jobsearch-SerpJobCard'
            ]
            
            job_cards = []
            for selector in job_selectors:
                job_cards = soup.select(selector)
                if job_cards:
                    break
            
            for card in job_cards[:num_results]:
                try:
                    # Try multiple title selectors
                    title_selectors = ['h2 a[data-jk]', 'h2.jobTitle a', 'a[data-jk]', 'h2 a']
                    title_elem = None
                    for selector in title_selectors:
                        title_elem = card.select_one(selector)
                        if title_elem:
                            break
                    
                    # Try multiple company selectors
                    company_selectors = ['span.companyName', 'div.company', 'span[data-testid="company-name"]']
                    company_elem = None
                    for selector in company_selectors:
                        company_elem = card.select_one(selector)
                        if company_elem:
                            break
                    
                    # Try multiple location selectors
                    location_selectors = ['div.companyLocation', 'div.location', 'span[data-testid="job-location"]']
                    location_elem = None
                    for selector in location_selectors:
                        location_elem = card.select_one(selector)
                        if location_elem:
                            break
                    
                    if title_elem and company_elem:
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'location': location_elem.get_text(strip=True) if location_elem else location,
                            'job_url': f"https://www.indeed.com{title_elem.get('href', '')}" if title_elem.get('href') else '',
                            'description': 'Job description available on Indeed',
                            'company_url': '',
                            'source': 'Indeed'
                        }
                        jobs.append(job)
                except Exception as e:
                    print(f"Error parsing Indeed job card: {e}")
                    continue
                    
        time.sleep(random.uniform(2, 4))  # Rate limiting
    except Exception as e:
        print(f"Error scraping Indeed: {e}")
    
    return jobs

def scrape_monster_jobs(search_term: str, location: str, num_results: int = 20) -> List[dict]:
    """Scrape jobs from Monster"""
    jobs = []
    try:
        # Monster search URL
        base_url = "https://www.monster.com/jobs/search"
        params = {
            'q': search_term,
            'where': location,
            'sort': 'dt.rv.di'  # Sort by date
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for Monster's changing structure
            job_selectors = [
                'div[data-testid="job-card"]',
                'div.card-content',
                'div.job-card',
                'div[data-job-id]',
                'article[data-job-id]'
            ]
            
            job_cards = []
            for selector in job_selectors:
                job_cards = soup.select(selector)
                if job_cards:
                    break
            
            for card in job_cards[:num_results]:
                try:
                    # Try multiple title selectors
                    title_selectors = ['h3.title', 'h2.title', 'a[data-testid="job-title"]', 'h3 a', 'h2 a']
                    title_elem = None
                    for selector in title_selectors:
                        title_elem = card.select_one(selector)
                        if title_elem:
                            break
                    
                    # Try multiple company selectors
                    company_selectors = ['div.company', 'span.company', 'div[data-testid="company-name"]', 'div.company-name']
                    company_elem = None
                    for selector in company_selectors:
                        company_elem = card.select_one(selector)
                        if company_elem:
                            break
                    
                    # Try multiple location selectors
                    location_selectors = ['div.location', 'span.location', 'div[data-testid="job-location"]', 'div.job-location']
                    location_elem = None
                    for selector in location_selectors:
                        location_elem = card.select_one(selector)
                        if location_elem:
                            break
                    
                    if title_elem and company_elem:
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'location': location_elem.get_text(strip=True) if location_elem else location,
                            'job_url': f"https://www.monster.com{title_elem.get('href', '')}" if title_elem.get('href') else '',
                            'description': 'Job description available on Monster',
                            'company_url': '',
                            'source': 'Monster'
                        }
                        jobs.append(job)
                except Exception as e:
                    print(f"Error parsing Monster job card: {e}")
                    continue
                    
        time.sleep(random.uniform(2, 4))  # Rate limiting
    except Exception as e:
        print(f"Error scraping Monster: {e}")
    
    return jobs

def scrape_dice_jobs(search_term: str, location: str, num_results: int = 20) -> List[dict]:
    """Scrape jobs from Dice"""
    jobs = []
    try:
        # Dice search URL
        base_url = "https://www.dice.com/jobs"
        params = {
            'q': search_term,
            'location': location,
            'sort': 'date'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for Dice's changing structure
            job_selectors = [
                'div[data-testid="job-card"]',
                'div.card',
                'div.job-card',
                'div[data-job-id]',
                'article[data-job-id]'
            ]
            
            job_cards = []
            for selector in job_selectors:
                job_cards = soup.select(selector)
                if job_cards:
                    break
            
            for card in job_cards[:num_results]:
                try:
                    # Try multiple title selectors
                    title_selectors = ['h5.card-title', 'h3.card-title', 'a[data-testid="job-title"]', 'h5 a', 'h3 a']
                    title_elem = None
                    for selector in title_selectors:
                        title_elem = card.select_one(selector)
                        if title_elem:
                            break
                    
                    # Try multiple company selectors
                    company_selectors = ['div.card-company', 'span.card-company', 'div[data-testid="company-name"]', 'div.company-name']
                    company_elem = None
                    for selector in company_selectors:
                        company_elem = card.select_one(selector)
                        if company_elem:
                            break
                    
                    # Try multiple location selectors
                    location_selectors = ['div.card-location', 'span.card-location', 'div[data-testid="job-location"]', 'div.job-location']
                    location_elem = None
                    for selector in location_selectors:
                        location_elem = card.select_one(selector)
                        if location_elem:
                            break
                    
                    if title_elem and company_elem:
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'location': location_elem.get_text(strip=True) if location_elem else location,
                            'job_url': f"https://www.dice.com{title_elem.get('href', '')}" if title_elem.get('href') else '',
                            'description': 'Job description available on Dice',
                            'company_url': '',
                            'source': 'Dice'
                        }
                        jobs.append(job)
                except Exception as e:
                    print(f"Error parsing Dice job card: {e}")
                    continue
                    
        time.sleep(random.uniform(2, 4))  # Rate limiting
    except Exception as e:
        print(f"Error scraping Dice: {e}")
    
    return jobs

def scrape_google_jobs(search_term: str, location: str, num_results: int = 20) -> List[dict]:
    """Scrape jobs from Google Jobs"""
    jobs = []
    try:
        # Google Jobs search URL
        base_url = "https://www.google.com/search"
        params = {
            'q': f'{search_term} jobs in {location}',
            'ibp': 'htl;jobs',
            'sa': 'X'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for Google Jobs
            job_selectors = [
                'div[data-ved]',
                'div.g',
                'div[data-testid="job-card"]',
                'div.job-card'
            ]
            
            job_cards = []
            for selector in job_selectors:
                job_cards = soup.select(selector)
                if job_cards:
                    break
            
            for card in job_cards[:num_results]:
                try:
                    # Try multiple title selectors
                    title_selectors = ['h3', 'h2', 'a[data-testid="job-title"]', 'h3 a', 'h2 a']
                    title_elem = None
                    for selector in title_selectors:
                        title_elem = card.select_one(selector)
                        if title_elem:
                            break
                    
                    # Try multiple company selectors
                    company_selectors = ['div.VfPpkd-rymPhb-ibnC6b', 'span.company', 'div[data-testid="company-name"]', 'div.company-name']
                    company_elem = None
                    for selector in company_selectors:
                        company_elem = card.select_one(selector)
                        if company_elem:
                            break
                    
                    # Try multiple location selectors
                    location_selectors = ['div.VfPpkd-rymPhb-fpDzbe-fmcmS', 'span.location', 'div[data-testid="job-location"]', 'div.job-location']
                    location_elem = None
                    for selector in location_selectors:
                        location_elem = card.select_one(selector)
                        if location_elem:
                            break
                    
                    if title_elem and company_elem:
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'location': location_elem.get_text(strip=True) if location_elem else location,
                            'job_url': title_elem.get('href', '') if title_elem.get('href') else '',
                            'description': 'Job description available on Google Jobs',
                            'company_url': '',
                            'source': 'Google Jobs'
                        }
                        jobs.append(job)
                except Exception as e:
                    print(f"Error parsing Google Jobs card: {e}")
                    continue
                    
        time.sleep(random.uniform(2, 4))  # Rate limiting
    except Exception as e:
        print(f"Error scraping Google Jobs: {e}")
    
    return jobs

def scrape_hiring_cafe_jobs(search_term: str, location: str, num_results: int = 20) -> List[dict]:
    """Scrape jobs from Hiring Cafe"""
    jobs = []
    try:
        # Hiring Cafe search URL
        base_url = "https://www.hiringcafe.com/jobs"
        params = {
            'search': search_term,
            'location': location
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        response = session.get(base_url, params=params, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for Hiring Cafe
            job_selectors = [
                'div.job-item',
                'div[data-testid="job-card"]',
                'div.job-card',
                'div[data-job-id]',
                'article[data-job-id]'
            ]
            
            job_cards = []
            for selector in job_selectors:
                job_cards = soup.select(selector)
                if job_cards:
                    break
            
            for card in job_cards[:num_results]:
                try:
                    # Try multiple title selectors
                    title_selectors = ['h3.job-title', 'h2.job-title', 'a[data-testid="job-title"]', 'h3 a', 'h2 a']
                    title_elem = None
                    for selector in title_selectors:
                        title_elem = card.select_one(selector)
                        if title_elem:
                            break
                    
                    # Try multiple company selectors
                    company_selectors = ['div.company-name', 'span.company-name', 'div[data-testid="company-name"]', 'div.company']
                    company_elem = None
                    for selector in company_selectors:
                        company_elem = card.select_one(selector)
                        if company_elem:
                            break
                    
                    # Try multiple location selectors
                    location_selectors = ['div.job-location', 'span.job-location', 'div[data-testid="job-location"]', 'div.location']
                    location_elem = None
                    for selector in location_selectors:
                        location_elem = card.select_one(selector)
                        if location_elem:
                            break
                    
                    if title_elem and company_elem:
                        job = {
                            'title': title_elem.get_text(strip=True),
                            'company': company_elem.get_text(strip=True),
                            'location': location_elem.get_text(strip=True) if location_elem else location,
                            'job_url': f"https://www.hiringcafe.com{title_elem.get('href', '')}" if title_elem.get('href') else '',
                            'description': 'Job description available on Hiring Cafe',
                            'company_url': '',
                            'source': 'Hiring Cafe'
                        }
                        jobs.append(job)
                except Exception as e:
                    print(f"Error parsing Hiring Cafe job card: {e}")
                    continue
                    
        time.sleep(random.uniform(2, 4))  # Rate limiting
    except Exception as e:
        print(f"Error scraping Hiring Cafe: {e}")
    
    return jobs

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
        
        location = request.location if request.location else "United States"
        optimized_results = request.num_results  # No cap - use full requested results
        
        all_jobs = []
        
        # 1. Scrape from multiple platforms using jobspy
        print(f"🔍 Scraping jobs from multiple platforms using jobspy...")
        
        # Define platforms to scrape (optimized for more results)
        platforms = [
            {"name": "linkedin", "display": "LinkedIn"},
            {"name": "indeed", "display": "Indeed"},
            {"name": "glassdoor", "display": "Glassdoor"}
        ]
        
        # Use only the requested location for faster scraping
        locations_to_try = [location] if location else ["United States"]
        
        for platform in platforms:
            platform_jobs_found = 0
            
            # Use only the primary location for maximum speed
            for loc in locations_to_try[:1]:
                try:
                    print(f"🔍 Scraping {platform['display']} jobs in {loc}...")
                    
                    # Prepare search parameters
                    search_params = {
                        "site_name": [platform["name"]],
                        "search_term": search_term,
                        "location": loc,
                            "results_wanted": min(optimized_results, 25),  # Increased to get more jobs (25 per platform = 75 total)
                        "hours_old": request.posted_within_days * 24,
                        "country_indeed": "us"
                    }
                    
                    # Add platform-specific parameters
                    if platform["name"] == "linkedin":
                        search_params["linkedin_fetch_description"] = True
                    elif platform["name"] == "glassdoor":
                        search_params["glassdoor_fetch_description"] = True
                    elif platform["name"] == "google":
                        search_params["google_search_term"] = f"{search_term} jobs in {loc}"
                    
                    # Scrape jobs
                    jobs_df = scrape_jobs(**search_params)
                    
                    if len(jobs_df) > 0:
                        print(f"✅ Scraped {len(jobs_df)} jobs from {platform['display']} in {loc}")
                        platform_jobs_found += len(jobs_df)
                        
                        # Convert jobs to our format
                        for _, row in jobs_df.iterrows():
                            # Clean up NaN values
                            company = row.get('company', '')
                            if pd.isna(company) or company == '' or str(company).lower() == 'nan':
                                company = 'Company Not Specified'
                            
                            title = row.get('title', '')
                            if pd.isna(title) or title == '' or str(title).lower() == 'nan':
                                title = 'Job Title Not Specified'
                            
                            job = {
                                'title': str(title),
                                'company': str(company),
                                'location': str(row.get('location', loc)),
                                'job_url': str(row.get('job_url', '')),
                                'description': str(row.get('description', f'Job description available on {platform["display"]}')),
                                'company_url': str(row.get('company_url', '')),
                                'source': platform['display']  # Use our platform name
                            }
                            all_jobs.append(job)
                    else:
                        print(f"⚠️ No jobs found from {platform['display']} in {loc}")
                        
                except Exception as e:
                    print(f"⚠️ {platform['display']} scraping failed for {loc}: {e}")
                    continue
            
            if platform_jobs_found == 0:
                print(f"❌ No jobs found from {platform['display']} in any location")
        
        # 2. If we have less than 40 jobs, try additional searches to get more results
        print(f"✅ Primary job search completed with {len(all_jobs)} jobs")
        
        # If we have less than 40 jobs, try additional searches
        if len(all_jobs) < 40:
            print(f"🔍 Only {len(all_jobs)} jobs found, trying additional searches to reach 40+ jobs...")
            
            # Try with different search terms
            additional_terms = [
                f"{search_term} developer",
                f"{search_term} engineer", 
                "software engineer",
                "developer"
            ]
            
            for term in additional_terms[:2]:  # Try 2 additional terms
                if len(all_jobs) >= 40:
                    break
                    
                try:
                    print(f"🔍 Trying additional search with term: '{term}'...")
                    
                    # Try all platforms with the additional term
                    additional_jobs = scrape_jobs(
                        site_name=["linkedin", "indeed", "glassdoor"],
                        search_term=term,
                        location=location,
                        results_wanted=min(15, 40 - len(all_jobs)),  # Only get what we need
                        hours_old=request.posted_within_days * 24,
                        country_indeed="us",
                        linkedin_fetch_description=True,
                        glassdoor_fetch_description=True
                    )
                    
                    if len(additional_jobs) > 0:
                        print(f"✅ Found {len(additional_jobs)} additional jobs with term '{term}'")
                        
                        for _, row in additional_jobs.iterrows():
                            company = row.get('company', '')
                            if pd.isna(company) or company == '' or str(company).lower() == 'nan':
                                company = 'Company Not Specified'
                            
                            title = row.get('title', '')
                            if pd.isna(title) or title == '' or str(title).lower() == 'nan':
                                title = 'Job Title Not Specified'
                            
                            # Check if this job is already in our list (avoid duplicates)
                            job_exists = any(
                                existing_job['title'] == str(title) and existing_job['company'] == str(company)
                                for existing_job in all_jobs
                            )
                            
                            if not job_exists:
                                job = {
                                    'title': str(title),
                                    'company': str(company),
                                    'location': str(row.get('location', location)),
                                    'job_url': str(row.get('job_url', '')),
                                    'description': str(row.get('description', f'Job description available on {row.get("source", "job board")}')),
                                    'company_url': str(row.get('company_url', '')),
                                    'source': str(row.get('source', 'Additional Search'))
                                }
                                all_jobs.append(job)
                                
                                if len(all_jobs) >= 40:
                                    break
                    
                except Exception as e:
                    print(f"⚠️ Additional search with term '{term}' failed: {e}")
                    continue
        
        # If no jobs found from scraping, try one more time with broader search
        if not all_jobs:
            print("⚠️ No jobs found from scraping, trying broader search...")
            try:
                # Try with a very broad search term
                broad_jobs = scrape_jobs(
                    site_name=["linkedin", "indeed", "glassdoor"],
                    search_term="software",
                    location=location,
                    results_wanted=30,
                    hours_old=request.posted_within_days * 24,
                    country_indeed="us",
                    linkedin_fetch_description=True,
                    glassdoor_fetch_description=True
                )
                
                if len(broad_jobs) > 0:
                    print(f"✅ Found {len(broad_jobs)} jobs with broader search")
                    
                    for _, row in broad_jobs.iterrows():
                        company = row.get('company', '')
                        if pd.isna(company) or company == '' or str(company).lower() == 'nan':
                            company = 'Company Not Specified'
                        
                        title = row.get('title', '')
                        if pd.isna(title) or title == '' or str(title).lower() == 'nan':
                            title = 'Job Title Not Specified'
                        
                        # Map the site to proper platform name
                        site_name = str(row.get('site', 'Unknown')).lower()
                        if 'linkedin' in site_name:
                            platform_name = 'LinkedIn'
                        elif 'indeed' in site_name:
                            platform_name = 'Indeed'
                        elif 'glassdoor' in site_name:
                            platform_name = 'Glassdoor'
                        elif 'ziprecruiter' in site_name or 'zip_recruiter' in site_name:
                            platform_name = 'ZipRecruiter'
                        elif 'google' in site_name:
                            platform_name = 'Google Jobs'
                        else:
                            platform_name = 'Unknown'
                        
                        job = {
                            'title': str(title),
                            'company': str(company),
                            'location': str(row.get('location', location)),
                            'job_url': str(row.get('job_url', '')),
                            'description': str(row.get('description', 'Job description available')),
                            'company_url': str(row.get('company_url', '')),
                            'source': platform_name
                        }
                        all_jobs.append(job)
                else:
                    print("❌ No jobs found even with broader search")
                    
            except Exception as e:
                print(f"❌ Broader search also failed: {e}")
        
        # Filter for remote jobs if requested
        if request.remote_only:
            all_jobs = [job for job in all_jobs if 'remote' in job['location'].lower()]
        
        # Remove duplicates based on job_url
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            if job['job_url'] and job['job_url'] not in seen_urls:
                seen_urls.add(job['job_url'])
                unique_jobs.append(job)
        
        # No limit on final results - return all unique jobs found
        # unique_jobs = unique_jobs[:min(len(unique_jobs), 40)]  # Removed limit
        
        print(f"🎯 Total unique jobs found: {len(unique_jobs)}")
        
        # Convert to list of JobResponse objects
        jobs = []
        for job_data in unique_jobs:
            # Check if job already exists in database
            existing_job = db.query(Job).filter(Job.job_url == job_data['job_url']).first()
            
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
                    title=job_data['title'],
                    company=job_data['company'],
                    location=job_data['location'],
                    description=job_data['description'],
                    job_url=job_data['job_url'],
                    company_url=job_data['company_url'],
                    source=job_data['source'],
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
