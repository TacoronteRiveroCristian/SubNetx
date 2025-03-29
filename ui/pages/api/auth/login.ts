/**
 * Login API endpoint
 * This file handles login requests and returns appropriate responses
 */

import { NextApiRequest, NextApiResponse } from 'next'
import { verifyAdminCredentials } from '../../../lib/auth.ts'
import prisma from '../../../lib/db'

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

    // Check if using default credentials
    const isDefaultCredentials = username === 'admin' && password === 'admin'

    // Verify credentials against database
    const isValid = await verifyAdminCredentials(username, password)

    if (isValid) {
      // Get user data including role
      const user = await prisma.user.findUnique({
        where: { username },
        select: {
          id: true,
          username: true,
          role: true
        }
      })

      if (!user) {
        return res.status(401).json({ message: 'User not found' })
      }

      // Set session cookie or JWT token here
      return res.status(200).json({
        message: 'Login successful',
        isDefaultCredentials, // Add flag to indicate if default credentials were used
        user: {
          id: user.id,
          username: user.username,
          role: user.role
        }
      })
    } else {
      return res.status(401).json({ message: 'Invalid credentials' })
    }
  } catch (error) {
    console.error('Login error:', error)
    return res.status(500).json({ message: 'Internal server error' })
  }
}
