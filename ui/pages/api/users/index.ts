/**
 * Users API endpoint
 * This file handles fetching and creating users
 */

import { hash } from 'bcryptjs'
import { NextApiRequest, NextApiResponse } from 'next'
import prisma from '../../../lib/db'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === 'GET') {
    try {
      // Fetch all users
      const users = await prisma.admin.findMany({
        select: {
          id: true,
          username: true,
          createdAt: true,
          updatedAt: true,
        },
        orderBy: {
          createdAt: 'desc',
        },
      })

      return res.status(200).json(users)
    } catch (error) {
      console.error('Error fetching users:', error)
      return res.status(500).json({ message: 'Internal server error' })
    }
  } else if (req.method === 'POST') {
    try {
      const { username, password } = req.body

      // Validate input
      if (!username || !password) {
        return res.status(400).json({ message: 'Username and password are required' })
      }

      // Check if username already exists
      const existingUser = await prisma.admin.findFirst({
        where: { username }
      })

      if (existingUser) {
        return res.status(400).json({ message: 'Username already exists' })
      }

      // Hash password and create user
      const hashedPassword = await hash(password, 12)
      const newUser = await prisma.admin.create({
        data: {
          username,
          password: hashedPassword
        },
        select: {
          id: true,
          username: true,
          createdAt: true,
          updatedAt: true
        }
      })

      return res.status(201).json(newUser)
    } catch (error) {
      console.error('Error creating user:', error)
      return res.status(500).json({ message: 'Internal server error' })
    }
  }

  return res.status(405).json({ message: 'Method not allowed' })
}
