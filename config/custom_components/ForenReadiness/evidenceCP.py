from homeassistant.helpers.typing import HomeAssistantType

from .const import DEVICE_PROFILE, LAN_PROFILE, PLATFORM_PROFILE


class EvidenceCP:
    def __init__(self):
        self.profiles = None
        self.cloud_evidence_store = {}
        self.lan_evidence_store = {}
        self.device_evidence_store = {}

    def potential_source_identification(self, profiles):
        # TODO: Given device lists, we need to identify all evidence sources.
        # Temporarily, given a device, we classify source of evidence into three parts: cloud, device, LAN
        # Since all devices are identified in DeviceSetup, all devices in profiles are what we focused.
        self.profiles = profiles
        return 0

    async def async_evidence_storage_configuration(self, hass, profiles):
        # In order to avoid storage naming conflicts, for the key of forensic evidence storage, we add FORENSIC_EVIDENCE_PREFIX="fe_" in advance.
        # For example, if we want to store logs from smartthings platform, the key of smartthings evidence storage is "fe_smartthings"
        for platform_item in profiles[PLATFORM_PROFILE]
        # TODO: Configure evidence storage for each device
        return 1

    def register_cloud_evidence_collection(profiles):
        # TODO: Collect cloud evidence
        return 1

    def register_lan_evidence_collection():
        # TODO: Collect LAN evidence
        return 1

    def register_device_evidence_collection():
        # TODO Collect device evidence
        return 1
