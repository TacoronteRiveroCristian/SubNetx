/**
 * API proxy endpoint to forward VPN management requests to the VPN container
 * This is a catch-all route that will handle all VPN API endpoints
 */

import type { NextApiRequest, NextApiResponse } from 'next';

// The internal URL to the VPN container (only accessible from server-side)
const VPN_API_URL = 'http://subnetx_vpn:8000';

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
) {
    try {
        // Get the path from the query params (will be an array with catch-all route)
        const { path } = req.query;

        if (!path || !Array.isArray(path)) {
            return res.status(400).json({
                success: false,
                error: 'Invalid path'
            });
        }

        // Build the target URL - note we use /api/vpn/ prefix required by the backend
        const targetUrl = `${VPN_API_URL}/api/vpn/${path.join('/')}`;
        console.log(`Proxying VPN request to: ${targetUrl}`);
        console.log(`Request method: ${req.method}`);
        console.log(`Request body:`, req.body);
        console.log(`Path parts:`, path);

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

        // Log the response status
        console.log(`Response status: ${response.status}`);

        // Get the response data
        const data = await response.json();
        console.log(`Response data:`, data);

        // Return the proxied response
        res.status(response.status).json(data);
    } catch (error) {
        console.error('VPN Proxy error:', error);
        console.error('Error details:', error instanceof Error ? {
            name: error.name,
            message: error.message,
            stack: error.stack
        } : String(error));

        res.status(500).json({
            success: false,
            error: 'Failed to proxy VPN request',
            details: error instanceof Error ? error.message : String(error)
        });
    }
}
