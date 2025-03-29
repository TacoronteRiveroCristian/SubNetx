/**
 * Token verification API endpoint
 * This file handles JWT token verification and returns user data
 */

import { NextApiRequest, NextApiResponse } from 'next';
import { verifyToken } from '../../../lib/jwt';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // Only allow GET requests
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    // Get token from cookie
    const token = req.cookies.token;

    if (!token) {
      return res.status(401).json({ message: 'No token provided' });
    }

    // Verify token
    const decoded = verifyToken(token);

    if (!decoded) {
      return res.status(401).json({ message: 'Invalid token' });
    }

    // Return user data
    return res.status(200).json({
      user: {
        id: decoded.userId,
        username: decoded.username,
        role: decoded.role
      }
    });
  } catch (error) {
    console.error('Token verification error:', error);
    return res.status(401).json({ message: 'Authentication failed' });
  }
}
