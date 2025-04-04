/**
 * API proxy endpoint for VPN reset operation
 *
 * Este archivo maneja la eliminación de toda la configuración del servidor VPN,
 * actuando como un proxy entre la UI y el contenedor del servidor VPN.
 */

import type { NextApiRequest, NextApiResponse } from 'next';

// La URL interna al contenedor VPN (solo accesible del lado del servidor)
const VPN_API_URL = 'http://subnetx_vpn:8000';

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
) {
    // Solo permitir solicitudes POST
    if (req.method !== 'POST') {
        return res.status(405).json({ success: false, error: 'Method not allowed' });
    }

    try {
        // Construir la URL destino
        const targetUrl = `${VPN_API_URL}/api/vpn/reset`;
        console.log(`Enviando solicitud de reset al VPN: ${targetUrl}`);

        // Enviar la solicitud al destino
        const response = await fetch(targetUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        });

        // Registrar el estado de la respuesta
        console.log(`Estado de respuesta: ${response.status}`);

        // Obtener los datos de la respuesta
        const data = await response.json();
        console.log(`Datos de respuesta:`, data);

        // Devolver la respuesta proxeada
        res.status(response.status).json(data);
    } catch (error) {
        console.error('Error en proxy VPN Reset:', error);

        res.status(500).json({
            success: false,
            message: 'Failed to delete VPN server configuration',
            error: error instanceof Error ? error.message : String(error)
        });
    }
}
