@echo off
echo Installing Python requirements for Attendance System...
echo ==================================================

cd /d "C:\xampp\htdocs\attendance\module"

echo Step 1: Creating requirements.txt...
(
echo Flask==2.3.3
echo mysql-connector-python==8.0.33
echo face-recognition==1.3.0
echo opencv-python==4.8.1.78
echo numpy==1.24.3
echo pandas==2.0.3
echo Werkzeug==2.3.7
echo pillow==10.0.1
echo python-dotenv==1.0.0
echo scikit-learn==1.3.0
echo matplotlib==3.7.2
echo seaborn==0.12.2
) > requirements.txt

echo Step 2: Installing packages...
pip install -r requirements.txt

echo.
echo ==================================================
echo Installation complete!
echo Press any key to exit...
pause > nul