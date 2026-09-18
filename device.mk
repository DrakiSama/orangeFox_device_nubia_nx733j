#
# Copyright (C) 2025 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/nubia/NX733J

$(call inherit-product, $(SRC_TARGET_DIR)/product/base.mk)

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)

$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota/compression_with_xor.mk)

$(call inherit-product, $(SRC_TARGET_DIR)/product/emulated_storage.mk)

$(call inherit-product, vendor/recovery/config/common.mk)

BOARD_SHIPPING_API_LEVEL := 35
PRODUCT_SHIPPING_API_LEVEL := 35

PRODUCT_USE_DYNAMIC_PARTITIONS := true

PRODUCT_APEX_SYSTEM_SERVER_JARS += com.android.crashrecovery:service-crashrecovery

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

PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/recovery/root/init.recovery.qcom.rc:$(TARGET_COPY_OUT_RECOVERY)/root/init.recovery.qcom.rc \
    $(DEVICE_PATH)/recovery/root/init.recovery.usb.rc:$(TARGET_COPY_OUT_RECOVERY)/root/init.recovery.usb.rc \
    $(DEVICE_PATH)/recovery/root/vendor/bin/mount_vendor_dlkm.sh:$(TARGET_COPY_OUT_RECOVERY)/root/vendor/bin/mount_vendor_dlkm.sh \
    $(DEVICE_PATH)/recovery/root/vendor/bin/set_branding.sh:$(TARGET_COPY_OUT_RECOVERY)/root/vendor/bin/set_branding.sh
