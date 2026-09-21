# Qualcomm HIDL BootControl adapter

Source: https://github.com/LineageOS/android_hardware_qcom_bootctrl/tree/846dfb0652cc142e1783cbe085783527bbe4a190

BootControl.cpp/.h come from 1.2/impl; libboot_control_qti.h from
1.1/libboot_control_qti. Sources are unchanged. Link against the shipped
libboot_control_qti.so, whose exported function signatures match this header.
This supplies the passthrough implementation missing from the Android 12.1
boot-hal-1-2 service. Do not substitute AOSP libboot_control: this device uses
Qualcomm GPT slot metadata, not the generic bootloader_control block in misc.
Full compilation and physical slot/snapshot validation remain required.
