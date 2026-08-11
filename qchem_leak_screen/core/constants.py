# SPDX-FileCopyrightText: 2026 Pedro Sordo Martínez <amurlaniakea@gmail.com>
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Constantes fisicas para los umbrales del filtro.

NO estan tuneadas para que los fixtures pasen; se derivan de fisica documentada:
- TOL_KOOPMANS: Koopmans es una aproximacion; el DFT real desvia ~1-2 eV del
  valor de -epsilon_HOMO. 2.0 eV cubre esa desviacion sin marcar falsos positivos.
- DIP_MAX: las moleculas conocidas tienen dipolo <~15 D. 50 D es un limite de
  sanidad que solo una "halucionacion" superaria.
"""

from __future__ import annotations

TOL_KOOPMANS_EV: float = 2.0
DIP_MAX_DEBYE: float = 50.0
