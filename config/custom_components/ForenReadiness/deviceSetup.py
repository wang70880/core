import logging

import homeassistant
from homeassistant.config_entries import ConfigEntries as ce
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.entity_registry import (
    async_entries_for_device,
    async_get_registry,
)
from homeassistant.helpers.event import TrackStates, async_track_state_change_filtered

from .const import (
    DEVICE_PROFILE,
    LAN_PROFILE,
    PLATFORM_PROFILE,
    ROUTER_IP,
    ROUTER_PASSWD,
    ROUTER_USERNAME,
    SUPPORTED_CONFIGURATION_CATEGORY,
    SUPPORTED_DEVICE_TYPE,
    SUPPORTED_PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)


class DeviceSetup:
    def __init__(self):
        self.filter = Filter()
        self.unsub_device_tracker = None
        self.profiles = {}

    # Get the user preference to configure forensic filter list
    # Currently our forensic system only support platform and device_type filter category
    def build_filter(self, platforms, device_types):
        self.filter.build_platform_filter(platforms)
        self.filter.build_device_type_filter(device_types)
        return 1

    # An initial device list is constructed when the system starts
    # Note that only devices which are not filtered out can be added to the list
    async def async_initialize_device_list(self, hass: HomeAssistant):
        device_registry = await dr.async_get_registry(hass)
        config_entries = hass.config_entries
        entity_registry = await async_get_registry(hass)
        # Load every stored device entry, and build a DeviceProfile instance. Then store all DeviceProfile in self.profiles["device_profile"]
        self.profiles[DEVICE_PROFILE] = {}
        for temp_device in device_registry.devices.values():
            # Use the filter to filter out devices which users don't care
            if await self.filter.async_check_device(hass, temp_device):
                # Get Entities
                entity_registry_entries = async_entries_for_device(
                    entity_registry, temp_device.id
                )
                # Get config_Entries
                device_config_entries = []
                for entity_registry_entity in entity_registry_entries:
                    config_entry_id = entity_registry_entity.config_entry_id
                    device_config_entries.append(
                        config_entries.async_get_entry(config_entry_id)
                    )
                # Build DeviceProfile
                device_profile = DeviceProfile(
                    temp_device, entity_registry_entries, device_config_entries
                )
                self.profiles[DEVICE_PROFILE][device_profile.id] = device_profile

        # Build RouterProfile and store in self.profiles["router_profile"]
        # TODO: Here we hardcoded router information. A user configuration step is needed.
        self.profiles[LAN_PROFILE] = RouterProfile(
            ROUTER_IP, ROUTER_USERNAME, ROUTER_PASSWD
        )
        # Build PlatformProfile and store in self.profiles["platform_profile"]
        # TODO: Here we hardcoded platform information. A user configuration step is needed
        self.profiles[PLATFORM_PROFILE] = {}
        for platform_name in self.filter.platforms:
            self.profiles[PLATFORM_PROFILE][platform_name] = PlatformProfile(
                platform_name
            )
        return 1

    @callback
    def handle_state_change(self, event):
        """callback function to handle state change event"""
        print(f"Event comes: {event}")
        # TODO: This is the callback function which is used by async_dynamic_maintain_device_list()
        return 1

    # Dynamic maintaince of device lists by subscribing to device events
    async def async_dynamic_maintain_device_list(self, hass: HomeAssistant):
        """Register Listener for device change event"""
        # TODO: This is not the core functionality of forensics. Implement it later.
        self.unsub_device_tracker = async_track_state_change_filtered(
            hass,
            TrackStates(True, entities=set(), domains={"hue"}),
            self.handle_state_change,
        ).async_remove
        return 1


class Filter:
    def __init__(self):
        self.platforms = []
        self.device_types = []

    def build_platform_filter(self, platforms):
        if "all" in platforms:
            self.platforms = [x for x in SUPPORTED_PLATFORMS if x != "all"]
        else:
            self.platforms = platforms
        return 1

    def build_device_type_filter(self, device_types):
        if "all" in device_types:
            self.device_types = [x for x in SUPPORTED_DEVICE_TYPE if x != "all"]
        else:
            self.device_types = device_types
        return 1

    async def async_check_device(self, hass: HomeAssistant, device_entry: DeviceEntry):
        """Check whether a device is in user's preference list."""
        CHECK_PLATFORM = 1
        CHECK_DEVICE_TYPE = 2
        flag = 0
        # Load Platform and Device_Type information from config_entries
        for config_entry_id in device_entry.config_entries:
            config_entry = hass.config_entries.async_get_entry(config_entry_id)
            # Check Platform
            if config_entry.domain in self.platforms:
                flag = flag | CHECK_PLATFORM
            # TODO: Check Device Type. This is an additional feature, and leave for future development.
            flag = flag | CHECK_DEVICE_TYPE
            # if config_entry.domain == "hue":
            #    print(
            #        "******* id:{}, name:{}, manufacturer:{}, model:{}, sw_version:{}, via_device_id:{}, \
            #   area_id:{}, entry_type:{}, connections:{}, identifiers{}, config_entries:{} ******".format(
            #            device_entry.id,
            #            device_entry.name,
            #            device_entry.manufacturer,
            #            device_entry.model,
            #            device_entry.sw_version,
            #            device_entry.via_device_id,
            #            device_entry.area_id,
            #            device_entry.entry_type,
            #            device_entry.connections,
            #            device_entry.identifiers,
            #            device_entry.config_entries,
            #        )
            #    )
            #    print("config_entry:{}".format(config_entry.as_dict()))
        if flag == CHECK_PLATFORM | CHECK_DEVICE_TYPE:
            return 1
        return 0


class PlatformProfile:
    def __init__(self, name):
        self.name = name


class RouterProfile:
    def __init__(self, ip, username, passwd):
        self.ip = ip
        self.username = username
        self.passwd = passwd


class DeviceProfile:
    def __init__(
        self, device_entry: DeviceEntry, entity_entries, device_config_entries
    ):
        self.id = device_entry.id
        self.name = device_entry.name
        self.connections = device_entry.connections
        self.identifiers = device_entry.identifiers
        self.manufacturer = device_entry.manufacturer
        self.model = device_entry.model
        self.sw_version = device_entry.sw_version
        self.via_device_id = device_entry.via_device_id
        self.area_id = device_entry.area_id
        self.entry_type = device_entry.entry_type

        # Platform Information is in config_entries. For example, hue connection or smartthings connection
        # print method: as_dict()
        self.device_config_entries = device_config_entries
        # Entity Entries store information about the entity. A device might be composed of multiple entities
        self.entity_entries = entity_entries
        # Device Entry stores information about the device
        self.device_entry = device_entry
        # Leave for adding new information which home assistant didn't record