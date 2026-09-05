import httpx
import asyncio

async def test_api():
    base_url = 'http://127.0.0.1:8000'
    async with httpx.AsyncClient(base_url=base_url) as client:
        # Register
        res = await client.post('/api/v1/auth/register', json={
            'email': 'testuser@example.com',
            'password': 'password123',
            'name': 'Test User'
        })
        print('Register:', res.status_code, res.text)
        
        # Login
        res = await client.post('/api/v1/auth/login', data={
            'username': 'testuser@example.com',
            'password': 'password123'
        })
        print('Login:', res.status_code)
        if res.status_code == 200:
            token = res.json()['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Get User
            res = await client.get('/api/v1/auth/me', headers=headers)
            print('Me:', res.status_code, res.text)
            
            # Catalog
            res = await client.get('/api/v1/products', headers=headers)
            print('Products:', res.status_code, len(res.json().get('items', [])))

if __name__ == '__main__':
    asyncio.run(test_api())
