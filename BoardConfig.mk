#
# Copyright (C) 2025 The Android Open Source Project
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/nubia/NX733J

ALLOW_MISSING_DEPENDENCIES := true

BUILD_BROKEN_DUP_RULES := true
BUILD_BROKEN_ELF_PREBUILT_PRODUCT_COPY_FILES := true
BUILD_BROKEN_NINJA_USES_ENV_VARS += RTIC_MPGEN
BUILD_BROKEN_PLUGIN_VALIDATION := soong-libaosprecovery_defaults soong-libguitwrp_defaults soong-libminuitwrp_defaults soong-vold_defaults

# Architecture
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_ABI2 :=
TARGET_CPU_VARIANT := generic
TARGET_CPU_VARIANT_RUNTIME := oryon

ENABLE_CPUSETS := true
ENABLE_SCHEDBOOST := true

# Bootloader
PRODUCT_PLATFORM := sun
TARGET_BOOTLOADER_BOARD_NAME := sun
TARGET_NO_BOOTLOADER := true
TARGET_USES_UEFI := true

# Platform
TARGET_BOARD_PLATFORM := sun
TARGET_BOARD_PLATFORM_GPU := qcom-adreno830
QCOM_BOARD_PLATFORMS += sun

# Kernel
TARGET_KERNEL_ARCH := arm64
TARGET_KERNEL_HEADER_ARCH := arm64
BOARD_KERNEL_IMAGE_NAME := Image
BOARD_BOOT_HEADER_VERSION := 4
BOARD_KERNEL_PAGESIZE := 4096

TARGET_KERNEL_CLANG_COMPILE := true
TARGET_KERNEL_CLANG_VERSION := r510928
TARGET_KERNEL_ADDITIONAL_FLAGS := LLVM=1 LLVM_IAS=1

ifneq ($(wildcard kernel/nubia/nx733j/msm-kernel/Makefile),)
TARGET_KERNEL_SOURCE := kernel/nubia/nx733j/msm-kernel
TARGET_KERNEL_CONFIG := gki_defconfig
TARGET_KERNEL_CONFIG += vendor/sun_perf.config
else
TARGET_PREBUILT_KERNEL := $(DEVICE_PATH)/prebuilt/kernel
endif

BOARD_PREBUILT_DTBOIMAGE := $(DEVICE_PATH)/prebuilt/dtbo.img
BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOT_HEADER_VERSION)
BOARD_MKBOOTIMG_ARGS += --pagesize $(BOARD_KERNEL_PAGESIZE)

BOARD_RAMDISK_USE_LZ4 := true

# A/B
BOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE := true
AB_OTA_UPDATER := true
AB_OTA_PARTITIONS += \
    boot \
    init_boot \
    vendor_boot \
    dtbo \
    vbmeta \
    vbmeta_system \
    odm \
    product \
    system \
    system_ext \
    system_dlkm \
    vendor \
    vendor_dlkm

BOARD_AVB_ENABLE := true
BOARD_AVB_ALGORITHM := SHA256_RSA4096
BOARD_AVB_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_ROLLBACK_INDEX_LOCATION := 1
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --flags 3

# Partitions — tamaños verificados con "fastboot getvar" en NX733J real (PQ84A01)
BOARD_BOOTIMAGE_PARTITION_SIZE        := 100663296   # 0x06000000
BOARD_INIT_BOOT_IMAGE_PARTITION_SIZE  := 8388608     # 0x00800000
BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE := 100663296   # 0x06000000
BOARD_DTBOIMG_PARTITION_SIZE          := 25165824    # 0x01800000
BOARD_RECOVERYIMAGE_PARTITION_SIZE    := 104857600   # 0x06400000

BOARD_PROPERTY_OVERRIDES_SPLIT_ENABLED := true

# Las particiones lógicas stock del NX733J son EROFS (verificado en lpdump/fstab stock)
TARGET_COPY_OUT_VENDOR := vendor
TARGET_COPY_OUT_ODM := odm
BOARD_ODMIMAGE_FILE_SYSTEM_TYPE := erofs
BOARD_USES_VENDOR_DLKMIMAGE := true
TARGET_COPY_OUT_VENDOR_DLKM := vendor_dlkm
BOARD_VENDOR_DLKMIMAGE_FILE_SYSTEM_TYPE := erofs

# Dynamic Partitions — super verificado: 0x400000000 = 17179869184 bytes (16 GB)
# Grupo real del dispositivo: qti_dynamic_partitions (NO existe odm_dlkm)
BOARD_SUPER_PARTITION_SIZE := 17179869184
BOARD_SUPER_PARTITION_GROUPS := qti_dynamic_partitions
# Reservar ~4 MB para metadata del super
BOARD_QTI_DYNAMIC_PARTITIONS_SIZE := 17175674880
BOARD_QTI_DYNAMIC_PARTITIONS_PARTITION_LIST := \
    system \
    system_ext \
    product \
    vendor \
    vendor_dlkm \
    odm \
    system_dlkm

TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_USE_F2FS := true

TARGET_SYSTEM_PROP += $(DEVICE_PATH)/system.prop

BOARD_HAS_LARGE_FILESYSTEM := true
TARGET_RECOVERY_PIXEL_FORMAT := RGBX_8888
TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/recovery.fstab

# Crypto — FBE completo para Android 15/16
TW_INCLUDE_CRYPTO := true
TW_INCLUDE_CRYPTO_FBE := true
TW_INCLUDE_FBE_METADATA_DECRYPT := true
BOARD_USES_QCOM_FBE_DECRYPTION := true
BOARD_USES_METADATA_PARTITION := true
TW_USE_FSCRYPT_POLICY := 2

PLATFORM_VERSION := 99.87.36
PLATFORM_VERSION_LAST_STABLE := $(PLATFORM_VERSION)
PLATFORM_SECURITY_PATCH := 2099-12-31
VENDOR_SECURITY_PATCH := $(PLATFORM_SECURITY_PATCH)
BOOT_SECURITY_PATCH := $(PLATFORM_SECURITY_PATCH)

# Tools
TW_INCLUDE_7ZA := true
TW_INCLUDE_REPACKTOOLS := true
TW_INCLUDE_RESETPROP := true
TW_INCLUDE_LIBRESETPROP := true
TW_ENABLE_ALL_PARTITION_TOOLS := true

TW_ENABLE_FS_COMPRESSION := false

# Debug
TARGET_USES_LOGD := true
TWRP_INCLUDE_LOGCAT := true
TARGET_RECOVERY_DEVICE_MODULES += debuggerd
RECOVERY_BINARY_SOURCE_FILES += $(TARGET_OUT_EXECUTABLES)/debuggerd
TARGET_RECOVERY_DEVICE_MODULES += strace
RECOVERY_BINARY_SOURCE_FILES += $(TARGET_OUT_EXECUTABLES)/strace

TW_INCLUDE_FASTBOOTD := true

# OrangeFox / TWRP Configuration
TW_THEME := portrait_hdpi
TW_FRAMERATE := 120
RECOVERY_SDCARD_ON_DATA := true
TARGET_RECOVERY_QCOM_RTC_FIX := true
TW_EXCLUDE_DEFAULT_USB_INIT := true
TW_INCLUDE_NTFS_3G := true
TW_NO_EXFAT_FUSE := true
TW_NO_SCREEN_BLANK := true
TW_USE_DMCTL := true
TW_USE_TOOLBOX := true
TARGET_USES_MKE2FS := true
TW_INCLUDE_FUSE_EXFAT := true
TW_INCLUDE_FUSE_NTFS := true
TW_INPUT_BLACKLIST := "hbtp_vm:goodix_fp:nubia_tgk_aw_sar0_ch0:nubia_tgk_aw_sar1_ch0:sun-mtp-snd-card Headset Jack:sun-mtp-snd-card Button Jack"
TW_BRIGHTNESS_PATH := "/sys/class/backlight/panel0-backlight/brightness"
TW_MAX_BRIGHTNESS := 2047
TW_DEFAULT_BRIGHTNESS := 250
TW_DEFAULT_LANGUAGE := es-ES
TW_EXTRA_LANGUAGES := true
TW_FONT_SIZE := 20
TW_EXCLUDE_APEX := true
TW_HAS_EDL_MODE := true
# Direct Awinic sysfs haptics (duration_aw/activate_aw); no vendor vibrator HAL
# (vendor.qti.vibrator causaba lag táctil en este dispositivo).
TW_NO_HAPTICS := false
TW_USE_SERIALNO_PROPERTY_FOR_DEVICE_ID := true
TW_SCREEN_BLANK_ON_BOOT := true
# Módulos de vendor requeridos para display, touch y battery (Nubia/ZTE sun platform)
# Verificados contra kernel source NX733J V(15) y vendor_boot stock
TW_LOAD_VENDOR_MODULES := "msm.ko drm_display_helper.ko panel_event_notifier.ko dispcc-sun.ko gpucc-sun.ko zte_tpd.ko aw9620x.ko"
TW_LOAD_VENDOR_MODULES_EXCLUDE_GKI := true
TW_LOAD_PREBUILT_MODULES_AT_FIRST := true
TW_CUSTOM_CPU_TEMP_PATH := "/tmp/nx733j-cpu-temp"
TW_BACKUP_EXCLUSIONS := /data/fonts
TW_HAS_USB_OTG := true
TW_CUSTOM_BATTERY_PATH := "/sys/class/power_supply/battery"
TW_DEVICE_VERSION := by Draki local
-include $(DEVICE_PATH)/build-version.mk

# OrangeFox Specific Flags
OF_SCREEN_H := 2400
OF_STATUS_H := 100
OF_STATUS_INDENT_LEFT := 48
OF_STATUS_INDENT_RIGHT := 48
OF_CLOCK_POS := 0
OF_ALLOW_DISABLE_NAVBAR := 0
OF_HIDE_NOTCH := 1
OF_USE_LOCKSCREEN_BUTTON := 0

OF_AB_DEVICE_WITH_RECOVERY_PARTITION := 1

OF_MAINTAINER := Draki
OF_DEFAULT_TIMEZONE := CET-1;CEST,M3.5.0,M10.5.0

OF_SKIP_FBE_DECRYPTION := 0
OF_NO_TREBLE_COMPATIBILITY_CHECK := 0
OF_NO_MIUI_OTA_VENDOR_BACKUP := 1
OF_DISABLE_MIUI_OTA_BY_DEFAULT := 1
# orangefox.mk adds the C++ string quotes. Keep the Make value unquoted.
OF_QUICK_BACKUP_LIST := /boot;/data;/system;/vendor;
OF_DISABLE_EXTRA_ABOUT_PAGE := 0
OF_USE_MAGISKBOOT := 1
OF_USE_MAGISKBOOT_FOR_ALL_PATCHES := 1


OF_ENABLE_LPTOOLS := 1
OF_SUPPORT_ALL_BLOCK_OTA_UPDATES := 0
OF_FIX_DECRYPTION_ON_DATA_MEDIA := 0
OF_USE_LZMA_COMPRESSION := 0
OF_USE_LZ4_COMPRESSION := 1
