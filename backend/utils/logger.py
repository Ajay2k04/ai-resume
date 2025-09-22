"""
Enhanced logging utility for QuantiPeak platform
"""

import logging
import sys
from datetime import datetime
from typing import Optional
import json
import traceback

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        return super().format(record)

class QuantiPeakLogger:
    """Enhanced logger for QuantiPeak platform"""
    
    def __init__(self, name: str = "quantipeak", level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console and file handlers"""
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler
        file_handler = logging.FileHandler('quantipeak.log')
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(self._format_message(message, **kwargs))
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(self._format_message(message, **kwargs))
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(self._format_message(message, **kwargs))
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message with optional exception"""
        if exception:
            kwargs['exception'] = str(exception)
            kwargs['traceback'] = traceback.format_exc()
        
        self.logger.error(self._format_message(message, **kwargs))
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message with optional exception"""
        if exception:
            kwargs['exception'] = str(exception)
            kwargs['traceback'] = traceback.format_exc()
        
        self.logger.critical(self._format_message(message, **kwargs))
    
    def _format_message(self, message: str, **kwargs) -> str:
        """Format message with additional context"""
        if not kwargs:
            return message
        
        context = json.dumps(kwargs, indent=2, default=str)
        return f"{message}\nContext: {context}"
    
    def log_api_request(self, method: str, endpoint: str, status_code: int, 
                       response_time: float, user_id: Optional[str] = None):
        """Log API request details"""
        self.info(
            f"API Request: {method} {endpoint}",
            status_code=status_code,
            response_time_ms=round(response_time * 1000, 2),
            user_id=user_id
        )
    
    def log_resume_parsing(self, filename: str, file_size: int, 
                          parsing_time: float, success: bool, 
                          extracted_fields: dict):
        """Log resume parsing details"""
        level = "info" if success else "error"
        getattr(self, level)(
            f"Resume Parsing: {filename}",
            file_size_bytes=file_size,
            parsing_time_ms=round(parsing_time * 1000, 2),
            success=success,
            extracted_fields=extracted_fields
        )
    
    def log_job_scraping(self, platform: str, search_term: str, 
                        jobs_found: int, scraping_time: float):
        """Log job scraping details"""
        self.info(
            f"Job Scraping: {platform}",
            search_term=search_term,
            jobs_found=jobs_found,
            scraping_time_ms=round(scraping_time * 1000, 2)
        )
    
    def log_ai_generation(self, content_type: str, generation_time: float, 
                         success: bool, tokens_used: Optional[int] = None):
        """Log AI generation details"""
        level = "info" if success else "error"
        getattr(self, level)(
            f"AI Generation: {content_type}",
            generation_time_ms=round(generation_time * 1000, 2),
            success=success,
            tokens_used=tokens_used
        )

# Global logger instance
logger = QuantiPeakLogger()

# Convenience functions
def log_info(message: str, **kwargs):
    logger.info(message, **kwargs)

def log_error(message: str, exception: Optional[Exception] = None, **kwargs):
    logger.error(message, exception, **kwargs)

def log_warning(message: str, **kwargs):
    logger.warning(message, **kwargs)

def log_debug(message: str, **kwargs):
    logger.debug(message, **kwargs)
