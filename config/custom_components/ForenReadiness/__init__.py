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
    evidenceCollector = EvidenceCP(deviceSetuper.profiles)
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
    await deviceSetuper.async_initialize_source_list(hass)
    # TODO: Register dynamic maintaince service of device lists.
    await deviceSetuper.async_dynamic_maintain_device_list(hass)
    deviceSetuper.debug_profiles()
    """Evidence Collection and Preservation Module"""
    # Configure Evidence Storage
    await evidenceCollector.async_evidence_storage_configuration(hass)
    # Register Evidence Collection Service and Start Collecting
    await evidenceCollector.async_register_evidence_collection(hass)
    return True