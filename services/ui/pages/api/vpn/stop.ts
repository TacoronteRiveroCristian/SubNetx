/**
 * API proxy endpoint for stopping the VPN server
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import { buildServerUrl, serverConfig } from '../../../lib/apiConfig';

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
) {
    // Only allow POST requests
    if (req.method !== 'POST') {
        return res.status(405).json({ success: false, error: 'Method not allowed' });
    }

    try {
        // Build the target URL
        const targetUrl = buildServerUrl(serverConfig.vpnEndpoints.stop);
        console.log(`Proxying VPN stop request to: ${targetUrl}`);

        // Forward the request to the target
        const response = await fetch(targetUrl, {
            method: 'POST',
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
        console.error('VPN Stop Proxy error:', error);

        res.status(500).json({
            success: false,
            message: 'Failed to stop VPN server',
            error: error instanceof Error ? error.message : String(error)
        });
    }
}
