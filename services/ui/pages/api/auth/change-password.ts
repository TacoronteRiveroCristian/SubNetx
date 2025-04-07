/**
 * Password Change API endpoint
 * This file handles password change requests and updates the admin password in the database
 */

import { hash } from 'bcryptjs'
import { NextApiRequest, NextApiResponse } from 'next'
import { verifyAdminCredentials } from '../../../lib/auth'
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
    const { username, currentPassword, newPassword } = req.body

    // Check if using default credentials
    const isDefaultCredentials = username === 'admin' && currentPassword === 'admin'

    // Verify current credentials
    const isValid = await verifyAdminCredentials(username, currentPassword)

    if (!isValid) {
      return res.status(401).json({ message: 'Current password is incorrect' })
    }

    // Hash the new password
    const hashedPassword = await hash(newPassword, 12)

    // Update the password in the database and set role to admin if using default credentials
    await prisma.user.update({
      where: { username },
      data: {
        password: hashedPassword,
        ...(isDefaultCredentials && { role: 'admin' }) // Set role to admin only if changing from default credentials
      }
    })

    return res.status(200).json({
      message: 'Password updated successfully',
      isAdmin: isDefaultCredentials // Let the frontend know if the user was promoted to admin
    })
  } catch (error) {
    console.error('Password change error:', error)
    return res.status(500).json({ message: 'Internal server error' })
  }
}
