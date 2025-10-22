import { helloWorld } from '../src/index'

// モック用のRequest/Response型
interface MockRequest {
  method: string
  url: string
  body: any
  query: any
  headers: any
  get: jest.Mock
}

interface MockResponse {
  send: jest.Mock
  status: jest.Mock
}

describe('HelloWorld Function', () => {
  let req: MockRequest
  let res: MockResponse

  beforeEach(() => {
    req = {
      body: {},
      query: {},
      headers: {},
      method: 'GET',
      url: '',
      get: jest.fn(),
    }

    res = {
      send: jest.fn(),
      status: jest.fn().mockReturnThis(),
    }
  })

  it('should return "Hello World!" message', async () => {
    await helloWorld(req as any, res as any)

    expect(res.send).toHaveBeenCalledWith('Hello World!')
  })

  it('should handle POST requests', async () => {
    req.method = 'POST'
    req.body = { name: 'Test User' }

    await helloWorld(req as any, res as any)

    expect(res.send).toHaveBeenCalledWith('Hello World!')
  })
})
