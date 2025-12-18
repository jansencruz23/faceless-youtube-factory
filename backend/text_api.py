"""Quick API test script."""
import asyncio
import httpx
import time

BASE_URL = "http://localhost:8000/api/v1"


async def test_full_flow():
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("1. Creating project...")
        response = await client.post(
            f"{BASE_URL}/projects",
            json={
                "title": "Test: Python Explained",
                "script_prompt": "Create a 2-minute educational video explaining what Python programming is. Use a Host who introduces topics and an Expert who provides details.",
                "auto_upload": False
            }
        )
        project = response.json()
        project_id = project["id"]
        print(f"Created project: {project_id}")
        print(f"Status: {project['status']}")

        # Poll for completion
        print("\n2. Waiting for generation...")
        for i in range(60):
            await asyncio.sleep(5)
            response = await client.get(f"{BASE_URL}/projects/{project_id}")
            data = response.json()
            status = data["status"]
            print(f"[{i*5}s] Status: {status}")

            if status == "completed":
                print("\n3. Generation completed!")
                print(f"   Script scenes: {len(data.get('script', {}).get('scenes', []))}")
                print(f"   Assets: {len(data.get('assets', []))}")

                # Find video asset
                video = next(
                    (a for a in data.get("assets", []) if a["asset_type"] == "video"),
                    None
                )
                if video:
                    print(f"   Video URL: http://localhost:8000{video['url']}")
                break
            elif status == "failed":
                print(f"\n   FAILED: {data.get('error_message')}")
                break
        else:
            print("\n   Timeout waiting for completion")

    
if __name__ == "__main__":
    asyncio.run(test_full_flow())
