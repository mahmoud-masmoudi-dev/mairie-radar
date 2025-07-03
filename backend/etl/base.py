"""
Base classes for the ETL (Extract, Transform, Load) layer.

This module defines abstract base classes and interfaces for data collection,
processing, and loading operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

from ..core.logging import get_logger


@dataclass
class BudgetDocument:
    """Represents a budget document with metadata."""
    
    city_name: str
    year: int
    category: str
    amount: float
    document_url: str
    extracted_text: str
    metadata: Dict[str, Any]
    source_type: str  # 'pdf', 'csv', 'json', 'web'
    collection_date: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'city_name': self.city_name,
            'year': self.year,
            'category': self.category,
            'amount': self.amount,
            'document_url': self.document_url,
            'extracted_text': self.extracted_text,
            'metadata': self.metadata,
            'source_type': self.source_type,
            'collection_date': self.collection_date,
        }


class BaseCollector(ABC):
    """Abstract base class for data collectors."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"collector.{name}")
    
    @abstractmethod
    async def collect(self, **kwargs) -> List[BudgetDocument]:
        """Collect budget documents from a source."""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate collector configuration."""
        pass


class BaseParser(ABC):
    """Abstract base class for document parsers."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"parser.{name}")
    
    @abstractmethod
    async def parse(self, document_path: Path, **kwargs) -> List[BudgetDocument]:
        """Parse a document and extract budget data."""
        pass
    
    @abstractmethod
    def supports_format(self, file_path: Path) -> bool:
        """Check if parser supports the given file format."""
        pass


class BaseValidator(ABC):
    """Abstract base class for data validators."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"validator.{name}")
    
    @abstractmethod
    async def validate(self, document: BudgetDocument) -> bool:
        """Validate a budget document."""
        pass
    
    @abstractmethod
    def get_validation_errors(self, document: BudgetDocument) -> List[str]:
        """Get validation errors for a document."""
        pass


class BaseLoader(ABC):
    """Abstract base class for data loaders."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = get_logger(f"loader.{name}")
    
    @abstractmethod
    async def load(self, documents: List[BudgetDocument]) -> bool:
        """Load documents into storage."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if loader is healthy and ready."""
        pass


class ETLPipeline:
    """Main ETL pipeline coordinator."""
    
    def __init__(self):
        self.logger = get_logger("etl.pipeline")
        self.collectors: List[BaseCollector] = []
        self.parsers: List[BaseParser] = []
        self.validators: List[BaseValidator] = []
        self.loaders: List[BaseLoader] = []
    
    def add_collector(self, collector: BaseCollector) -> None:
        """Add a collector to the pipeline."""
        self.collectors.append(collector)
        self.logger.info(f"Added collector: {collector.name}")
    
    def add_parser(self, parser: BaseParser) -> None:
        """Add a parser to the pipeline."""
        self.parsers.append(parser)
        self.logger.info(f"Added parser: {parser.name}")
    
    def add_validator(self, validator: BaseValidator) -> None:
        """Add a validator to the pipeline."""
        self.validators.append(validator)
        self.logger.info(f"Added validator: {validator.name}")
    
    def add_loader(self, loader: BaseLoader) -> None:
        """Add a loader to the pipeline."""
        self.loaders.append(loader)
        self.logger.info(f"Added loader: {loader.name}")
    
    async def run(self, **kwargs) -> Dict[str, Any]:
        """Run the complete ETL pipeline."""
        self.logger.info("Starting ETL pipeline")
        
        results = {
            'collected': 0,
            'parsed': 0,
            'validated': 0,
            'loaded': 0,
            'errors': []
        }
        
        try:
            # Collection phase
            all_documents = []
            for collector in self.collectors:
                try:
                    documents = await collector.collect(**kwargs)
                    all_documents.extend(documents)
                    results['collected'] += len(documents)
                    self.logger.info(f"Collected {len(documents)} documents from {collector.name}")
                except Exception as e:
                    error_msg = f"Collection failed for {collector.name}: {str(e)}"
                    results['errors'].append(error_msg)
                    self.logger.error(error_msg)
            
            # Validation phase
            validated_documents = []
            for document in all_documents:
                is_valid = True
                for validator in self.validators:
                    try:
                        if not await validator.validate(document):
                            is_valid = False
                            errors = validator.get_validation_errors(document)
                            results['errors'].extend(errors)
                            break
                    except Exception as e:
                        error_msg = f"Validation failed for {validator.name}: {str(e)}"
                        results['errors'].append(error_msg)
                        is_valid = False
                        break
                
                if is_valid:
                    validated_documents.append(document)
                    results['validated'] += 1
            
            # Loading phase
            for loader in self.loaders:
                try:
                    if await loader.load(validated_documents):
                        results['loaded'] += len(validated_documents)
                        self.logger.info(f"Loaded {len(validated_documents)} documents via {loader.name}")
                    else:
                        error_msg = f"Loading failed for {loader.name}"
                        results['errors'].append(error_msg)
                except Exception as e:
                    error_msg = f"Loading failed for {loader.name}: {str(e)}"
                    results['errors'].append(error_msg)
                    self.logger.error(error_msg)
            
            self.logger.info("ETL pipeline completed", **results)
            return results
            
        except Exception as e:
            error_msg = f"ETL pipeline failed: {str(e)}"
            results['errors'].append(error_msg)
            self.logger.error(error_msg)
            return results 