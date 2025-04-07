/**
 * API proxy endpoint to forward requests to the VPN container
 */

import type { NextApiRequest, NextApiResponse } from 'next';

// The internal URL to the VPN container (only accessible from server-side)
const VPN_API_URL = 'http://subnetx_vpn:8000';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  try {
    // Get the path from the query
    const path = req.query.path || '';

    // Build the target URL
    const targetUrl = `${VPN_API_URL}/api/metrics/${Array.isArray(path) ? path.join('/') : path}`;
    console.log(`Proxying request to: ${targetUrl}`);
    console.log(`Request method: ${req.method}`);
    console.log(`Request headers:`, req.headers);

    // Forward the request to the target
    const response = await fetch(targetUrl, {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      // Include body for POST, PUT, PATCH
      ...(req.method !== 'GET' && req.method !== 'HEAD' && {
        body: JSON.stringify(req.body)
      }),
    });

    // Log the response status and headers
    console.log(`Response status: ${response.status}`);
    console.log(`Response headers:`, Object.fromEntries(response.headers.entries()));

    // Get the response data
    const data = await response.json();
    console.log(`Response data sample:`, JSON.stringify(data).substring(0, 200) + '...');

    // Return the proxied response
    res.status(response.status).json(data);
  } catch (error) {
    console.error('Proxy error:', error);
    res.status(500).json({ error: 'Failed to proxy request', details: error instanceof Error ? error.message : String(error) });
  }
}
