/**
 * Logout API endpoint
 * This file handles user logout by clearing the authentication cookie
 */

import { NextApiRequest, NextApiResponse } from 'next';
import prisma from '../../../lib/db';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    // Reset monitoring state to false when a user logs out
    try {
      await prisma.systemSettings.update({
        where: { key: 'monitoring_active' },
        data: {
          value: 'false',
          lastUpdated: new Date()
        }
      });
    } catch (monitoringError) {
      console.error('Failed to reset monitoring state:', monitoringError);
      // Continue with logout even if resetting monitoring fails
    }

    // Clear the authentication cookie
    res.setHeader('Set-Cookie', 'token=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0');

    return res.status(200).json({ message: 'Logged out successfully' });
  } catch (error) {
    console.error('Logout error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
}
