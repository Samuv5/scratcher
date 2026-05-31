import { describe, it, expect } from 'vitest'

describe('App', () => {
  it('should have correct imports available', () => {
    // Just verify the test environment works
    expect(typeof window).toBe('object')
  })

  it('jsPDF should be importable', async () => {
    const { jsPDF } = await import('jspdf')
    expect(typeof jsPDF).toBe('function')
  })
})
