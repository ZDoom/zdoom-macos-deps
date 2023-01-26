#include <vulkan/vulkan_core.h>

int main()
{
    uint32_t version;
    AEDI_EXPECT(vkEnumerateInstanceVersion(&version) == VK_SUCCESS);
    AEDI_EXPECT(version >= VK_API_VERSION_1_1);

    uint32_t count;
    AEDI_EXPECT(vkEnumerateInstanceLayerProperties(&count, nullptr) == VK_SUCCESS);
    AEDI_EXPECT(vkEnumerateInstanceExtensionProperties(nullptr, &count, nullptr) == VK_SUCCESS);

    return 0;
}
