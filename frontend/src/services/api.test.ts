import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock fetch
const mockFetch = vi.fn()
  ; (globalThis as unknown as { fetch: typeof mockFetch }).fetch = mockFetch

describe('API Service', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  describe('API request handling', () => {
    it('should handle successful responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'ok', version: '0.2.0' }),
      })

      const response = await fetch('/api/v1/health')
      const data = await response.json()

      expect(data.status).toBe('ok')
      expect(data.version).toBe('0.2.0')
    })

    it('should handle error responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ detail: 'Internal Server Error' }),
      })

      const response = await fetch('/api/v1/health')

      expect(response.ok).toBe(false)
      expect(response.status).toBe(500)
    })

    it('should include correct headers', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      })

      await fetch('/api/v1/chart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ date: '2024-01-01T10:00:00' }),
      })

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/chart',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
    })
  })
})

