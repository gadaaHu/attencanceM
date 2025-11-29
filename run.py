from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    print("🚀 Starting Membership System...")
    print("📊 Access the application at: http://localhost:80")
    app.run(debug=True, host='127.0.0.1', port=3306)