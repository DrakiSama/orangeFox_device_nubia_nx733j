#
# Copyright (C) 2025 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/nubia/NX733J

$(call inherit-product, $(SRC_TARGET_DIR)/product/base.mk)

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)

# Android 12.1 has compression.mk; newer compression_with_xor.mk only adds
# this property. Preserve the device declaration without inventing a dependency.
$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota/compression.mk)
PRODUCT_VENDOR_PROPERTIES += ro.virtual_ab.compression.xor.enabled=true

$(call inherit-product, $(SRC_TARGET_DIR)/product/emulated_storage.mk)

# fox_12.1 official sync retains vendor/twrp for product rules and installs
# OrangeFox hooks in build/make plus vendor/recovery/OrangeFox_A12.sh.
$(call inherit-product, vendor/twrp/config/common.mk)

BOARD_SHIPPING_API_LEVEL := 35
PRODUCT_SHIPPING_API_LEVEL := 35

PRODUCT_USE_DYNAMIC_PARTITIONS := true


PRODUCT_PROPERTY_OVERRIDES += persist.sys.fuse.passthrough.enable=true

PRODUCT_EXTRA_RECOVERY_KEYS += \
    $(DEVICE_PATH)/security/releasekey

PRODUCT_SOONG_NAMESPACES += \
    $(DEVICE_PATH)

# Recovery fstab is separate from the stock Android first-stage fstab.
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/recovery.fstab:$(TARGET_COPY_OUT_RECOVERY)/root/system/etc/recovery.fstab \
    $(DEVICE_PATH)/fstab.qcom:$(TARGET_VENDOR_RAMDISK_OUT)/first_stage_ramdisk/fstab.qcom \
    $(DEVICE_PATH)/recovery/root/vendor/etc/vintf/manifest.xml:$(TARGET_COPY_OUT_RECOVERY)/root/vendor/etc/vintf/manifest.xml

PRODUCT_PACKAGES += fastbootd

# Init scripts. Los scripts se instalan en /sbin deliberadamente: montar el
# /vendor stock durante el arranque no debe ocultarlos.
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/recovery/root/init.recovery.qcom.rc:$(TARGET_COPY_OUT_RECOVERY)/root/init.recovery.qcom.rc \
    $(DEVICE_PATH)/recovery/root/init.recovery.usb.rc:$(TARGET_COPY_OUT_RECOVERY)/root/init.recovery.usb.rc \
    $(DEVICE_PATH)/recovery/root/vendor/bin/mount_vendor_dlkm.sh:$(TARGET_COPY_OUT_RECOVERY)/root/sbin/mount_vendor_dlkm.sh

# Recovery servicemanager reads HAL declarations from system/etc/vintf.
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/recovery/root/system/etc/vintf/manifest/nx733j-hals.xml:$(TARGET_COPY_OUT_RECOVERY)/root/system/etc/vintf/manifest/nx733j-hals.xml

# Hardware initialization validated on NX733J in recovery RAM (ADSP para batería).
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/recovery/root/vendor/bin/init_nx733j_hardware.sh:$(TARGET_COPY_OUT_RECOVERY)/root/sbin/init_nx733j_hardware.sh \
    $(DEVICE_PATH)/recovery/root/vendor/firmware/haptic_ram.bin:$(TARGET_COPY_OUT_RECOVERY)/root/vendor/firmware/haptic_ram.bin

# Read-only support report, available before data decryption.
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/recovery/root/vendor/bin/nx733j-diagnose.sh:$(TARGET_COPY_OUT_RECOVERY)/root/sbin/nx733j-diagnose.sh

# Independent bounded CPU sensor discovery; does not wait for ADSP.
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/recovery/root/vendor/bin/init_nx733j_cpu.sh:$(TARGET_COPY_OUT_RECOVERY)/root/sbin/init_nx733j_cpu.sh
