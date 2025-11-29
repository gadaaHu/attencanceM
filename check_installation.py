import importlib

required_packages = [
    'flask',
    'mysql.connector',
    'face_recognition',
    'cv2',
    'numpy',
    'pandas',
    'werkzeug',
    'PIL',
    'dotenv',
    'sklearn',
    'matplotlib',
    'seaborn'
]

print("Checking package installations...")
print("=" * 40)

for package in required_packages:
    try:
        if package == 'PIL':
            import PIL
            version = PIL.__version__
        elif package == 'cv2':
            import cv2
            version = cv2.__version__
        else:
            mod = importlib.import_module(package)
            version = getattr(mod, '__version__', 'Unknown version')
        
        print(f"✅ {package:20} - {version}")
    except ImportError as e:
        print(f"❌ {package:20} - NOT INSTALLED")
        print(f"   Error: {e}")

print("=" * 40)
print("Installation check complete!")