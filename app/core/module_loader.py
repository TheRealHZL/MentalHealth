"""
Module Loader System

Automatically discovers and loads modules from app/modules/
Each module must have a manifest.json file that defines its metadata.

Module Structure:
    /app/modules/module_name/
        manifest.json    # Module metadata
        routes.py        # FastAPI router
        models.py        # SQLAlchemy models (optional)
        schemas.py       # Pydantic schemas (optional)
        service.py       # Business logic (optional)

Example manifest.json:
    {
        "name": "mood",
        "version": "1.0.0",
        "description": "Mood tracking and analysis",
        "enabled": true,
        "routes_prefix": "/mood",
        "tags": ["mood-tracking"],
        "dependencies": [],
        "author": "MindBridge Team"
    }
"""

import importlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, FastAPI

logger = logging.getLogger(__name__)


class Module:
    """Represents a loaded module"""

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        enabled: bool,
        routes_prefix: str,
        tags: List[str],
        dependencies: List[str],
        author: str,
        router: Optional[APIRouter] = None,
        path: Optional[Path] = None,
    ):
        self.name = name
        self.version = version
        self.description = description
        self.enabled = enabled
        self.routes_prefix = routes_prefix
        self.tags = tags
        self.dependencies = dependencies
        self.author = author
        self.router = router
        self.path = path

    def __repr__(self) -> str:
        return f"<Module {self.name} v{self.version} ({self.routes_prefix})>"


class ModuleLoader:
    """
    Module Loader

    Automatically discovers and loads modules from app/modules/
    """

    def __init__(self, modules_dir: str = "app/modules"):
        self.modules_dir = Path(modules_dir)
        self.modules: Dict[str, Module] = {}
        self.loaded_count = 0
        self.failed_count = 0

    def discover_modules(self) -> List[Path]:
        """
        Discover all modules in modules directory

        Returns:
            List of module directories
        """
        if not self.modules_dir.exists():
            logger.warning(f"Modules directory not found: {self.modules_dir}")
            return []

        modules = []
        for module_path in self.modules_dir.iterdir():
            if module_path.is_dir() and not module_path.name.startswith("_"):
                manifest_path = module_path / "manifest.json"
                if manifest_path.exists():
                    modules.append(module_path)
                else:
                    logger.warning(
                        f"Module {module_path.name} missing manifest.json - skipping"
                    )

        logger.info(f"📦 Discovered {len(modules)} modules")
        return modules

    def load_manifest(self, module_path: Path) -> Optional[Dict[str, Any]]:
        """
        Load module manifest

        Args:
            module_path: Path to module directory

        Returns:
            Manifest dict or None if failed
        """
        manifest_path = module_path / "manifest.json"

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            # Validate required fields
            required_fields = ["name", "version", "description", "routes_prefix"]
            for field in required_fields:
                if field not in manifest:
                    logger.error(
                        f"Module {module_path.name}: Missing required field '{field}'"
                    )
                    return None

            return manifest

        except json.JSONDecodeError as e:
            logger.error(f"Module {module_path.name}: Invalid JSON in manifest: {e}")
            return None
        except Exception as e:
            logger.error(f"Module {module_path.name}: Failed to load manifest: {e}")
            return None

    def load_router(self, module_path: Path, module_name: str) -> Optional[APIRouter]:
        """
        Load module router

        Args:
            module_path: Path to module directory
            module_name: Name of the module

        Returns:
            FastAPI router or None if failed
        """
        try:
            # Construct module import path
            module_import_path = f"app.modules.{module_name}.routes"

            # Import the module
            module = importlib.import_module(module_import_path)

            # Get router from module
            if hasattr(module, "router"):
                router = module.router
                if isinstance(router, APIRouter):
                    return router
                else:
                    logger.error(
                        f"Module {module_name}: 'router' is not an APIRouter instance"
                    )
                    return None
            else:
                logger.error(f"Module {module_name}: No 'router' found in routes.py")
                return None

        except ImportError as e:
            logger.error(f"Module {module_name}: Failed to import routes: {e}")
            return None
        except Exception as e:
            logger.error(f"Module {module_name}: Failed to load router: {e}")
            return None

    def check_dependencies(
        self, module_name: str, dependencies: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Check if module dependencies are met

        Args:
            module_name: Name of the module
            dependencies: List of required module names

        Returns:
            Tuple of (all_met, missing_dependencies)
        """
        missing = []
        for dep in dependencies:
            if dep not in self.modules or not self.modules[dep].enabled:
                missing.append(dep)

        return len(missing) == 0, missing

    def load_module(self, module_path: Path) -> Optional[Module]:
        """
        Load a single module

        Args:
            module_path: Path to module directory

        Returns:
            Module instance or None if failed
        """
        module_name = module_path.name

        # Load manifest
        manifest = self.load_manifest(module_path)
        if not manifest:
            return None

        # Check if enabled
        enabled = manifest.get("enabled", True)
        if not enabled:
            logger.info(f"⏭️  Module {module_name}: Disabled in manifest - skipping")
            return None

        # Check dependencies
        dependencies = manifest.get("dependencies", [])
        if dependencies:
            deps_met, missing_deps = self.check_dependencies(module_name, dependencies)
            if not deps_met:
                logger.error(
                    f"Module {module_name}: Missing dependencies: {missing_deps}"
                )
                return None

        # Load router
        router = self.load_router(module_path, module_name)
        if not router:
            logger.error(f"Module {module_name}: Failed to load router")
            return None

        # Create module instance
        module = Module(
            name=manifest["name"],
            version=manifest["version"],
            description=manifest["description"],
            enabled=enabled,
            routes_prefix=manifest["routes_prefix"],
            tags=manifest.get("tags", [module_name]),
            dependencies=dependencies,
            author=manifest.get("author", "Unknown"),
            router=router,
            path=module_path,
        )

        logger.info(
            f"✅ Loaded module: {module.name} v{module.version} ({module.routes_prefix})"
        )
        return module

    def load_all_modules(self) -> None:
        """
        Discover and load all modules
        """
        logger.info("🔍 Discovering modules...")
        module_paths = self.discover_modules()

        self.loaded_count = 0
        self.failed_count = 0

        for module_path in module_paths:
            try:
                module = self.load_module(module_path)
                if module:
                    self.modules[module.name] = module
                    self.loaded_count += 1
                else:
                    self.failed_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to load module {module_path.name}: {e}")
                self.failed_count += 1

        logger.info(
            f"📊 Module loading complete: {self.loaded_count} loaded, {self.failed_count} failed"
        )

    def register_modules(self, app: FastAPI) -> None:
        """
        Register all loaded modules with FastAPI app

        Args:
            app: FastAPI application instance
        """
        if not self.modules:
            logger.warning("⚠️  No modules to register")
            return

        logger.info(f"🔗 Registering {len(self.modules)} modules with FastAPI...")

        for module_name, module in self.modules.items():
            if module.router:
                app.include_router(
                    module.router,
                    prefix=module.routes_prefix,
                    tags=module.tags,
                )
                logger.info(
                    f"   ✓ {module.name}: {module.routes_prefix} ({', '.join(module.tags)})"
                )

        logger.info("✅ All modules registered successfully")

    def get_module(self, name: str) -> Optional[Module]:
        """
        Get module by name

        Args:
            name: Module name

        Returns:
            Module instance or None
        """
        return self.modules.get(name)

    def get_modules_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all loaded modules

        Returns:
            List of module info dicts
        """
        return [
            {
                "name": module.name,
                "version": module.version,
                "description": module.description,
                "enabled": module.enabled,
                "routes_prefix": module.routes_prefix,
                "tags": module.tags,
                "dependencies": module.dependencies,
                "author": module.author,
            }
            for module in self.modules.values()
        ]


# Global module loader instance
_module_loader: Optional[ModuleLoader] = None


def get_module_loader() -> ModuleLoader:
    """
    Get global module loader instance

    Returns:
        ModuleLoader instance
    """
    global _module_loader
    if _module_loader is None:
        _module_loader = ModuleLoader()
    return _module_loader


def init_modules(app: FastAPI) -> ModuleLoader:
    """
    Initialize and register all modules

    Args:
        app: FastAPI application instance

    Returns:
        ModuleLoader instance
    """
    loader = get_module_loader()
    loader.load_all_modules()
    loader.register_modules(app)
    return loader
