import os
import httpx
from dotenv import load_dotenv

load_dotenv()

def register():
    payload = {
        "email": os.getenv("EMAIL"),
        "name": os.getenv("NAME"),
        "mobileNo": os.getenv("MOBILE_NO", "9999999999"),
        "githubUsername": os.getenv("GITHUB_USERNAME", "my_github"),
        "rollNo": os.getenv("ROLL_NO"),
        "accessCode": os.getenv("ACCESS_CODE")
    }
    
    print("Registering with:", payload)
    
    response = httpx.post("http://20.207.122.201/evaluation-service/register", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Registration Successful!")
        print(f"CLIENT_ID={data.get('clientID')}")
        print(f"CLIENT_SECRET={data.get('clientSecret')}")
        print("\n👉 Now, copy the CLIENT_ID and CLIENT_SECRET above into your .env file!")
    else:
        print("\n❌ Registration Failed:")
        print(response.text)

if __name__ == "__main__":
    register()
