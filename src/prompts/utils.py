"""
Advanced Prompt Management System for the Agentic Ecosystem.
Implements Factory, Singleton, and Lazy Loading patterns for efficient prompt handling.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import lru_cache
import logging
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class PromptMetadata:
    """Metadata for prompt templates."""
    name: str
    description: str
    version: str
    required_params: List[str]
    optional_params: List[str]
    category: str


class PromptTemplate:
    """Represents a prompt template with metadata and formatting capabilities."""
    
    def __init__(self, content: Union[str, Dict[str, Any]], metadata: Optional[PromptMetadata] = None):
        self.content = content
        self.metadata = metadata
        self._compiled_template = None
    
    def format(self, **kwargs) -> str:
        """Format the prompt template with provided variables."""
        try:
            if isinstance(self.content, dict):
                # Handle complex prompt structures
                return self._format_complex_prompt(**kwargs)
            else:
                # Simple string template
                return str(self.content).format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required parameter: {e}")
        except Exception as e:
            logger.error(f"Error formatting prompt: {e}")
            raise
    
    def _format_complex_prompt(self, **kwargs) -> str:
        """Format complex nested prompt structures."""
        if isinstance(self.content, str):
            return str(self.content).format(**kwargs)
        elif 'content' in self.content:
            # Handle new structure with content field
            return str(self.content['content']).format(**kwargs)
        elif 'system' in self.content and 'template' in self.content:
            system_part = str(self.content['system']).format(**kwargs)
            template_part = str(self.content['template']).format(**kwargs)
            return f"{system_part}\n\n{template_part}"
        elif 'system' in self.content and 'process' in self.content and 'template' in self.content:
            # Chain of thought structure
            system_part = str(self.content['system']).format(**kwargs)
            process_part = str(self.content['process']).format(**kwargs)
            template_part = str(self.content['template']).format(**kwargs)
            return f"{system_part}\n\n{process_part}\n\n{template_part}"
        else:
            # Join all string values
            parts = [str(v).format(**kwargs) for v in self.content.values() if isinstance(v, str)]
            return "\n\n".join(parts)
    
    def validate_params(self, **kwargs) -> bool:
        """Validate that all required parameters are provided."""
        if not self.metadata:
            return True
        
        provided_params = set(kwargs.keys())
        required_params = set(self.metadata.required_params)
        
        missing_params = required_params - provided_params
        if missing_params:
            raise ValueError(f"Missing required parameters: {missing_params}")
        
        return True


class PromptLoader(ABC):
    """Abstract base class for prompt loaders."""
    
    @abstractmethod
    def load(self, file_path: Path) -> Dict[str, Any]:
        """Load prompts from a file."""
        pass
    
    @abstractmethod
    def supports_extension(self, extension: str) -> bool:
        """Check if this loader supports the given file extension."""
        pass


class JSONPromptLoader(PromptLoader):
    """Loader for JSON prompt files."""
    
    def load(self, file_path: Path) -> Dict[str, Any]:
        """Load prompts from a JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def supports_extension(self, extension: str) -> bool:
        """Check if this loader supports JSON files."""
        return extension.lower() == '.json'


class YAMLPromptLoader(PromptLoader):
    """Loader for YAML prompt files."""
    
    def load(self, file_path: Path) -> Dict[str, Any]:
        """Load prompts from a YAML file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def supports_extension(self, extension: str) -> bool:
        """Check if this loader supports YAML files."""
        return extension.lower() in ['.yaml', '.yml']


class PromptLoaderFactory:
    """Factory for creating appropriate prompt loaders."""
    
    _loaders = [
        JSONPromptLoader(),
        YAMLPromptLoader(),
    ]
    
    @classmethod
    def get_loader(cls, file_path: Path) -> Optional[PromptLoader]:
        """Get the appropriate loader for a file."""
        extension = file_path.suffix
        for loader in cls._loaders:
            if loader.supports_extension(extension):
                return loader
        return None
    
    @classmethod
    def register_loader(cls, loader: PromptLoader):
        """Register a new prompt loader."""
        cls._loaders.append(loader)


class PromptRegistry:
    """Thread-safe registry for managing prompt templates with caching."""
    
    def __init__(self):
        self._prompts: Dict[str, Dict[str, PromptTemplate]] = {}
        self._metadata: Dict[str, Dict[str, PromptMetadata]] = {}
        self._lock = Lock()
        self._loaded_files: Dict[Path, float] = {}  # file_path -> modification_time
    
    def register_prompt(self, agent_name: str, prompt_name: str, template: PromptTemplate):
        """Register a prompt template."""
        with self._lock:
            if agent_name not in self._prompts:
                self._prompts[agent_name] = {}
                self._metadata[agent_name] = {}
            
            self._prompts[agent_name][prompt_name] = template
            if template.metadata:
                self._metadata[agent_name][prompt_name] = template.metadata
    
    def get_prompt(self, agent_name: str, prompt_name: str) -> Optional[PromptTemplate]:
        """Get a prompt template."""
        with self._lock:
            return self._prompts.get(agent_name, {}).get(prompt_name)
    
    def list_agents(self) -> List[str]:
        """List all registered agents."""
        with self._lock:
            return list(self._prompts.keys())
    
    def list_prompts(self, agent_name: str) -> List[str]:
        """List all prompts for an agent."""
        with self._lock:
            return list(self._prompts.get(agent_name, {}).keys())
    
    def get_metadata(self, agent_name: str, prompt_name: str) -> Optional[PromptMetadata]:
        """Get prompt metadata."""
        with self._lock:
            return self._metadata.get(agent_name, {}).get(prompt_name)


class PromptManager:
    """
    Main prompt manager implementing Singleton pattern with lazy loading and caching.
    Provides efficient prompt management with auto-reload capabilities.
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls, prompt_dir: Optional[Path] = None):
        """Singleton implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, prompt_dir: Optional[Path] = None):
        """Initialize the prompt manager."""
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self.prompt_dir = prompt_dir or Path(__file__).parent
        self.registry = PromptRegistry()
        self.loader_factory = PromptLoaderFactory()
        self._auto_reload = True
        self._initialized = True
        
        # Load all prompts on initialization
        self._load_all_prompts()
    
    def _load_all_prompts(self):
        """Load all prompt files from the prompts directory."""
        try:
            prompt_files = []
            for pattern in ['*.json', '*.yaml', '*.yml']:
                prompt_files.extend(self.prompt_dir.glob(pattern))
            
            for prompt_file in prompt_files:
                self._load_prompt_file(prompt_file)
            
            logger.info(f"Loaded prompts for {len(self.registry.list_agents())} agents")
        except Exception as e:
            logger.error(f"Error loading prompts: {e}")
    
    def _load_prompt_file(self, file_path: Path):
        """Load prompts from a single file."""
        try:
            loader = self.loader_factory.get_loader(file_path)
            if not loader:
                logger.warning(f"No loader found for file: {file_path}")
                return
            
            data = loader.load(file_path)
            agent_name = file_path.stem
            
            # Check for file modification if auto-reload is enabled
            if self._auto_reload:
                mod_time = file_path.stat().st_mtime
                if file_path in self.registry._loaded_files:
                    if self.registry._loaded_files[file_path] >= mod_time:
                        return  # File hasn't changed
                self.registry._loaded_files[file_path] = mod_time
            
            # Process each prompt in the file
            for prompt_name, prompt_data in data.items():
                metadata = self._extract_metadata(prompt_data)
                template = PromptTemplate(prompt_data, metadata)
                self.registry.register_prompt(agent_name, prompt_name, template)
            
            logger.debug(f"Loaded {len(data)} prompts for {agent_name}")
            
        except Exception as e:
            logger.error(f"Error loading prompt file {file_path}: {e}")
    
    def _extract_metadata(self, prompt_data: Any) -> Optional[PromptMetadata]:
        """Extract metadata from prompt data if available."""
        if isinstance(prompt_data, dict) and '_metadata' in prompt_data:
            meta = prompt_data['_metadata']
            return PromptMetadata(
                name=meta.get('name', ''),
                description=meta.get('description', ''),
                version=meta.get('version', '1.0'),
                required_params=meta.get('required_params', []),
                optional_params=meta.get('optional_params', []),
                category=meta.get('category', 'general')
            )
        return None
    
    def get_prompt(self, agent_name: str, prompt_type: str, **kwargs) -> str:
        """
        Get a formatted prompt.
        
        Args:
            agent_name: Name of the agent (e.g., 'ba_agent')
            prompt_type: Type of prompt (e.g., 'chain_of_thought', 'persona')
            **kwargs: Variables to substitute in the prompt template
            
        Returns:
            Formatted prompt string
        """
        try:
            template = self.registry.get_prompt(agent_name, prompt_type)
            if not template:
                logger.warning(f"Prompt not found: {agent_name}.{prompt_type}")
                return ""
            
            # Validate parameters if metadata is available
            if template.metadata and template.metadata.required_params:
                template.validate_params(**kwargs)
            
            return template.format(**kwargs)
            
        except ValueError as e:
            # Parameter validation error
            logger.error(f"Parameter validation error for {agent_name}.{prompt_type}: {e}")
            return ""
        except Exception as e:
            logger.error(f"Error getting prompt {agent_name}.{prompt_type}: {e}")
            return ""
    
    def get_persona(self, agent_name: str) -> str:
        """Get the persona prompt for an agent."""
        return self.get_prompt(agent_name, 'persona')
    
    def get_chain_of_thought(self, agent_name: str, **kwargs) -> str:
        """Get the chain of thought prompt for an agent."""
        return self.get_prompt(agent_name, 'chain_of_thought', **kwargs)
    
    def reload_prompts(self):
        """Reload all prompts from files."""
        self.registry._prompts.clear()
        self.registry._metadata.clear()
        self.registry._loaded_files.clear()
        self._load_all_prompts()
    
    def list_available_prompts(self) -> Dict[str, List[str]]:
        """List all available prompts by agent."""
        return {
            agent: self.registry.list_prompts(agent)
            for agent in self.registry.list_agents()
        }
    
    def get_prompt_metadata(self, agent_name: str, prompt_name: str) -> Optional[PromptMetadata]:
        """Get metadata for a specific prompt."""
        return self.registry.get_metadata(agent_name, prompt_name)
    
    def set_auto_reload(self, enabled: bool):
        """Enable or disable automatic file reloading."""
        self._auto_reload = enabled


# Global prompt manager instance (Singleton)
_prompt_manager_instance = None

def get_prompt_manager() -> PromptManager:
    """Get the global prompt manager instance."""
    global _prompt_manager_instance
    if _prompt_manager_instance is None:
        _prompt_manager_instance = PromptManager()
    return _prompt_manager_instance


# Convenience functions for backward compatibility
def get_prompt(agent_name: str, prompt_type: str, **kwargs) -> str:
    """Convenience function to get a prompt."""
    return get_prompt_manager().get_prompt(agent_name, prompt_type, **kwargs)


def get_persona(agent_name: str) -> str:
    """Convenience function to get agent persona."""
    return get_prompt_manager().get_persona(agent_name)


def get_chain_of_thought(agent_name: str, **kwargs) -> str:
    """Convenience function to get chain of thought prompt."""
    return get_prompt_manager().get_chain_of_thought(agent_name, **kwargs)


def reload_prompts():
    """Convenience function to reload all prompts."""
    get_prompt_manager().reload_prompts()


def list_available_prompts() -> Dict[str, List[str]]:
    """Convenience function to list all available prompts."""
    return get_prompt_manager().list_available_prompts()