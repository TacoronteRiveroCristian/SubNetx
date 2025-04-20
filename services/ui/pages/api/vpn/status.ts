/**
 * API proxy endpoint for VPN status requests
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import { buildServerUrl, serverConfig } from '../../../lib/apiConfig';

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
        const targetUrl = buildServerUrl(serverConfig.vpnEndpoints.status);
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

        // Standardize response format for UI consumption
        let responseData = {
            success: data.success || false,
            message: data.message || 'Status retrieved',
            details: data.details || {},
            status: 'unknown' as 'running' | 'stopped' | 'unknown',
            hasCertificates: false
        };

        // Extract status from different possible API response formats
        if (data.details && data.details.status) {
            // New API format
            const serverState = data.details.status.state;
            responseData.status = (serverState === 'running') ? 'running' : 'stopped';
        } else if (data.status) {
            // Old API format
            responseData.status = data.status;
        }

        // Try to get certificate information
        try {
            // Verificar si existe el endpoint auxiliar para detectar certificados
            const certCheckUrl = `${serverConfig.vpnApiBaseUrl}/has-certificates`;
            const certCheckResponse = await fetch(certCheckUrl, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                }
            });

            if (certCheckResponse.ok) {
                const certData = await certCheckResponse.json();
                responseData.hasCertificates = certData.hasCertificates;
            } else {
                // Si el endpoint no existe, asumimos que hay certificados si el servidor está en ejecución
                responseData.hasCertificates = responseData.status === 'running';
            }
        } catch (certError) {
            console.warn('Error checking certificates status:', certError);
            // En caso de error, asumimos que el estado depende de si el servidor está en ejecución
            responseData.hasCertificates = responseData.status === 'running';
        }

        // Return the standardized response
        res.status(response.status).json(responseData);
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
