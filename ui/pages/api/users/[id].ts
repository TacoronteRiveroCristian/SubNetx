/**
 * User API endpoint
 * This file handles updating and deleting users
 */

import { hash } from 'bcryptjs'
import { NextApiRequest, NextApiResponse } from 'next'
import prisma from '../../../lib/db'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === 'PUT') {
    try {
      const { id } = req.query
      const { username, newPassword } = req.body

      // Validate input
      if (!username) {
        return res.status(400).json({ message: 'Username is required' })
      }

      // Check if username is already taken by another user
      const existingUser = await prisma.admin.findFirst({
        where: {
          username,
          NOT: {
            id: parseInt(id as string),
          },
        },
      })

      if (existingUser) {
        return res.status(400).json({ message: 'Username is already taken' })
      }

      // Prepare update data
      const updateData: any = {
        username,
      }

      // If new password is provided, hash it
      if (newPassword) {
        updateData.password = await hash(newPassword, 12)
      }

      // Update user
      const updatedUser = await prisma.admin.update({
        where: {
          id: parseInt(id as string),
        },
        data: updateData,
        select: {
          id: true,
          username: true,
          createdAt: true,
          updatedAt: true,
        },
      })

      return res.status(200).json(updatedUser)
    } catch (error) {
      console.error('Error updating user:', error)
      return res.status(500).json({ message: 'Internal server error' })
    }
  } else if (req.method === 'DELETE') {
    try {
      const { id } = req.query

      // Check if user exists
      const user = await prisma.admin.findUnique({
        where: { id: parseInt(id as string) }
      })

      if (!user) {
        return res.status(404).json({ message: 'User not found' })
      }

      // Count total users
      const totalUsers = await prisma.admin.count()

      // Don't allow deleting the last user
      if (totalUsers <= 1) {
        return res.status(400).json({ message: 'Cannot delete the last user' })
      }

      // Delete user
      await prisma.admin.delete({
        where: { id: parseInt(id as string) }
      })

      return res.status(200).json({ message: 'User deleted successfully' })
    } catch (error) {
      console.error('Error deleting user:', error)
      return res.status(500).json({ message: 'Internal server error' })
    }
  }

  return res.status(405).json({ message: 'Method not allowed' })
}
