"""
conftest.py — Configuração global do pytest para os testes do Ontrackchain.

Adiciona ao sys.path os caminhos dos pacotes Python internos do monorepo,
permitindo que os testes importem módulos sem instalar os pacotes via pip.
"""
import sys
from pathlib import Path

# Raiz do workspace (ontrackchain/)
_ONTRACKCHAIN_ROOT = Path(__file__).parent.parent

# Scripts de orquestração de janela de staging
sys.path.insert(0, str(_ONTRACKCHAIN_ROOT / "scripts"))

# Pacote de agentes (ontrackchain_agents)
sys.path.insert(0, str(_ONTRACKCHAIN_ROOT / "packages" / "agents" / "src"))

# Auth service (auth_service)
sys.path.insert(0, str(_ONTRACKCHAIN_ROOT / "apps" / "auth-service" / "src"))
