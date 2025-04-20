/**
 * API proxy endpoint for setting up the VPN server
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
        // Get configuration from request body
        const config = req.body;

        // Build the target URL
        const targetUrl = buildServerUrl(serverConfig.vpnEndpoints.setup);
        console.log(`Proxying VPN setup request to: ${targetUrl}`);

        // Forward the request to the target
        const response = await fetch(targetUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify(config)
        });

        // Log the response status
        console.log(`Response status: ${response.status}`);

        // Get the response data
        const data = await response.json();
        console.log(`Response data:`, data);

        // Return the proxied response
        res.status(response.status).json(data);
    } catch (error) {
        console.error('VPN Setup Proxy error:', error);

        res.status(500).json({
            success: false,
            message: 'Failed to setup VPN server',
            error: error instanceof Error ? error.message : String(error)
        });
    }
}
