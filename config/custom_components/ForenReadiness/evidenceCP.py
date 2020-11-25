from homeassistant.core import callback
from homeassistant.helpers.event import TrackStates, async_track_state_change_filtered
from homeassistant.helpers.typing import HomeAssistantType

from .const import (
    DEVICE_PROFILE,
    FORENSIC_STORAGE_PREFIX,
    LAN_PROFILE,
    PLATFORM_POLL_PUSH,
    PLATFORM_PROFILE,
    STORAGE_VERSION,
)


class EvidenceCP:
    def __init__(self, profiles):
        self.profiles = profiles
        self.cloud_evidence_store = {}
        self.lan_evidence_store = {}
        self.device_evidence_store = {}

    async def async_evidence_storage_configuration(self, hass):
        """
        Create Storage object for each OOFI.
        For each OOFI in profiles, we create a Store object for it, and store the object into corresponding store list
        Also, in order to avoid storage naming conflicts, for each id of OOFI, we add FORENSIC_EVIDENCE_PREFIX at the beginning as the storage key. For example, "fe_hue"
        """
        # Create Store objects of OOFIs in platform categories. There are three parts from platforms: poll/push device logs, Automation logs and Connector logs
        for platform_name, platform_profile in self.profiles[PLATFORM_PROFILE].items():
            self.cloud_evidence_store[platform_name] = {}
            platform_poll_push_storage_key = (
                FORENSIC_STORAGE_PREFIX + PLATFORM_POLL_PUSH + platform_name
            )
            # Create the poll/push device log storage objects for current platform
            platform_poll_push_storage = hass.helpers.storage.Store(
                STORAGE_VERSION, platform_poll_push_storage_key
            )
            # Add poll/push device log storage objects
            self.cloud_evidence_store[platform_name][
                PLATFORM_POLL_PUSH
            ] = platform_poll_push_storage
            # TODO: Add automation storage objects for each platform
            # TODO: Add Connector storage objects for each platform

        # Create Store objects of OOFIs in device categories
        for device_id, device_profile in self.profiles[DEVICE_PROFILE].items():
            device_storage_key = FORENSIC_STORAGE_PREFIX + device_id
            device_storage = hass.helpers.storage.Store(
                STORAGE_VERSION, device_storage_key
            )
            self.device_evidence_store[device_id] = device_storage

        # Create Store objects of OOFIs in LAN categories
        for lan_component_id, lan_component_profile in self.profiles[
            LAN_PROFILE
        ].items():
            lan_component_storage_key = FORENSIC_STORAGE_PREFIX + lan_component_id
            lan_component_storage = hass.helpers.storage.Store(
                STORAGE_VERSION, lan_component_storage_key
            )
            self.lan_evidence_store[lan_component_id] = lan_component_storage
        # TODO: Configure evidence storage for each device
        return 1

    async def async_register_evidence_collection(self, hass):
        """
        Central function for register evidence from Cloud, LAN and Device
        """
        await self.async_register_cloud_evidence_collection(hass)
        self.register_lan_evidence_collection()
        self.register_device_evidence_collection()

    async def async_register_cloud_evidence_collection(self, hass):
        """
        Register Cloud Evidence Collection Service. We collect poll/push device logs, automation logs and collector logs
        For poll/push logs: We track logs for each device entity from Home Assistant
        """

        @callback
        def handle_state_change(event):
            print(event)
            return 1

        entity_id_list = set()
        # Build entity_id_list to listen to events for these devices
        for device_id, device_profile in self.profiles[DEVICE_PROFILE].items():
            for entity_registry in device_profile.entity_entries:
                entity_id_list.add(entity_registry.entity_id)
        # Register listener
        print(entity_id_list)
        async_track_state_change_filtered(
            hass,
            TrackStates(False, entities=entity_id_list, domains=set()),
            handle_state_change,
        )
        # TODO: Then, for each platform, collect SmartApp/Automation logs
        # TODO: Finally, collect Platform Connector logs
        return 1

    def register_lan_evidence_collection(self):
        # TODO: Collect LAN evidence
        return 1

    def register_device_evidence_collection(self):
        # TODO Collect device evidence
        return 1
