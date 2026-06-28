"""
Compatibility checker and environment validator
"""
import sys
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required!")
        return False
    
    if version.major == 3 and version.minor >= 13:
        print("⚠️  Python 3.13+ detected. Some packages may have compatibility issues.")
        print("💡 Recommended: Use Python 3.8-3.11 for best compatibility")
    
    return True

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    spec = importlib.util.find_spec(import_name)
    if spec is None:
        print(f"❌ {package_name} not installed")
        return False
    else:
        print(f"✅ {package_name} installed")
        return True

def main():
    print("=" * 60)
    print("🔍 Environment Compatibility Check")
    print("=" * 60)
    print()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    print()
    print("📦 Checking Required Packages:")
    print("-" * 60)
    
    packages = [
        ("opencv-python", "cv2"),
        ("mediapipe", "mediapipe"),
        ("deepface", "deepface"),
        ("tensorflow", "tensorflow"),
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("pygame", "pygame"),
        ("kaggle", "kaggle"),
    ]
    
    missing = []
    for pkg_name, import_name in packages:
        if not check_package(pkg_name, import_name):
            missing.append(pkg_name)
    
    print()
    print("=" * 60)
    
    if missing:
        print("❌ Missing packages:")
        for pkg in missing:
            print(f"   - {pkg}")
        print()
        print("💡 Install with: pip install -r requirements.txt")
        sys.exit(1)
    else:
        print("✅ All required packages are installed!")
        print("🚀 System ready to run!")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
