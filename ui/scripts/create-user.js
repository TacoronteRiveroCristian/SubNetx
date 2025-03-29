/**
 * User Setup Script
 * Creates a new user with specified credentials
 */

const { createAdmin } = require('../lib/auth')

async function setupUser() {
  try {
    // Crear usuario con las credenciales deseadas
    await createAdmin('user', 'password123')
    console.log('Usuario creado exitosamente')
  } catch (error) {
    console.error('Error creando usuario:', error)
  }
}

setupUser()
