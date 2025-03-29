/**
 * Database Initialization Script
 * This script creates the database tables and initial admin user if they don't exist
 */

import { PrismaClient } from '@prisma/client'
import { createAdmin } from '../lib/auth'

const prisma = new PrismaClient()

async function initDatabase() {
  try {
    // Check if admin exists
    const admin = await prisma.admin.findUnique({
      where: { username: 'admin' }
    })

    // If no admin exists, create default admin
    if (!admin) {
      await createAdmin('admin', 'admin')
      console.log('Default admin user created successfully')
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
