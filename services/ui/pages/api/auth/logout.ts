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
      await prisma.systemSettings.upsert({
        where: { key: 'monitoring_active' },
        update: {
          value: 'false',
          lastUpdated: new Date()
        },
        create: {
          key: 'monitoring_active',
          value: 'false',
          lastUpdated: new Date()
        }
      });
    } catch (monitoringError) {
      console.error('Failed to reset monitoring state:', monitoringError);
      // Continue with logout even if resetting monitoring fails
    }

    // Clear all possible authentication cookies to ensure session is terminated
    const cookieOptions = 'Path=/; HttpOnly; SameSite=Strict; Max-Age=0';
    res.setHeader('Set-Cookie', [
      `token=; ${cookieOptions}`,
      `session=; ${cookieOptions}`,
      `auth=; ${cookieOptions}`
    ]);

    // Add cache control headers to prevent browsers from caching the response
    res.setHeader('Cache-Control', 'no-store, no-cache, must-revalidate, proxy-revalidate');
    res.setHeader('Pragma', 'no-cache');
    res.setHeader('Expires', '0');

    return res.status(200).json({ message: 'Logged out successfully' });
  } catch (error) {
    console.error('Logout error:', error);
    return res.status(500).json({ message: 'Internal server error' });
  }
}
