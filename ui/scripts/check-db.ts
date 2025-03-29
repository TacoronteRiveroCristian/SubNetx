/**
 * Database Check Script
 * This script checks the contents of the admin table
 */

import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

async function checkDatabase() {
  try {
    // Get all admins
    const admins = await prisma.admin.findMany()

    console.log('Contenido de la tabla Admin:')
    console.log(JSON.stringify(admins, null, 2))
  } catch (error) {
    console.error('Error checking database:', error)
  } finally {
    await prisma.$disconnect()
  }
}

// Run the check
checkDatabase()
