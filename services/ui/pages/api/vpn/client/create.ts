/**
 * API proxy endpoint for creating a new VPN client
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import { buildServerUrl, serverConfig } from '../../../../lib/apiConfig';

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
) {
    // Only allow POST requests
    if (req.method !== 'POST') {
        return res.status(405).json({ success: false, error: 'Method not allowed' });
    }

    try {
        // Get client data from request body
        const clientData = req.body;

        // Build the target URL
        const targetUrl = buildServerUrl(serverConfig.vpnEndpoints.clients);
        console.log(`Proxying VPN client creation request to: ${targetUrl}`);

        // Forward the request to the target
        const response = await fetch(targetUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify(clientData)
        });

        // Log the response status
        console.log(`Response status: ${response.status}`);

        // Get the response data
        const data = await response.json();
        console.log(`Response data:`, data);

        // Return the proxied response
        res.status(response.status).json(data);
    } catch (error) {
        console.error('VPN Client Creation Proxy error:', error);

        res.status(500).json({
            success: false,
            message: 'Failed to create VPN client',
            error: error instanceof Error ? error.message : String(error)
        });
    }
}
