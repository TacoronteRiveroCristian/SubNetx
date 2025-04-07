/**
 * Database Initialization Script
 * This script creates the database tables and initial admin user if they don't exist
 */

import { PrismaClient } from '@prisma/client'
import { hash } from 'bcryptjs'

const prisma = new PrismaClient()

async function initDatabase() {
  try {
    // Check if admin user already exists
    const admin = await prisma.user.findUnique({
      where: { username: 'admin' }
    })

    // If no admin exists, create default admin
    if (!admin) {
      const defaultUsername = 'admin'
      const defaultPassword = 'admin'
      const hashedPassword = await hash(defaultPassword, 12)

      const user = await prisma.user.create({
        data: {
          username: defaultUsername,
          password: hashedPassword,
          role: 'admin'
        }
      })

      console.log('Default admin user created:', user)
    } else {
      console.log('Admin user already exists')
    }

    console.log('Database initialization completed')
  } catch (error) {
    console.error('Error initializing database:', error)
    process.exit(1)
  } finally {
    await prisma.$disconnect()
  }
}

// Run initialization
initDatabase()
