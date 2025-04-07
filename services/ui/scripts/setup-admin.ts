/**
 * Admin Setup Script
 * This script creates the initial admin user in the database
 */

import { createAdmin } from '../lib/auth'

async function setupInitialAdmin() {
  try {
    // Create initial admin with username 'admin' and password 'admin'
    await createAdmin('admin', 'admin')
    console.log('Initial admin user created successfully')
  } catch (error) {
    console.error('Error creating initial admin:', error)
  }
}

// Run the setup
setupInitialAdmin()
