import { describe, it, expect, beforeEach, vi } from 'vitest'
import { helloWorld } from '../src/index'

// モック用のRequest/Response型
interface MockRequest {
  method: string
  url: string
  body: any
  query: any
  headers: any
  get: ReturnType<typeof vi.fn>
}

interface MockResponse {
  send: ReturnType<typeof vi.fn>
  status: ReturnType<typeof vi.fn>
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
      get: vi.fn(),
    }

    res = {
      send: vi.fn(),
      status: vi.fn().mockReturnThis(),
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
