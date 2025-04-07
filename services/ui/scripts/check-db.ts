/**
 * Database Check Script
 * This script checks the contents of the admin table
 */

import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function checkDatabase() {
  try {
    // Check if any users exist
    const userCount = await prisma.user.count()
    console.log(`Found ${userCount} users in database`)

    // List all users
    const users = await prisma.user.findMany()
    console.log('Users:', users)
  } catch (error) {
    console.error('Error checking database:', error)
  } finally {
    await prisma.$disconnect()
  }
}

// Run the check
checkDatabase()
