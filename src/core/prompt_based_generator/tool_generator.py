"""
Tool Generator

Generates tools from natural language prompts using LLM interpretation.
"""


import ast
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from ..agno_agent_framework.tools import Tool, ToolParameter, ToolType
from ..utils.type_helpers import ConfigDict, GatewayProtocol
from .exceptions import CodeValidationError, ToolGenerationError
from .generator_cache import GeneratorCache
from .prompt_interpreter import PromptInterpreter


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
        cache: Optional[GeneratorCache] = None,
    ):
        """
        Initialize tool generator.
        
        Args:
            gateway (GatewayProtocol): Gateway client used for LLM calls.
            interpreter (Optional[PromptInterpreter]): Input parameter for this operation.
            cache (Optional[GeneratorCache]): Cache instance used to store and fetch cached results.
        """
        self.gateway = gateway
        self.interpreter = interpreter or PromptInterpreter(gateway)
        self.cache = cache or GeneratorCache()

    def _validate_code(self, code: str) -> tuple[bool, list[str]]:
        """
        Validate generated code.
        
        Args:
            code (str): Input parameter for this operation.
        
        Returns:
            tuple[bool, list[str]]: True if the operation succeeds, else False.
        """
        errors = []

        try:
            # Parse code to check syntax
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")
            return False, errors

        # Check for dangerous imports
        dangerous_imports = ["os", "sys", "subprocess", "eval", "exec", "__import__"]
        for dangerous in dangerous_imports:
            if dangerous in code and f"import {dangerous}" in code:
                errors.append(f"Dangerous import detected: {dangerous}")

        # Check for file operations (optional - can be allowed)
        file_ops = ["open(", "file(", "__file__"]
        for op in file_ops:
            if op in code:
                # Warning, not error
                pass

        return len(errors) == 0, errors

    def _validate_dangerous_imports(self, node: ast.AST, code: str) -> None:
        """
        Validate that no dangerous imports are present.
        
        Args:
            node (ast.AST): Input parameter for this operation.
            code (str): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        
        Raises:
            CodeValidationError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in (node.names if isinstance(node, ast.Import) else [node.module]):
                module_name = alias.name if isinstance(alias, ast.alias) else alias
                if module_name and module_name.split('.')[0] in ['os', 'sys', 'subprocess', '__builtin__', 'builtins']:
                    raise CodeValidationError(
                        message=f"Dangerous import detected: {module_name}",
                        code=code,
                        validation_errors=[f"Import of '{module_name}' is not allowed for security reasons"],
                    )

    def _validate_dangerous_calls(self, node: ast.AST, code: str) -> None:
        """
        Validate that no dangerous function calls are present.
        
        Args:
            node (ast.AST): Input parameter for this operation.
            code (str): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        
        Raises:
            CodeValidationError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ['eval', 'exec', '__import__']:
                raise CodeValidationError(
                    message=f"Dangerous function call detected: {node.func.id}",
                    code=code,
                    validation_errors=[f"Call to '{node.func.id}' is not allowed for security reasons"],
                )

    def _create_safe_namespace(self) -> Dict[str, Any]:
        """
        Create a restricted namespace with only safe builtins.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        safe_builtins = {
            'abs', 'all', 'any', 'bool', 'dict', 'float', 'int', 'len', 'list',
            'max', 'min', 'range', 'round', 'str', 'sum', 'tuple', 'type', 'zip',
            'enumerate', 'isinstance', 'hasattr', 'getattr', 'setattr', 'delattr',
            'print', 'sorted', 'reversed', 'iter', 'next', 'map', 'filter',
        }
        return {
            '__builtins__': {k: v for k, v in __builtins__.items() if k in safe_builtins},
            '__name__': '__main__',
        }

    def _create_function_from_code(self, code: str, function_name: str) -> Optional[Callable]:
        """
        Create a function from generated code using safe AST compilation.
        
        Args:
            code (str): Input parameter for this operation.
            function_name (str): Input parameter for this operation.
        
        Returns:
            Optional[Callable]: Result if available, else None.
        
        Raises:
            CodeValidationError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        try:
            # Parse code into AST for validation
            tree = ast.parse(code, mode='exec')
            
            # Validate AST - check for dangerous operations
            for node in ast.walk(tree):
                self._validate_dangerous_imports(node, code)
                self._validate_dangerous_calls(node, code)
            
            # Compile AST to bytecode
            compiled_code = compile(tree, '<string>', 'exec')
            
            # Create restricted namespace and execute
            namespace = self._create_safe_namespace()
            exec(compiled_code, namespace)

            # Extract and return function
            return namespace.get(function_name)

        except SyntaxError as e:
            raise CodeValidationError(
                message=f"Syntax error in generated code: {str(e)}",
                code=code,
                validation_errors=[f"Syntax error at line {e.lineno}: {str(e)}"],
            )
        except CodeValidationError:
            raise
        except Exception as e:
            raise CodeValidationError(
                message=f"Failed to create function from code: {str(e)}",
                code=code,
                validation_errors=[str(e)],
            )

    async def generate_tool_from_prompt(
        self,
        prompt: str,
        tool_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        **kwargs: ConfigDict,
    ) -> Tool:
        """
        Generate a tool from a natural language prompt.
        
        Args:
            prompt (str): Prompt text sent to the model.
            tool_id (Optional[str]): Tool identifier.
            tenant_id (Optional[str]): Tenant identifier used for tenant isolation.
            **kwargs (ConfigDict): Input parameter for this operation.
        
        Returns:
            Tool: Result of the operation.
        
        Raises:
            CodeValidationError: Raised when this function detects an invalid state or when an underlying call fails.
            ToolGenerationError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        try:
            # Generate tool ID if not provided
            if not tool_id:
                tool_id = f"tool_{uuid.uuid4().hex[:8]}"

            # Interpret prompt
            requirements = await self.interpreter.interpret_tool_prompt(
                prompt=prompt,
                cache=self.cache.cache if hasattr(self.cache, "cache") else None,  # type: ignore[arg-type]
                tenant_id=tenant_id,
            )

            # Get code template
            code = requirements.code_template or ""

            # Validate code
            is_valid, errors = self._validate_code(code)
            if not is_valid:
                raise CodeValidationError(
                    message=f"Generated code failed validation: {', '.join(errors)}",
                    code=code,
                    validation_errors=errors,
                )

            # Create function from code
            function = self._create_function_from_code(code, requirements.function_name)

            if not function:
                raise ToolGenerationError(
                    message=f"Failed to extract function '{requirements.function_name}' from code",
                    prompt=prompt,
                    tool_id=tool_id,
                    stage="function_extraction",
                )

            # Create tool parameters
            parameters = []
            for param_def in requirements.parameters:
                parameters.append(
                    ToolParameter(
                        name=param_def.get("name", ""),
                        type=param_def.get("type", "string"),
                        description=param_def.get("description", ""),
                        required=param_def.get("required", True),
                        default=param_def.get("default"),
                    )
                )

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
                    **kwargs,
                },
            )

            # Cache tool schema and code
            await self.cache.cache_tool_schema(
                tool_id=tool_id,
                schema={
                    "name": requirements.name,
                    "description": requirements.description,
                    "parameters": [
                        p.model_dump() if hasattr(p, "model_dump") else p for p in parameters
                    ],
                    "return_type": requirements.return_type,
                },
                tenant_id=tenant_id,
            )

            await self.cache.cache_tool_code(tool_id=tool_id, code=code, tenant_id=tenant_id)

            return tool

        except (CodeValidationError, ToolGenerationError):
            raise
        except Exception as e:
            raise ToolGenerationError(
                message=f"Failed to generate tool from prompt: {str(e)}",
                prompt=prompt,
                tool_id=tool_id,
                stage="generation",
                original_error=e,
            )
