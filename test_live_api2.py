import httpx
import asyncio

async def test_api():
    base_url = 'http://127.0.0.1:8000'
    async with httpx.AsyncClient(base_url=base_url) as client:
        # Login
        res = await client.post('/api/v1/auth/login', data={
            'username': 'testuser@example.com',
            'password': 'password123'
        })
        print('Login:', res.status_code, res.text)

if __name__ == '__main__':
    asyncio.run(test_api())
