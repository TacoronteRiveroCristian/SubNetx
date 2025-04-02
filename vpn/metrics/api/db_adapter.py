"""
Adaptador de Base de Datos para la API de SubNetx VPN.

Este módulo actúa como intermediario entre la API y la base de datos,
proporcionando métodos específicos para las necesidades de los endpoints
de la API y realizando las transformaciones de datos necesarias.

:module: vpn.metrics.api.db_adapter
:author: SubNetx Team
:version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from vpn.metrics.collector.classes.databases.database_ping import PingDatabase

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricsDBAdapter:
    """
    Adaptador para la base de datos de métricas.

    Proporciona métodos específicos para los endpoints de la API
    de métricas, realizando las transformaciones necesarias en los datos.

    :param db: Instancia de la base de datos
    :type db: PingDatabase
    """

    def __init__(self, db: PingDatabase):
        """
        Inicializar el adaptador con una instancia de base de datos.

        :param db: Instancia de la base de datos
        :type db: PingDatabase
        """
        self.db = db

    def get_targets(self) -> List[Dict[str, Any]]:
        """
        Obtener todos los objetivos de monitoreo.

        :return: Lista de objetivos
        :rtype: List[Dict[str, Any]]
        """
        targets = self.db.get_all_targets()
        return targets

    def get_target(self, target_id: int) -> Dict[str, Any]:
        """
        Obtener información de un objetivo específico.

        :param target_id: ID del objetivo
        :type target_id: int
        :return: Información del objetivo
        :rtype: Dict[str, Any]
        """
        targets = self.db.get_all_targets()
        for target in targets:
            if target['id'] == target_id:
                return target
        return {}

    def get_latest_metric(self, target_id: int) -> Dict[str, Any]:
        """
        Obtener la métrica más reciente para un objetivo.

        :param target_id: ID del objetivo
        :type target_id: int
        :return: Última métrica
        :rtype: Dict[str, Any]
        """
        # Obtener el objetivo
        target = self.get_target(target_id)
        if not target:
            return {}

        # Obtener la última métrica
        latest = self.db.get_latest_ping(target['target'])
        if not latest:
            return {}

        # Adaptar el formato para la API
        return self._format_metric(latest, target_id)

    def get_metrics_paginated(
        self,
        target_id: int,
        page: int = 1,
        size: int = 20,
        hours: Optional[int] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Obtener métricas paginadas para un objetivo.

        :param target_id: ID del objetivo
        :type target_id: int
        :param page: Número de página
        :type page: int
        :param size: Tamaño de página
        :type size: int
        :param hours: Filtrar por horas hacia atrás
        :type hours: Optional[int]
        :return: Tupla con lista de métricas y conteo total
        :rtype: Tuple[List[Dict[str, Any]], int]
        """
        # Obtener el objetivo
        target = self.get_target(target_id)
        if not target:
            return [], 0

        # Calcular offset
        offset = (page - 1) * size

        # Obtener historial
        metrics = self.db.get_ping_history(target['target'], limit=size, offset=offset)

        # Filtrar por horas si es necesario
        if hours is not None:
            cutoff = datetime.now() - timedelta(hours=hours)
            metrics = [
                m for m in metrics
                if datetime.fromisoformat(m['timestamp']) > cutoff
            ]

        # Adaptar el formato para la API
        formatted_metrics = [self._format_metric(m, target_id) for m in metrics]

        # Calcular total (aproximado)
        # NOTA: Esta es una aproximación simple ya que no tenemos un método de conteo directo
        total = len(metrics) + offset
        if len(metrics) >= size:
            total += size  # Asumimos que hay al menos una página más

        return formatted_metrics, total

    def get_connection_quality(self, target_id: int, hours: int = 24) -> Dict[str, Any]:
        """
        Obtener análisis de calidad de conexión.

        :param target_id: ID del objetivo
        :type target_id: int
        :param hours: Período de análisis en horas
        :type hours: int
        :return: Resumen de calidad de conexión
        :rtype: Dict[str, Any]
        """
        # Obtener el objetivo
        target = self.get_target(target_id)
        if not target:
            return {}

        # Obtener resumen
        summary = self.db.get_connection_quality_summary(target['target'], hours=hours)

        # Añadir información adicional
        summary['target'] = target['target']
        summary['period_hours'] = hours

        return summary

    def _format_metric(self, metric: Dict[str, Any], target_id: int) -> Dict[str, Any]:
        """
        Formatear una métrica para la API.

        :param metric: Métrica de la base de datos
        :type metric: Dict[str, Any]
        :param target_id: ID del objetivo
        :type target_id: int
        :return: Métrica formateada
        :rtype: Dict[str, Any]
        """
        # Mapear los campos para coincidir con el esquema de la API
        icmp_details = []
        for detail in metric.get('icmp_details', []):
            icmp_details.append({
                'sequence': detail.get('sequence', 0),
                'response_time_ms': detail.get('response_time_ms', 0.0)
            })

        tls_info = None
        tls_data = metric.get('tls_info')
        if tls_data:
            tls_info = {
                'cert_expiry': tls_data.get('cert_expiry'),
                'issuer': tls_data.get('issuer'),
                'subject': tls_data.get('subject'),
                'version': tls_data.get('version'),
                'cipher': tls_data.get('cipher')
            }

        return {
            'id': metric.get('id', 0),
            'target_id': target_id,
            'timestamp': metric.get('timestamp', ''),
            'status': metric.get('status', 'unknown'),
            'connection_quality': metric.get('connection_quality', 'unknown'),
            'packet_loss_percent': metric.get('packet_loss_percent', 0.0),
            'min_rtt': metric.get('min_rtt', metric.get('rtt_stats', {}).get('min_ms', 0.0)),
            'avg_rtt': metric.get('avg_rtt', metric.get('rtt_stats', {}).get('avg_ms', 0.0)),
            'max_rtt': metric.get('max_rtt', metric.get('rtt_stats', {}).get('max_ms', 0.0)),
            'mdev_rtt': metric.get('mdev_rtt', metric.get('rtt_stats', {}).get('mdev_ms', 0.0)),
            'packets_transmitted': metric.get('packets_transmitted', metric.get('packets', {}).get('transmitted', 0)),
            'packets_received': metric.get('packets_received', metric.get('packets', {}).get('received', 0)),
            'icmp_details': icmp_details,
            'tls_info': tls_info
        }
