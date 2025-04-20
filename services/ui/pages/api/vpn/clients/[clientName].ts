/**
 * API proxy endpoint for operations on a specific VPN client
 *
 * Este endpoint maneja operaciones sobre un cliente específico:
 * - GET: Obtiene información de un cliente
 * - DELETE: Elimina un cliente
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import { serverConfig, buildServerUrl } from '../../../../lib/apiConfig';

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
) {
    // Verificar método válido
    if (req.method !== 'GET' && req.method !== 'DELETE') {
        return res.status(405).json({ success: false, error: 'Method not allowed' });
    }

    // Obtener el nombre del cliente de la URL
    const { clientName } = req.query;

    if (!clientName || Array.isArray(clientName)) {
        return res.status(400).json({
            success: false,
            error: 'Client name is required and must be a string'
        });
    }

    try {
        // Build the target URL
        const targetUrl = buildServerUrl(serverConfig.vpnEndpoints.clientByName(clientName));
        console.log(`Proxying VPN client request (${req.method}) to: ${targetUrl}`);

        // Forward the request to the target
        const response = await fetch(targetUrl, {
            method: req.method,
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
        console.error(`VPN Client ${req.method} Proxy error:`, error);

        const errorMessage = req.method === 'GET'
            ? `Failed to get VPN client ${clientName}`
            : `Failed to delete VPN client ${clientName}`;

        res.status(500).json({
            success: false,
            message: errorMessage,
            error: error instanceof Error ? error.message : String(error)
        });
    }
}
