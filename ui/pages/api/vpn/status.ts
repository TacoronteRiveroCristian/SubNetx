/**
 * API proxy endpoint for VPN status requests
 */

import type { NextApiRequest, NextApiResponse } from 'next';

// The internal URL to the VPN container (only accessible from server-side)
const VPN_API_URL = 'http://subnetx_vpn:8000';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // Only allow GET requests
  if (req.method !== 'GET') {
    return res.status(405).json({ success: false, error: 'Method not allowed' });
  }

  try {
    // Build the target URL
    const targetUrl = `${VPN_API_URL}/api/vpn/status`;
    console.log(`Proxying VPN status request to: ${targetUrl}`);

    // Forward the request to the target
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      }
    });

    // Log the response status
    console.log(`Response status: ${response.status}`);

    // Get the response data
    const data = await response.json();
    console.log(`Response data:`, data);

    // Return the proxied response
    res.status(response.status).json(data);
  } catch (error) {
    console.error('VPN Status Proxy error:', error);

    res.status(500).json({
      success: false,
      status: 'unknown',
      uptime: 0,
      connected_clients: 0,
      message: 'Failed to connect to VPN server',
      error: error instanceof Error ? error.message : String(error)
    });
  }
}
