#ifndef VOLK_H_
#define VOLK_H_

#include <vulkan/vulkan.h>

#ifdef __cplusplus
extern "C" {
#endif

VkResult volkInitialize(void);
void volkInitializeCustom(PFN_vkGetInstanceProcAddr handler);
uint32_t volkGetInstanceVersion(void);
void volkLoadInstance(VkInstance instance);
void volkLoadInstanceOnly(VkInstance instance);
void volkLoadDevice(VkDevice device);

#ifdef __cplusplus
}
#endif

#endif
