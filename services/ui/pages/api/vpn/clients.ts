/**
 * API proxy endpoint for VPN clients operations
 *
 * Este endpoint maneja tanto listado de clientes (GET) como
 * creación de nuevos clientes (POST)
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import { serverConfig, buildServerUrl } from '../../../lib/apiConfig';

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
) {
    // Verificar método válido
    if (req.method !== 'GET' && req.method !== 'POST') {
        return res.status(405).json({ success: false, error: 'Method not allowed' });
    }

    try {
        // Build the target URL
        const targetUrl = buildServerUrl(serverConfig.vpnEndpoints.clients);
        console.log(`Proxying VPN clients request (${req.method}) to: ${targetUrl}`);

        // Preparar opciones de fetch según el método
        const fetchOptions: RequestInit = {
            method: req.method,
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        };

        // Si es POST, añadir cuerpo de la petición
        if (req.method === 'POST') {
            fetchOptions.body = JSON.stringify(req.body);
        }

        // Forward the request to the target
        const response = await fetch(targetUrl, fetchOptions);

        // Log the response status
        console.log(`Response status: ${response.status}`);

        // Get the response data
        const data = await response.json();
        console.log(`Response data:`, data);

        // Return the proxied response
        res.status(response.status).json(data);
    } catch (error) {
        console.error(`VPN Clients ${req.method} Proxy error:`, error);

        const errorMessage = req.method === 'GET'
            ? 'Failed to list VPN clients'
            : 'Failed to create VPN client';

        res.status(500).json({
            success: false,
            message: errorMessage,
            error: error instanceof Error ? error.message : String(error)
        });
    }
}
