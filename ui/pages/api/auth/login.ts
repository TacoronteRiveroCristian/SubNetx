/**
 * Login API endpoint
 * This file handles login requests and returns appropriate responses
 */

import { NextApiRequest, NextApiResponse } from 'next'
import { verifyAdminCredentials } from '../../../lib/auth.ts'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    const { username, password } = req.body

    // Verify credentials against database
    const isValid = await verifyAdminCredentials(username, password)

    if (isValid) {
      // Set session cookie or JWT token here
      return res.status(200).json({ message: 'Login successful' })
    } else {
      return res.status(401).json({ message: 'Invalid credentials' })
    }
  } catch (error) {
    console.error('Login error:', error)
    return res.status(500).json({ message: 'Internal server error' })
  }
}
