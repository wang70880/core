import logging

import homeassistant
from homeassistant.config_entries import ConfigEntries as ce
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceEntry, DeviceRegistry
from homeassistant.helpers.entity_registry import (
    async_entries_for_device,
    async_get_registry,
)
from homeassistant.helpers.event import TrackStates, async_track_state_change_filtered

from .const import (
    ALL,
    CHECK_DEVICE_TYPE,
    CHECK_PLATFORM,
    DEVICE_PROFILE,
    LAN_PROFILE,
    PLATFORM_PROFILE,
    ROUTER,
    ROUTER_IP,
    ROUTER_PASSWD,
    ROUTER_USERNAME,
    SUPPORTED_CONFIGURATION_CATEGORY,
    SUPPORTED_DEVICE_TYPE,
    SUPPORTED_PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)


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
        # Platform id which devices belongs to
        self.platform_name = ""


class PlatformProfile:
    def __init__(self, name):
        self.name = name
        self.devices = {}
        self.connection = {}
        self.apps = {}

    def add_device(self, deviceProfile):
        """
        Record that the deviceProfile belongs to current platform
        """
        self.devices[deviceProfile.device_entry.id] = deviceProfile


class RouterProfile:
    def __init__(self, ip, username, passwd):
        self.ip = ip
        self.username = username
        self.passwd = passwd


class Filter:
    def __init__(self):
        self.platforms = []
        self.device_types = []

    def build_platform_filter(self, platforms):
        """
        Build filter lists of platform
        """
        if ALL in platforms:
            self.platforms = [x for x in SUPPORTED_PLATFORMS if x != "all"]
        else:
            self.platforms = platforms
        return 1

    def build_device_type_filter(self, device_types):
        """
        Build filter lists of device type
        """
        if ALL in device_types:
            self.device_types = [x for x in SUPPORTED_DEVICE_TYPE if x != "all"]
        else:
            self.device_types = device_types
        return 1

    def check_platform(self, platform_name):
        """
        Check whether current platform is of user's interest
        """
        if platform_name in self.platforms:
            return CHECK_PLATFORM
        return 0

    async def async_check_device(
        self, hass: HomeAssistant, device_profile: DeviceProfile
    ):
        """
        Check whether current device type is of user's interest.
        Check whether current device's platform is of users' interest.
        """
        flag = 0
        for config_entry in device_profile.device_config_entries:
            # Check if the device belongs to a user-focused platform
            if config_entry.domain in self.platforms:
                flag = flag | CHECK_PLATFORM
                # Modify the DeviceProfile to update platform information
                device_profile.platform_name = config_entry.domain
        # TODO: Implement it to check device type
        flag = flag | CHECK_DEVICE_TYPE
        if flag == CHECK_DEVICE_TYPE | CHECK_PLATFORM:
            return flag
        return 0


class DeviceSetup:
    def __init__(self):
        self.filter = Filter()
        self.unsub_device_tracker = None
        # profiles for objects of forensic interests (OOFI)
        self.profiles = {}

    # Get the user preference to configure forensic filter list
    # Currently our forensic system only support platform and device_type filter category
    def build_filter(self, platforms, device_types):
        self.filter.build_platform_filter(platforms)
        self.filter.build_device_type_filter(device_types)
        return 1

    # Note that only devices which are not filtered out can be added to the list
    async def async_initialize_source_list(self, hass: HomeAssistant):
        """
        This function is used for identifying potential forensic devices.
        As a result, an initial OOFI list is constructed.
        Note that only devices which are not filtered out can be added to the list
        """
        device_registry: DeviceRegistry = await dr.async_get_registry(hass)
        config_entries = hass.config_entries
        entity_registry = await async_get_registry(hass)

        self.profiles[PLATFORM_PROFILE] = {}
        self.profiles[DEVICE_PROFILE] = {}
        self.profiles[LAN_PROFILE] = {}

        # Build PlatformProfile and store in self.profiles["platform_profile"]
        for platform_name in self.filter.platforms:
            # Use the filter to filter out platforms which users don't care
            if self.filter.check_platform(platform_name):
                self.profiles[PLATFORM_PROFILE][platform_name] = PlatformProfile(
                    platform_name
                )

        # Traverse each stored device entry, and build DeviceProfile instance
        for temp_device in device_registry.devices.values():
            # Get Entity registries
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
            # Build DeviceProfile and add it to profiles
            # It contains three parts: DeviceProperties + DeviceEntries + DeviceConfigEntries
            device_profile = DeviceProfile(
                temp_device, entity_registry_entries, device_config_entries
            )
            # Use Filter to check if current device is of user's interest
            if await self.filter.async_check_device(hass, device_profile):
                # Add the deviceProfile to profiles
                self.profiles[DEVICE_PROFILE][
                    device_profile.device_entry.id
                ] = device_profile
                try:
                    # Update PlatformProfile to add this device
                    platform_profile: PlatformProfile = self.profiles[PLATFORM_PROFILE][
                        device_profile.platform_name
                    ]
                    platform_profile.add_device(device_profile)
                except:
                    _LOGGER.error("Cannot find the platform!")
                    return 0

        # Build LANProfile and store in self.profiles["lan_profile"]
        # TODO: Currently there is only router information. Also, the router information is hardcoded.
        self.profiles[LAN_PROFILE][ROUTER] = RouterProfile(
            ROUTER_IP, ROUTER_USERNAME, ROUTER_PASSWD
        )

        return 1

    async def async_dynamic_maintain_device_list(self, hass: HomeAssistant):
        """Register Listener for device change event"""

        @callback
        def handle_state_change(event):
            """ callback function to handle state change event"""
            # TODO: we need to extract device join/leave from the state change event
            return 1

        # TODO: This is not the core functionality of forensics. Implement it later.
        # self.unsub_device_tracker = async_track_state_change_filtered(
        #    hass,
        #    TrackStates(True, entities=set(), domains={"hue"}),
        #    handle_state_change,
        # ).async_remove
        return 1

    def debug_profiles(self):
        print("****** Number for each profile categories ******")
        print(
            "platform_profiles: {}, device_profiles: {}, lan_profiles: {}".format(
                len(self.profiles[PLATFORM_PROFILE]),
                len(self.profiles[DEVICE_PROFILE]),
                len(self.profiles[LAN_PROFILE]),
            )
        )
        print("****** Device Profile Components ******")
        for device_profile_id, device_profile in self.profiles[DEVICE_PROFILE].items():
            print(
                "name: {}, platform: {}".format(
                    device_profile.device_entry.name, device_profile.platform_name
                )
            )
            print(
                "size of entity_entries:{}".format(len(device_profile.entity_entries))
            )
            for entity_entry in device_profile.entity_entries:
                print(
                    "entity_domain: {}, entity_id: {}".format(
                        entity_entry.domain, entity_entry.entity_id
                    )
                )
