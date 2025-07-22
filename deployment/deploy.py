#!/usr/bin/env python3
"""
LightRAG Deployment Manager
Reads deployment.yml and manages deployments across different environments
"""

import os
import sys
import yaml
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class DeploymentManager:
    """Manages LightRAG deployments based on YAML configuration."""
    
    def __init__(self, config_path: str = "deployment.yml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.project_root = self.config_path.parent
        
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"❌ Config file not found: {self.config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"❌ Invalid YAML config: {e}")
            sys.exit(1)
    
    def validate_environment(self, env: str = "production") -> bool:
        """Validate environment variables and requirements."""
        print(f"🔍 Validating {env} environment...")
        
        env_config = self.config.get("environments", {}).get(env, {})
        required_vars = self.config.get("environment", {}).get("required", [])
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        print("✅ Environment validation passed")
        return True
    
    def set_railway_variables(self) -> bool:
        """Set environment variables in Railway from config."""
        print("🔧 Setting Railway environment variables...")
        
        # Get all environment variables from config
        required_vars = self.config.get("environment", {}).get("required", [])
        optional_vars = self.config.get("environment", {}).get("optional", [])
        
        success = True
        for var in required_vars + optional_vars:
            value = os.getenv(var)
            if value:
                try:
                    cmd = ["railway", "variables", "--set", f"{var}={value}"]
                    subprocess.run(cmd, check=True, capture_output=True)
                    print(f"✅ Set {var}")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Failed to set {var}: {e}")
                    success = False
        
        return success
    
    def run_migrations(self) -> bool:
        """Run database migrations."""
        print("🗄️ Running database migrations...")
        
        migration_script = self.project_root / "deployment" / "railway-migrations.py"
        if not migration_script.exists():
            print("⚠️ Migration script not found, skipping...")
            return True
        
        try:
            cmd = ["railway", "run", "python", str(migration_script)]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ Migrations completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Migration failed: {e.stderr}")
            return False
    
    def health_check(self) -> bool:
        """Perform health checks after deployment."""
        print("🏥 Performing health checks...")
        
        health_checks = self.config.get("monitoring", {}).get("health_checks", [])
        base_url = os.getenv("RAILWAY_STATIC_URL", "localhost:8000")
        
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        
        for check in health_checks:
            url = f"{base_url}{check['url']}"
            try:
                import requests
                response = requests.get(url, timeout=30)
                
                if response.status_code == check.get("expected_status", 200):
                    print(f"✅ Health check passed: {check['name']}")
                else:
                    print(f"❌ Health check failed: {check['name']} (status: {response.status_code})")
                    return False
                    
            except ImportError:
                print("⚠️ requests library not available for health checks")
                break
            except Exception as e:
                print(f"❌ Health check failed: {check['name']} - {e}")
                return False
        
        return True
    
    def deploy(self, env: str = "production", skip_validation: bool = False) -> bool:
        """Deploy the application to specified environment."""
        print(f"🚀 Starting deployment to {env}...")
        print(f"📋 Version: {self.config['metadata']['version']}")
        
        # Validation
        if not skip_validation and not self.validate_environment(env):
            return False
        
        # Set environment variables
        if not self.set_railway_variables():
            print("❌ Failed to set environment variables")
            return False
        
        # Deploy to Railway
        print("📦 Deploying to Railway...")
        try:
            cmd = ["railway", "up"]
            subprocess.run(cmd, check=True)
            print("✅ Deployment completed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Deployment failed: {e}")
            return False
        
        # Run migrations
        if not self.run_migrations():
            print("⚠️ Migrations failed, but deployment completed")
        
        # Health checks
        print("⏳ Waiting for application to start...")
        import time
        time.sleep(30)  # Wait for Railway deployment
        
        if not self.health_check():
            print("⚠️ Health checks failed, but deployment completed")
        
        print(f"🎉 Deployment to {env} completed successfully!")
        return True
    
    def status(self) -> None:
        """Show deployment status and information."""
        print("📊 LightRAG Deployment Status")
        print("=" * 40)
        
        metadata = self.config.get("metadata", {})
        print(f"Application: {metadata.get('name', 'N/A')}")
        print(f"Version: {metadata.get('version', 'N/A')}")
        print(f"Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'unknown')}")
        print(f"Description: {metadata.get('description', 'N/A')}")
        
        # Railway status
        try:
            result = subprocess.run(["railway", "status"], capture_output=True, text=True)
            print(f"\nRailway Status:\n{result.stdout}")
        except subprocess.CalledProcessError:
            print("\n❌ Could not get Railway status")
        
        # Environment variables status
        print("\nEnvironment Variables:")
        required_vars = self.config.get("environment", {}).get("required", [])
        for var in required_vars:
            status = "✅" if os.getenv(var) else "❌"
            print(f"  {status} {var}")
    
    def version_info(self) -> None:
        """Show version information and history."""
        print("📋 Version Information")
        print("=" * 40)
        
        metadata = self.config.get("metadata", {})
        current_version = metadata.get("version", "unknown")
        
        print(f"Current Version: {current_version}")
        print(f"Last Updated: {metadata.get('created', 'unknown')}")
        
        versions = self.config.get("versions", {})
        if versions:
            print("\nVersion History:")
            for version, info in versions.items():
                print(f"\n📦 {version} ({info.get('date', 'unknown')})")
                
                changes = info.get("changes", [])
                if changes:
                    print("  Changes:")
                    for change in changes:
                        print(f"    • {change}")
                
                features = info.get("features", [])
                if features:
                    print("  Features:")
                    for feature in features:
                        print(f"    • {feature}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="LightRAG Deployment Manager")
    parser.add_argument("--config", "-c", default="deployment.yml", 
                       help="Path to deployment config file")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy application")
    deploy_parser.add_argument("--env", "-e", default="production", 
                              help="Deployment environment")
    deploy_parser.add_argument("--skip-validation", action="store_true",
                              help="Skip environment validation")
    
    # Status command
    subparsers.add_parser("status", help="Show deployment status")
    
    # Version command
    subparsers.add_parser("version", help="Show version information")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate environment")
    validate_parser.add_argument("--env", "-e", default="production",
                                help="Environment to validate")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = DeploymentManager(args.config)
    
    if args.command == "deploy":
        success = manager.deploy(args.env, args.skip_validation)
        sys.exit(0 if success else 1)
    
    elif args.command == "status":
        manager.status()
    
    elif args.command == "version":
        manager.version_info()
    
    elif args.command == "validate":
        success = manager.validate_environment(args.env)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()