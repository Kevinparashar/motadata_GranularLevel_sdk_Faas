"""
Tool Generator

Generates tools from natural language prompts using LLM interpretation.
"""

import uuid
import ast
import inspect
from typing import Optional, Dict, Callable
from datetime import datetime

from ..agno_agent_framework.tools import Tool, ToolType, ToolParameter
from ..utils.type_helpers import GatewayProtocol, ConfigDict
from .prompt_interpreter import PromptInterpreter, ToolRequirements
from .generator_cache import GeneratorCache
from .exceptions import ToolGenerationError, CodeValidationError
from ..utils.error_handler import create_error_with_suggestion


class ToolGenerator:
    """
    Generates tools from natural language prompts.
    
    Uses prompt interpretation to extract requirements and
    creates fully functional Tool instances with generated code.
    """
    
    def __init__(
        self,
        gateway: GatewayProtocol,
        interpreter: Optional[PromptInterpreter] = None,
        cache: Optional[GeneratorCache] = None
    ):
        """
        Initialize tool generator.
        
        Args:
            gateway: LiteLLM Gateway instance
            interpreter: Optional PromptInterpreter instance
            cache: Optional GeneratorCache instance
        """
        self.gateway = gateway
        self.interpreter = interpreter or PromptInterpreter(gateway)
        self.cache = cache or GeneratorCache()
    
    def _validate_code(self, code: str) -> tuple[bool, list[str]]:
        """
        Validate generated code.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        try:
            # Parse code to check syntax
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")
            return False, errors
        
        # Check for dangerous imports
        dangerous_imports = ['os', 'sys', 'subprocess', 'eval', 'exec', '__import__']
        for dangerous in dangerous_imports:
            if dangerous in code and f"import {dangerous}" in code:
                errors.append(f"Dangerous import detected: {dangerous}")
        
        # Check for file operations (optional - can be allowed)
        file_ops = ['open(', 'file(', '__file__']
        for op in file_ops:
            if op in code:
                # Warning, not error
                pass
        
        return len(errors) == 0, errors
    
    def _create_function_from_code(
        self,
        code: str,
        function_name: str
    ) -> Optional[Callable]:
        """
        Create a function from generated code.
        
        Args:
            code: Python code
            function_name: Name of function to extract
            
        Returns:
            Function object or None
        """
        try:
            # Execute code in isolated namespace
            namespace = {}
            exec(code, namespace)
            
            # Extract function
            if function_name in namespace:
                return namespace[function_name]
            
            return None
            
        except Exception as e:
            raise CodeValidationError(
                message=f"Failed to create function from code: {str(e)}",
                code=code,
                validation_errors=[str(e)]
            )
    
    async def generate_tool_from_prompt(
        self,
        prompt: str,
        tool_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs: ConfigDict
    ) -> Tool:
        """
        Generate a tool from a natural language prompt.
        
        Args:
            prompt: Natural language description of desired tool
            tool_id: Optional tool ID (generated if not provided)
            tenant_id: Optional tenant ID
            user_id: Optional user ID
            **kwargs: Additional tool configuration
            
        Returns:
            Configured Tool instance
            
        Raises:
            ToolGenerationError: If generation fails
            CodeValidationError: If generated code is invalid
        """
        try:
            # Generate tool ID if not provided
            if not tool_id:
                tool_id = f"tool_{uuid.uuid4().hex[:8]}"
            
            # Interpret prompt
            requirements = await self.interpreter.interpret_tool_prompt(
                prompt=prompt,
                cache=self.cache.cache if hasattr(self.cache, 'cache') else None,
                tenant_id=tenant_id
            )
            
            # Get code template
            code = requirements.code_template or ""
            
            # Validate code
            is_valid, errors = self._validate_code(code)
            if not is_valid:
                raise CodeValidationError(
                    message=f"Generated code failed validation: {', '.join(errors)}",
                    code=code,
                    validation_errors=errors
                )
            
            # Create function from code
            function = self._create_function_from_code(code, requirements.function_name)
            
            if not function:
                raise ToolGenerationError(
                    message=f"Failed to extract function '{requirements.function_name}' from code",
                    prompt=prompt,
                    tool_id=tool_id,
                    stage="function_extraction"
                )
            
            # Create tool parameters
            parameters = []
            for param_def in requirements.parameters:
                parameters.append(ToolParameter(
                    name=param_def.get("name", ""),
                    type=param_def.get("type", "string"),
                    description=param_def.get("description", ""),
                    required=param_def.get("required", True),
                    default=param_def.get("default")
                ))
            
            # Create tool
            tool = Tool(
                tool_id=tool_id,
                name=requirements.name,
                description=requirements.description,
                tool_type=ToolType.FUNCTION,
                function=function,
                parameters=parameters,
                metadata={
                    "generated_from_prompt": True,
                    "prompt_hash": str(hash(prompt)),
                    "generated_at": datetime.now().isoformat(),
                    "tenant_id": tenant_id,
                    **(requirements.metadata or {}),
                    **kwargs
                }
            )
            
            # Cache tool schema and code
            self.cache.cache_tool_schema(
                tool_id=tool_id,
                schema={
                    "name": requirements.name,
                    "description": requirements.description,
                    "parameters": [p.model_dump() if hasattr(p, 'model_dump') else p for p in parameters],
                    "return_type": requirements.return_type
                },
                tenant_id=tenant_id
            )
            
            self.cache.cache_tool_code(
                tool_id=tool_id,
                code=code,
                tenant_id=tenant_id
            )
            
            return tool
            
        except (CodeValidationError, ToolGenerationError):
            raise
        except Exception as e:
            raise ToolGenerationError(
                message=f"Failed to generate tool from prompt: {str(e)}",
                prompt=prompt,
                tool_id=tool_id,
                stage="generation",
                original_error=e
            )

