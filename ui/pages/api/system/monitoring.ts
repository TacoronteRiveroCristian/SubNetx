/**
 * API endpoint for managing system monitoring state
 * Handles GET and POST requests to read/update monitoring status
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import prisma from '../../../lib/db';

// Define response type
type MonitoringResponse = {
  isMonitoring: boolean;
} | {
  error: string;
}

// Handler for monitoring state API requests
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<MonitoringResponse>
) {
  try {
    // Verify database connection
    await prisma.$connect();
    console.log('Database connection established');

    if (req.method === 'GET') {
      // Get current monitoring state
      const setting = await prisma.systemSettings.findUnique({
        where: { key: 'monitoring_active' }
      });
      console.log('Current monitoring state:', setting);

      // Retornar el estado del monitoreo (convertir 'true'/'false' string a boolean)
      return res.status(200).json({ isMonitoring: setting?.value === 'true' });
    }
    else if (req.method === 'POST') {
      // Update monitoring state
      const { isMonitoring } = req.body;
      console.log('Updating monitoring state to:', isMonitoring);

      if (typeof isMonitoring !== 'boolean') {
        return res.status(400).json({ error: 'isMonitoring must be a boolean value' });
      }

      // Convertir boolean a string para guardarlo
      const valueStr = String(isMonitoring);

      try {
        // Intentar actualizar el registro existente
        const setting = await prisma.systemSettings.update({
          where: { key: 'monitoring_active' },
          data: {
            value: valueStr,
            lastUpdated: new Date()
          }
        });
        console.log('Updated monitoring state:', setting);

        return res.status(200).json({ isMonitoring: setting.value === 'true' });
      } catch (updateError) {
        // Si el registro no existe, crearlo
        console.log('Record not found, creating new record');
        const setting = await prisma.systemSettings.create({
          data: {
            key: 'monitoring_active',
            value: valueStr,
            lastUpdated: new Date()
          }
        });
        console.log('Created monitoring state:', setting);

        return res.status(200).json({ isMonitoring: setting.value === 'true' });
      }
    }

    // Handle unsupported methods
    res.setHeader('Allow', ['GET', 'POST']);
    return res.status(405).json({ error: `Method ${req.method} Not Allowed` });
  } catch (error) {
    console.error('Error handling monitoring state:', error);
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
