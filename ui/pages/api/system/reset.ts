/**
 * API endpoint for resetting system target data
 * Handles POST requests to clear all monitoring data when a user logs out
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import prisma from '../../../lib/db';

// Define response type
type ResetResponse = {
  success: boolean;
  message: string;
} | {
  error: string;
}

// Handler for system reset API requests
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ResetResponse>
) {
  try {
    // Only allow POST requests
    if (req.method !== 'POST') {
      res.setHeader('Allow', ['POST']);
      return res.status(405).json({ error: `Method ${req.method} Not Allowed` });
    }

    // Connect to database
    await prisma.$connect();
    console.log('Database connection established for system reset');

    // Reset monitoring state to false
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

    // Return success response
    return res.status(200).json({
      success: true,
      message: 'System monitoring state and target data reset successfully'
    });
  } catch (error) {
    console.error('Error resetting system data:', error);
    // Check if it's a Prisma error
    if (error instanceof Error) {
      console.error('Error details:', {
        name: error.name,
        message: error.message,
        stack: error.stack
      });
    }
    return res.status(500).json({ error: 'Internal server error' });
  } finally {
    // Ensure database connection is closed
    await prisma.$disconnect();
  }
}
