/**
 * API proxy endpoint for downloading a VPN client configuration
 */

import type { NextApiRequest, NextApiResponse } from 'next';
import { serverConfig, buildServerUrl } from '../../../../../lib/apiConfig';

export default async function handler(
    req: NextApiRequest,
    res: NextApiResponse
) {
    // Only allow GET requests
    if (req.method !== 'GET') {
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
        // Construir la URL para obtener el cliente primero (necesitamos verificar que existe)
        const clientUrl = buildServerUrl(serverConfig.vpnEndpoints.clientByName(clientName));
        console.log(`Verificando existencia del cliente VPN: ${clientUrl}`);

        // Verificar que el cliente existe
        const clientResponse = await fetch(clientUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            }
        });

        if (!clientResponse.ok) {
            const error = await clientResponse.json();
            return res.status(clientResponse.status).json(error);
        }

        // El cliente existe, ahora obtenemos su configuración
        // Intentamos obtener un endpoint específico para la configuración
        const configUrl = `${serverConfig.vpnApiBaseUrl}/clients/${clientName}/config`;
        console.log(`Obteniendo configuración del cliente desde: ${configUrl}`);

        const configResponse = await fetch(configUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            }
        });

        if (configResponse.ok) {
            const configData = await configResponse.json();

            // Si la API devuelve la configuración en base64
            if (configData.config) {
                return res.status(200).json({
                    success: true,
                    config: configData.config // Ya está en base64
                });
            }
            // Si la API devuelve la configuración en texto plano
            else if (configData.config_text) {
                // Convertir a base64
                const base64Config = Buffer.from(configData.config_text).toString('base64');
                return res.status(200).json({
                    success: true,
                    config: base64Config
                });
            }
            // Si la API devuelve un error específico
            else if (configData.error) {
                return res.status(404).json({
                    success: false,
                    message: configData.error
                });
            }
        }

        // Si el endpoint específico no está disponible o falló,
        // intentamos obtener la configuración desde la respuesta del cliente
        const clientData = await clientResponse.json();

        if (clientData.success && clientData.details && clientData.details.client_config) {
            // Convertir a base64 si no lo está ya
            const configText = clientData.details.client_config;
            const isBase64 = /^[A-Za-z0-9+/=]+$/.test(configText) && configText.length % 4 === 0;

            const base64Config = isBase64
                ? configText
                : Buffer.from(configText).toString('base64');

            return res.status(200).json({
                success: true,
                config: base64Config
            });
        }

        // Si llegamos aquí, no pudimos obtener la configuración
        return res.status(404).json({
            success: false,
            message: `No se encontró la configuración para el cliente ${clientName}`
        });

    } catch (error) {
        console.error('VPN Client Config Download error:', error);

        res.status(500).json({
            success: false,
            message: `Error al obtener la configuración del cliente ${clientName}`,
            error: error instanceof Error ? error.message : String(error)
        });
    }
}
