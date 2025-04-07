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

        // Añadir información sobre la existencia de certificados
        // Esto se utiliza por la UI para determinar si el servidor tiene una configuración
        // Nota: En un entorno real, esto debería ser determinado por el backend
        try {
            // Verificar si existe el endpoint auxiliar para detectar certificados
            const certCheckResponse = await fetch(`${VPN_API_URL}/api/vpn/has-certificates`, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                }
            });

            if (certCheckResponse.ok) {
                const certData = await certCheckResponse.json();
                data.hasCertificates = certData.hasCertificates;
            } else {
                // Si el endpoint no existe, asumimos que hay certificados si el servidor está en ejecución
                data.hasCertificates = data.status === 'running';
            }
        } catch (certError) {
            console.warn('Error checking certificates status:', certError);
            // En caso de error, asumimos que el estado depende de si el servidor está en ejecución
            data.hasCertificates = data.status === 'running';
        }

        // Return the proxied response with the additional information
        res.status(response.status).json(data);
    } catch (error) {
        console.error('VPN Status Proxy error:', error);

        res.status(500).json({
            success: false,
            status: 'unknown',
            uptime: 0,
            connected_clients: 0,
            hasCertificates: false,
            message: 'Failed to connect to VPN server',
            error: error instanceof Error ? error.message : String(error)
        });
    }
}
