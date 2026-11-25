"""Capa de casos de uso (orquestación de escenarios multiagente)."""

from use_cases.cu01_gestion_congestion import ejecutar_cu01
from use_cases.cu02_regulacion_frecuencias import ejecutar_cu02

__all__ = ["ejecutar_cu01", "ejecutar_cu02"]
