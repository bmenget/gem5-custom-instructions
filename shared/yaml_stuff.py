import shared.paths as paths

baseFields = {
    "name": str,
    "description": str,
    "opclass": str,
    "auto_manage": bool
}

opclassFields = {
    "latency": int,
    "fu_count": int,
    "pipelined": bool
}

architectureInfo = {
    "riscv-instructions": {
        "registry": paths.STATE_DIR / "riscv-registry.json",
        "templates": paths.TEMPLATE_DIR / "riscv-configs.json"
    }
#     "x86": {                                          future support for different archs
#         "registry": paths.STATE_DIR / "x86-registry.json",
#     },
#     "arm": {
#         "registry": paths.STATE_DIR / "arm-registry.json",
#     }
}

