from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .deviceSetup import DeviceSetup
from .evidenceCP import EvidenceCP
from .incidentConfig import IncidentConfig

deviceSetuper = None
evidenceCollector = None


async def async_setup(hass, config):
    global deviceSetuper
    global evidenceCollector
    deviceSetuper = DeviceSetup()
    evidenceCollector = EvidenceCP()
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    global deviceSetuper
    global evidenceCollector
    """Readiness Configuration Module"""
    platforms = entry.data["platform"]
    device_types = entry.data["device_type"]
    """ Device Setup Module """
    # Load filter preferences to Device Setup Module
    deviceSetuper.build_filter(platforms, device_types)
    # Construct initial device list
    await deviceSetuper.async_initialize_device_list(hass)
    # TODO: Register dynamic maintaince service of device lists.
    await deviceSetuper.async_dynamic_maintain_device_list(hass)
    """Evidence Collection and Preservation Module"""
    # TODO: Build potential source lists for each device
    evidenceCollector.potential_source_identification(deviceSetuper.profiles)
    # Configure Evidence Storage
    await evidenceCollector.async_evidence_storage_configuration(
        hass, deviceSetuper.profiles
    )
    return True