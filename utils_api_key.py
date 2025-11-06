#!/usr/bin/env python3
"""
OpenAI API Key Management Utility
Centralized handling of OpenAI API keys with automatic .env loading and validation
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv

# Optional imports for other providers (do not fail hard if missing)
try:
    import google.generativeai as genai  # type: ignore
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False

import json
import urllib.request
import urllib.error

# Try to import OpenAI, but don't fail if not available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = object  # type: ignore


def load_env_files() -> None:
    """
    Load environment variables from multiple .env file locations.
    
    Searches for .env files in:
    1. Current working directory
    2. Code directory (where this file is located)
    3. Parent directory of code directory
    4. Project root (parent of parent)
    
    Stops loading once a valid API key is found.
    """
    # Get the directory where this utility is located
    code_dir = Path(__file__).parent
    
    # List of potential .env file locations
    env_locations = [
        Path.cwd(),  # Current working directory
        code_dir,    # Code directory
        code_dir.parent,  # Parent directory
        code_dir.parent.parent,  # Project root
    ]
    
    # Load .env files from all locations, avoid duplicates
    seen: set[str] = set()
    for location in env_locations:
        env_file = str((location / '.env').resolve())
        if env_file in seen:
            continue
        seen.add(env_file)
        env_path = Path(env_file)
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✓ Loaded environment variables from: {env_path}")
            # Stop when a plausible API key is present
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key and api_key.startswith('sk-'):
                print("✓ Found valid API key, stopping search")
                break


def get_openai_api_key() -> str:
    """
    Get OpenAI API key with automatic .env loading and validation.
    
    Returns:
        str: The OpenAI API key
        
    Raises:
        ValueError: If no API key is found or if validation fails
    """
    # Clear any existing environment variable to avoid conflicts
    if 'OPENAI_API_KEY' in os.environ:
        del os.environ['OPENAI_API_KEY']
    
    # Load environment variables from .env files
    load_env_files()
    
    # Try multiple environment variable names
    api_key = (
        os.getenv('OPENAI_API_KEY') or 
        os.getenv('OPENAI_KEY') or 
        os.getenv('API_KEY')
    )
    
    if not api_key:
        raise ValueError(
            "No OpenAI API key found. Please create a .env file with:\n"
            "OPENAI_API_KEY=your-api-key-here\n\n"
            "The .env file should be placed in one of these locations:\n"
            f"- {Path.cwd() / '.env'}\n"
            f"- {Path(__file__).parent / '.env'}\n"
            f"- {Path(__file__).parent.parent / '.env'}"
        )
    
    # Clean up the API key (remove export statements, quotes, etc.)
    api_key = clean_api_key(api_key)
    
    # Basic format validation
    if not api_key.startswith('sk-'):
        print("⚠️  Warning: API key doesn't start with 'sk-' - this might not be a valid OpenAI API key")
    
    return api_key


def clean_api_key(raw_key: str) -> str:
    """
    Clean up API key by removing common formatting issues.
    
    Args:
        raw_key: Raw API key string that might contain export statements, quotes, etc.
        
    Returns:
        str: Cleaned API key
    """
    key = raw_key.strip()

    # If the raw string contains a clear OpenAI key fragment, extract it robustly
    if 'sk-' in key:
        # Take the substring starting at first 'sk-' up to first whitespace or quote/paren/semicolon
        start = key.find('sk-')
        tail = key[start:]
        terminators = ['\n', '\r', '"', "'", ')', ';', ' ', '\t']
        end_idx = len(tail)
        for term in terminators:
            idx = tail.find(term)
            if idx != -1:
                end_idx = min(end_idx, idx)
        candidate = tail[:end_idx].strip()
        if candidate.startswith('sk-') and len(candidate) >= 10:
            return candidate
    
    # Remove leading export statements
    if key.lower().startswith("export "):
        key = key[len("export "):].strip()
    
    # If provided as KEY=VALUE, split and take the value part
    if "=" in key:
        parts = key.split("=", 1)
        # If the left side looks like the key name, use right side
        if parts[0].strip().upper() in {"OPENAI_API_KEY", "API_KEY", "KEY"}:
            key = parts[1].strip()
    
    # Strip surrounding quotes
    if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
        key = key[1:-1].strip()
    
    # Remove command substitution syntax $(...) and similar
    if key.startswith("$(") and key.endswith(")"):
        key = key[2:-1].strip()
    
    # Handle macOS security command patterns - only if key doesn't already look like a valid API key
    # Skip security command detection if the key already starts with 'sk-' (valid API key)
    if not key.startswith('sk-'):
        # Check if this is a security command (starts with "security" or contains the full command pattern)
        if key.startswith("security ") or "security find-generic-password" in key:
            print("⚠️  Warning: Found macOS security command in API key")
            print("   This suggests the .env file contains a security command instead of the actual key")
            print("   Please replace with the actual API key value")
            # Try to extract the actual key by executing the security command
            try:
                import subprocess
                # Extract the security command and execute it
                if key.startswith("security "):
                    result = subprocess.run(key.split(), capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        key = result.stdout.strip()
                        print(f"   ✓ Successfully retrieved key from macOS keychain")
                    else:
                        print(f"   ❌ Failed to retrieve key from keychain: {result.stderr}")
            except Exception as e:
                print(f"   ❌ Error executing security command: {e}")
    
    # Remove security command patterns
    if key.startswith("$(security ") and key.endswith('" -w'):
        # Extract the actual key from security command
        key = key[len("$(security "):-len('" -w')].strip()
    
    # Handle complex export patterns like "export OPENAI_API_KEY=sk-..." -w)"
    if " -w)" in key:
        key = key.split(" -w)")[0].strip()
    
    # Final cleanup of stray characters like trailing parentheses, semicolons, quotes
    key = key.strip().strip(";").strip(")").strip('"').strip("'")
    
    return key


def validate_openai_key(api_key: Optional[str] = None) -> bool:
    """
    Validate OpenAI API key with a test API call.
    
    Args:
        api_key: Optional API key to validate. If None, will load from environment.
        
    Returns:
        bool: True if key is valid and API is accessible, False otherwise
    """
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI package not available. Install with: pip install openai")
        return False
    
    try:
        # Get API key if not provided
        if api_key is None:
            api_key = get_openai_api_key()
        
        # Create client and test with minimal API call
        client = OpenAI(api_key=api_key)
        
        print("🔄 Testing OpenAI API key...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        
        print("✅ OpenAI API key validation successful")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API key validation failed: {e}")
        print("Please check your API key and try again")
        return False


def get_gemini_api_key() -> str:
    """Return Gemini API key from environment with common fallbacks."""
    load_env_files()
    key = os.getenv("GOOGLE_GEMINI_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_KEY")
    if not key:
        raise ValueError(
            "No Gemini API key found. Please set GOOGLE_GEMINI_KEY (or GEMINI_API_KEY / GEMINI_KEY) in your .env file."
        )
    return clean_api_key(key)


def validate_gemini_key(api_key: Optional[str] = None) -> bool:
    """
    Validate Gemini API key with a minimal test call using the official client if available.
    Falls back to a simple configuration attempt if the SDK is not installed.
    """
    try:
        if api_key is None:
            api_key = get_gemini_api_key()

        if not GEMINI_AVAILABLE:
            print("❌ Gemini SDK not installed. Install with: pip install google-generativeai")
            return False

        print("🔄 Testing Gemini API key...")
        genai.configure(api_key=api_key)
        # Use a lightweight call: list models (does not consume tokens) if possible
        try:
            _ = list(genai.list_models())  # type: ignore
        except Exception:
            # Fallback: minimal generate request
            model = genai.GenerativeModel("gemini-1.5-flash")  # type: ignore
            _ = model.generate_content("ping")  # type: ignore
        print("✅ Gemini API key validation successful")
        return True
    except Exception as e:
        print(f"❌ Gemini API key validation failed: {e}")
        print("Please check your Gemini key and try again")
        return False


def get_router_api_key() -> str:
    """Return OpenRouter API key from environment with common fallbacks."""
    load_env_files()
    key = os.getenv("ROUTER_API_KEY") or os.getenv("ROUTER_KEY") or os.getenv("ROUTER") or os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise ValueError(
            "No OpenRouter API key found. Please set ROUTER_API_KEY (or ROUTER_KEY / OPENROUTER_API_KEY) in your .env file."
        )
    return clean_api_key(key)


def validate_router_key(api_key: Optional[str] = None) -> bool:
    """
    Validate OpenRouter API key via a lightweight GET to /models endpoint.
    Uses only standard library to avoid adding dependencies.
    """
    try:
        if api_key is None:
            api_key = get_router_api_key()

        print("🔄 Testing OpenRouter API key...")
        req = urllib.request.Request(
            url="https://openrouter.ai/api/v1/models",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                # Basic parse to confirm JSON
                _ = json.loads(resp.read().decode("utf-8"))
                print("✅ OpenRouter API key validation successful")
                return True
            print(f"❌ OpenRouter responded with status {resp.status}")
            return False
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
        except Exception:
            body = "<no body>"
        print(f"❌ OpenRouter API key validation failed: HTTP {e.code} — {body}")
        return False
    except Exception as e:
        print(f"❌ OpenRouter API key validation failed: {e}")
        print("Please check your OpenRouter key and try again")
        return False


def create_openai_client() -> OpenAI:
    """
    Create an OpenAI client with automatic API key loading and validation.
    
    Returns:
        OpenAI: Configured OpenAI client
        
    Raises:
        ValueError: If API key is not found or invalid
        ImportError: If OpenAI package is not installed
    """
    if not OPENAI_AVAILABLE:
        raise ImportError(
            "OpenAI package not available. Install with: pip install openai"
        )
    
    api_key = get_openai_api_key()
    return OpenAI(api_key=api_key)


def get_provider_for_model(model_name: str) -> str:
    """Infer provider from model name.

    Returns one of: "openai", "gemini", "router".
    
    Model routing:
    - GPT-5 models → "openai"
    - Gemini models → "gemini"
    - Mistral, Llama, and all other models → "router" (OpenRouter)
    """
    name = (model_name or "").lower()
    if name.startswith("gpt-5") or name.startswith("gpt-"):
        return "openai"
    if "gemini" in name:
        return "gemini"
    # All other models (Mistral, Llama, etc.) are routed through OpenRouter
    return "router"


def get_api_key_for_model(model_name: str) -> str:
    """Return the appropriate API key based on the model/provider.

    Policy:
    - OpenAI GPT-5 models → OPENAI_API_KEY (with fallbacks OPENAI_KEY, API_KEY)
    - Gemini models → GOOGLE_GEMINI_KEY (with fallbacks GEMINI_API_KEY, GEMINI_KEY)
    - Mistral, Llama, and all other models → ROUTER_API_KEY (with fallbacks ROUTER_KEY, ROUTER, OPENROUTER_API_KEY)
    """
    load_env_files()

    provider = get_provider_for_model(model_name)
    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY") or os.getenv("API_KEY")
    elif provider == "gemini":
        key = os.getenv("GOOGLE_GEMINI_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_KEY")
    else:
        key = os.getenv("ROUTER_API_KEY") or os.getenv("ROUTER_KEY") or os.getenv("ROUTER")

    if not key:
        raise ValueError(
            f"No API key found for provider '{provider}'. Please set the appropriate environment variable."
        )

    return clean_api_key(key)


def check_env_setup() -> bool:
    """
    Check if the environment is properly set up for OpenAI API usage.
    
    Returns:
        bool: True if environment is properly configured, False otherwise
    """
    print("🔍 Checking OpenAI API environment setup...")
    
    # Check if OpenAI package is available
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI package not installed")
        print("   Install with: pip install openai")
        return False
    
    # Check if API key is available
    try:
        api_key = get_openai_api_key()
        print(f"✅ API key found: {api_key[:8]}...{api_key[-4:]}")
    except ValueError as e:
        print(f"❌ API key not found: {e}")
        return False
    
    # Validate the API key
    if not validate_openai_key(api_key):
        return False
    
    print("✅ Environment setup complete!")
    return True


def validate_api_key_for_model(model_name: str) -> bool:
    """
    Validate the appropriate API key based on the model provider.
    
    Args:
        model_name: The model name (e.g., "gpt-5-nano", "gemini-flash-latest", 
                   "mistral-reasoning-latest", "llama-reasoning-latest")
        
    Returns:
        bool: True if the API key for the model's provider is valid, False otherwise
        
    Raises:
        ValueError: If no API key is found for the provider
        
    Examples:
        - GPT-5 models → validates OPENAI_API_KEY
        - Gemini models → validates GOOGLE_GEMINI_KEY
        - Mistral/Llama models → validates ROUTER_API_KEY (OpenRouter)
        - Other models → validates ROUTER_API_KEY (OpenRouter)
    """
    provider = get_provider_for_model(model_name)
    
    if provider == "openai":
        return validate_openai_key()
    elif provider == "gemini":
        return validate_gemini_key()
    elif provider == "router":
        # Mistral, Llama, and all other non-OpenAI/Gemini models use OpenRouter
        return validate_router_key()
    else:
        raise ValueError(f"Unknown provider for model: {model_name}")


def check_env_setup_all() -> bool:
    """Check and validate all supported provider API keys if present."""
    overall_ok = True

    # OpenAI
    print("\n=== OpenAI ===")
    try:
        if validate_openai_key():
            pass
        else:
            overall_ok = False
    except Exception as e:
        print(f"OpenAI check failed: {e}")
        overall_ok = False

    # Gemini
    print("\n=== Gemini ===")
    try:
        key_present = (
            os.getenv("GOOGLE_GEMINI_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_KEY")
        )
        if key_present:
            if not validate_gemini_key():
                overall_ok = False
        else:
            print("(no Gemini key found in env — skipping)")
    except Exception as e:
        print(f"Gemini check failed: {e}")
        overall_ok = False

    # OpenRouter
    print("\n=== OpenRouter ===")
    try:
        key_present = (
            os.getenv("ROUTER_API_KEY") or os.getenv("ROUTER_KEY") or os.getenv("ROUTER") or os.getenv("OPENROUTER_API_KEY")
        )
        if key_present:
            if not validate_router_key():
                overall_ok = False
        else:
            print("(no OpenRouter key found in env — skipping)")
    except Exception as e:
        print(f"OpenRouter check failed: {e}")
        overall_ok = False

    return overall_ok


def main():
    """Command-line interface for API key management."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "validate":
            # Backward compatible: validate OpenAI only
            success = check_env_setup()
            sys.exit(0 if success else 1)
        elif command == "validate-all":
            success = check_env_setup_all()
            sys.exit(0 if success else 1)
        elif command == "validate-gemini":
            try:
                ok = validate_gemini_key()
                sys.exit(0 if ok else 1)
            except Exception as e:
                print(f"❌ Gemini validation failed: {e}")
                sys.exit(1)
        elif command == "validate-router":
            try:
                ok = validate_router_key()
                sys.exit(0 if ok else 1)
            except Exception as e:
                print(f"❌ OpenRouter validation failed: {e}")
                sys.exit(1)
        
        elif command == "test":
            try:
                client = create_openai_client()
                print("✅ OpenAI client created successfully")
            except Exception as e:
                print(f"❌ Failed to create OpenAI client: {e}")
                sys.exit(1)
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: validate, validate-all, validate-gemini, validate-router, test")
            sys.exit(1)
    else:
        # Default: check environment setup
        success = check_env_setup()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
