#define VK_USE_PLATFORM_MACOS_MVK
#define VK_USE_PLATFORM_METAL_EXT

#include "volk.h"

#ifdef __cplusplus
extern "C" {
#endif

VkResult volkInitialize(void)
{
	return VK_SUCCESS;
}

uint32_t volkGetInstanceVersion(void)
{
	uint32_t apiVersion = 0;
	if (vkEnumerateInstanceVersion(&apiVersion) == VK_SUCCESS)
		return apiVersion;
	return 0;
}

void volkLoadInstance(VkInstance instance)
{
}

void volkLoadDevice(VkDevice device)
{
}

VkResult vkCreateAccelerationStructureKHR(
	VkDevice                                    device,
	const VkAccelerationStructureCreateInfoKHR* pCreateInfo,
	const VkAllocationCallbacks*                pAllocator,
	VkAccelerationStructureKHR*                 pAccelerationStructure)
{
	return VK_ERROR_UNKNOWN;
}

void vkDestroyAccelerationStructureKHR(
	VkDevice                                    device,
	VkAccelerationStructureKHR                  accelerationStructure,
	const VkAllocationCallbacks*                pAllocator)
{
}

void vkCmdBuildAccelerationStructuresKHR(
	VkCommandBuffer                             commandBuffer,
	uint32_t                                    infoCount,
	const VkAccelerationStructureBuildGeometryInfoKHR* pInfos,
	const VkAccelerationStructureBuildRangeInfoKHR* const* ppBuildRangeInfos)
{
}

void vkGetAccelerationStructureBuildSizesKHR(
	VkDevice                                    device,
	VkAccelerationStructureBuildTypeKHR         buildType,
	const VkAccelerationStructureBuildGeometryInfoKHR* pBuildInfo,
	const uint32_t*                             pMaxPrimitiveCounts,
	VkAccelerationStructureBuildSizesInfoKHR*   pSizeInfo)
{
}

VkDeviceAddress vkGetAccelerationStructureDeviceAddressKHR(
	VkDevice                                    device,
	const VkAccelerationStructureDeviceAddressInfoKHR* pInfo)
{
	return 0;
}

#ifdef __cplusplus
}
#endif
