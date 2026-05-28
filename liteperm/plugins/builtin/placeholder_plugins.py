"""Future plugin slots exposed through the discovery layer."""

from __future__ import annotations

from liteperm.plugins.base import TransformationContext, TransformationPlugin


class _PlaceholderPlugin(TransformationPlugin):
    plugin_name = "placeholder"
    plugin_description = "Placeholder"
    plugin_family = "future"

    def name(self) -> str:
        return self.plugin_name

    def description(self) -> str:
        return self.plugin_description

    def calculate(self, context: TransformationContext):
        raise NotImplementedError(f"{self.plugin_name} has not been implemented yet.")

    def validate(self, context: TransformationContext) -> list[str]:
        return [f"{self.plugin_name} is a reserved future plugin slot."]

    def metadata(self) -> dict[str, object]:
        return {
            "display_name": self.plugin_name.replace("_", " ").title(),
            "validation_status": "planned",
            "assumptions": "Interface only; no calculation is available yet.",
            "implemented": False,
            "family": self.plugin_family,
        }


class PatchSensorPlugin(_PlaceholderPlugin):
    plugin_name = "patch_sensor"
    plugin_description = "Reserved slot for patch-antenna inverse sensing models."
    plugin_family = "patch antenna"


class CSRRPlugin(_PlaceholderPlugin):
    plugin_name = "csrr"
    plugin_description = "Reserved slot for complementary split-ring resonator sensing models."
    plugin_family = "csrr"


class MicrostripResonatorPlugin(_PlaceholderPlugin):
    plugin_name = "microstrip_resonator"
    plugin_description = "Reserved slot for microstrip resonator inverse models."
    plugin_family = "microstrip"


class ImplantSensorPlugin(_PlaceholderPlugin):
    plugin_name = "implant_sensor"
    plugin_description = "Reserved slot for implantable and biomedical RF sensor models."
    plugin_family = "biomedical"


class CustomMLPlugin(_PlaceholderPlugin):
    plugin_name = "custom_ml"
    plugin_description = "Reserved slot for future learned inverse models or hybrid surrogates."
    plugin_family = "machine learning"
