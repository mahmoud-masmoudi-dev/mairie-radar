"""
Core configuration module for Mairie Radar.

This module handles all configuration settings using Pydantic Settings
for type safety and validation.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Main configuration class for Mairie Radar."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Core Application Settings
    app_name: str = Field(default="mairie-radar", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(default="development", description="Environment (development/production)")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_reload: bool = Field(default=True, description="API auto-reload")
    
    # LLM Configuration
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229", description="Anthropic model")
    google_api_key: Optional[str] = Field(default=None, description="Google Gemini API key")
    google_model: str = Field(default="gemini-2.0-flash-exp", description="Google Gemini model")
    
    # Vector Store Configuration (Weaviate)
    weaviate_url: Optional[str] = Field(default=None, description="Weaviate cluster URL")
    weaviate_api_key: Optional[str] = Field(default=None, description="Weaviate API key")
    weaviate_class_name: str = Field(default="BudgetDocument", description="Weaviate class name")
    
    # Data Sources Configuration
    data_gouv_api_url: str = Field(
        default="https://www.data.gouv.fr/api/1", 
        description="data.gouv.fr API URL"
    )
    data_gouv_api_key: Optional[str] = Field(default=None, description="data.gouv.fr API key")
    
    # Web Scraping Settings
    scraper_user_agent: str = Field(
        default="MairieRadar/1.0", 
        description="User agent for web scraping"
    )
    scraper_delay: int = Field(default=1, description="Delay between scraping requests")
    scraper_timeout: int = Field(default=30, description="Scraping timeout in seconds")
    scraper_max_retries: int = Field(default=3, description="Maximum scraping retries")
    
    # File Storage Configuration
    data_dir: str = Field(default="./data", description="Data directory")
    documents_dir: str = Field(default="./data/documents", description="Documents directory")
    cache_dir: str = Field(default="./data/cache", description="Cache directory")
    logs_dir: str = Field(default="./data/logs", description="Logs directory")
    
    # Security Configuration
    secret_key: str = Field(
        default="your_secret_key_here_change_in_production", 
        description="Secret key for JWT"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(default=60, description="JWT expiration in minutes")
    
    # Feature Flags
    enable_anomaly_detection: bool = Field(default=True, description="Enable anomaly detection")
    enable_real_time_collection: bool = Field(default=False, description="Enable real-time collection")
    enable_batch_processing: bool = Field(default=True, description="Enable batch processing")
    enable_web_scraping: bool = Field(default=True, description="Enable web scraping")
    enable_pdf_processing: bool = Field(default=True, description="Enable PDF processing")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per window")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")
    
    # Development Settings
    use_mock_data: bool = Field(default=False, description="Use mock data instead of real APIs")
    mock_delay: float = Field(default=0.5, description="Mock delay in seconds")
    verbose_logging: bool = Field(default=True, description="Enable verbose logging")
    enable_docs: bool = Field(default=True, description="Enable API documentation")
    
    def get_llm_config(self) -> dict:
        """Get LLM configuration based on available API keys."""
        if self.google_api_key:
            return {
                "provider": "google",
                "api_key": self.google_api_key,
                "model": self.google_model
            }
        elif self.openai_api_key:
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model
            }
        elif self.anthropic_api_key:
            return {
                "provider": "anthropic", 
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model
            }
        else:
            raise ValueError("No LLM API key provided. Please set GOOGLE_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY")
    
    def get_weaviate_config(self) -> dict:
        """Get Weaviate configuration."""
        if not self.weaviate_url:
            raise ValueError("WEAVIATE_URL is required")
        
        config = {
            "url": self.weaviate_url,
            "class_name": self.weaviate_class_name
        }
        
        if self.weaviate_api_key:
            config["api_key"] = self.weaviate_api_key
            
        return config


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings 