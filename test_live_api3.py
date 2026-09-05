import httpx
import asyncio

async def test_api():
    base_url = 'http://127.0.0.1:8000'
    async with httpx.AsyncClient(base_url=base_url) as client:
        # Login
        res = await client.post('/api/v1/auth/login', json={
            'email': 'testuser@example.com',
            'password': 'password123'
        })
        print('Login:', res.status_code)
        
        if res.status_code == 200:
            token = res.json()['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Me
            res = await client.get('/api/v1/auth/me', headers=headers)
            print('Me:', res.status_code, res.json())
            
            # Products
            res = await client.get('/api/v1/products', headers=headers)
            print('Products:', res.status_code, len(res.json().get('items', [])))
            
            # Agent Chat
            res = await client.post('/api/v1/agent/chat', json={'message': 'hello'}, headers=headers)
            print('Agent:', res.status_code, res.text)
            
            # Ensure Tenant Exists and Set Current Tenant (If needed, although the user endpoint might handle it)

if __name__ == '__main__':
    asyncio.run(test_api())
