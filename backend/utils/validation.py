"""
Enhanced validation utilities for QuantiPeak platform
"""

import re
import email_validator
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, validator, Field
import magic
from .logger import logger

class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(message)

class FileValidator:
    """File validation utility"""
    
    ALLOWED_EXTENSIONS = {'.pdf', '.docx'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_MIME_TYPES = {
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    }
    
    @classmethod
    def validate_file(cls, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Validate uploaded file"""
        errors = []
        
        # Check file size
        if len(file_content) > cls.MAX_FILE_SIZE:
            errors.append(f"File size exceeds {cls.MAX_FILE_SIZE / (1024*1024):.1f}MB limit")
        
        # Check file extension
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        if file_ext not in cls.ALLOWED_EXTENSIONS:
            errors.append(f"File extension '{file_ext}' not allowed. Allowed: {', '.join(cls.ALLOWED_EXTENSIONS)}")
        
        # Check MIME type
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
            if mime_type not in cls.ALLOWED_MIME_TYPES:
                errors.append(f"File type '{mime_type}' not allowed")
        except Exception as e:
            logger.warning(f"Could not detect MIME type: {e}")
            # Fallback to extension check
            if file_ext not in cls.ALLOWED_EXTENSIONS:
                errors.append("Invalid file type")
        
        # Check if file is not empty
        if len(file_content) == 0:
            errors.append("File is empty")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'file_size': len(file_content),
            'mime_type': mime_type if 'mime_type' in locals() else None
        }

class EmailValidator:
    """Email validation utility"""
    
    @classmethod
    def validate_email(cls, email: str) -> Dict[str, Any]:
        """Validate email address"""
        try:
            # Use email-validator library
            email_validator.validate_email(email)
            return {'valid': True, 'email': email}
        except email_validator.EmailNotValidError as e:
            return {'valid': False, 'error': str(e)}
        except Exception as e:
            return {'valid': False, 'error': f"Email validation failed: {str(e)}"}

class PhoneValidator:
    """Phone number validation utility"""
    
    PHONE_PATTERNS = [
        r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$',  # US format
        r'^\+?[1-9]\d{1,14}$',  # International format
        r'^\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$',  # Simple US format
    ]
    
    @classmethod
    def validate_phone(cls, phone: str) -> Dict[str, Any]:
        """Validate phone number"""
        if not phone or not phone.strip():
            return {'valid': True, 'phone': ''}  # Empty phone is valid
        
        phone = phone.strip()
        
        for pattern in cls.PHONE_PATTERNS:
            if re.match(pattern, phone):
                return {'valid': True, 'phone': phone}
        
        return {'valid': False, 'error': 'Invalid phone number format'}

class URLValidator:
    """URL validation utility"""
    
    @classmethod
    def validate_url(cls, url: str) -> Dict[str, Any]:
        """Validate URL"""
        if not url or not url.strip():
            return {'valid': True, 'url': ''}  # Empty URL is valid
        
        url = url.strip()
        
        # Basic URL pattern
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if url_pattern.match(url):
            return {'valid': True, 'url': url}
        
        return {'valid': False, 'error': 'Invalid URL format'}

class ResumeDataValidator:
    """Resume data validation utility"""
    
    @classmethod
    def validate_resume_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parsed resume data"""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['name', 'contact_info']
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Validate name
        if 'name' in data and data['name']:
            name = data['name'].strip()
            if len(name) < 2:
                errors.append("Name must be at least 2 characters long")
            elif len(name) > 100:
                errors.append("Name must be less than 100 characters")
            elif not re.match(r'^[a-zA-Z\s\-\.]+$', name):
                warnings.append("Name contains unusual characters")
        
        # Validate contact info
        if 'contact_info' in data and data['contact_info']:
            contact_info = data['contact_info']
            
            # Validate email
            if 'email' in contact_info and contact_info['email']:
                email_validation = EmailValidator.validate_email(contact_info['email'])
                if not email_validation['valid']:
                    errors.append(f"Invalid email: {email_validation['error']}")
            
            # Validate phone
            if 'phone' in contact_info and contact_info['phone']:
                phone_validation = PhoneValidator.validate_phone(contact_info['phone'])
                if not phone_validation['valid']:
                    errors.append(f"Invalid phone: {phone_validation['error']}")
            
            # Validate LinkedIn URL
            if 'linkedin' in contact_info and contact_info['linkedin']:
                linkedin_url = contact_info['linkedin']
                if not linkedin_url.startswith('http'):
                    linkedin_url = 'https://' + linkedin_url
                
                url_validation = URLValidator.validate_url(linkedin_url)
                if not url_validation['valid']:
                    warnings.append(f"Invalid LinkedIn URL: {url_validation['error']}")
                elif 'linkedin.com' not in linkedin_url.lower():
                    warnings.append("LinkedIn URL doesn't appear to be a LinkedIn profile")
        
        # Validate skills
        if 'skills' in data and data['skills']:
            skills = data['skills']
            if not isinstance(skills, list):
                errors.append("Skills must be a list")
            elif len(skills) == 0:
                warnings.append("No skills found in resume")
            elif len(skills) > 50:
                warnings.append("Unusually high number of skills found")
        
        # Validate experience
        if 'experience' in data and data['experience']:
            experience = data['experience']
            if not isinstance(experience, list):
                errors.append("Experience must be a list")
            else:
                for i, exp in enumerate(experience):
                    if not isinstance(exp, dict):
                        errors.append(f"Experience item {i+1} must be a dictionary")
                        continue
                    
                    required_exp_fields = ['title', 'company']
                    for field in required_exp_fields:
                        if field not in exp or not exp[field]:
                            errors.append(f"Experience item {i+1} missing {field}")
        
        # Validate education
        if 'education' in data and data['education']:
            education = data['education']
            if not isinstance(education, list):
                errors.append("Education must be a list")
            elif len(education) == 0:
                warnings.append("No education found in resume")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'has_warnings': len(warnings) > 0
        }

class JobSearchValidator:
    """Job search validation utility"""
    
    @classmethod
    def validate_job_search_request(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate job search request"""
        errors = []
        
        # Validate job titles
        if 'job_titles' not in data or not data['job_titles']:
            errors.append("Job titles are required")
        else:
            job_titles = data['job_titles']
            if not isinstance(job_titles, list):
                errors.append("Job titles must be a list")
            elif len(job_titles) == 0:
                errors.append("At least one job title is required")
            elif len(job_titles) > 10:
                errors.append("Maximum 10 job titles allowed")
            else:
                for i, title in enumerate(job_titles):
                    if not isinstance(title, str) or not title.strip():
                        errors.append(f"Job title {i+1} must be a non-empty string")
                    elif len(title.strip()) > 100:
                        errors.append(f"Job title {i+1} is too long (max 100 characters)")
        
        # Validate location
        if 'location' not in data or not data['location']:
            errors.append("Location is required")
        else:
            location = data['location']
            if not isinstance(location, str) or not location.strip():
                errors.append("Location must be a non-empty string")
            elif len(location.strip()) > 100:
                errors.append("Location is too long (max 100 characters)")
        
        # Validate optional fields
        if 'remote_only' in data and not isinstance(data['remote_only'], bool):
            errors.append("remote_only must be a boolean")
        
        if 'posted_within_days' in data:
            days = data['posted_within_days']
            if not isinstance(days, int) or days < 1 or days > 30:
                errors.append("posted_within_days must be between 1 and 30")
        
        if 'num_results' in data:
            num_results = data['num_results']
            if not isinstance(num_results, int) or num_results < 1 or num_results > 100:
                errors.append("num_results must be between 1 and 100")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

# Convenience functions
def validate_file(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Validate uploaded file"""
    return FileValidator.validate_file(file_content, filename)

def validate_email(email: str) -> Dict[str, Any]:
    """Validate email address"""
    return EmailValidator.validate_email(email)

def validate_phone(phone: str) -> Dict[str, Any]:
    """Validate phone number"""
    return PhoneValidator.validate_phone(phone)

def validate_url(url: str) -> Dict[str, Any]:
    """Validate URL"""
    return URLValidator.validate_url(url)

def validate_resume_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate resume data"""
    return ResumeDataValidator.validate_resume_data(data)

def validate_job_search_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate job search request"""
    return JobSearchValidator.validate_job_search_request(data)
