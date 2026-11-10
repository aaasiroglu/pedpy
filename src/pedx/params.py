"""Physical parameters shared by the batch pipeline and the on-demand service (single source of truth)."""

PARAMS = {
    "roof_utilization": {"value": 0.26, "low": 0.26, "high": 0.50,
                         "source": "Gagnon et al. (2016) NREL/TP-6A20-65298 (26% of small-building roof area suitable); upper bound until G2 calibration with Demirel et al. (2025)"},
    "module_efficiency": {"value": 0.20, "low": 0.17, "high": 0.25,
                          "source": "Fraunhofer ISE Photovoltaics Report: commercial Si modules ~17% → just under 25% over the last decade"},
}
